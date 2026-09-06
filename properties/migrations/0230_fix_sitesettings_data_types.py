# Migration to fix data type issues in SiteSettings

from django.db import migrations


def fix_sitesettings_data_types(apps, schema_editor):
    """Fix data type issues in SiteSettings table"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Fix spam_filter_level column type from INTEGER to VARCHAR
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'properties_sitesettings' 
                AND column_name = 'spam_filter_level'
                AND data_type = 'integer'
            );
        """)
        if cursor.fetchone()[0]:
            # First, convert existing values to text
            cursor.execute("""
                ALTER TABLE properties_sitesettings 
                ALTER COLUMN spam_filter_level TYPE VARCHAR(20) 
                USING spam_filter_level::text;
            """)
            print("Fixed spam_filter_level column type from INTEGER to VARCHAR")
        
        # Fix account_lockout_threshold column type from INTEGER to VARCHAR if needed
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
            print("Fixed account_lockout_threshold column type from INTEGER to VARCHAR")


def reverse_migration(apps, schema_editor):
    """No-op for reverse - data type changes are complex to reverse"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0229_add_missing_tables_and_columns'),
    ]

    operations = [
        migrations.RunPython(fix_sitesettings_data_types, reverse_migration),
    ]
