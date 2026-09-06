# Comprehensive migration to fix all database issues at once
# This migration:
# 1. Clears inconsistent migration records
# 2. Adds missing tables (Country, Hotel, BrokerChannel)
# 3. Adds missing columns (is_pinned, pinned_until, theme_mode, publication_end_date)
# 4. Fixes data type issues in SiteSettings

from django.db import migrations


def comprehensive_fix(apps, schema_editor):
    """Comprehensive fix for all database issues"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Step 1: Clear all inconsistent migration records
        cursor.execute("""
            DELETE FROM django_migrations 
            WHERE app = 'properties' AND name LIKE '022%';
        """)
        print("Cleared all 022x migration records")
        
        # Step 2: Create Country table if it doesn't exist
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
        
        # Step 3: Create Hotel table if it doesn't exist (minimal version)
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
        
        # Step 4: Create BrokerChannel table if it doesn't exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'properties_brokerchannel'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                CREATE TABLE properties_brokerchannel (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    description TEXT DEFAULT '' NOT NULL,
                    category VARCHAR(100) DEFAULT 'general' NOT NULL,
                    governorate VARCHAR(100) DEFAULT '' NOT NULL,
                    status VARCHAR(20) DEFAULT 'active' NOT NULL,
                    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
                    is_featured BOOLEAN DEFAULT FALSE NOT NULL,
                    subscriber_count INTEGER DEFAULT 0 NOT NULL,
                    video_count INTEGER DEFAULT 0 NOT NULL,
                    post_count INTEGER DEFAULT 0 NOT NULL,
                    cover_image VARCHAR(200) DEFAULT '' NOT NULL,
                    profile_image VARCHAR(200) DEFAULT '' NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    broker_id INTEGER NULL,
                    UNIQUE (name, broker_id)
                );
            """)
            print("Created properties_brokerchannel table")
        
        # Step 5: Add missing columns to properties_property
        property_columns = [
            ('is_pinned', 'BOOLEAN', 'FALSE'),
            ('pinned_until', 'TIMESTAMP WITH TIME ZONE', 'NULL'),
            ('publication_end_date', 'TIMESTAMP WITH TIME ZONE', 'NULL'),
        ]
        
        for col_name, col_type, default_val in property_columns:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'properties_property' 
                    AND column_name = %s
                );
            """, [col_name])
            if not cursor.fetchone()[0]:
                if default_val == 'NULL':
                    cursor.execute(f"""
                        ALTER TABLE properties_property 
                        ADD COLUMN {col_name} {col_type} NULL;
                    """)
                elif col_type == 'BOOLEAN':
                    cursor.execute(f"""
                        ALTER TABLE properties_property 
                        ADD COLUMN {col_name} {col_type} DEFAULT {default_val} NOT NULL;
                    """)
                else:
                    cursor.execute(f"""
                        ALTER TABLE properties_property 
                        ADD COLUMN {col_name} {col_type} DEFAULT '{default_val}' NOT NULL;
                    """)
                print(f"Added {col_name} column to properties_property")
        
        # Step 6: Add theme_mode to properties_sitesettings if it doesn't exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'properties_sitesettings' 
                AND column_name = 'theme_mode'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE properties_sitesettings 
                ADD COLUMN theme_mode VARCHAR(20) DEFAULT 'light' NOT NULL;
            """)
            print("Added theme_mode column to properties_sitesettings")
        
        # Step 7: Fix data type issues in SiteSettings
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'properties_sitesettings' 
                AND column_name = 'spam_filter_level'
                AND data_type = 'integer'
            );
        """)
        if cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE properties_sitesettings 
                ALTER COLUMN spam_filter_level TYPE VARCHAR(20) 
                USING spam_filter_level::text;
            """)
            print("Fixed spam_filter_level column type")
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'properties_sitesettings' 
                AND column_name = 'account_lockout_threshold'
                AND data_type = 'integer'
            );
        """)
        if cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE properties_sitesettings 
                ALTER COLUMN account_lockout_threshold TYPE VARCHAR(20) 
                USING account_lockout_threshold::text;
            """)
            print("Fixed account_lockout_threshold column type")


def reverse_migration(apps, schema_editor):
    """No-op for reverse - this is a comprehensive fix"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0227_useronlinestatus_chatmessage_delivered_at_and_more'),
    ]

    operations = [
        migrations.RunPython(comprehensive_fix, reverse_migration),
    ]
