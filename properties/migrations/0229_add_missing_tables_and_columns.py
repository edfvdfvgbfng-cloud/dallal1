# Migration to add missing tables and columns that cause runtime errors

from django.db import migrations, models


def add_missing_tables_and_columns(apps, schema_editor):
    """Add missing tables and columns"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Create Country table if it doesn't exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'properties_country'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                CREATE TABLE properties_country (
                    id BIGSERIAL PRIMARY KEY,
                    name_ar VARCHAR(100) NOT NULL,
                    name_en VARCHAR(100) NOT NULL,
                    flag_emoji VARCHAR(10) NOT NULL,
                    code VARCHAR(3) UNIQUE NOT NULL,
                    currency_code VARCHAR(3) NOT NULL,
                    currency_name_ar VARCHAR(50) NOT NULL,
                    currency_name_en VARCHAR(50) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    "order" INTEGER DEFAULT 0 NOT NULL
                );
            """)
            print("Created properties_country table")
        
        # Create Hotel table if it doesn't exist (minimal version)
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'properties_hotel'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                CREATE TABLE properties_hotel (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    description TEXT DEFAULT '' NOT NULL,
                    address VARCHAR(300) DEFAULT '' NOT NULL,
                    city VARCHAR(100) DEFAULT '' NOT NULL,
                    governorate VARCHAR(100) DEFAULT '' NOT NULL,
                    country VARCHAR(100) DEFAULT '' NOT NULL,
                    price INTEGER DEFAULT 0 NOT NULL,
                    rating DECIMAL(2,1) DEFAULT 0.0 NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
                );
            """)
            print("Created properties_hotel table")
        
        # Add publication_end_date column to properties_property if it doesn't exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'properties_property' 
                AND column_name = 'publication_end_date'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE properties_property 
                ADD COLUMN publication_end_date TIMESTAMP WITH TIME ZONE NULL;
            """)
            print("Added publication_end_date column to properties_property")


def reverse_migration(apps, schema_editor):
    """Reverse migration - drop tables and columns"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Drop tables
        cursor.execute("DROP TABLE IF EXISTS properties_hotel CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS properties_country CASCADE;")
        
        # Drop column
        try:
            cursor.execute("ALTER TABLE properties_property DROP COLUMN IF EXISTS publication_end_date;")
        except Exception:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0228_create_brokerchannel_and_fix_columns'),
    ]

    operations = [
        migrations.RunPython(add_missing_tables_and_columns, reverse_migration),
    ]
