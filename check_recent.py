import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from properties.models import Property
from django.utils import timezone
from datetime import timedelta

print('=== Check Recent Outside Properties ===')

# Get properties created in the last 30 minutes
recent_time = timezone.now() - timedelta(minutes=30)
recent_props = Property.objects.filter(
    category='property_outside',
    created_at__gte=recent_time
).order_by('-created_at')

print(f'Recent outside properties (last 30 min): {recent_props.count()}')
print()

for prop in recent_props:
    print(f'ID: {prop.id}')
    print(f'Title: {prop.title}')
    print(f'Status: {prop.status}')
    print(f'Created: {prop.created_at}')
    print()
