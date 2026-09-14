import os
import sys
import django
import re

# Set UTF-8 encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from properties.models import HotelPage

# Delete hotels with invalid Arabic slugs
print("=== Deleting hotels with invalid slugs ===")
invalid_hotels = HotelPage.objects.filter(slug__regex=r'[\u0600-\u06FF]')
for hotel in invalid_hotels:
    print(f"Deleting: {hotel.name} with slug: {hotel.slug}")
    hotel.delete()

print(f"Deleted {invalid_hotels.count()} hotels with invalid slugs")

# Update the main hotel
hotel = HotelPage.objects.filter(slug='hotel-tb04c0pf').first()
if hotel:
    print(f"\nHotel found: {hotel.name}")
    print(f"Current is_outside_iraq: {hotel.is_outside_iraq}")
    print(f"Current status: {hotel.status}")

    # Update to outside Iraq
    hotel.is_outside_iraq = True
    hotel.status = 'active'
    hotel.save()

    print(f"Updated hotel:")
    print(f"New is_outside_iraq: {hotel.is_outside_iraq}")
    print(f"New status: {hotel.status}")
else:
    print("Hotel not found")

# Check all remaining hotels
print("\n=== All Remaining Hotels ===")
for h in HotelPage.objects.all():
    print(f"Name: {h.name}, Slug: {h.slug}, Outside: {h.is_outside_iraq}, Status: {h.status}")
