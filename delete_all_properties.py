import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from properties.models import Property

# Delete all properties
count = Property.objects.count()
if count > 0:
    Property.objects.all().delete()
    print(f"Deleted {count} properties")
else:
    print("No properties to delete")
