# Generated to fix duplicate slug index issue
from django.db import migrations


def remove_duplicate_slug_index(apps, schema_editor):
    """Remove the duplicate slug index if it exists"""
    try:
        with schema_editor.connection.cursor() as cursor:
            # Try to drop the problematic index
            cursor.execute("DROP INDEX IF EXISTS properties_property_slug_f3b16024_like")
            print("Dropped duplicate slug index")
    except Exception as e:
        print(f"Error dropping index (may not exist): {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0004_propertyimage_sitesettings_alter_property_options_and_more'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_slug_index, migrations.RunPython.noop),
    ]
