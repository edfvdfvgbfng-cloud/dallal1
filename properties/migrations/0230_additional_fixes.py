# Migration to apply additional fixes after 0227

from django.db import migrations


def apply_additional_fixes(apps, schema_editor):
    """Apply additional fixes for Resort table, expiry_date, and data types"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Create Resort table if it doesn't exist
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
        
        # Add expiry_date column to properties_property if it doesn't exist
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'properties_property' 
                AND column_name = 'expiry_date'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE properties_property 
                ADD COLUMN expiry_date TIMESTAMP WITH TIME ZONE NULL;
            """)
            print("Added expiry_date column to properties_property")
        
        # Fix data type issues in SiteSettings (multiple columns that might be INTEGER instead of VARCHAR)
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
    """No-op for reverse"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0229_comprehensive_fix'),
    ]

    operations = [
        migrations.RunPython(apply_additional_fixes, reverse_migration),
    ]
