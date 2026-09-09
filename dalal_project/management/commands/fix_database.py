from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Fix corrupted database state and recreate missing tables'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        self.stdout.write("Starting database fix...")
        
        # 1. Drop all properties tables
        self.stdout.write("Step 1: Dropping all properties tables...")
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' AND tablename LIKE 'properties_%'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                self.stdout.write(f"  Dropped: {table}")
            except Exception as e:
                self.stdout.write(f"  Error dropping {table}: {e}")
        
        self.stdout.write(f"Dropped {len(tables)} properties tables")
        
        # 2. Drop all properties indexes
        self.stdout.write("Step 2: Dropping all properties indexes...")
        cursor.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE schemaname = 'public' AND indexname LIKE 'properties_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        for index in indexes:
            try:
                cursor.execute(f"DROP INDEX IF EXISTS {index}")
                self.stdout.write(f"  Dropped index: {index}")
            except Exception as e:
                self.stdout.write(f"  Error dropping index {index}: {e}")
        
        self.stdout.write(f"Dropped {len(indexes)} properties indexes")
        
        # 3. Delete migration records for properties app
        self.stdout.write("Step 3: Resetting migration history...")
        try:
            cursor.execute("DELETE FROM django_migrations WHERE app = 'properties'")
            self.stdout.write("  Reset properties migration history")
        except Exception as e:
            self.stdout.write(f"  Error resetting migrations: {e}")
        
        # 4. Also reset django_contenttypes to avoid foreign key issues
        self.stdout.write("Step 4: Resetting content types...")
        try:
            cursor.execute("DELETE FROM django_content_type WHERE app_label = 'properties'")
            self.stdout.write("  Reset properties content types")
        except Exception as e:
            self.stdout.write(f"  Error resetting content types: {e}")
        
        # 5. Commit changes
        transaction.commit()
        
        self.stdout.write("Database fix completed successfully!")
        self.stdout.write("Please run: python manage.py migrate")
