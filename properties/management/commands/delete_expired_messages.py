from django.core.management.base import BaseCommand
from django.utils import timezone
from properties.models import Message


class Command(BaseCommand):
    help = 'حذف الرسائل المنتهية صلاحيتها (أكثر من 90 يوم)'

    def handle(self, *args, **options):
        """حذف الرسائل التي انتهت صلاحيتها"""
        now = timezone.now()
        
        # البحث عن الرسائل المنتهية
        expired_messages = Message.objects.filter(
            expires_at__lte=now
        )
        
        count = expired_messages.count()
        
        if count > 0:
            # حذف الرسائل المنتهية
            expired_messages.delete()
            self.stdout.write(
                self.style.SUCCESS(f'تم حذف {count} رسالة منتهية الصلاحية.')
            )
        else:
            self.stdout.write(
                self.style.WARNING('لا توجد رسائل منتهية الصلاحية.')
            )
