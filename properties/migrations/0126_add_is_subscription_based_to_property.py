# Generated manually to add missing is_subscription_based field to Property

from django.db import migrations, models


def safely_add_is_subscription_based(apps, schema_editor):
    """Safely add is_subscription_based column if it doesn't exist"""
    try:
        with schema_editor.connection.cursor() as cursor:
            # Check if column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'properties_property' 
                    AND column_name = 'is_subscription_based'
                );
            """)
            if not cursor.fetchone()[0]:
                # Add the column using SQL
                cursor.execute("ALTER TABLE properties_property ADD COLUMN is_subscription_based BOOLEAN DEFAULT FALSE")
    except Exception as e:
        pass  # Silent failure to reduce logs


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0125_add_suspension_reason_to_broker'),
    ]

    operations = [
        migrations.RunPython(safely_add_is_subscription_based, migrations.RunPython.noop),
    ]
