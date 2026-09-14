from django.core.management.base import BaseCommand
from properties.models import Property, Country
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Create sample properties outside Iraq'

    def handle(self, *args, **options):
        # Get or create countries
        turkey, _ = Country.objects.get_or_create(
            code='TR',
            defaults={
                'name_ar': 'تركيا',
                'name_en': 'Turkey',
                'flag_emoji': '🇹🇷',
                'is_active': True
            }
        )
        
        uae, _ = Country.objects.get_or_create(
            code='AE',
            defaults={
                'name_ar': 'الإمارات العربية المتحدة',
                'name_en': 'United Arab Emirates',
                'flag_emoji': '🇦🇪',
                'is_active': True
            }
        )
        
        egypt, _ = Country.objects.get_or_create(
            code='EG',
            defaults={
                'name_ar': 'مصر',
                'name_en': 'Egypt',
                'flag_emoji': '🇪🇬',
                'is_active': True
            }
        )
        
        # Create sample properties
        properties_data = [
            {
                'title': 'Luxury Apartment in Istanbul',
                'type': 'apartment',
                'country': turkey,
                'city': 'Istanbul',
                'price': 150000,
                'currency': 'USD',
                'purpose': 'sale',
                'description': 'Luxury apartment in the heart of Istanbul with Bosphorus view',
                'governorate': 'Istanbul',
                'location': 'Independence Avenue, Istanbul'
            },
            {
                'title': 'Villa in Dubai Marina',
                'type': 'villa',
                'country': uae,
                'city': 'Dubai',
                'price': 2500000,
                'currency': 'AED',
                'purpose': 'sale',
                'description': 'Luxury villa in Dubai Marina with private pool and sea view',
                'governorate': 'Dubai',
                'location': 'Dubai Marina, Dubai'
            },
            {
                'title': 'Apartment for Rent in Cairo',
                'type': 'apartment',
                'country': egypt,
                'city': 'Cairo',
                'price': 15000,
                'currency': 'EGP',
                'purpose': 'rent',
                'description': 'Modern apartment in Maadi, fully furnished',
                'governorate': 'Cairo',
                'location': 'Maadi, Cairo'
            }
        ]
        
        created_count = 0
        for prop_data in properties_data:
            try:
                prop = Property.objects.create(
                    category='property_outside',
                    status='published',
                    title=prop_data['title'],
                    slug=slugify(prop_data['title']),
                    type=prop_data['type'],
                    country=prop_data['country'],
                    city=prop_data['city'],
                    price=prop_data['price'],
                    currency=prop_data['currency'],
                    purpose=prop_data['purpose'],
                    description=prop_data['description'],
                    governorate=prop_data['governorate'],
                    location=prop_data['location']
                )
                created_count += 1
                print(f'Created: {prop.title}')
            except Exception as e:
                print(f'Error creating {prop_data["title"]}: {str(e)}')
        
        print(f'Successfully created {created_count} sample properties outside Iraq')