"""
Message Service - Unified Messaging Layer

This service provides a unified interface for messaging operations,
abstracting the differences between Message (legacy) and ChatMessage (modern) models.

Architecture:
REST API → MessageService → Database
WebSocket → MessageService → Database
"""

import logging
from typing import Optional, Dict, List, Any, Union
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.core.files.uploadedfile import UploadedFile

from .models import (
    # Modern chat models
    ChatMessage,
    Conversation,
    ConversationParticipant,
    MessageReadStatus,
    BlockedUser,
    # Legacy message models (for compatibility)
    Message,
    MessageAttachment,
    MessageReaction,
    # Property models
    Property,
    Hotel,
    Resort,
)

logger = logging.getLogger('properties')


class LegacyMessageAdapter:
    """
    Adapter for legacy Message model to provide compatibility
    with the new MessageService interface.

    This allows gradual migration from Message to ChatMessage.
    """

    @staticmethod
    def to_chat_message(legacy_message: Message) -> Optional[ChatMessage]:
        """
        Convert legacy Message to ChatMessage format

        Args:
            legacy_message: The legacy Message instance

        Returns:
            Dictionary representing ChatMessage format or None
        """
        if not legacy_message:
            return None

        return {
            'message_id': str(legacy_message.id),  # Use integer ID for legacy
            'conversation_id': str(legacy_message.conversation.conversation_id) if legacy_message.conversation else None,
            'sender_id': legacy_message.sender.id if legacy_message.sender else None,
            'sender_username': legacy_message.sender.username if legacy_message.sender else 'Unknown',
            'message_type': legacy_message.message_type,
            'content': legacy_message.content,
            'reply_to': legacy_message.reply_to.id if legacy_message.reply_to else None,
            'is_edited': False,  # Legacy doesn't track edits
            'edited_at': None,
            'is_deleted': legacy_message.is_deleted_by_sender or legacy_message.is_deleted_by_recipient,
            'deleted_at': legacy_message.deleted_at,
            'is_pinned': False,  # Legacy doesn't support pinning
            'created_at': legacy_message.created_at.isoformat(),
            'updated_at': legacy_message.updated_at.isoformat(),
            'is_legacy': True,  # Mark as legacy message
        }

    @staticmethod
    def from_chat_message_format(data: Dict) -> Dict:
        """
        Convert ChatMessage format to legacy Message format

        Args:
            data: ChatMessage format data

        Returns:
            Dictionary in legacy Message format
        """
        return {
            'id': data.get('message_id'),
            'conversation_id': data.get('conversation_id'),
            'sender_id': data.get('sender_id'),
            'message_type': data.get('message_type'),
            'content': data.get('content'),
            'reply_to_id': data.get('reply_to'),
            'is_read': data.get('is_read', False),
            'read_at': data.get('read_at'),
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at'),
        }


class MessageServiceError(Exception):
    """Base exception for message service errors"""
    pass


class PermissionDeniedError(MessageServiceError):
    """Raised when user lacks permission"""
    pass


class MessageNotFoundError(MessageServiceError):
    """Raised when message is not found"""
    pass


class InvalidMessageTypeError(MessageServiceError):
    """Raised when message type is invalid"""
    pass


class MessageService:
    """
    Unified messaging service for handling all message operations.

    This service abstracts the complexity of having two message models
    (Message and ChatMessage) and provides a consistent interface.

    Primary Model: ChatMessage (modern, feature-rich)
    Legacy Model: Message (for backward compatibility)
    """

    # Message types (unified)
    TYPE_TEXT = 'text'
    TYPE_IMAGE = 'image'
    TYPE_VIDEO = 'video'
    TYPE_AUDIO = 'audio'
    TYPE_FILE = 'file'
    TYPE_LOCATION = 'location'
    TYPE_PROPERTY = 'property'
    TYPE_HOTEL = 'hotel'
    TYPE_RESORT = 'resort'
    TYPE_SYSTEM = 'system'

    MESSAGE_TYPES = [
        TYPE_TEXT, TYPE_IMAGE, TYPE_VIDEO, TYPE_AUDIO,
        TYPE_FILE, TYPE_LOCATION, TYPE_PROPERTY,
        TYPE_HOTEL, TYPE_RESORT, TYPE_SYSTEM
    ]

    # Message status
    STATUS_SENT = 'sent'
    STATUS_DELIVERED = 'delivered'
    STATUS_READ = 'read'
    STATUS_FAILED = 'failed'

    # Reaction types
    REACTION_LIKE = 'like'
    REACTION_LOVE = 'love'
    REACTION_HAHA = 'haha'
    REACTION_WOW = 'wow'
    REACTION_SAD = 'sad'
    REACTION_ANGRY = 'angry'
    REACTION_CLAP = 'clap'

    REACTION_TYPES = [
        REACTION_LIKE, REACTION_LOVE, REACTION_HAHA,
        REACTION_WOW, REACTION_SAD, REACTION_ANGRY, REACTION_CLAP
    ]

    REACTION_EMOJIS = {
        REACTION_LIKE: '👍',
        REACTION_LOVE: '❤️',
        REACTION_HAHA: '😂',
        REACTION_WOW: '😮',
        REACTION_SAD: '😢',
        REACTION_ANGRY: '😡',
        REACTION_CLAP: '👏',
    }

    @staticmethod
    def validate_message_type(message_type: str) -> bool:
        """Validate message type"""
        return message_type in MessageService.MESSAGE_TYPES

    @staticmethod
    def validate_reaction_type(reaction_type: str) -> bool:
        """Validate reaction type"""
        return reaction_type in MessageService.REACTION_TYPES

    @staticmethod
    def check_conversation_access(user: User, conversation: Conversation) -> bool:
        """
        Check if user has access to conversation

        Args:
            user: The user to check
            conversation: The conversation to check access for

        Returns:
            True if user has access, False otherwise
        """
        if not conversation.participants.filter(id=user.id).exists():
            return False

        # Check if user is blocked by any participant
        if BlockedUser.objects.filter(
            blocker__in=conversation.participants.all(),
            blocked=user
        ).exists():
            return False

        return True

    @staticmethod
    def check_message_edit_permission(user: User, message: ChatMessage) -> bool:
        """
        Check if user can edit the message

        Args:
            user: The user to check
            message: The message to check

        Returns:
            True if user can edit, False otherwise
        """
        # Only sender can edit
        if message.sender != user:
            return False

        # Check if message is too old to edit (24 hours)
        time_since_creation = timezone.now() - message.created_at
        if time_since_creation.total_seconds() > 86400:  # 24 hours
            return False

        return True

    @staticmethod
    def check_message_delete_permission(user: User, message: ChatMessage) -> bool:
        """
        Check if user can delete the message

        Args:
            user: The user to check
            message: The message to check

        Returns:
            True if user can delete, False otherwise
        """
        # Only sender can delete
        if message.sender != user:
            return False

        # Check if message is too old to delete (24 hours)
        time_since_creation = timezone.now() - message.created_at
        if time_since_creation.total_seconds() > 86400:  # 24 hours
            return False

        return True

    @staticmethod
    @transaction.atomic
    def send_message(
        sender: User,
        conversation: Conversation,
        message_type: str,
        content: str = '',
        reply_to: Optional[ChatMessage] = None,
        property_obj: Optional[Property] = None,
        hotel: Optional[Hotel] = None,
        resort: Optional[Resort] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location_name: str = '',
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """
        Send a new message

        Args:
            sender: The user sending the message
            conversation: The conversation to send to
            message_type: Type of message (text, image, etc.)
            content: Message content
            reply_to: Message to reply to (optional)
            property_obj: Property to share (optional)
            hotel: Hotel to share (optional)
            resort: Resort to share (optional)
            latitude: Location latitude (optional)
            longitude: Location longitude (optional)
            location_name: Location name (optional)
            metadata: Additional metadata (optional)

        Returns:
            Created ChatMessage instance

        Raises:
            PermissionDeniedError: If user lacks access
            InvalidMessageTypeError: If message type is invalid
        """
        # Validate message type
        if not MessageService.validate_message_type(message_type):
            raise InvalidMessageTypeError(f"Invalid message type: {message_type}")

        # Check conversation access
        if not MessageService.check_conversation_access(sender, conversation):
            raise PermissionDeniedError("User does not have access to this conversation")

        # Validate reply_to
        if reply_to:
            if reply_to.conversation != conversation:
                raise PermissionDeniedError("Cannot reply to message from different conversation")
            if reply_to.is_deleted:
                raise PermissionDeniedError("Cannot reply to deleted message")

        # Create message
        message = ChatMessage.objects.create(
            conversation=conversation,
            sender=sender,
            message_type=message_type,
            content=content,
            reply_to=reply_to,
            property=property_obj,
            hotel=hotel,
            resort=resort,
        )

        # Update conversation timestamp
        conversation.last_message_at = timezone.now()
        conversation.save()

        logger.info(
            f"Message sent: {message.message_id} by {sender.username} "
            f"in conversation {conversation.conversation_id}"
        )

        return message

    @staticmethod
    @transaction.atomic
    def edit_message(
        user: User,
        message: ChatMessage,
        new_content: str
    ) -> ChatMessage:
        """
        Edit an existing message

        Args:
            user: The user editing the message
            message: The message to edit
            new_content: New message content

        Returns:
            Updated ChatMessage instance

        Raises:
            PermissionDeniedError: If user lacks permission
            MessageNotFoundError: If message is not found
        """
        # Check permission
        if not MessageService.check_message_edit_permission(user, message):
            raise PermissionDeniedError("User does not have permission to edit this message")

        # Update message
        message.edit(new_content)

        logger.info(
            f"Message edited: {message.message_id} by {user.username}"
        )

        return message

    @staticmethod
    @transaction.atomic
    def delete_message(
        user: User,
        message: ChatMessage,
        delete_for_everyone: bool = False
    ) -> bool:
        """
        Delete a message (soft delete)

        Args:
            user: The user deleting the message
            message: The message to delete
            delete_for_everyone: If True, delete for all participants

        Returns:
            True if successful

        Raises:
            PermissionDeniedError: If user lacks permission
            MessageNotFoundError: If message is not found
        """
        # Check permission
        if not MessageService.check_message_delete_permission(user, message):
            raise PermissionDeniedError("User does not have permission to delete this message")

        # Soft delete
        message.soft_delete()

        logger.info(
            f"Message deleted: {message.message_id} by {user.username} "
            f"(for everyone: {delete_for_everyone})"
        )

        return True

    @staticmethod
    @transaction.atomic
    def mark_as_delivered(message: ChatMessage) -> bool:
        """
        Mark message as delivered

        Args:
            message: The message to mark as delivered

        Returns:
            True if successful
        """
        message.mark_as_delivered()
        logger.info(f"Message marked as delivered: {message.message_id}")
        return True

    @staticmethod
    @transaction.atomic
    def mark_as_read(user: User, message: ChatMessage) -> bool:
        """
        Mark message as read by user

        Args:
            user: The user reading the message
            message: The message to mark as read

        Returns:
            True if successful
        """
        # Check if user is in conversation
        if not message.conversation.participants.filter(id=user.id).exists():
            raise PermissionDeniedError("User is not a participant in this conversation")

        # Create or update read status
        MessageReadStatus.objects.get_or_create(
            message=message,
            user=user,
            defaults={'read_at': timezone.now()}
        )

        logger.info(
            f"Message marked as read: {message.message_id} by {user.username}"
        )

        return True

    @staticmethod
    @transaction.atomic
    def mark_conversation_as_read(user: User, conversation: Conversation) -> int:
        """
        Mark all messages in conversation as read for user

        Args:
            user: The user reading the conversation
            conversation: The conversation to mark as read

        Returns:
            Number of messages marked as read
        """
        # Check access
        if not MessageService.check_conversation_access(user, conversation):
            raise PermissionDeniedError("User does not have access to this conversation")

        # Get unread messages
        unread_messages = conversation.chat_messages.filter(
            ~Q(read_by=user)
        ).exclude(sender=user)

        count = 0
        for message in unread_messages:
            MessageService.mark_as_read(user, message)
            count += 1

        logger.info(
            f"Conversation marked as read: {conversation.conversation_id} "
            f"by {user.username} ({count} messages)"
        )

        return count

    @staticmethod
    @transaction.atomic
    def reply_message(
        sender: User,
        conversation: Conversation,
        reply_to: ChatMessage,
        content: str
    ) -> ChatMessage:
        """
        Reply to a message

        Args:
            sender: The user sending the reply
            conversation: The conversation
            reply_to: The message to reply to
            content: Reply content

        Returns:
            Created ChatMessage instance

        Raises:
            PermissionDeniedError: If user lacks permission
            MessageNotFoundError: If reply_to message is not found
        """
        return MessageService.send_message(
            sender=sender,
            conversation=conversation,
            message_type=MessageService.TYPE_TEXT,
            content=content,
            reply_to=reply_to
        )

    @staticmethod
    @transaction.atomic
    def forward_message(
        sender: User,
        message: ChatMessage,
        target_conversations: List[Conversation]
    ) -> List[ChatMessage]:
        """
        Forward a message to multiple conversations

        Args:
            sender: The user forwarding the message
            message: The message to forward
            target_conversations: List of conversations to forward to

        Returns:
            List of created ChatMessage instances

        Raises:
            PermissionDeniedError: If user lacks permission
        """
        forwarded_messages = []

        for conversation in target_conversations:
            # Check access
            if not MessageService.check_conversation_access(sender, conversation):
                logger.warning(
                    f"User {sender.username} cannot forward to "
                    f"conversation {conversation.conversation_id}"
                )
                continue

            # Create forwarded message
            forwarded = ChatMessage.objects.create(
                conversation=conversation,
                sender=sender,
                message_type=message.message_type,
                content=message.content,
                property=message.property,
                hotel=message.hotel,
                resort=message.resort,
            )

            forwarded_messages.append(forwarded)

        logger.info(
            f"Message {message.message_id} forwarded by {sender.username} "
            f"to {len(forwarded_messages)} conversations"
        )

        return forwarded_messages

    @staticmethod
    @transaction.atomic
    def add_reaction(
        user: User,
        message: ChatMessage,
        reaction_type: str
    ) -> bool:
        """
        Add or update reaction to message

        Args:
            user: The user adding the reaction
            message: The message to react to
            reaction_type: Type of reaction (like, love, etc.)

        Returns:
            True if successful

        Raises:
            InvalidMessageTypeError: If reaction type is invalid
            PermissionDeniedError: If user lacks access
        """
        # Validate reaction type
        if not MessageService.validate_reaction_type(reaction_type):
            raise InvalidMessageTypeError(f"Invalid reaction type: {reaction_type}")

        # Check access
        if not message.conversation.participants.filter(id=user.id).exists():
            raise PermissionDeniedError("User is not a participant in this conversation")

        # Check if user already has a reaction
        existing_reaction = MessageReaction.objects.filter(
            message=message,  # Note: This is for Message model, need to adapt
            user=user
        ).first()

        # TODO: Adapt for ChatMessage - create ChatMessageReaction model
        # For now, we'll log the action
        logger.info(
            f"Reaction added: {reaction_type} by {user.username} "
            f"to message {message.message_id}"
        )

        return True

    @staticmethod
    @transaction.atomic
    def remove_reaction(
        user: User,
        message: ChatMessage
    ) -> bool:
        """
        Remove user's reaction from message

        Args:
            user: The user removing the reaction
            message: The message to remove reaction from

        Returns:
            True if successful
        """
        # TODO: Adapt for ChatMessage - create ChatMessageReaction model
        logger.info(
            f"Reaction removed by {user.username} from message {message.message_id}"
        )

        return True

    @staticmethod
    @transaction.atomic
    def send_attachment(
        sender: User,
        conversation: Conversation,
        attachment_type: str,
        file: UploadedFile,
        file_name: str,
        file_size: int,
        duration: Optional[int] = None,
        mime_type: Optional[str] = None
    ) -> ChatMessage:
        """
        Send a file attachment

        Args:
            sender: The user sending the attachment
            conversation: The conversation
            attachment_type: Type of attachment (image, video, audio, file)
            file: The uploaded file
            file_name: Original file name
            file_size: File size in bytes
            duration: Duration for audio/video (optional)
            mime_type: MIME type (optional)

        Returns:
            Created ChatMessage instance

        Raises:
            PermissionDeniedError: If user lacks access
            InvalidMessageTypeError: If attachment type is invalid
        """
        # Validate attachment type
        valid_types = [MessageService.TYPE_IMAGE, MessageService.TYPE_VIDEO,
                      MessageService.TYPE_AUDIO, MessageService.TYPE_FILE]
        if attachment_type not in valid_types:
            raise InvalidMessageTypeError(f"Invalid attachment type: {attachment_type}")

        # Check access
        if not MessageService.check_conversation_access(sender, conversation):
            raise PermissionDeniedError("User does not have access to this conversation")

        # Create message with attachment
        message = ChatMessage.objects.create(
            conversation=conversation,
            sender=sender,
            message_type=attachment_type,
            content=file_name,
        )

        # TODO: Create ChatMessageAttachment model
        # For now, we'll log the action
        logger.info(
            f"Attachment sent: {attachment_type} by {sender.username} "
            f"in conversation {conversation.conversation_id}"
        )

        return message

    @staticmethod
    @transaction.atomic
    def share_property(
        sender: User,
        conversation: Conversation,
        property_obj: Property
    ) -> ChatMessage:
        """
        Share a property in conversation

        Args:
            sender: The user sharing the property
            conversation: The conversation
            property_obj: The property to share

        Returns:
            Created ChatMessage instance

        Raises:
            PermissionDeniedError: If user lacks access
        """
        return MessageService.send_message(
            sender=sender,
            conversation=conversation,
            message_type=MessageService.TYPE_PROPERTY,
            content=f"Shared property: {property_obj.display_title}",
            property_obj=property_obj
        )

    @staticmethod
    @transaction.atomic
    def share_hotel(
        sender: User,
        conversation: Conversation,
        hotel: Hotel
    ) -> ChatMessage:
        """
        Share a hotel in conversation

        Args:
            sender: The user sharing the hotel
            conversation: The conversation
            hotel: The hotel to share

        Returns:
            Created ChatMessage instance

        Raises:
            PermissionDeniedError: If user lacks access
        """
        return MessageService.send_message(
            sender=sender,
            conversation=conversation,
            message_type=MessageService.TYPE_HOTEL,
            content=f"Shared hotel: {hotel.name}",
            hotel=hotel
        )

    @staticmethod
    @transaction.atomic
    def share_resort(
        sender: User,
        conversation: Conversation,
        resort: Resort
    ) -> ChatMessage:
        """
        Share a resort in conversation

        Args:
            sender: The user sharing the resort
            conversation: The conversation
            resort: The resort to share

        Returns:
            Created ChatMessage instance

        Raises:
            PermissionDeniedError: If user lacks access
        """
        return MessageService.send_message(
            sender=sender,
            conversation=conversation,
            message_type=MessageService.TYPE_RESORT,
            content=f"Shared resort: {resort.name}",
            resort=resort
        )

    @staticmethod
    def get_unread_count(user: User, conversation: Conversation) -> int:
        """
        Get unread message count for user in conversation

        Args:
            user: The user
            conversation: The conversation

        Returns:
            Number of unread messages
        """
        return conversation.chat_messages.exclude(
            read_by=user
        ).exclude(sender=user).count()

    @staticmethod
    def get_conversation_messages(
        conversation: Conversation,
        user: User,
        limit: int = 50,
        before: Optional[str] = None
    ) -> List[ChatMessage]:
        """
        Get messages from conversation with pagination

        Args:
            conversation: The conversation
            user: The user requesting messages
            limit: Maximum number of messages to return
            before: Get messages before this message_id (cursor pagination)

        Returns:
            List of ChatMessage instances

        Raises:
            PermissionDeniedError: If user lacks access
        """
        # Check access
        if not MessageService.check_conversation_access(user, conversation):
            raise PermissionDeniedError("User does not have access to this conversation")

        # Build queryset
        queryset = conversation.chat_messages.filter(is_deleted=False)

        # Cursor pagination
        if before:
            queryset = queryset.filter(message_id__lt=before)

        # Order and limit
        queryset = queryset.order_by('-created_at')[:limit]

        return list(queryset)

    @staticmethod
    def search_messages(
        user: User,
        query: str,
        conversation: Optional[Conversation] = None
    ) -> List[ChatMessage]:
        """
        Search messages by content

        Args:
            user: The user searching
            query: Search query
            conversation: Optional conversation to limit search to

        Returns:
            List of matching ChatMessage instances
        """
        from django.db.models import Q

        # Build base queryset
        queryset = ChatMessage.objects.filter(
            conversation__participants=user
        ).filter(is_deleted=False)

        # Limit to specific conversation if provided
        if conversation:
            queryset = queryset.filter(conversation=conversation)

        # Search in content
        queryset = queryset.filter(content__icontains=query)

        return list(queryset.order_by('-created_at')[:50])


class MessageServiceCompatibility:
    """
    Compatibility layer for legacy Message model operations.

    This provides methods to work with the legacy Message model
    while the system transitions to ChatMessage.
    """

    @staticmethod
    @transaction.atomic
    def send_legacy_message(
        sender: User,
        recipient: User,
        message_type: str,
        content: str = '',
        conversation: Optional[Conversation] = None
    ) -> Message:
        """
        Send a legacy message using the old Message model

        Args:
            sender: The user sending the message
            recipient: The user receiving the message
            message_type: Type of message
            content: Message content
            conversation: Optional conversation

        Returns:
            Created Message instance
        """
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            content=content,
            status=Message.STATUS_SENT
        )

        logger.info(
            f"Legacy message sent: {message.id} from {sender.username} to {recipient.username}"
        )

        return message

    @staticmethod
    def get_legacy_messages(user: User, limit: int = 50) -> List[Message]:
        """
        Get legacy messages for a user

        Args:
            user: The user
            limit: Maximum number of messages

        Returns:
            List of Message instances
        """
        return list(
            Message.objects.filter(
                Q(sender=user) | Q(recipient=user)
            ).order_by('-created_at')[:limit]
        )

    @staticmethod
    def migrate_to_chat_message(legacy_message: Message) -> Optional[ChatMessage]:
        """
        Migrate a legacy Message to ChatMessage

        Args:
            legacy_message: The legacy Message to migrate

        Returns:
            Created ChatMessage instance or None
        """
        # Check if conversation exists
        if not legacy_message.conversation:
            logger.warning(f"Legacy message {legacy_message.id} has no conversation, skipping migration")
            return None

        # Create ChatMessage
        chat_message = ChatMessage.objects.create(
            conversation=legacy_message.conversation,
            sender=legacy_message.sender,
            message_type=legacy_message.message_type,
            content=legacy_message.content,
            reply_to=None,  # Will need to handle reply_to migration separately
        )

        logger.info(
            f"Migrated legacy message {legacy_message.id} to ChatMessage {chat_message.message_id}"
        )

        return chat_message
