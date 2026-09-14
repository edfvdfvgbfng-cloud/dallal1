from django.core.management.base import BaseCommand
from properties.models import Property

class Command(BaseCommand):
    help = 'Check properties outside Iraq'

    def handle(self, *args, **options):
        properties = Property.objects.filter(category='property_outside', status='published')
        self.stdout.write(f'Found {properties.count()} properties outside Iraq')
        for prop in properties[:5]:
            country_name = prop.country.name_ar if prop.country else "No country"
            self.stdout.write(f'- {prop.title} ({prop.type}) - {country_name}')