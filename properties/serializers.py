from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Property, PropertyVerification, PropertyImage, Broker,
    Conversation, ConversationParticipant, ChatMessage,
    MessageReadStatus, MessageAttachment, MessageReport,
    ChatSettings, BlockedUser
)


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'is_primary', 'sort_order']


class BrokerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Broker
        fields = ['id', 'office_name', 'phone', 'governorate', 'is_verified', 'is_active']


class PropertyVerificationSerializer(serializers.ModelSerializer):
    """Serializer for property verification"""
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    is_verified = serializers.SerializerMethodField()
    verification_badge = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyVerification
        fields = [
            'id', 'property', 'verification_status', 'verification_status_display',
            'verification_date', 'verified_by', 'identity_verified', 'ownership_verified',
            'location_verified', 'images_verified', 'price_verified', 'verification_notes',
            'rejection_reason', 'identity_document', 'ownership_document', 'is_verified',
            'verification_badge', 'created_at', 'updated_at'
        ]
        read_only_fields = ['verification_date', 'created_at', 'updated_at']
    
    def get_is_verified(self, obj):
        return obj.is_verified()
    
    def get_verification_badge(self, obj):
        return obj.get_verification_badge()


class PropertySerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    broker = BrokerSerializer(read_only=True)
    verification = PropertyVerificationSerializer(read_only=True)
    property_type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_since_creation = serializers.SerializerMethodField()
    relevant_fields = serializers.SerializerMethodField()
    required_fields = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'slug', 'type', 'property_type_display',
            'status', 'status_display', 'district', 'street', 'location',
            'area', 'price', 'description', 'phone', 'bedrooms',
            'bathrooms', 'floors', 'year_built', 'parking', 'furnished',
            'latitude', 'longitude', 'is_featured', 'is_promoted',
            'views_count', 'created_at', 'updated_at', 'images', 'broker',
            'days_since_creation', 'verification', 'relevant_fields', 'required_fields',
            # New broker/office fields
            'office_name', 'license_number', 'additional_phone', 'preferred_contact_method',
            # New ownership fields
            'deed_type', 'deed_number', 'deed_issuing_authority', 'land_registration_status',
            'is_mortgaged', 'has_legal_issues', 'legal_issues_description', 'permit_type',
            'ownership_transfer_possible',
            # New location fields
            'complex_name', 'building_number', 'unit_number', 'floor_in_building',
            'sector_direction', 'approximate_location', 'distance_to_main_road',
            # Service proximity fields
            'distance_to_school', 'distance_to_hospital', 'distance_to_market',
            'distance_to_mosque', 'distance_to_university', 'distance_to_gas_station',
            # New pricing fields
            'total_price', 'price_per_square_meter', 'down_payment_amount',
            'number_of_installments', 'installment_amount', 'installment_duration',
            'payment_method', 'rental_deposit', 'monthly_rent', 'annual_rent',
            # New rental fields
            'minimum_rental_period', 'rental_commission', 'allows_pets', 'allows_families',
            'allows_students', 'allows_companies', 'furnishing_status',
            'includes_electricity', 'includes_water', 'includes_internet', 'includes_generator',
            # New amenities fields
            'number_of_elevators', 'has_closed_garage', 'has_security_gate', 'has_security_guard',
            'has_cctv_cameras', 'has_private_generator', 'generator_amperage',
            'has_national_electricity_line', 'has_24_hour_electricity', 'has_sewerage_system',
            'has_gas_supply', 'has_central_heating', 'has_central_cooling', 'has_central_ac',
            'has_air_conditioners', 'has_furniture', 'has_equipped_kitchen', 'has_satellite',
            'has_fiber_internet',
            # New property condition fields
            'property_age', 'number_of_facades', 'facade_type', 'street_width', 'view_type',
            'is_corner_property', 'is_corner_lot', 'distance_from_main_road', 'furniture_condition',
            'needs_renovation', 'completion_percentage',
        ]

    def get_days_since_creation(self, obj):
        from django.utils import timezone
        delta = timezone.now() - obj.created_at
        return delta.days
    
    def get_relevant_fields(self, obj):
        return obj.get_relevant_fields()
    
    def get_required_fields(self, obj):
        return obj.get_required_fields_for_type()


class PropertyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    primary_image = serializers.SerializerMethodField()
    property_type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'slug', 'type', 'property_type_display',
            'status', 'status_display', 'district', 'location',
            'area', 'price', 'phone', 'bedrooms', 'bathrooms',
            'is_featured', 'is_promoted', 'views_count', 'created_at',
            'primary_image'
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return primary.image.url if primary.image else None
        first = obj.images.first()
        return first.image.url if first and first.image else None


# ==================== Chat System Serializers ====================

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class ConversationParticipantSerializer(serializers.ModelSerializer):
    """Serializer for conversation participants"""
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ConversationParticipant
        fields = ['id', 'user', 'user_id', 'role', 'nickname', 'is_muted', 'is_pinned', 'last_read_at', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for conversations"""
    participants = ConversationParticipantSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'conversation_type', 'name', 'description',
            'group_avatar', 'created_by', 'is_active', 'is_archived',
            'last_message_at', 'created_at', 'updated_at', 'participants',
            'unread_count', 'last_message'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'updated_at']
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_unread_count(request.user)
        return 0
    
    def get_last_message(self, obj):
        last_msg = obj.get_last_message()
        if last_msg:
            return ChatMessageSerializer(last_msg, context=self.context).data
        return None


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for message attachments"""
    file_size_display = serializers.CharField(source='get_file_size_display', read_only=True)
    
    class Meta:
        model = MessageAttachment
        fields = [
            'id', 'attachment_type', 'file', 'thumbnail', 'file_name',
            'file_size', 'file_size_display', 'mime_type', 'width', 'height',
            'duration', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_at']


class MessageReadStatusSerializer(serializers.ModelSerializer):
    """Serializer for message read status"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageReadStatus
        fields = ['id', 'message', 'user', 'read_at']
        read_only_fields = ['id', 'read_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""
    sender = UserSerializer(read_only=True)
    reply_to = serializers.SerializerMethodField()
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    read_by_users = UserSerializer(many=True, source='read_by', read_only=True)
    is_read_by_current_user = serializers.SerializerMethodField()
    property_data = serializers.SerializerMethodField()
    hotel_data = serializers.SerializerMethodField()
    resort_data = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            'message_id', 'conversation', 'sender', 'message_type', 'content',
            'reply_to', 'is_edited', 'edited_at', 'is_deleted', 'deleted_at',
            'is_pinned', 'read_by_users', 'is_read_by_current_user',
            'status', 'delivered_at',
            'property', 'hotel', 'resort',
            'property_data', 'hotel_data', 'resort_data',
            'created_at', 'updated_at', 'attachments'
        ]
        read_only_fields = ['message_id', 'created_at', 'updated_at', 'delivered_at']

    def get_reply_to(self, obj):
        if obj.reply_to:
            return ChatMessageSerializer(obj.reply_to, context=self.context).data
        return None

    def get_is_read_by_current_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_read_by_user(request.user)
        return False

    def get_property_data(self, obj):
        if obj.property:
            return {
                'id': obj.property.id,
                'display_title': obj.property.display_title,
                'price': str(obj.property.price),
                'location': obj.property.get_location_display(),
                'image': obj.property.main_image.url if obj.property.main_image else None
            }
        return None

    def get_hotel_data(self, obj):
        if obj.hotel:
            return {
                'id': obj.hotel.id,
                'name': obj.hotel.name,
                'city': obj.hotel.city,
                'country': obj.hotel.country,
                'rating': obj.hotel.rating,
                'price_per_night': str(obj.hotel.price_per_night) if obj.hotel.price_per_night else None
            }
        return None

    def get_resort_data(self, obj):
        if obj.resort:
            return {
                'id': obj.resort.id,
                'name': obj.resort.name,
                'city': obj.resort.city,
                'country': obj.resort.country,
                'rating': obj.resort.rating,
                'price_per_night': str(obj.resort.price_per_night) if obj.resort.price_per_night else None
            }
        return None


class MessageReportSerializer(serializers.ModelSerializer):
    """Serializer for message reports"""
    reporter = UserSerializer(read_only=True)
    reported_user = UserSerializer(read_only=True)
    message = ChatMessageSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageReport
        fields = [
            'id', 'reporter', 'message', 'reported_user', 'report_type',
            'description', 'status', 'admin_notes', 'reviewed_by',
            'reviewed_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'reviewed_at', 'status']


class ChatSettingsSerializer(serializers.ModelSerializer):
    """Serializer for chat settings"""
    user = UserSerializer(read_only=True)
    blocked_users = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatSettings
        fields = [
            'id', 'user', 'enable_notifications', 'enable_sound',
            'enable_typing_indicator', 'enable_read_receipts',
            'enable_online_status', 'auto_archive_days',
            'message_retention_days', 'blocked_users',
            'muted_conversations', 'theme', 'font_size',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class BlockedUserSerializer(serializers.ModelSerializer):
    """Serializer for blocked users"""
    blocker = UserSerializer(read_only=True)
    blocked = UserSerializer(read_only=True)
    
    class Meta:
        model = BlockedUser
        fields = ['id', 'blocker', 'blocked', 'reason', 'blocked_at']
        read_only_fields = ['id', 'blocked_at']


class CreateConversationSerializer(serializers.Serializer):
    """Serializer for creating a new conversation"""
    conversation_type = serializers.ChoiceField(choices=Conversation.TYPE_CHOICES)
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    
    def validate(self, attrs):
        if attrs['conversation_type'] == Conversation.TYPE_GROUP:
            if not attrs.get('name'):
                raise serializers.ValidationError({'name': 'اسم المجموعة مطلوب للمحادثات الجماعية'})
        return attrs


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending a message"""
    conversation_id = serializers.UUIDField()
    message_type = serializers.ChoiceField(choices=ChatMessage.TYPE_CHOICES, default=ChatMessage.TYPE_TEXT)
    content = serializers.CharField(required=False, allow_blank=True)
    reply_to_message_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate(self, attrs):
        if attrs['message_type'] == ChatMessage.TYPE_TEXT and not attrs.get('content'):
            raise serializers.ValidationError({'content': 'المحتوى مطلوب للرسائل النصية'})
        return attrs
