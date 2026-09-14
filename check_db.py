import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from properties.models import HotelPage

# Get all HotelPages
all_pages = HotelPage.objects.all()
print(f"Total HotelPages: {all_pages.count()}")

# Get resorts (inside Iraq) - include all resort types
resort_types = ['resort', 'chalet', 'cabin', 'guesthouse', 'inn']
resorts = HotelPage.objects.filter(page_type__in=resort_types, is_outside_iraq=False)
print(f"Resorts inside Iraq: {resorts.count()}")

# Get active resorts
active_resorts = resorts.filter(status='active')
print(f"Active resorts: {active_resorts.count()}")

# Show details
print("\n=== All Pages ===")
for page in all_pages:
    print(f"ID: {page.id}, Name: {page.name}, Type: {page.page_type}, Outside: {page.is_outside_iraq}, Status: {page.status}, Slug: {page.slug}")

print("\n=== Resorts that should show ===")
for resort in active_resorts:
    print(f"ID: {resort.id}, Name: {resort.name}, Type: {resort.page_type}, Status: {resort.status}, Slug: {resort.slug}")
