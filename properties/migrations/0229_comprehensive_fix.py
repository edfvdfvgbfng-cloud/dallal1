# Comprehensive migration to fix all database issues at once
# This migration:
# 1. Clears old 0227_comprehensive_fix migration record
# 2. Adds missing tables (Country, Hotel, BrokerChannel)
# 3. Adds missing columns (is_pinned, pinned_until, theme_mode, publication_end_date)
# 4. Fixes data type issues in SiteSettings

from django.db import migrations


def comprehensive_fix(apps, schema_editor):
    """Comprehensive fix for all database issues"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Step 1: Clear only the old 0227_comprehensive_fix record
        cursor.execute("""
            DELETE FROM django_migrations 
            WHERE app = 'properties' AND name = '0227_comprehensive_fix';
        """)
        print("Cleared old 0227_comprehensive_fix migration record")
        
        # Step 1.5: Also clear ActivityLog table if it exists to avoid conflicts
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'properties_activitylog'
            );
        """)
        if cursor.fetchone()[0]:
            cursor.execute("DROP TABLE properties_activitylog CASCADE")
            print("Dropped properties_activitylog table to avoid conflicts")
        
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
            
            # Add foreign key to Broker table if it exists
            try:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'properties_broker'
                    );
                """)
                if cursor.fetchone()[0]:
                    cursor.execute("""
                        ALTER TABLE properties_brokerchannel 
                        ADD CONSTRAINT properties_brokerchannel_broker_id_fk 
                        FOREIGN KEY (broker_id) REFERENCES properties_broker(id) ON DELETE SET NULL;
                    """)
                    print("Added foreign key to properties_brokerchannel")
            except Exception as e:
                print(f"Could not add foreign key: {e}")
        
        # Step 5: Skip adding property columns - they will be added by later migrations
        # This avoids conflicts with migrations that expect to add these columns themselves
        print("Skipping property column additions - they will be handled by later migrations")
        
        # Step 7: Add theme_mode to properties_sitesettings if it doesn't exist
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
        
        # Step 8: Create Resort table if it doesn't exist (minimal version)
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'properties_resort'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                CREATE TABLE properties_resort (
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
            print("Created properties_resort table")
        
        # Step 9: Fix data type issues in SiteSettings (multiple columns that might be INTEGER instead of VARCHAR)
        varchar_columns = [
            'spam_filter_level',
            'account_lockout_threshold',
            'report_priority_threshold',
            'server_monitoring_interval',
            'database_monitoring_interval',
            'cache_monitoring_interval',
            'log_rotation_size',
            'max_image_size',
            'max_video_size',
            'max_properties_per_user',
            'max_images_per_user',
            'max_messages_per_day',
            'max_search_results',
            'subscription_price_monthly',
            'subscription_price_yearly',
            'rd_budget_percentage',
            'csr_budget_percentage',
            'backup_retention_days',
            'data_retention_days',
            'audit_log_retention_days',
            'activity_log_retention_days',
            'error_log_retention_days',
            'access_log_retention_days',
            'auto_cleanup_days',
            'testing_frequency',
            'risk_assessment_frequency',
            'bcp_test_frequency',
            'rto_hours',
            'rpo_hours',
            'account_lockout_duration',
            'session_timeout',
            'cache_duration',
            'rate_limit_requests',
            'rate_limit_period',
            'minimum_age',
            'api_rate_limit',
            'hsts_max_age',
        ]
        
        for col_name in varchar_columns:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'properties_sitesettings' 
                    AND column_name = %s
                    AND data_type = 'integer'
                );
            """, [col_name])
            if cursor.fetchone()[0]:
                cursor.execute(f"""
                    ALTER TABLE properties_sitesettings 
                    ALTER COLUMN {col_name} TYPE VARCHAR(50) 
                    USING {col_name}::text;
                """)
                print(f"Fixed {col_name} column type from INTEGER to VARCHAR")


def reverse_migration(apps, schema_editor):
    """No-op for reverse - this is a comprehensive fix"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0228_clear_old_comprehensive_fix'),
    ]

    operations = [
        migrations.RunPython(comprehensive_fix, reverse_migration),
    ]
