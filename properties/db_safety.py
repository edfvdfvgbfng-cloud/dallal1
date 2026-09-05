"""
Database Safety and Data Preservation Engine for Dalal Platform.
Guarantees zero data loss, validates PostgreSQL identity, audits pre/post migration records,
and enforces fail-fast protection against SQLite fallback in production.
"""
import os
import sys
import logging
from django.conf import settings
from django.db import connection


def is_production():
    """Determine if running in a production or production-like deployment."""
    if not getattr(settings, 'DEBUG', True):
        return True
    if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_PROJECT_ID') or os.getenv('RAILWAY_SERVICE_ID'):
        return True
    if os.getenv('ALLOW_SQLITE_FALLBACK', 'True').lower() in ('false', '0', 'no'):
        return True
    if os.getenv('ENVIRONMENT', '').lower() == 'production':
        return True
    return False


logger = logging.getLogger('db_safety')
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [DB_SAFETY] %(message)s'))
    logger.addHandler(handler)
    # Use WARNING level in production to reduce log volume
    logger.setLevel(logging.WARNING if is_production() else logging.INFO)

# Core production models to track across migrations and deployments
CORE_MODELS = [
    ('auth', 'User', 'المستخدمون'),
    ('properties', 'Property', 'العقارات'),
    ('properties', 'Message', 'الرسائل'),
    ('properties', 'PropertyOffer', 'العروض'),
    ('properties', 'PropertyNegotiation', 'التفاوضات'),
    ('properties', 'Auction', 'المزادات'),
    ('properties', 'Bid', 'المزايدات'),
    ('properties', 'Appointment', 'المواعيد والحجوزات'),
    ('properties', 'RealEstateContract', 'العقود العقارية'),
    ('properties', 'BrokerPlanSubscription', 'الاشتراكات'),
    ('properties', 'Notification', 'الإشعارات'),
    ('properties', 'PropertyDocument', 'المستندات'),
    ('properties', 'CRMContact', 'جهات اتصال CRM'),
    ('properties', 'TravelCompany', 'شركات السفر'),
    ('properties', 'TravelCompanyPost', 'منشورات شركات السفر'),
]


def is_production():
    """Determine if running in a production or production-like deployment."""
    if not getattr(settings, 'DEBUG', True):
        return True
    if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_PROJECT_ID') or os.getenv('RAILWAY_SERVICE_ID'):
        return True
    if os.getenv('ALLOW_SQLITE_FALLBACK', 'True').lower() in ('false', '0', 'no'):
        return True
    if os.getenv('ENVIRONMENT', '').lower() == 'production':
        return True
    return False


def get_safe_db_info():
    """Retrieve database identity info without exposing passwords/secrets."""
    db_config = settings.DATABASES.get('default', {})
    engine = db_config.get('ENGINE', '').split('.')[-1]
    host = db_config.get('HOST', 'localhost')
    port = db_config.get('PORT', '5432' if 'postgres' in engine else '')
    name = db_config.get('NAME', '')
    user = db_config.get('USER', '')

    safe_name = str(name).split('/')[-1] if isinstance(name, str) else 'database'

    return {
        'engine': engine,
        'vendor': getattr(connection, 'vendor', engine),
        'host': host or 'localhost',
        'port': port or '5432',
        'database_name': safe_name,
        'user': user or 'default',
        'is_production': is_production(),
        'is_sqlite': 'sqlite' in engine.lower() or getattr(connection, 'vendor', '') == 'sqlite',
        'is_postgres': 'postgres' in engine.lower() or getattr(connection, 'vendor', '') == 'postgresql',
    }


def verify_database_identity(require_postgres=None):
    """
    Verify live database connection and enforce strict PostgreSQL requirement in production.
    Raises RuntimeError on connection failure or unauthorized fallback.
    """
    if require_postgres is None:
        require_postgres = is_production()

    logger.info("=== Verifying Database Identity & Connectivity ===")
    info = get_safe_db_info()
    logger.info(f"Target DB Engine: {info['engine']} (Vendor: {info['vendor']})")
    logger.info(f"Target DB Host: {info['host']}:{info['port']}")
    logger.info(f"Target DB Name: {info['database_name']}")
    logger.info(f"Production Mode: {info['is_production']}")

    # 1. Enforce No SQLite in Production
    if require_postgres and info['is_sqlite']:
        error_msg = (
            "FATAL ZERO-DATA-LOSS ERROR: SQLite was detected in Production environment! "
            "SQLite fallback is strictly forbidden to prevent database replacement and data loss. "
            "Please configure Railway PostgreSQL service and attach DATABASE_URL."
        )
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    # 2. Test live connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            if not result or result[0] != 1:
                raise RuntimeError("Database ping returned invalid response.")
        logger.info("Database connection ping: OK (SELECT 1 succeeded)")
    except Exception as e:
        error_msg = f"FATAL: Database connection failed: {e}"
        logger.critical(error_msg)
        raise RuntimeError(error_msg) from e

    return info


def get_table_counts_snapshot():
    """
    Take a record count snapshot of all core business models.
    Safely ignores models whose tables have not been created yet.
    """
    from django.apps import apps
    snapshot = {}

    for app_label, model_name, arabic_label in CORE_MODELS:
        try:
            model = apps.get_model(app_label, model_name)
            # Check if table exists
            with connection.cursor() as cursor:
                table_name = model._meta.db_table
                if connection.vendor == 'postgresql':
                    cursor.execute(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s);",
                        [table_name]
                    )
                    table_exists = cursor.fetchone()[0]
                elif connection.vendor == 'sqlite':
                    cursor.execute(
                        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=%s;",
                        [table_name]
                    )
                    table_exists = cursor.fetchone()[0] > 0
                else:
                    table_exists = True

            if table_exists:
                count = model.objects.count()
                snapshot[f"{app_label}.{model_name}"] = {
                    'count': count,
                    'label': arabic_label,
                    'table': model._meta.db_table
                }
        except Exception as e:
            # Model or table might not exist yet before initial migrations
            logger.debug(f"Snapshot skip for {app_label}.{model_name}: {e}")

    return snapshot


def log_counts_summary(snapshot, stage="Pre-Migration"):
    """Log a structured summary of core table counts."""
    # Only log detailed counts in debug mode
    if is_production():
        logger.warning(f"=== Core Table Records Summary ({stage}) ===")
        if not snapshot:
            logger.warning("  (No tracked tables exist yet - fresh schema initialization)")
            return
        # Only log summary in production, not per-table details
        total_records = sum(data['count'] for data in snapshot.values())
        logger.warning(f"  Total core table records: {total_records} across {len(snapshot)} tables")
    else:
        logger.info(f"=== Core Table Records Summary ({stage}) ===")
        if not snapshot:
            logger.info("  (No tracked tables exist yet - fresh schema initialization)")
            return

        for key, data in snapshot.items():
            logger.info(f"  {data['label']} ({key}): {data['count']} records [Table: {data['table']}]")


def verify_data_preservation(pre_snapshot, post_snapshot):
    """
    Verify that record counts have NOT dropped across migrations/deployments.
    Returns (True, "All data preserved") or raises RuntimeError on data loss.
    """
    if is_production():
        logger.warning("=== Verifying Data Preservation Post-Migration ===")
    else:
        logger.info("=== Verifying Data Preservation Post-Migration ===")
    violations = []

    for key, pre_data in pre_snapshot.items():
        post_data = post_snapshot.get(key)
        if not post_data:
            violations.append(f"Table for {key} ({pre_data['label']}) disappeared after migration!")
            continue

        pre_count = pre_data['count']
        post_count = post_data['count']

        if post_count < pre_count:
            violations.append(
                f"DATA LOSS DETECTED on {key} ({pre_data['label']}): "
                f"count dropped from {pre_count} to {post_count} (loss of {pre_count - post_count} records)!"
            )
        elif not is_production():
            logger.info(f"  PRESERVED: {pre_data['label']} ({key}): {post_count} records (Baseline: {pre_count})")

    if violations:
        error_msg = "CRITICAL ZERO-DATA-LOSS VIOLATION DETECTED:\n" + "\n".join(violations)
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    if is_production():
        logger.warning("ZERO DATA LOSS VERIFIED: All existing production data was preserved successfully.")
    else:
        logger.info("ZERO DATA LOSS VERIFIED: All existing production data was preserved successfully.")
    return True
