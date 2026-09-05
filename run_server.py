#!/usr/bin/env python
"""
Railway production entrypoint for Dalal Platform.
Zero Data Loss Architecture:
1. Environment & Database Identity Verification (Enforces PostgreSQL, rejects SQLite in production)
2. Live Database Connection Health Ping
3. Pre-Migration Record Counts Snapshot
4. Safe Migrations Execution (migrate --noinput ONLY, NO flush, NO reset, NO makemigrations)
5. Post-Migration Record Counts Verification (Ensures zero data loss)
6. Collectstatic
7. Gunicorn Production Server Execution
"""
import os
import subprocess
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [STARTUP] %(message)s'
)
logger = logging.getLogger('startup')

# Force disable WebSockets to use Gunicorn instead of Daphne
os.environ['USE_WEBSOCKETS'] = 'false'

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
cwd = os.getcwd()
candidate_paths = [project_root, cwd, '/app', '/workspace']
for p in candidate_paths:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)
os.environ['PYTHONPATH'] = ':'.join([p for p in candidate_paths if os.path.isdir(p)]) + ':' + os.environ.get('PYTHONPATH', '')



def run(cmd, allow_fail=False):
    """Run command with proper PYTHONPATH and strict error checking."""
    logger.info(f"Running: {' '.join(str(c) for c in cmd)}")
    env = os.environ.copy()
    env['PYTHONPATH'] = project_root
    try:
        subprocess.run(cmd, check=True, env=env, cwd=project_root)
    except subprocess.CalledProcessError as e:
        if allow_fail:
            logger.warning(f"Command failed (non-fatal): {e}. Continuing.")
        else:
            logger.critical(f"FATAL: Command failed with exit code {e.returncode}: {e}")
            raise


def main():
    port = os.getenv('PORT', '8080')
    logger.info(f"=== Dalal Platform Startup Initialized (port {port}) ===")
    logger.info(f"DEBUG={os.getenv('DEBUG', 'False')}")
    logger.info(f"DJANGO_SETTINGS_MODULE={os.getenv('DJANGO_SETTINGS_MODULE')}")

    # 1. Setup Django
    try:
        import django
        django.setup()
        from django.conf import settings
        from properties import db_safety
        
        logger.info(f"Django {django.__version__} loaded successfully")
        logger.info(f"Properties in INSTALLED_APPS: {'properties' in settings.INSTALLED_APPS}")
    except Exception as e:
        logger.critical(f"FATAL: Error initializing Django: {e}")
        raise

    # 2. Database Identity & Connectivity Verification
    # Enforces strict PostgreSQL in Production, verifies live connection
    try:
        db_info = db_safety.verify_database_identity()
        logger.info(f"Database Identity: {db_info['vendor']} ({db_info['database_name']} on {db_info['host']}) - VERIFIED")
    except Exception as e:
        logger.critical(f"FATAL: Database Identity Verification failed: {e}")
        sys.exit(1)

    # 3. Pre-Migration Data Snapshot (Capture baseline record counts)
    pre_snapshot = {}
    try:
        pre_snapshot = db_safety.get_table_counts_snapshot()
        db_safety.log_counts_summary(pre_snapshot, "Pre-Migration Baseline")
    except Exception as e:
        logger.warning(f"Could not capture pre-migration snapshot: {e}")

    # 4. Run Safe Database Migrations
    logger.info("Executing safe database migrations (migrate --noinput)...")
    # CRITICAL: We run migrate --noinput ONLY. Never flush, reset, or drop.
    try:
        run([sys.executable, 'manage.py', 'migrate', '--noinput'], allow_fail=False)
        logger.info("Database migrations completed successfully.")
    except Exception as e:
        logger.critical(f"FATAL: Migration execution failed: {e}")
        sys.exit(1)

    # 5. Post-Migration Verification (Validate zero data loss)
    try:
        post_snapshot = db_safety.get_table_counts_snapshot()
        db_safety.log_counts_summary(post_snapshot, "Post-Migration Audit")
        db_safety.verify_data_preservation(pre_snapshot, post_snapshot)
    except Exception as e:
        logger.critical(f"FATAL: Post-migration data preservation check failed: {e}")
        sys.exit(1)

    # 6. Collect Static Files
    logger.info("Collecting static files...")
    run([sys.executable, 'manage.py', 'collectstatic', '--noinput'], allow_fail=True)

    # 7. Start Production Gunicorn Web Server
    workers = os.getenv('GUNICORN_WORKERS', '2')
    log_level = os.getenv('GUNICORN_LOG_LEVEL', 'info')
    timeout = os.getenv('GUNICORN_TIMEOUT', '120')

    logger.info(f"Starting Gunicorn server: workers={workers}, timeout={timeout}, log_level={log_level}")

    os.execvp(
        'gunicorn',
        [
            'gunicorn',
            'dalal_project.wsgi:application',
            '--bind', f'0.0.0.0:{port}',
            '--workers', workers,
            '--timeout', timeout,
            '--log-level', log_level,
            '--access-logfile', '-',
            '--error-logfile', '-',
            '--forwarded-allow-ips', '*',
            '--capture-output',
        ],
    )


if __name__ == '__main__':
    main()
