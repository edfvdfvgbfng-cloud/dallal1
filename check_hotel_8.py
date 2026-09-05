import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from properties.models import HotelPage

page = HotelPage.objects.filter(id=8).first()
if page:
    print(f'ID: {page.id}, Name: {page.name}, Slug: {page.slug}')
else:
    print('No HotelPage with ID 8 found')

print('\nAll HotelPages:')
for p in HotelPage.objects.all()[:5]:
    print(f'ID: {p.id}, Name: {p.name}, Slug: {p.slug}')