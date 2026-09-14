import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from properties.models import Property, OutsideProperty

# Check the property with slug "luxury-apartment-in-dubai-3"
try:
    property = Property.objects.get(slug='luxury-apartment-in-dubai-3')
    print(f"Property Found: {property.title}")
    print(f"ID: {property.id}")
    print(f"Type: {property.type}")
    print(f"Category: {property.category}")
    print(f"Status: {property.status}")
    print(f"Price: {property.price}")
    print(f"Owner: {property.owner.username if property.owner else 'None'}")
    print(f"Created: {property.created_at}")

    # Check if it has OutsideProperty
    outside_prop = OutsideProperty.objects.filter(property=property).first()
    if outside_prop:
        print(f"OutsideProperty exists: Yes")
        print(f"Country: {property.country.name if property.country else 'None'}")
    else:
        print(f"OutsideProperty exists: No")

except Property.DoesNotExist:
    print("Property not found with slug: luxury-apartment-in-dubai-3")
