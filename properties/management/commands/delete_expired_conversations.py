from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from properties.models import BrokerConversation, BrokerMessage


class Command(BaseCommand):
    help = 'Delete expired broker conversations and their messages'

    def handle(self, *args, **options):
        # Get conversations that are expired
        expired_conversations = BrokerConversation.objects.filter(
            is_active=True,
            expires_at__lt=timezone.now()
        )
        
        count = expired_conversations.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No expired conversations found.'))
            return
        
        # Delete expired conversations
        for conversation in expired_conversations:
            conversation.is_active = False
            conversation.save()
            self.stdout.write(f'Marked conversation {conversation.conversation_id} as expired')
        
        # Optionally, you can also completely delete old conversations (older than 2 months)
        two_months_ago = timezone.now() - timedelta(days=60)
        old_conversations = BrokerConversation.objects.filter(
            expires_at__lt=two_months_ago
        )
        
        old_count = old_conversations.count()
        if old_count > 0:
            # Delete messages first
            BrokerMessage.objects.filter(
                conversation__in=old_conversations
            ).delete()
            
            # Delete conversations
            old_conversations.delete()
            self.stdout.write(f'Deleted {old_count} old conversations permanently')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {count} expired conversations. '
                f'Deleted {old_count} old conversations permanently.'
            )
        )