"""
Middleware to ensure Django core tables exist before serving requests.
This is a fallback when entrypoint.sh migrations fail to run.
"""
import logging
from django.db import connection
from django.core.management import call_command

logger = logging.getLogger(__name__)


class EnsureTablesMiddleware:
    """
    Check if Django core tables exist and create them if they don't.
    This ensures the application works even if migrations fail during startup.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.tables_checked = False
    
    def __call__(self, request):
        # Only check tables once to avoid overhead
        if not self.tables_checked:
            self.ensure_django_tables()
            self.tables_checked = True
        
        return self.get_response(request)
    
    def ensure_django_tables(self):
        """Ensure Django core tables exist"""
        try:
            cursor = connection.cursor()
            
            # Check if django_session exists
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'django_session'
            """)
            result = cursor.fetchone()
            
            if not result:
                logger.warning("django_session table missing - attempting to create it")
                try:
                    # Try to run syncdb to create missing tables
                    call_command('syncdb', interactive=False, verbosity=0)
                    logger.info("syncdb completed successfully")
                except Exception as e:
                    logger.error(f"syncdb failed: {e}")
                    
                    # Alternative: try to create just django_session
                    try:
                        cursor.execute("""
                            CREATE TABLE django_session (
                                session_key VARCHAR(40) NOT NULL PRIMARY KEY,
                                session_data TEXT NOT NULL,
                                expire_date TIMESTAMP NOT NULL
                            )
                        """)
                        logger.info("django_session table created manually")
                    except Exception as e2:
                        logger.error(f"Manual django_session creation failed: {e2}")
            else:
                logger.info("django_session table exists")
                
        except Exception as e:
            logger.error(f"Error checking tables: {e}")
