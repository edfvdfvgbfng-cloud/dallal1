from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

from .models import (
    Property, PropertyImage, SiteSettings, Broker, BrokerJoinRequest, Office,
    PropertyRating, BrokerRating, TwoFactorAuth, SecurityLog,
    DallalGlobalSettings, BasicDallalSettings, PremiumDallalSettings,
    DallalSubscription, PropertyDallalAssignment, SubscriptionPlan, BrokerChannel,
    Conversation, Message, MessageAttachment, MessageReaction, MessageReport,
    Country, City, Area, LiveStream, LiveStreamComment, PropertyVideo, PropertyDocument,
    PropertyMediaStats, PropertyViewStats, PropertyEngagementStats, PropertyConversionStats,
    AdvancedSubscriptionPlan, BrokerPlanSubscription, SubscriptionRenewalRequest,
    AuctionSubscription, Role, UserRole, PermissionLog,
    JobCategory, Job, JobApplication,
    TravelCompany, TravelCompanyImage, TravelCompanyVideo, TravelCompanyReview, TravelCompanyRatingBreakdown,
    ServiceProviderCategory, ServiceProviderPage, ServiceProviderService, ServiceBooking, ServiceProviderSchedule, 
    ServiceProviderAvailability, ServiceProviderReview, ServiceProviderRatingBreakdown, SupportMessage
)


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ('image', 'caption', 'sort_order', 'is_primary', 'image_type')


class PropertyVideoInline(admin.TabularInline):
    model = PropertyVideo
    extra = 1
    fields = ('video', 'caption', 'sort_order', 'video_type', 'duration')


class PropertyDocumentInline(admin.TabularInline):
    model = PropertyDocument
    extra = 1
    fields = ('document_type', 'title', 'file', 'description')


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        'display_title', 'type', 'district', 'price', 'status',
        'is_featured', 'is_promoted', 'views_count', 'like_count', 'created_at',
    )
    list_filter = ('type', 'status', 'category', 'governorate', 'is_featured', 'is_promoted', 'parking', 'furnished')
    search_fields = ('title', 'location', 'district', 'street', 'description', 'phone', 'slug', 'property_number')
    list_editable = ('is_featured', 'is_promoted')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('views_count', 'created_at', 'updated_at', 'short_share_code')
    inlines = [PropertyImageInline, PropertyVideoInline, PropertyDocumentInline]
    list_per_page = 25
    actions = ['mark_as_featured', 'mark_as_promoted', 'activate_properties', 'deactivate_properties']

    def like_count(self, obj):
        try:
            return obj.propertylike.count()
        except:
            return 0
    like_count.short_description = 'الإعجابات'

    @admin.action(description='تعليم كمميز')
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f'تم تعليم {queryset.count()} عقار كمميز')

    @admin.action(description='تعليم كمروج')
    def mark_as_promoted(self, request, queryset):
        queryset.update(is_promoted=True)
        self.message_user(request, f'تم تعليم {queryset.count()} عقار كمروج')

    @admin.action(description='تفعيل العقارات')
    def activate_properties(self, request, queryset):
        queryset.update(status='available')
        self.message_user(request, f'تم تفعيل {queryset.count()} عقار')

    @admin.action(description='تعطيل العقارات')
    def deactivate_properties(self, request, queryset):
        queryset.update(status='sold')
        self.message_user(request, f'تم تعطيل {queryset.count()} عقار')

    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('title', 'slug', 'property_number', 'category', 'type', 'status', 
                      'is_featured', 'is_promoted', 'promotion_until', 'publication_type')
        }),
        ('المالك والدلال', {
            'fields': ('owner', 'owner_name', 'broker', 'office')
        }),
        ('الموقع داخل العراق', {
            'fields': ('governorate', 'city', 'district', 'subdistrict', 'nahiyah', 
                      'street', 'landmark', 'location')
        }),
        ('الموقع خارج العراق', {
            'fields': ('country', 'city_outside', 'area_outside', 'postal_code',
                      'taxes', 'registration_fees', 'foreign_ownership_laws'),
            'classes': ('collapse',)
        }),
        ('الإحداثيات', {
            'fields': ('latitude', 'longitude', 'nearest_landmark', 
                      'distance_to_city_center', 'distance_to_airport')
        }),
        ('السعر والعملة', {
            'fields': ('price', 'currency', 'original_price', 'negotiable')
        }),
        ('المساحة والبناء', {
            'fields': ('total_area', 'building_area', 'area', 'facade', 'direction', 
                      'year_built', 'building_condition', 'total_floors', 'floor_number',
                      'property_age', 'last_renovation')
        }),
        ('الغرف والمرافق', {
            'fields': ('bedrooms', 'living_rooms', 'dining_rooms', 'bathrooms', 
                      'kitchens', 'balconies', 'parking_spaces', 'parking_type')
        }),
        ('المرافق الأساسية', {
            'fields': ('parking', 'furnished', 'has_pool', 'has_garden', 'has_elevator', 
                      'has_generator', 'has_national_electricity', 'has_water', 'has_internet', 
                      'has_sewerage', 'has_heating', 'has_cooling', 'has_solar_power')
        }),
        ('الأمان', {
            'fields': ('has_security_system', 'has_cctv', 'has_alarm'),
            'classes': ('collapse',)
        }),
        ('معلومات الفنادق والمنتجعات', {
            'fields': ('hotel_stars', 'hotel_rating', 'hotel_rooms', 'hotel_suites', 
                      'hotel_family_rooms', 'has_restaurant', 'has_cafe', 'has_swimming_pool', 
                      'has_gym', 'has_spa', 'has_conference_hall', 'has_wifi', 'has_parking', 
                      'has_room_service', 'has_laundry', 'has_airport_shuttle'),
            'classes': ('collapse',)
        }),
        ('معلومات المنتجعات السياحية', {
            'fields': ('resort_capacity', 'resort_activities', 'booking_available', 
                      'booking_url', 'min_booking_duration', 'max_booking_duration'),
            'classes': ('collapse',)
        }),
        ('الجولات الافتراضية والوسائط', {
            'fields': ('virtual_tour_url', 'vr_tour_url', 'ar_available', 'qr_code', 
                      'short_share_code'),
            'classes': ('collapse',)
        }),
        ('البث المباشر', {
            'fields': ('live_stream_enabled', 'live_stream_url', 'live_stream_scheduled', 
                      'live_stream_status'),
            'classes': ('collapse',)
        }),
        ('الذكاء الاصطناعي', {
            'fields': ('ai_generated_description', 'ai_suggested_price', 'ai_keywords', 
                      'ai_image_enhanced'),
            'classes': ('collapse',)
        }),
        ('الرسوم الإضافية', {
            'fields': ('maintenance_fee', 'hoa_fee'),
            'classes': ('collapse',)
        }),
        ('إمكانية الوصول', {
            'fields': ('wheelchair_accessible', 'has_ramp', 'has_elevator_accessibility'),
            'classes': ('collapse',)
        }),
        ('الميزات الخضراء', {
            'fields': ('energy_efficient', 'has_green_building_cert', 'has_smart_home', 
                      'has_double_glazing', 'has_insulation'),
            'classes': ('collapse',)
        }),
        ('الإطلالة', {
            'fields': ('view_type',)
        }),
        ('المحتوى', {
            'fields': ('description', 'phone')
        }),
        ('إحصائيات', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_participants', 'created_at', 'updated_at')
    search_fields = ('participants__username',)
    
    def get_participants(self, obj):
        return ', '.join([p.username for p in obj.participants.all()])
    get_participants.short_description = 'المشاركون'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'recipient', 'message_type', 'status', 'is_read', 'created_at')
    list_filter = ('message_type', 'status', 'is_read', 'created_at')
    search_fields = ('content', 'sender__username', 'recipient__username')
    list_editable = ('is_read',)
    actions = ['mark_read', 'mark_unread']

    @admin.action(description='تعليم كمقروء')
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description='تعليم كغير مقروء')
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ('message', 'attachment_type', 'file_name', 'file_size')
    list_filter = ('attachment_type',)
    search_fields = ('file_name', 'message__content')


@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ('message', 'user', 'reaction_type', 'created_at')
    list_filter = ('reaction_type', 'created_at')
    search_fields = ('user__username', 'message__content')


@admin.register(MessageReport)
class MessageReportAdmin(admin.ModelAdmin):
    list_display = ('message', 'reporter', 'report_type', 'status', 'created_at')
    list_filter = ('report_type', 'status', 'created_at')
    search_fields = ('reporter__username', 'description')
    list_editable = ('status',)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'sort_order', 'is_primary', 'preview')
    list_filter = ('is_primary',)

    @admin.display(description='معاينة')
    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" style="border-radius:8px"/>', obj.image.url)
        return '-'

@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'role', 'phone', 'subscription_plan', 'is_verified', 'is_active', 'properties_count')
    list_filter = ('role', 'subscription_plan', 'is_verified', 'is_active')
    search_fields = ('user__username', 'user__first_name', 'phone', 'office_name')
    actions = ['verify_brokers', 'activate_brokers', 'deactivate_brokers']

    def properties_count(self, obj):
        return obj.property_set.count()
    properties_count.short_description = 'عدد العقارات'

    @admin.action(description='توثيق الوسطاء')
    def verify_brokers(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f'تم توثيق {queryset.count()} وسيط')

    @admin.action(description='تفعيل الوسطاء')
    def activate_brokers(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'تم تفعيل {queryset.count()} وسيط')

    @admin.action(description='تعطيل الوسطاء')
    def deactivate_brokers(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'تم تعطيل {queryset.count()} وسيط')


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'period', 'ads_limit', 'price', 'is_active')
    list_filter = ('period', 'is_active')
    search_fields = ('name',)
    list_editable = ('is_active',)


@admin.register(AdvancedSubscriptionPlan)
class AdvancedSubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'tier', 'price_per_day', 'max_properties', 'is_active')
    list_filter = ('plan_type', 'tier', 'is_active')
    search_fields = ('name',)
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(BrokerPlanSubscription)
class BrokerPlanSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('broker', 'plan', 'start_date', 'end_date', 'status', 'properties_used', 'get_seconds_remaining')
    list_filter = ('status', 'plan__plan_type', 'plan__tier')
    search_fields = ('broker__display_name', 'plan__name')
    readonly_fields = ('get_seconds_remaining', 'created_at', 'updated_at', 'properties_used', 'auctions_used', 'building_requests_used')
    
    def get_seconds_remaining(self, obj):
        return obj.get_seconds_remaining()
    get_seconds_remaining.short_description = 'الثواني المتبقية'
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(SubscriptionRenewalRequest)
class SubscriptionRenewalRequestAdmin(admin.ModelAdmin):
    list_display = ('broker', 'plan', 'days_requested', 'estimated_cost', 'status', 'created_at')
    list_filter = ('status', 'plan__plan_type')
    search_fields = ('broker__display_name', 'plan__name')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'ip_address', 'user_agent')
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(AuctionSubscription)
class AuctionSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('broker', 'price_per_auction', 'status', 'auctions_used', 'auctions_paid', 'total_paid')
    list_filter = ('status',)
    search_fields = ('broker__display_name',)
    readonly_fields = ('created_at', 'updated_at', 'auctions_used', 'auctions_paid', 'total_paid')
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'priority', 'is_active')
    list_filter = ('is_active', 'priority')
    search_fields = ('name', 'display_name')
    list_editable = ('is_active',)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_at', 'expires_at', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('user__username', 'role__display_name')
    readonly_fields = ('assigned_at',)


@admin.register(PermissionLog)
class PermissionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'action', 'performed_by', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'role__display_name')
    readonly_fields = ('created_at',)


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'governorate', 'phone', 'broker_count', 'is_active')
    search_fields = ('name', 'address')


@admin.register(BrokerJoinRequest)
class BrokerJoinRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'governorate', 'office_name', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'phone', 'office_name')


@admin.register(PropertyRating)
class PropertyRatingAdmin(admin.ModelAdmin):
    list_display = ('property_obj', 'user', 'rating', 'average_detailed_rating', 'is_verified', 'created_at')
    list_filter = ('rating', 'is_verified', 'created_at')
    search_fields = ('property_obj__title', 'user__username', 'review')
    readonly_fields = ('average_detailed_rating', 'created_at', 'updated_at')
    list_per_page = 25


@admin.register(BrokerRating)
class BrokerRatingAdmin(admin.ModelAdmin):
    list_display = ('broker', 'user', 'rating', 'average_detailed_rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('broker__name', 'user__username', 'review')
    readonly_fields = ('average_detailed_rating', 'created_at', 'updated_at')
    list_per_page = 25


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    list_display = ('user', 'method', 'is_enabled', 'last_used', 'created_at')
    list_filter = ('method', 'is_enabled', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('secret_key', 'backup_codes', 'created_at', 'updated_at')


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'success', 'created_at')
    list_filter = ('action', 'success', 'created_at')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('created_at',)
    list_per_page = 50


@admin.register(DallalGlobalSettings)
class DallalGlobalSettingsAdmin(admin.ModelAdmin):
    list_display = ('is_dallal_system_enabled', 'max_brokers_per_user', 'max_properties_per_dallal', 'show_dallal_on_homepage', 'dallal_display_order')
    fieldsets = (
        ('الإعدادات العامة', {
            'fields': ('is_dallal_system_enabled', 'max_brokers_per_user', 'max_properties_per_dallal')
        }),
        ('العرض', {
            'fields': ('show_dallal_on_homepage', 'dallal_display_order', 'show_expired_dallal')
        }),
    )

    def has_add_permission(self, request):
        return not DallalGlobalSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BasicDallalSettings)
class BasicDallalSettingsAdmin(admin.ModelAdmin):
    list_display = ('max_properties', 'duration_days', 'auto_renewal', 'impressions_limit', 'cost', 'is_enabled')
    fieldsets = (
        ('الحدود', {
            'fields': ('max_properties', 'impressions_limit')
        }),
        ('المدة والتجديد', {
            'fields': ('duration_days', 'auto_renewal')
        }),
        ('التكلفة', {
            'fields': ('cost',)
        }),
        ('التفعيل', {
            'fields': ('is_enabled',)
        }),
    )

    def has_add_permission(self, request):
        return not BasicDallalSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PremiumDallalSettings)
class PremiumDallalSettingsAdmin(admin.ModelAdmin):
    list_display = ('max_properties', 'duration_days', 'priority_display', 'impressions_limit', 'cost', 'is_enabled', 'visual_badge', 'highlight_effect')
    fieldsets = (
        ('الحدود', {
            'fields': ('max_properties', 'impressions_limit')
        }),
        ('المدة والأولوية', {
            'fields': ('duration_days', 'priority_display')
        }),
        ('التكلفة', {
            'fields': ('cost',)
        }),
        ('التفعيل', {
            'fields': ('is_enabled',)
        }),
        ('المظهر', {
            'fields': ('visual_badge', 'highlight_effect')
        }),
    )

    def has_add_permission(self, request):
        return not PremiumDallalSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DallalSubscription)
class DallalSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('broker', 'subscription_type', 'start_date', 'end_date', 'properties_used', 'impressions_count', 'is_active', 'auto_renewal')
    list_filter = ('subscription_type', 'is_active', 'auto_renewal', 'start_date', 'end_date')
    search_fields = ('broker__display_name', 'broker__user__username')
    readonly_fields = ('get_days_remaining', 'get_days_elapsed', 'get_properties_remaining', 'is_expired')
    fieldsets = (
        ('معلومات الاشتراك', {
            'fields': ('broker', 'subscription_type', 'start_date', 'end_date')
        }),
        ('الاستخدام', {
            'fields': ('properties_used', 'impressions_count')
        }),
        ('الحالة', {
            'fields': ('is_active', 'auto_renewal')
        }),
        ('معلومات إضافية', {
            'fields': ('get_days_remaining', 'get_days_elapsed', 'get_properties_remaining', 'is_expired')
        }),
    )


@admin.register(PropertyDallalAssignment)
class PropertyDallalAssignmentAdmin(admin.ModelAdmin):
    list_display = ('property', 'dallal_subscription', 'assigned_at')
    list_filter = ('assigned_at',)
    search_fields = ('property__title', 'dallal_subscription__broker__display_name')
    readonly_fields = ('assigned_at',)


@admin.register(BrokerChannel)
class BrokerChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'broker', 'status', 'is_verified', 'followers_count', 'views_count', 'created_at')
    list_filter = ('status', 'is_verified', 'created_at')
    search_fields = ('name', 'description', 'broker__display_name', 'broker__user__username')
    readonly_fields = ('properties_count', 'views_count', 'followers_count', 'created_at', 'updated_at')
    list_editable = ('status', 'is_verified')
    fieldsets = (
        ('معلومات القناة', {
            'fields': ('broker', 'name', 'description', 'status', 'is_verified')
        }),
        ('الصور', {
            'fields': ('logo', 'cover_image')
        }),
        ('الإحصائيات', {
            'fields': ('followers_count', 'views_count', 'properties_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )





@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'name_en', 'code', 'currency_code', 'is_active')
    search_fields = ('name_ar', 'name_en', 'code')
    list_filter = ('is_active', 'currency_code')


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'name_en', 'country', 'governorate_state', 'is_active')
    search_fields = ('name_ar', 'name_en', 'country__name_ar')
    list_filter = ('country', 'is_active')


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'name_en', 'city', 'is_active')
    search_fields = ('name_ar', 'name_en', 'city__name_ar')
    list_filter = ('city', 'is_active')


@admin.register(LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):
    list_display = ('title', 'property', 'broker', 'status', 'scheduled_start', 'viewers_count')
    list_filter = ('status', 'platform', 'scheduled_start')
    search_fields = ('title', 'description', 'property__title', 'broker__display_name')
    readonly_fields = ('actual_start', 'actual_end', 'created_at', 'updated_at')
    list_editable = ('status',)
    actions = ['start_streams', 'end_streams', 'cancel_streams']

    @admin.action(description='بدء البث المباشر')
    def start_streams(self, request, queryset):
        for stream in queryset.filter(status='scheduled'):
            stream.start_stream()
        self.message_user(request, f'تم بدء {queryset.count()} بث مباشر')

    @admin.action(description='إنهاء البث المباشر')
    def end_streams(self, request, queryset):
        for stream in queryset.filter(status='live'):
            stream.end_stream()
        self.message_user(request, f'تم إنهاء {queryset.count()} بث مباشر')

    @admin.action(description='إلغاء البث المباشر')
    def cancel_streams(self, request, queryset):
        for stream in queryset.filter(status__in=['scheduled', 'live']):
            stream.cancel_stream()
        self.message_user(request, f'تم إلغاء {queryset.count()} بث مباشر')


@admin.register(LiveStreamComment)
class LiveStreamCommentAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'live_stream', 'comment', 'created_at')
    list_filter = ('created_at', 'live_stream')
    search_fields = ('author_name', 'comment', 'live_stream__title')


@admin.register(PropertyVideo)
class PropertyVideoAdmin(admin.ModelAdmin):
    list_display = ('property', 'video_type', 'sort_order', 'duration', 'created_at')
    list_filter = ('video_type', 'created_at')
    search_fields = ('property__title', 'caption')


@admin.register(PropertyDocument)
class PropertyDocumentAdmin(admin.ModelAdmin):
    list_display = ('property', 'document_type', 'title', 'created_at')
    list_filter = ('document_type', 'created_at')
    search_fields = ('property__title', 'title', 'description')


@admin.register(PropertyMediaStats)
class PropertyMediaStatsAdmin(admin.ModelAdmin):
    list_display = ('property', 'total_images', 'total_videos', 'total_360_tours', 'updated_at')
    search_fields = ('property__title',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PropertyViewStats)
class PropertyViewStatsAdmin(admin.ModelAdmin):
    list_display = ('property', 'total_views', 'unique_views', 'views_today', 'updated_at')
    search_fields = ('property__title',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PropertyEngagementStats)
class PropertyEngagementStatsAdmin(admin.ModelAdmin):
    list_display = ('property', 'total_favorites', 'total_shares', 'total_calls', 'updated_at')
    search_fields = ('property__title',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PropertyConversionStats)
class PropertyConversionStatsAdmin(admin.ModelAdmin):
    list_display = ('property', 'total_leads', 'total_appointments', 'total_sales', 'updated_at')
    search_fields = ('property__title',)
    readonly_fields = ('created_at', 'updated_at')


# Job Opportunity Admin Classes
@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'name_en', 'is_active', 'jobs_count')
    list_filter = ('is_active',)
    search_fields = ('name_ar', 'name_en')
    list_editable = ('is_active',)
    
    def jobs_count(self, obj):
        return obj.jobs.count()
    jobs_count.short_description = 'عدد الوظائف'


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company_name', 'category', 'job_type', 'governorate', 'status', 'is_featured', 'is_urgent', 'views_count', 'applications_count', 'created_at')
    list_filter = ('status', 'job_type', 'experience_level', 'governorate', 'is_featured', 'is_urgent', 'category')
    search_fields = ('title', 'company_name', 'description', 'skills')
    list_editable = ('status', 'is_featured', 'is_urgent')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('views_count', 'applications_count', 'created_at', 'updated_at')
    actions = ['activate_jobs', 'close_jobs', 'mark_as_featured', 'mark_as_urgent']
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('title', 'slug', 'category', 'status', 'is_featured', 'is_urgent')
        }),
        ('معلومات الشركة', {
            'fields': ('company_name', 'company_logo', 'company_description')
        }),
        ('تفاصيل الوظيفة', {
            'fields': ('job_type', 'experience_level', 'is_remote')
        }),
        ('الموقع', {
            'fields': ('governorate', 'city', 'address')
        }),
        ('الراتب', {
            'fields': ('salary_min', 'salary_max', 'salary_currency', 'salary_period', 'is_salary_negotiable')
        }),
        ('الوصف والمتطلبات', {
            'fields': ('description', 'requirements', 'responsibilities', 'benefits', 'skills')
        }),
        ('معلومات الاتصال', {
            'fields': ('contact_name', 'contact_email', 'contact_phone')
        }),
        ('الإعدادات', {
            'fields': ('expiry_date', 'posted_by')
        }),
        ('الإحصائيات', {
            'fields': ('views_count', 'applications_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.action(description='تفعيل الوظائف')
    def activate_jobs(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f'تم تفعيل {queryset.count()} وظيفة')
    
    @admin.action(description='إغلاق الوظائف')
    def close_jobs(self, request, queryset):
        queryset.update(status='closed')
        self.message_user(request, f'تم إغلاق {queryset.count()} وظيفة')
    
    @admin.action(description='تعليم كمميز')
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f'تم تعليم {queryset.count()} وظيفة كمميزة')
    
    @admin.action(description='تعليم كعادية')
    def mark_as_urgent(self, request, queryset):
        queryset.update(is_urgent=True)
        self.message_user(request, f'تم تعليم {queryset.count()} وظيفة كعادية')


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'job', 'email', 'phone', 'status', 'years_of_experience', 'applied_at')
    list_filter = ('status', 'job__category', 'job__governorate', 'applied_at')
    search_fields = ('full_name', 'email', 'phone', 'job__title')
    list_editable = ('status',)
    readonly_fields = ('applied_at', 'updated_at')
    actions = ['accept_applications', 'reject_applications', 'shortlist_applications']
    
    fieldsets = (
        ('المعلومات الشخصية', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('المعلومات المهنية', {
            'fields': ('current_position', 'current_company', 'years_of_experience')
        }),
        ('المستندات', {
            'fields': ('cv_file', 'cover_letter', 'portfolio_url')
        }),
        ('التفاصيل الإضافية', {
            'fields': ('expected_salary', 'available_date')
        }),
        ('الحالة والملاحظات', {
            'fields': ('status', 'recruiter_notes')
        }),
        ('الوقت', {
            'fields': ('applied_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.action(description='قبول الطلبات')
    def accept_applications(self, request, queryset):
        queryset.update(status='accepted')
        self.message_user(request, f'تم قبول {queryset.count()} طلب')
    
    @admin.action(description='رفض الطلبات')
    def reject_applications(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f'تم رفض {queryset.count()} طلب')
    
    @admin.action(description='إدراج في القائمة المختصرة')
    def shortlist_applications(self, request, queryset):
        queryset.update(status='shortlisted')
        self.message_user(request, f'تم إدراج {queryset.count()} طلب في القائمة المختصرة')


# Travel Company Admin Classes
class TravelCompanyImageInline(admin.TabularInline):
    model = TravelCompanyImage
    extra = 1
    fields = ('image', 'caption', 'order')


class TravelCompanyVideoInline(admin.TabularInline):
    model = TravelCompanyVideo
    extra = 1
    fields = ('video', 'thumbnail', 'caption', 'order')


@admin.register(TravelCompany)
class TravelCompanyAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'company_type', 'travel_scope', 'travel_type', 'governorate',
        'rating', 'reviews_count', 'is_verified', 'is_featured', 'is_active', 'created_at'
    )
    list_filter = (
        'company_type', 'travel_scope', 'travel_type', 'governorate',
        'is_verified', 'is_featured', 'is_active', 'created_at'
    )
    search_fields = ('name', 'name_en', 'description', 'phone', 'email', 'city')
    list_editable = ('is_verified', 'is_featured', 'is_active')
    readonly_fields = ('rating', 'reviews_count', 'created_at', 'updated_at')
    inlines = [TravelCompanyImageInline, TravelCompanyVideoInline]
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('name', 'name_en', 'description', 'description_en', 'company_type')
        }),
        ('معلومات السفر', {
            'fields': ('travel_types', 'travel_scope', 'travel_type', 'departure_time')
        }),
        ('الأسعار والوجهات', {
            'fields': ('price', 'price_currency', 'destinations')
        }),
        ('المرافق والخدمات', {
            'fields': ('facilities', 'services')
        }),
        ('معلومات الفروع', {
            'fields': ('has_branches', 'branches_count', 'branch_locations')
        }),
        ('معلومات الحجز', {
            'fields': ('booking_methods', 'advance_booking_days', 'cancellation_policy', 'cancellation_policy_en')
        }),
        ('السعة والإنتاجية', {
            'fields': ('daily_capacity', 'monthly_capacity')
        }),
        ('الشهادات والشركاء', {
            'fields': ('certifications', 'partners')
        }),
        ('العروض الخاصة', {
            'fields': ('has_special_offers', 'special_offers')
        }),
        ('ساعات العمل', {
            'fields': ('working_hours',)
        }),
        ('معلومات الاتصال', {
            'fields': ('phone', 'whatsapp', 'email', 'website', 'facebook', 'instagram', 'twitter', 'telegram')
        }),
        ('الموقع الجغرافي', {
            'fields': ('address', 'governorate', 'city', 'latitude', 'longitude')
        }),
        ('الصور والوسائط', {
            'fields': ('logo', 'cover_image')
        }),
        ('التقييمات والحالة', {
            'fields': ('rating', 'reviews_count', 'is_verified', 'is_featured', 'is_active')
        }),
        ('الوقت', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TravelCompanyReview)
class TravelCompanyReviewAdmin(admin.ModelAdmin):
    list_display = (
        'company', 'user', 'overall_rating', 'service_quality', 'price_value',
        'reliability', 'customer_service', 'comfort', 'is_verified', 'is_approved', 'created_at'
    )
    list_filter = (
        'overall_rating', 'service_quality', 'price_value', 'reliability',
        'customer_service', 'comfort', 'is_verified', 'is_approved', 'created_at'
    )
    search_fields = ('title', 'comment', 'company__name', 'user__username', 'destination')
    list_editable = ('is_verified', 'is_approved')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('company', 'user', 'overall_rating')
        }),
        ('التقييمات التفصيلية', {
            'fields': ('service_quality', 'price_value', 'reliability', 'customer_service', 'comfort')
        }),
        ('محتوى التقييم', {
            'fields': ('title', 'comment', 'comment_en')
        }),
        ('تفاصيل الرحلة', {
            'fields': ('trip_date', 'destination', 'travel_type')
        }),
        ('الوسائط', {
            'fields': ('images',)
        }),
        ('الحالة', {
            'fields': ('is_verified', 'is_approved')
        }),
        ('الوقت', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TravelCompanyRatingBreakdown)
class TravelCompanyRatingBreakdownAdmin(admin.ModelAdmin):
    list_display = (
        'company', 'avg_service_quality', 'avg_price_value', 'avg_reliability',
        'avg_customer_service', 'avg_comfort', 'rating_5_count', 'rating_4_count',
        'rating_3_count', 'rating_2_count', 'rating_1_count', 'last_updated'
    )
    list_filter = ('last_updated',)
    search_fields = ('company__name',)
    readonly_fields = ('last_updated',)
    
    fieldsets = (
        ('الشركة', {
            'fields': ('company',)
        }),
        ('متوسطات التقييمات', {
            'fields': ('avg_service_quality', 'avg_price_value', 'avg_reliability', 'avg_customer_service', 'avg_comfort')
        }),
        ('توزيع التقييمات', {
            'fields': ('rating_5_count', 'rating_4_count', 'rating_3_count', 'rating_2_count', 'rating_1_count')
        }),
        ('الوقت', {
            'fields': ('last_updated',)
        }),
    )


# Service Provider Admin Classes

@admin.register(ServiceProviderCategory)
class ServiceProviderCategoryAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'name_en', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name_ar', 'name_en')
    list_editable = ('is_active', 'order')
    prepopulated_fields = {}


@admin.register(ServiceProviderPage)
class ServiceProviderPageAdmin(admin.ModelAdmin):
    list_display = ('name', 'page_type', 'category', 'governorate', 'city', 'rating', 'reviews_count', 'status', 'is_verified', 'created_at')
    list_filter = ('page_type', 'category', 'governorate', 'status', 'is_verified', 'created_at')
    search_fields = ('name', 'description', 'city', 'phone')
    list_editable = ('is_verified', 'status')
    readonly_fields = ('views_count', 'contacts_count', 'quotes_count', 'followers_count', 'rating', 'reviews_count', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('name', 'slug', 'page_type', 'description')
        }),
        ('الفئة والموقع', {
            'fields': ('category', 'sub_categories', 'governorate', 'city', 'working_areas', 'latitude', 'longitude')
        }),
        ('معلومات الاحترافية', {
            'fields': ('years_of_experience', 'projects_count', 'clients_count')
        }),
        ('الاتصال', {
            'fields': ('phone', 'whatsapp', 'telegram', 'facebook', 'instagram', 'website', 'email')
        }),
        ('الوسائط', {
            'fields': ('profile_image', 'cover_image', 'logo')
        }),
        ('أوقات العمل', {
            'fields': ('working_hours', 'availability')
        }),
        ('الإحصائيات', {
            'fields': ('views_count', 'contacts_count', 'quotes_count', 'followers_count', 'rating', 'reviews_count')
        }),
        ('الحالة والتوثيق', {
            'fields': ('status', 'is_verified', 'verification_date')
        }),
        ('الإحصائيات والمالك', {
            'fields': ('user', 'broker')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        ('الوقت', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ServiceProviderService)
class ServiceProviderServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'page', 'price', 'price_unit', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'page__name')
    list_editable = ('is_active', 'order')
    ordering = ['order', 'name']


@admin.register(ServiceBooking)
class ServiceBookingAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'service', 'provider_page', 'booking_date', 'booking_time', 'status', 'payment_status', 'total_price', 'created_at')
    list_filter = ('status', 'payment_status', 'booking_date', 'location_type', 'created_at')
    search_fields = ('customer_name', 'customer_phone', 'customer_email', 'service__name', 'provider_page__name')
    list_editable = ('status', 'payment_status')
    readonly_fields = ('created_at', 'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at')
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('service', 'provider_page')
        }),
        ('معلومات العميل', {
            'fields': ('customer', 'customer_name', 'customer_phone', 'customer_email')
        }),
        ('تفاصيل الحجز', {
            'fields': ('booking_date', 'booking_time', 'duration', 'location_type', 'address', 'latitude', 'longitude')
        }),
        ('التسعير', {
            'fields': ('total_price', 'deposit_amount', 'currency')
        }),
        ('الحالة', {
            'fields': ('status', 'payment_status')
        }),
        ('الملاحظات', {
            'fields': ('notes', 'customer_notes', 'provider_notes')
        }),
        ('الإشعارات', {
            'fields': ('reminder_sent', 'confirmation_sent')
        }),
        ('الوقت', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ServiceProviderSchedule)
class ServiceProviderScheduleAdmin(admin.ModelAdmin):
    list_display = ('provider', 'day', 'start_time', 'end_time', 'is_available', 'max_bookings', 'booking_duration')
    list_filter = ('day', 'is_available')
    search_fields = ('provider__name',)
    list_editable = ('is_available', 'max_bookings', 'booking_duration')


@admin.register(ServiceProviderAvailability)
class ServiceProviderAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('provider', 'date', 'availability_type', 'start_time', 'end_time', 'reason')
    list_filter = ('availability_type', 'date')
    search_fields = ('provider__name', 'reason')


@admin.register(ServiceProviderReview)
class ServiceProviderReviewAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'provider', 'service', 'overall_rating', 'quality', 'professionalism', 'punctuality', 'communication', 'value_for_money', 'is_verified', 'is_approved', 'is_featured', 'created_at')
    list_filter = ('overall_rating', 'quality', 'professionalism', 'punctuality', 'communication', 'value_for_money', 'is_verified', 'is_approved', 'is_featured', 'created_at')
    search_fields = ('title', 'comment', 'customer_name', 'provider__name', 'service__name')
    list_editable = ('is_verified', 'is_approved', 'is_featured')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('provider', 'service', 'booking', 'customer', 'customer_name')
        }),
        ('التقييم العام', {
            'fields': ('overall_rating',)
        }),
        ('التقييمات التفصيلية', {
            'fields': ('quality', 'professionalism', 'punctuality', 'communication', 'value_for_money')
        }),
        ('محتوى التقييم', {
            'fields': ('title', 'comment')
        }),
        ('تفاصيل الخدمة', {
            'fields': ('service_date', 'service_type')
        }),
        ('الوسائط', {
            'fields': ('images',)
        }),
        ('الحالة', {
            'fields': ('is_verified', 'is_approved', 'is_featured')
        }),
        ('الوقت', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ServiceProviderRatingBreakdown)
class ServiceProviderRatingBreakdownAdmin(admin.ModelAdmin):
    list_display = ('provider', 'avg_quality', 'avg_professionalism', 'avg_punctuality', 'avg_communication', 'avg_value_for_money', 'rating_5_count', 'rating_4_count', 'rating_3_count', 'rating_2_count', 'rating_1_count', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('provider__name',)
    readonly_fields = ['last_updated']
    
    fieldsets = (
        ('مقدم الخدمة', {
            'fields': ('provider',)
        }),
        ('متوسطات التقييمات', {
            'fields': ('avg_quality', 'avg_professionalism', 'avg_punctuality', 'avg_communication', 'avg_value_for_money')
        }),
        ('توزيع التقييمات', {
            'fields': ('rating_5_count', 'rating_4_count', 'rating_3_count', 'rating_2_count', 'rating_1_count')
        }),
        ('الوقت', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'subject', 'message_type', 'status', 'priority', 'is_read', 'created_at', 'assigned_to')
    list_filter = ('status', 'priority', 'message_type', 'is_read', 'created_at')
    search_fields = ('subject', 'content', 'user__username', 'user__email')
    list_editable = ('status', 'priority', 'assigned_to')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at')
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('user', 'message_type', 'subject', 'content')
        }),
        ('الحالة والأولوية', {
            'fields': ('status', 'priority', 'is_read')
        }),
        ('الرد الإداري', {
            'fields': ('admin_response', 'assigned_to')
        }),
        ('الوقت', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, 'تم تحديد الرسائل كمحلولة')
    mark_as_resolved.short_description = 'تحديد كمحلولة'
    
    def mark_as_in_progress(self, request, queryset):
        queryset.update(status='in_progress')
        self.message_user(request, 'تم تحديد الرسائل قيد المعالجة')
    mark_as_in_progress.short_description = 'تحديد قيد المعالجة'
    
    actions = [mark_as_resolved, mark_as_in_progress]