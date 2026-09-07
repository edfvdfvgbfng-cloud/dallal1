# Migration to clear old 0227_comprehensive_fix record from database

from django.db import migrations


def clear_old_comprehensive_fix_record(apps, schema_editor):
    """Remove old 0227_comprehensive_fix record and create missing usersettings table"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Remove the old migration record
        cursor.execute("""
            DELETE FROM django_migrations 
            WHERE app = 'properties' AND name = '0227_comprehensive_fix';
        """)
        print("Cleared old 0227_comprehensive_fix migration record")
        
        # Create usersettings table if it doesn't exist (needed for older migrations)
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'properties_usersettings'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                CREATE TABLE properties_usersettings (
                    id BIGSERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,
                    email_notifications BOOLEAN DEFAULT TRUE NOT NULL,
                    sms_notifications BOOLEAN DEFAULT FALSE NOT NULL,
                    push_notifications BOOLEAN DEFAULT TRUE NOT NULL,
                    language VARCHAR(10) DEFAULT 'ar' NOT NULL,
                    timezone VARCHAR(50) DEFAULT 'Asia/Baghdad' NOT NULL,
                    governorate VARCHAR(50) DEFAULT '' NOT NULL,
                    city VARCHAR(100) DEFAULT '' NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
                );
            """)
            print("Created properties_usersettings table")


def reverse_migration(apps, schema_editor):
    """No-op for reverse"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0021_broker_is_suspended_broker_subscription_duration_and_more'),
    ]

    operations = [
        migrations.RunPython(clear_old_comprehensive_fix_record, reverse_migration),
    ]
