import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from properties.models import HotelPage

print("=== HotelPage Records ===")
hotels = HotelPage.objects.all()
print(f"Total hotels: {hotels.count()}")

for hotel in hotels:
    print(f"ID: {hotel.id}")
    print(f"Name: {hotel.name}")
    print(f"Type: {hotel.page_type}")
    print(f"Outside Iraq: {hotel.is_outside_iraq}")
    print(f"Status: {hotel.status}")
    print(f"Slug: {hotel.slug}")
    print("---")
