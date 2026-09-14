import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from properties.models import Property, OutsideProperty

print('=== Check Published Outside Properties ===')

# Get all properties with category='property_outside'
outside_props = Property.objects.filter(category='property_outside').order_by('-created_at')

print(f'Total outside properties: {outside_props.count()}')
print()

for prop in outside_props:
    print(f'ID: {prop.id}')
    print(f'Title: {prop.title}')
    print(f'Status: {prop.status}')
    print(f'Category: {prop.category}')
    print(f'Created: {prop.created_at}')
    print(f'Owner: {prop.owner.username if prop.owner else "None"}')
    print(f'Broker: {prop.broker.id if prop.broker else "None"}')
    
    # Check if OutsideProperty exists
    outside_details = OutsideProperty.objects.filter(property=prop).first()
    print(f'OutsideProperty exists: {outside_details is not None}')
    print()
