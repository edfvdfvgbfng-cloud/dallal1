"""
Management command to analyze image storage and optimization status
"""

from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Avg
from properties.models import Property, PropertyImage
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Analyze image storage and optimization status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--property-id',
            type=int,
            help='Analyze a specific property only',
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed per-property statistics',
        )

    def handle(self, *args, **options):
        property_id = options.get('property_id')
        detailed = options.get('detailed')

        self.stdout.write('🔍 Image Storage Analysis')
        self.stdout.write('=' * 50)

        # Base queryset
        images_qs = PropertyImage.objects.all()
        if property_id:
            images_qs = images_qs.filter(property_obj__id=property_id)
            self.stdout.write(f'Analyzing property {property_id} only')

        # General statistics
        total_images = images_qs.count()
        images_with_files = images_qs.exclude(image='').count()
        images_without_files = total_images - images_with_files

        self.stdout.write(f'\n📊 General Statistics:')
        self.stdout.write(f'  Total images: {total_images}')
        self.stdout.write(f'  Images with files: {images_with_files}')
        self.stdout.write(f'  Images without files: {images_without_files}')

        # File size analysis
        media_root = settings.MEDIA_ROOT
        total_size = 0
        image_files = []

        for image in images_qs:
            if image.image and image.image.name:
                file_path = os.path.join(media_root, image.image.name)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    image_files.append({
                        'id': image.id,
                        'property_id': image.property_obj.id,
                        'file_name': image.image.name,
                        'size': file_size,
                        'size_mb': file_size / (1024 * 1024)
                    })

        self.stdout.write(f'\n💾 Storage Analysis:')
        self.stdout.write(f'  Total storage used: {total_size / (1024 * 1024):.2f} MB')
        self.stdout.write(f'  Average file size: {total_size / max(images_with_files, 1) / (1024 * 1024):.2f} MB')

        # Format analysis
        format_counts = {}
        for img_file in image_files:
            ext = os.path.splitext(img_file['file_name'])[1].lower()
            format_counts[ext] = format_counts.get(ext, 0) + 1

        self.stdout.write(f'\n📁 Format Distribution:')
        for ext, count in sorted(format_counts.items()):
            percentage = (count / max(len(image_files), 1)) * 100
            self.stdout.write(f'  {ext}: {count} ({percentage:.1f}%)')

        # Size distribution
        size_ranges = {
            '0-1MB': 0,
            '1-5MB': 0,
            '5-10MB': 0,
            '10-50MB': 0,
            '50MB+': 0
        }

        for img_file in image_files:
            size_mb = img_file['size_mb']
            if size_mb < 1:
                size_ranges['0-1MB'] += 1
            elif size_mb < 5:
                size_ranges['1-5MB'] += 1
            elif size_mb < 10:
                size_ranges['5-10MB'] += 1
            elif size_mb < 50:
                size_ranges['10-50MB'] += 1
            else:
                size_ranges['50MB+'] += 1

        self.stdout.write(f'\n📏 Size Distribution:')
        for range_name, count in size_ranges.items():
            percentage = (count / max(len(image_files), 1)) * 100
            self.stdout.write(f'  {range_name}: {count} ({percentage:.1f}%)')

        # Detailed property analysis
        if detailed:
            self.stdout.write(f'\n🏠 Detailed Property Analysis:')
            self.stdout.write('=' * 50)

            property_stats = {}
            for img_file in image_files:
                prop_id = img_file['property_id']
                if prop_id not in property_stats:
                    property_stats[prop_id] = {
                        'count': 0,
                        'total_size': 0,
                        'avg_size': 0
                    }
                property_stats[prop_id]['count'] += 1
                property_stats[prop_id]['total_size'] += img_file['size']
                property_stats[prop_id]['avg_size'] = (
                    property_stats[prop_id]['total_size'] / property_stats[prop_id]['count']
                )

            for prop_id, stats in sorted(property_stats.items(), key=lambda x: x[1]['total_size'], reverse=True):
                try:
                    property_obj = Property.objects.get(id=prop_id)
                    prop_name = property_obj.display_title
                except Property.DoesNotExist:
                    prop_name = f'Property {prop_id} (deleted)'

                self.stdout.write(f'\n  {prop_name} (ID: {prop_id}):')
                self.stdout.write(f'    Images: {stats["count"]}')
                self.stdout.write(f'    Total size: {stats["total_size"] / (1024 * 1024):.2f} MB')
                self.stdout.write(f'    Average size: {stats["avg_size"] / (1024 * 1024):.2f} MB')

        # Optimization recommendations
        self.stdout.write(f'\n💡 Optimization Recommendations:')
        
        non_webp_count = format_counts.get('.jpg', 0) + format_counts.get('.jpeg', 0) + format_counts.get('.png', 0)
        if non_webp_count > 0:
            potential_savings = non_webp_count * 0.3  # Estimated 30% savings with WebP
            self.stdout.write(f'  • Convert {non_webp_count} images to WebP (~{potential_savings * (total_size / max(len(image_files), 1)) / (1024 * 1024):.2f} MB savings)')

        large_images = size_ranges['10-50MB'] + size_ranges['50MB+']
        if large_images > 0:
            self.stdout.write(f'  • Optimize {large_images} large images (>10MB)')

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('Analysis complete'))