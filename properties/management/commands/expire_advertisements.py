from django.core.management.base import BaseCommand
from django.utils import timezone
from properties.models import ServiceAdvertisement


class Command(BaseCommand):
    help = 'Disable expired advertisements automatically'

    def handle(self, *args, **options):
        now = timezone.now()
        expired_ads = ServiceAdvertisement.objects.filter(
            status='active',
            expires_at__lt=now
        )
        
        count = expired_ads.update(status='expired')
        
        self.stdout.write(
            self.style.SUCCESS(f'Disabled {count} expired advertisements')
        )