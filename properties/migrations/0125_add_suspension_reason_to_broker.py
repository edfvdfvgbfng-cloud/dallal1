# Generated manually to add missing suspension_reason field to Broker

from django.db import migrations, models


def safely_add_suspension_reason(apps, schema_editor):
    """Safely add suspension_reason column if it doesn't exist"""
    try:
        with schema_editor.connection.cursor() as cursor:
            # Check if column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'properties_broker' 
                    AND column_name = 'suspension_reason'
                );
            """)
            if not cursor.fetchone()[0]:
                # Add the column using SQL
                cursor.execute("ALTER TABLE properties_broker ADD COLUMN suspension_reason VARCHAR(200) DEFAULT ''")
    except Exception as e:
        pass  # Silent failure to reduce logs


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0124_add_missing_fields_to_resortinside'),
    ]

    operations = [
        migrations.RunPython(safely_add_suspension_reason, migrations.RunPython.noop),
    ]
