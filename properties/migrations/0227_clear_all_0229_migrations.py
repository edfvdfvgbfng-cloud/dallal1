# Migration to clear all 0229 migration records from database

from django.db import migrations


def clear_all_0229_migrations(apps, schema_editor):
    """Remove all 0229 migration records from django_migrations"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Remove all 0229 migration records (both old and new)
        cursor.execute("""
            DELETE FROM django_migrations 
            WHERE app = 'properties' AND name LIKE '0229%';
        """)
        print("Cleared all 0229 migration records from database")


def reverse_migration(apps, schema_editor):
    """No-op for reverse"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0227_useronlinestatus_chatmessage_delivered_at_and_more'),
    ]

    operations = [
        migrations.RunPython(clear_all_0229_migrations, reverse_migration),
    ]
