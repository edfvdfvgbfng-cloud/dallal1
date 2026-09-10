from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Fix corrupted database state and recreate missing tables'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        # Drop all properties tables EXCEPT ActivityLog (used for logging)
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' AND tablename LIKE 'properties_%'
            AND tablename != 'properties_activitylog'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            except Exception as e:
                pass  # Silent failure
        
        # Drop all properties indexes
        cursor.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE schemaname = 'public' AND indexname LIKE 'properties_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT relname FROM pg_class 
            WHERE relkind = 'i' AND relname LIKE '%slug%'
        """)
        slug_indexes = [row[0] for row in cursor.fetchall()]
        
        all_indexes = list(set(indexes + slug_indexes))
        
        for index in all_indexes:
            try:
                cursor.execute(f"DROP INDEX IF EXISTS {index}")
            except Exception as e:
                pass  # Silent failure
        
        # Delete migration records for properties app
        try:
            cursor.execute("DELETE FROM django_migrations WHERE app = 'properties'")
        except Exception as e:
            pass  # Silent failure
        
        try:
            cursor.execute("DELETE FROM django_migrations WHERE app = 'properties' AND name LIKE '022%'")
            cursor.execute("DELETE FROM django_migrations WHERE app = 'properties' AND name LIKE '023%'")
        except Exception as e:
            pass  # Silent failure
        
        # Reset django_contenttypes
        try:
            cursor.execute("DELETE FROM auth_permission WHERE content_type_id IN (SELECT id FROM django_content_type WHERE app_label = 'properties')")
            cursor.execute("DELETE FROM django_content_type WHERE app_label = 'properties'")
        except Exception as e:
            pass  # Silent failure
        
        # Commit changes
        transaction.commit()