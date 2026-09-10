# Generated manually to fix migration issue
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


def safely_skip_property_removal(apps, schema_editor):
    """Skip property field removal if column doesn't exist"""
    try:
        with schema_editor.connection.cursor() as cursor:
            # Check if property_id column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'properties_notification' 
                    AND column_name = 'property_id'
                );
            """)
            if cursor.fetchone()[0]:
                print("property_id column exists, will be handled by existing migration")
            else:
                print("property_id column does not exist, migration already applied")
    except Exception as e:
        print(f"Error checking property field: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0041_remove_notification_property_notification_link_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(safely_skip_property_removal, migrations.RunPython.noop),
    ]