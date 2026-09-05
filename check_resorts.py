import os
import sys
import django

# Set UTF-8 encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dalal_project.settings')
django.setup()

from properties.models import HotelPage

resorts = HotelPage.objects.all()
print('=== All HotelPages ===')
for r in resorts:
    print(f'ID: {r.id}, Name: {r.name}, Type: {r.page_type}, Outside: {r.is_outside_iraq}, Status: {r.status}, Slug: {r.slug}')
