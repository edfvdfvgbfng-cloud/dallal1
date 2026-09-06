# Migration to clear inconsistent migration history

def clear_inconsistent_migration_history(apps, schema_editor):
    """Remove inconsistent migration record from django_migrations"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Remove the inconsistent migration record
        cursor.execute("""
            DELETE FROM django_migrations 
            WHERE app = 'properties' AND name = '0229_create_brokerchannel';
        """)
        print("Cleared inconsistent migration record: properties.0229_create_brokerchannel")


def reverse_migration(apps, schema_editor):
    """No-op for reverse"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0227_useronlinestatus_chatmessage_delivered_at_and_more'),
    ]

    operations = [
        migrations.RunPython(clear_inconsistent_migration_history, reverse_migration),
    ]
