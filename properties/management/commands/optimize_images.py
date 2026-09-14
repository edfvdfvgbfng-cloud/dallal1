"""
Management command to optimize existing property images
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from properties.models import Property, PropertyImage
from properties.image_optimization import ImageOptimizer, ImageCDNService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Optimize existing property images and create thumbnails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--property-id',
            type=int,
            help='Optimize images for a specific property only',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-optimization even if optimized versions exist',
        )
        parser.add_argument(
            '--upload-cdn',
            action='store_true',
            help='Upload optimized images to CDN',
        )
        parser.add_argument(
            '--quality',
            type=int,
            default=85,
            help='JPEG quality (1-100)',
        )
        parser.add_argument(
            '--webp',
            action='store_true',
            default=True,
            help='Convert to WebP format',
        )

    def handle(self, *args, **options):
        property_id = options.get('property_id')
        force = options.get('force')
        upload_cdn = options.get('upload_cdn')
        quality = options.get('quality')
        webp = options.get('webp')

        self.stdout.write('Starting image optimization...')

        # Get properties to process
        if property_id:
            properties = Property.objects.filter(id=property_id)
            self.stdout.write(f'Processing property {property_id} only')
        else:
            properties = Property.objects.all()
            self.stdout.write('Processing all properties')

        total_processed = 0
        total_errors = 0

        for property_obj in properties:
            self.stdout.write(f'\nProcessing property: {property_obj.display_title} (ID: {property_obj.id})')

            images = property_obj.gallery_images.all()
            property_processed = 0
            property_errors = 0

            for image in images:
                try:
                    if not image.image:
                        self.stdout.write(f'  Skipping image {image.id} - no file')
                        continue

                    # Optimize main image
                    self.stdout.write(f'  Optimizing image {image.id}: {image.image.name}')

                    optimized_file = ImageOptimizer.optimize_image(
                        image.image,
                        quality=quality,
                        convert_to_webp=webp
                    )

                    if optimized_file != image.image:
                        # Save optimized version
                        image.image.save(
                            optimized_file.name,
                            optimized_file,
                            save=True
                        )
                        self.stdout.write(f'    ✓ Optimized: {optimized_file.name}')
                        property_processed += 1

                    # Create thumbnails
                    thumbnails = ImageOptimizer.create_thumbnails(image.image)
                    if thumbnails:
                        self.stdout.write(f'    ✓ Created {len(thumbnails)} thumbnails')
                        property_processed += len(thumbnails)

                    # Upload to CDN if requested
                    if upload_cdn:
                        cdn_url = ImageCDNService.upload_to_cdn(
                            image.image,
                            f'properties/{property_obj.id}'
                        )
                        if cdn_url:
                            self.stdout.write(f'    ✓ Uploaded to CDN: {cdn_url}')
                            property_processed += 1

                except Exception as e:
                    self.stdout.write(f'  ✗ Error processing image {image.id}: {str(e)}')
                    property_errors += 1
                    total_errors += 1

            total_processed += property_processed
            total_errors += property_errors

            self.stdout.write(
                f'  Property completed: {property_processed} images processed, '
                f'{property_errors} errors'
            )

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(f'Total images processed: {total_processed}')
        self.stdout.write(f'Total errors: {total_errors}')
        self.stdout.write('=' * 50)

        if total_errors > 0:
            self.stdout.write(self.style.WARNING('Completed with errors'))
        else:
            self.stdout.write(self.style.SUCCESS('Completed successfully'))