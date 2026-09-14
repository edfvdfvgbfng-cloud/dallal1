# Ensure muqtada123 is a superuser
# Fix potential issue with create_superuser migration

from django.db import migrations
from django.contrib.auth.models import User

def ensure_superuser(apps, schema_editor):
    """Ensure muqtada123 is a superuser"""
    try:
        user = User.objects.get(username='muqtada123')
        if not user.is_superuser:
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            user.save()
    except User.DoesNotExist:
        # Create if doesn't exist
        User.objects.create_superuser(
            username='muqtada123',
            email='muqtada123@example.com',
            password='12345'
        )

def reverse_ensure_superuser(apps, schema_editor):
    """Reverse - do nothing for safety"""
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('properties', '0191_merge_migration_conflict'),
    ]

    operations = [
        migrations.RunPython(ensure_superuser, reverse_ensure_superuser),
    ]