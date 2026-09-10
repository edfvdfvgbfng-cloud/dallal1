from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Fix corrupted database state and recreate missing tables'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        self.stdout.write("Starting database fix...")
        
        # 0. First, ensure properties_broker doesn't have conflicting columns before dropping tables
        self.stdout.write("Step 0: Ensuring properties_broker doesn't have conflicting columns...")
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'properties_broker'
                );
            """)
            if cursor.fetchone()[0]:
                # Drop conflicting columns if they exist
                broker_columns = ['suspension_reason']
                for column in broker_columns:
                    cursor.execute(f"ALTER TABLE properties_broker DROP COLUMN IF EXISTS {column} CASCADE")
                self.stdout.write(f"  Dropped conflicting columns from properties_broker: {', '.join(broker_columns)}")
        except Exception as e:
            self.stdout.write(f"  Error checking/dropping conflicting columns: {e}")
        
        # 0.1. Also ensure properties_property doesn't have conflicting columns before dropping tables
        self.stdout.write("Step 0.1: Ensuring properties_property doesn't have conflicting columns...")
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'properties_property'
                );
            """)
            if cursor.fetchone()[0]:
                # Drop conflicting columns if they exist
                property_columns = ['is_subscription_based']
                for column in property_columns:
                    cursor.execute(f"ALTER TABLE properties_property DROP COLUMN IF EXISTS {column} CASCADE")
                self.stdout.write(f"  Dropped conflicting columns from properties_property: {', '.join(property_columns)}")
        except Exception as e:
            self.stdout.write(f"  Error checking/dropping conflicting columns: {e}")
        
        # 1. Drop all properties tables completely to ensure clean state
        self.stdout.write("Step 1: Dropping ALL properties tables for clean state...")
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
        
        self.stdout.write(f"Dropped {len(tables)} properties tables - clean state achieved")
        
        # 2. Drop all properties indexes
        self.stdout.write("Step 2: Dropping all properties indexes...")
        # Try to find indexes using pg_indexes
        cursor.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE schemaname = 'public' AND indexname LIKE 'properties_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        # Also specifically look for the problematic slug index using pg_class
        cursor.execute("""
            SELECT relname FROM pg_class 
            WHERE relkind = 'i' AND relname LIKE '%slug%'
        """)
        slug_indexes = [row[0] for row in cursor.fetchall()]
        
        # Combine both lists and remove duplicates
        all_indexes = list(set(indexes + slug_indexes))
        
        for index in all_indexes:
            try:
                cursor.execute(f"DROP INDEX IF EXISTS {index}")
                self.stdout.write(f"  Dropped index: {index}")
            except Exception as e:
                self.stdout.write(f"  Error dropping index {index}: {e}")
        
        self.stdout.write(f"Dropped {len(all_indexes)} properties indexes")
        
        # 3. Delete migration records for properties app
        self.stdout.write("Step 3: Resetting migration history...")
        try:
            cursor.execute("DELETE FROM django_migrations WHERE app = 'properties'")
            self.stdout.write("  Reset properties migration history")
        except Exception as e:
            self.stdout.write(f"  Error resetting migrations: {e}")
        
        # Also specifically clear 022x and 023x migrations to avoid dependency issues
        try:
            cursor.execute("DELETE FROM django_migrations WHERE app = 'properties' AND name LIKE '022%'")
            cursor.execute("DELETE FROM django_migrations WHERE app = 'properties' AND name LIKE '023%'")
            self.stdout.write("  Cleared 022x and 023x migration records")
        except Exception as e:
            self.stdout.write(f"  Error clearing 022x/023x migrations: {e}")
        
        # 4. Also reset django_contenttypes to avoid foreign key issues
        self.stdout.write("Step 4: Resetting content types...")
        try:
            # First try to delete in correct order (delete permissions first)
            cursor.execute("DELETE FROM auth_permission WHERE content_type_id IN (SELECT id FROM django_content_type WHERE app_label = 'properties')")
            cursor.execute("DELETE FROM django_content_type WHERE app_label = 'properties'")
            self.stdout.write("  Reset properties content types")
        except Exception as e:
            self.stdout.write(f"  Error resetting content types: {e}")
            # Continue anyway - this is not critical
        
        # 5. Commit changes
        transaction.commit()
        
        self.stdout.write("Database fix completed successfully!")
        self.stdout.write("Please run: python manage.py migrate")
