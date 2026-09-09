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
        
        # 2. Drop problematic index
        self.stdout.write("Step 2: Dropping problematic index...")
        try:
            cursor.execute("DROP INDEX IF EXISTS properties_property_slug_f3b16024_like")
            self.stdout.write("  Dropped duplicate slug index")
        except Exception as e:
            self.stdout.write(f"  Error dropping index: {e}")
        
        # 3. Delete migration records for properties app
        self.stdout.write("Step 3: Resetting migration history...")
        try:
            cursor.execute("DELETE FROM django_migrations WHERE app = 'properties'")
            self.stdout.write("  Reset properties migration history")
        except Exception as e:
            self.stdout.write(f"  Error resetting migrations: {e}")
        
        # 4. Commit changes
        transaction.commit()
        
        self.stdout.write("Database fix completed successfully!")
        self.stdout.write("Please run: python manage.py migrate")
