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

# Configure logging - minimal in production
debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'

if debug_mode:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] [STARTUP] %(message)s'
    )
    logger = logging.getLogger('startup')
else:
    # Minimal logging in production - only CRITICAL
    logging.basicConfig(
        level=logging.CRITICAL,
        format='%(asctime)s [CRITICAL] %(message)s'
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

# Debug logging for path resolution (only in development)
if debug_mode:
    logger.info(f"Project root: {project_root}")
    logger.info(f"Current directory: {cwd}")
    logger.info(f"Python path: {sys.path[:5]}")
    logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")


def run(cmd, allow_fail=False):
    """Run command with proper PYTHONPATH and strict error checking."""
    if debug_mode:
        logger.info(f"Running: {' '.join(str(c) for c in cmd)}")
    env = os.environ.copy()
    env['PYTHONPATH'] = project_root
    try:
        # Redirect to DEVNULL in production to reduce log volume
        if debug_mode:
            subprocess.run(cmd, check=True, env=env, cwd=project_root)
        else:
            subprocess.run(cmd, check=True, env=env, cwd=project_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        if allow_fail:
            logger.critical(f"Command failed (non-fatal): {e}. Continuing.")
        else:
            logger.critical(f"FATAL: Command failed with exit code {e.returncode}: {e}")
            raise


def main():
    port = os.getenv('PORT', '8080')
    if debug_mode:
        logger.info(f"=== Dalal Platform Startup Initialized (port {port}) ===")
        logger.info(f"DEBUG={os.getenv('DEBUG', 'False')}")
        logger.info(f"DJANGO_SETTINGS_MODULE={os.getenv('DJANGO_SETTINGS_MODULE')}")

    # Verify module can be imported
    try:
        import dalal_project
        if debug_mode:
            logger.info("dalal_project module imported successfully")
    except ImportError as e:
        logger.critical(f"FATAL: Cannot import dalal_project: {e}")
        if debug_mode:
            logger.critical(f"Python path: {sys.path}")
        sys.exit(1)

    # 1. Setup Django
    try:
        import django
        django.setup()
        from django.conf import settings
        from properties import db_safety

        if debug_mode:
            logger.info(f"Django {django.__version__} loaded successfully")
            logger.info(f"Properties in INSTALLED_APPS: {'properties' in settings.INSTALLED_APPS}")
    except Exception as e:
        logger.critical(f"FATAL: Error initializing Django: {e}")
        raise

    # 2. Database Identity & Connectivity Verification
    # Enforces strict PostgreSQL in Production, verifies live connection
    try:
        db_info = db_safety.verify_database_identity()
        if debug_mode:
            logger.info(f"Database Identity: {db_info['vendor']} ({db_info['database_name']} on {db_info['host']}) - VERIFIED")
    except Exception as e:
        logger.critical(f"FATAL: Database Identity Verification failed: {e}")
        sys.exit(1)

    # 3. Pre-Migration Data Snapshot (Capture baseline record counts)
    pre_snapshot = {}
    try:
        pre_snapshot = db_safety.get_table_counts_snapshot()
        if debug_mode:
            db_safety.log_counts_summary(pre_snapshot, "Pre-Migration Baseline")
    except Exception as e:
        logger.warning(f"Could not capture pre-migration snapshot: {e}")

    # 4. Run Safe Database Migrations
    if debug_mode:
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
        if debug_mode:
            db_safety.log_counts_summary(post_snapshot, "Post-Migration Audit")
        db_safety.verify_data_preservation(pre_snapshot, post_snapshot)
    except Exception as e:
        logger.critical(f"FATAL: Post-migration data preservation check failed: {e}")
        sys.exit(1)

    # 6. Collect Static Files
    if debug_mode:
        logger.info("Collecting static files...")
    run([sys.executable, 'manage.py', 'collectstatic', '--noinput'], allow_fail=True)

    # 7. Start Production Gunicorn Web Server
    workers = os.getenv('GUNICORN_WORKERS', '2')
    log_level = os.getenv('GUNICORN_LOG_LEVEL', 'error')  # Changed to error for production
    timeout = os.getenv('GUNICORN_TIMEOUT', '120')

    if debug_mode:
        logger.info(f"Starting Gunicorn server: workers={workers}, timeout={timeout}, log_level={log_level}")

    # Disable all logs in production to reduce log volume
    if not debug_mode:
        log_level = 'error'
        access_logfile = '/dev/null'
        error_logfile = '/dev/null'
    else:
        access_logfile = '-'
        error_logfile = '-'

    os.execvp(
        'gunicorn',
        [
            'gunicorn',
            'dalal_project.wsgi:application',
            '--bind', f'0.0.0.0:{port}',
            '--workers', workers,
            '--timeout', timeout,
            '--log-level', log_level,
            '--access-logfile', access_logfile,
            '--error-logfile', error_logfile,
            '--forwarded-allow-ips', '*',
            '--capture-output',
        ],
    )


if __name__ == '__main__':
    main()
