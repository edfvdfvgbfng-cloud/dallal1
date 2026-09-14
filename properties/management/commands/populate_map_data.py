"""
Django management command to populate map data
Generates area statistics, heatmap data, and sample amenities
"""

from django.core.management.base import BaseCommand
from django.db.models import Avg, Min, Max, Count
from properties.models import Property, AreaStats, Amenity, HeatmapData
from properties.constants import IRAQ_GOVERNORATES


class Command(BaseCommand):
    help = 'Populate map data including area statistics, heatmap data, and sample amenities'

    def handle(self, *args, **options):
        self.stdout.write('Starting to populate map data...')

        # Generate area statistics
        self.generate_area_stats()

        # Generate heatmap data
        self.generate_heatmap_data()

        # Create sample amenities
        self.create_sample_amenities()

        self.stdout.write(self.style.SUCCESS('Successfully populated map data'))

    def generate_area_stats(self):
        """Generate area statistics for all cities"""
        self.stdout.write('Generating area statistics...')

        cities = Property.objects.filter(
            status='available',
            city__isnull=False
        ).values_list('governorate', 'city').distinct()

        for governorate, city in cities:
            # Create or update area stats
            area_stats, created = AreaStats.objects.get_or_create(
                governorate=governorate,
                city=city,
                district='',
                area=''
            )

            # Update statistics
            area_stats.update_stats()

            self.stdout.write(f'  - Updated stats for {governorate} - {city}')

        self.stdout.write(self.style.SUCCESS('Area statistics generated'))

    def generate_heatmap_data(self):
        """Generate heatmap data for major cities"""
        self.stdout.write('Generating heatmap data...')

        major_cities = [
            ('بغداد', 'بغداد'),
            ('البصرة', 'البصرة'),
            ('نينوى', 'الموصل'),
            ('أربيل', 'أربيل'),
            ('النجف', 'النجف'),
            ('كربلاء', 'كربلاء'),
        ]

        for governorate, city in major_cities:
            try:
                heatmap_data = HeatmapData.generate_heatmap(
                    governorate=governorate,
                    city=city,
                    grid_size=0.01
                )
                self.stdout.write(f'  - Generated {len(heatmap_data)} heatmap cells for {city}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  - Failed to generate heatmap for {city}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Heatmap data generated'))

    def create_sample_amenities(self):
        """Create sample amenities for major cities"""
        self.stdout.write('Creating sample amenities...')

        sample_amenities = [
            {
                'name': 'جامعة بغداد',
                'amenity_type': 'university',
                'governorate': 'بغداد',
                'city': 'بغداد',
                'latitude': 33.3152,
                'longitude': 44.3661,
                'education_level': 'جامعي',
                'student_count': 50000
            },
            {
                'name': 'مستشفى بغداد التعليمي',
                'amenity_type': 'hospital',
                'governorate': 'بغداد',
                'city': 'بغداد',
                'latitude': 33.3200,
                'longitude': 44.3700,
                'bed_count': 500,
                'emergency_services': True
            },
            {
                'name': 'سوق الشورجة',
                'amenity_type': 'market',
                'governorate': 'بغداد',
                'city': 'بغداد',
                'latitude': 33.3250,
                'longitude': 44.3750
            },
            {
                'name': 'جامعة البصرة',
                'amenity_type': 'university',
                'governorate': 'البصرة',
                'city': 'البصرة',
                'latitude': 30.5081,
                'longitude': 47.7835,
                'education_level': 'جامعي',
                'student_count': 30000
            },
            {
                'name': 'مستشفى البصرة العام',
                'amenity_type': 'hospital',
                'governorate': 'البصرة',
                'city': 'البصرة',
                'latitude': 30.5100,
                'longitude': 47.7900,
                'bed_count': 400,
                'emergency_services': True
            },
            {
                'name': 'جامعة الموصل',
                'amenity_type': 'university',
                'governorate': 'نينوى',
                'city': 'الموصل',
                'latitude': 36.3489,
                'longitude': 43.1576,
                'education_level': 'جامعي',
                'student_count': 35000
            },
            {
                'name': 'مستشفى الموصل العام',
                'amenity_type': 'hospital',
                'governorate': 'نينوى',
                'city': 'الموصل',
                'latitude': 36.3500,
                'longitude': 43.1600,
                'bed_count': 450,
                'emergency_services': True
            },
        ]

        for amenity_data in sample_amenities:
            amenity, created = Amenity.objects.get_or_create(
                name=amenity_data['name'],
                defaults=amenity_data
            )
            if created:
                self.stdout.write(f'  - Created {amenity.name}')
            else:
                self.stdout.write(f'  - {amenity.name} already exists')

        self.stdout.write(self.style.SUCCESS('Sample amenities created'))