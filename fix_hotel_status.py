import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from properties.models import HotelPage

# Update all hotels without status to active
hotels = HotelPage.objects.filter(status__isnull=True)
count = hotels.update(status='active')
print(f"Updated {count} hotels to active status")

# Check the specific hotel
hotel = HotelPage.objects.filter(slug='hotel-tb04c0pf').first()
if hotel:
    print(f"Hotel found: {hotel.name}, Status: {hotel.status}, Slug: {hotel.slug}")
    if hotel.status != 'active':
        hotel.status = 'active'
        hotel.save()
        print("Hotel status updated to active")
else:
    print("Hotel not found")
