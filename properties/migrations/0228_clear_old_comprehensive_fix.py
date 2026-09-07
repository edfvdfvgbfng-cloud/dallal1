# Migration to clear old 0227_comprehensive_fix record from database

from django.db import migrations


def clear_old_comprehensive_fix_record(apps, schema_editor):
    """Remove old 0227_comprehensive_fix record from django_migrations"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Remove the old migration record
        cursor.execute("""
            DELETE FROM django_migrations 
            WHERE app = 'properties' AND name = '0227_comprehensive_fix';
        """)
        print("Cleared old 0227_comprehensive_fix migration record")


def reverse_migration(apps, schema_editor):
    """No-op for reverse"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0227_useronlinestatus_chatmessage_delivered_at_and_more'),
    ]

    operations = [
        migrations.RunPython(clear_old_comprehensive_fix_record, reverse_migration),
    ]
