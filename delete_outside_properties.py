import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from properties.models import Property, OutsideProperty

# Delete all outside properties
properties = Property.objects.filter(category='property_outside')
count = properties.count()

if count > 0:
    print(f'Deleting {count} outside properties...')
    properties.delete()
    print('All outside properties deleted successfully!')
else:
    print('No outside properties found.')
