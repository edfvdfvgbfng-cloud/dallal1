import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from properties.models import Property

# Check all properties
properties = Property.objects.all()
print(f"Total properties in database: {properties.count()}")

if properties.exists():
    print("\nAll Properties:")
    print("=" * 80)
    for prop in properties:
        print(f"ID: {prop.id}")
        print(f"Title: {prop.title}")
        print(f"Slug: {prop.slug}")
        print(f"Category: {prop.category}")
        print(f"Status: {prop.status}")
        print(f"Type: {prop.type}")
        print(f"Owner: {prop.owner.username if prop.owner else 'None'}")
        print("-" * 80)
else:
    print("No properties found in database.")
