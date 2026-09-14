from django.urls import path
from django.http import FileResponse
from django.shortcuts import render
from django.conf import settings
from pathlib import Path

from . import views, api, broker_views, dallal_views, otp_views, channel_views, ai_chatbot_views, ai_admin_views, api_views, ai_gateway_api, contract_views, contract_api_views
try:
    from . import api_views_enterprise as api_enterprise
except ImportError:
    api_enterprise = None


def service_worker_view(request):
    """Serve service worker from root so it can control the whole origin."""
    sw_path = Path(settings.BASE_DIR) / 'static' / 'js' / 'sw.js'
    response = FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response


def offline_view(request):
    return render(request, 'properties/offline.html')


urlpatterns = [
    path('sw.js', service_worker_view, name='service_worker'),
    path('offline/', offline_view, name='offline'),
    # Existing template-based routes
    path('', views.home, name='home'),
    path('property/<str:slug>/', views.property_detail, name='property_detail'),
    path('property/id/<int:property_id>/', views.property_detail_legacy, name='property_detail_legacy'),
    path('about/', views.about_page, name='about'),
    path('contact/', views.contact_page, name='contact'),
    path('explore/', views.explore_view, name='explore'),
    path('map/', views.interactive_map_view, name='interactive_map'),
    path('properties-outside-iraq/', views.properties_outside_iraq_view, name='properties_outside_iraq'),
    path('search/', views.unified_search_view, name='unified_search'),
    path('services-categories/', views.service_categories_view, name='service_categories'),
    path('navigation-error/', views.navigation_error_view, name='navigation_error'),
    # Channel pages
    # Broker Channels
    # New Channel Features
    path('explore/like/<int:property_id>/', views.like_property, name='like_property'),
    path('explore/save/<int:property_id>/', views.save_property, name='save_property'),
    path('explore/comment/<int:property_id>/', views.add_comment, name='add_comment'),
    path('favorites/', views.favorites_view, name='favorites'),
    path('virtual-tour/add/<int:property_id>/', views.add_virtual_tour, name='add_virtual_tour'),
    path('virtual-tour/edit/<int:tour_id>/', views.edit_virtual_tour, name='edit_virtual_tour'),
    path('virtual-tour/delete/<int:tour_id>/', views.delete_virtual_tour, name='delete_virtual_tour'),
    path('virtual-tour/point/add/<int:tour_id>/', views.add_tour_point, name='add_tour_point'),
    path('virtual-tour/point/edit/<int:point_id>/', views.edit_tour_point, name='edit_tour_point'),
    path('virtual-tour/point/delete/<int:point_id>/', views.delete_tour_point, name='delete_tour_point'),

    path('broker/standalone-settings/', views.broker_standalone_settings, name='broker_standalone_settings'),
    path('d/<slug:slug>/', views.broker_standalone_page, name='broker_standalone_page'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset-confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-change/', views.password_change, name='password_change'),
    path('account-delete/', views.account_delete, name='account_delete'),
    # OTP Verification
    # Admin Panel
    path('admin-panel/brokers/', views.admin_brokers_management, name='admin_brokers_management'),
    path('api/location/share/', views.api_share_location, name='api_share_location'),
    path('api/messages/upload-attachments/', views.api_upload_attachments, name='api_upload_attachments'),
    path('api/properties/search/', views.api_search_properties, name='api_search_properties'),
    path('api/ratings/submit/', views.api_submit_rating, name='api_submit_rating'),
    path('api/media/upload/', views.api_media_upload, name='api_media_upload'),
    path('api/media/delete/', views.api_media_delete, name='api_media_delete'),
    # Messaging System
    path('settings/social/', views.social_settings, name='social_settings'),
    path('subscription-plans/', views.subscription_plans, name='subscription_plans'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/my-posts/', views.my_posts, name='my_posts'),
    path('dashboard/advanced-reports/', views.advanced_reports, name='advanced_reports'),
    path('api/property/<int:property_id>/toggle-featured/', views.toggle_property_featured, name='toggle_property_featured'),
    path('api/property/<int:property_id>/toggle-promoted/', views.toggle_property_promoted, name='toggle_property_promoted'),
    path('dashboard/settings/', views.update_site_settings, name='update_site_settings'),
    path('dashboard/settings/general/', views.settings_general, name='settings_general'),
    path('dashboard/settings/theme/', views.settings_theme, name='settings_theme'),
    path('dashboard/settings/homepage/', views.settings_homepage, name='settings_homepage'),
    path('dashboard/settings/users/', views.settings_users, name='settings_users'),
    path('dashboard/settings/properties/', views.settings_properties, name='settings_properties'),
    path('dashboard/settings/media/', views.settings_media, name='settings_media'),
    path('dashboard/settings/notifications/', views.settings_notifications, name='settings_notifications'),
    # Admin channel management
    path('dashboard/admin/channels/', views.admin_channels_list, name='admin_channels_list'),
    path('dashboard/admin/channels/<int:channel_id>/approve/', views.admin_channel_approve, name='admin_channel_approve'),
    path('dashboard/admin/channels/<int:channel_id>/reject/', views.admin_channel_reject, name='admin_channel_reject'),
    path('dashboard/admin/channels/<int:channel_id>/verify/', views.admin_channel_verify, name='admin_channel_verify'),
    path('dashboard/admin/channels/<int:channel_id>/delete/', views.admin_channel_delete, name='admin_channel_delete'),
    path('dashboard/admin/channels/<int:channel_id>/activate/', views.admin_channel_activate, name='admin_channel_activate'),
    path('dashboard/admin/channels/<int:channel_id>/properties/', views.admin_channel_properties, name='admin_channel_properties'),
    path('dashboard/admin/channels/<int:channel_id>/properties/<int:property_id>/delete/', views.admin_channel_property_delete, name='admin_channel_property_delete'),
    # Content Moderation
    # User Monitoring
    path('admin-panel/user-monitoring/<int:user_id>/details/', views.user_details_api, name='user_details_api'),
    path('dashboard/my-channel/', views.my_channel_view, name='my_channel'),
    path('dashboard/my-channel/post/create/', views.create_channel_post, name='create_channel_post'),
    path('dashboard/my-channel/video/create/', views.create_channel_video, name='create_channel_video'),
    path('dashboard/my-channel/media/update/', views.update_channel_media, name='update_channel_media'),
    path('api/channel/update-media/', views.channel_update_media_api, name='channel_update_media_api'),
    path('post/<int:post_id>/like/', views.toggle_post_like, name='toggle_post_like'),
    path('video/<int:video_id>/like/', views.toggle_video_like, name='toggle_video_like'),
    path('channel/<int:channel_id>/', views.channel_public_view, name='channel_public'),
    # User management API
    path('api/user/<int:user_id>/details/', views.user_details_api, name='user_details_api'),
    # Subscription plan management API
    path('api/subscription-plan/<int:plan_id>/details/', views.subscription_plan_details_api, name='subscription_plan_details_api'),
    path('api/subscription-plan/<int:plan_id>/update/', views.subscription_plan_update_api, name='subscription_plan_update_api'),
    path('api/subscription-plan/<int:plan_id>/toggle-status/', views.subscription_plan_toggle_status_api, name='subscription_plan_toggle_status_api'),
    # Subscription request management API
    path('api/subscription-request/<int:request_id>/approve/', views.subscription_request_approve_api, name='subscription_request_approve_api'),
    path('api/subscription-request/<int:request_id>/reject/', views.subscription_request_reject_api, name='subscription_request_reject_api'),
    path('api/subscription-request/create/', views.subscription_request_create_api, name='subscription_request_create_api'),
    # Broker management API
    path('api/brokers/<int:broker_id>/toggle-status/', views.api_broker_toggle_status, name='api_broker_toggle_status'),
    path('api/brokers/<int:broker_id>/verify/', views.api_broker_verify, name='api_broker_verify'),
    path('api/brokers/<int:broker_id>/delete/', views.api_broker_delete, name='api_broker_delete'),
    # AI Chatbot API - Redirected to AI Gateway for unification
    path('api/chatbot/', ai_gateway_api.ai_chat, name='ai_chatbot_api'),
    
    # Production AI API
    
    # AI Admin
    path('dashboard/settings/payments/', views.settings_payments, name='settings_payments'),
    path('dashboard/settings/security/', views.settings_security, name='settings_security'),
    path('dashboard/settings/reports/', views.settings_reports, name='settings_reports'),
    path('dashboard/settings/backup/', views.settings_backup, name='settings_backup'),
    path('dashboard/settings/seo/', views.settings_seo, name='settings_seo'),
    path('dashboard/settings/api/', views.settings_api, name='settings_api'),
    path('dashboard/settings/system/', views.settings_system, name='settings_system'),
    path('dashboard/settings/maintenance/', views.settings_maintenance, name='settings_maintenance'),
    path('dashboard/settings/oauth-diagnostics/', views.social_auth_diagnostics, name='social_auth_diagnostics'),
    # Sub-broker routes
    # User messaging routes
    # Broker conversation routes
    # Property view commissions
    path('dashboard/property/<int:property_id>/virtual-tour/add/', views.add_virtual_tour, name='add_virtual_tour'),
    path('dashboard/virtual-tour/<int:tour_id>/delete/', views.delete_virtual_tour, name='delete_virtual_tour'),

    # Tourism section
    
    # New category views
    
    # Travel companies
    
    # Travel packages
    
    # Resorts inside Iraq
    
    # Resorts outside Iraq



    # Dynamic property addition
    

    # Service Providers

    
    # Jobs / Employment
    # Jobs routes
    path('jobs/', views.jobs_list, name='jobs_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/my/', views.my_jobs, name='my_jobs'),
    path('jobs/<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('jobs/<int:pk>/delete/', views.job_delete, name='job_delete'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),

    path('api/messenger/poll/', views.api_messenger_poll, name='api_messenger_poll'),
    path('api/messenger/send/', views.api_messenger_send, name='api_messenger_send'),
    path('api/messenger/properties/', views.api_messenger_properties, name='api_messenger_properties'),
    path('api/conversations/check/', views.api_check_conversation, name='api_check_conversation'),
    path('api/conversations/create/', views.api_create_conversation, name='api_create_conversation'),
    path('api/notifications/unread/', views.api_notifications_unread, name='api_notifications_unread'),
    
    # Developer Panel APIs
    path('api/conversations/<uuid:conversation_id>/messages/', views.api_send_message, name='api_send_message_uuid'),
    path('api/upload-attachment/', views.api_upload_attachment, name='api_upload_attachment'),

    # Notifications
    
    # New Notification System
    
    # Admin Notifications

    # Broker system routes
    path('dashboard/brokers/main-panel/', views.main_broker_panel, name='main_broker_panel'),
    # Broker channel management
    path('dashboard/map/api/properties/', broker_views.map_api_properties, name='map_api_properties'),
    
    # Backup routes
    
    # System Settings routes

    # User management routes
    path('api/users/<int:user_id>/details/', views.user_details_api, name='user_details_api'),

    # Property management routes

    # Analytics routes

    # Dashboard stats routes
    
    # Dedicated dashboard APIs for each user type
    path('api/dashboard/user/', views.user_dashboard_api, name='user_dashboard_api'),

    # Advanced features routes
    path('api/api-keys/', views.api_keys_management, name='api_keys_management'),

    # New advanced features routes

    # New advanced features routes (round 2)

    # New advanced features routes (round 3)

    # Real Estate Specific routes
    
    # Contract Payments
    
    # Contract Documents
    
    # Contract Reminders
    
    path('api/map/properties/', views.map_api_properties, name='map_api_properties'),
    path('api/map/search/', views.map_api_search, name='map_api_search'),
    path('api/map/nearby/', views.map_api_nearby, name='map_api_nearby'),
    path('api/map/stats/', views.map_api_stats, name='map_api_stats'),

    # Real Estate Contracts Page

    # Dallal system routes
    
    # Dallal travel companies routes
    
    # Travel company reviews routes
    
    # New API endpoints for Next.js frontend
    path('api/health/', api.api_health, name='api_health'),
    path('api/properties/', api.api_properties, name='api_properties'),
    path('api/property/<str:slug>/', api.api_property_detail, name='api_property_detail'),
    path('api/featured/', api.api_featured_properties, name='api_featured_properties'),
    path('api/settings/', api.api_site_settings, name='api_site_settings'),
    path('api/search/suggestions/', api.api_search_suggestions, name='api_search_suggestions'),
    path('api/statistics/', api.api_statistics, name='api_statistics'),
    path('api/subscription/expire/', views.subscription_expire_notification, name='subscription_expire_notification'),
    
    # Payment system routes
    
    # User Moderation System routes
    
    # نظام الفنادق والمنتجعات الجديد
    
    # Hotel Posts
    
    # Hotel Rooms
    
    # Hotel Offers
    
    # Hotel Bookings
    
    # Service Provider System
    
    # Support Message System
    
    # Broker appointments

    # Appointment booking landing page
    
    # Advanced appointments management
    
    # Customer Management System
    
    # Agent Management System
    
    # Broker profile (must be last as it's a catch-all)
    path('broker/<str:username>/', views.broker_profile, name='broker_profile'),
    
    # Real Estate Contracts
    
    # New Contract Features
    
    # Contract API
]

# Enterprise API endpoints (only if available)
try:
    from . import api_enterprise
    api_enterprise_available = True
except ImportError:
    api_enterprise_available = False

if api_enterprise_available:
    urlpatterns += [
        path('api/v1/system/status/', api_enterprise.api_system_status, name='api_system_status'),
        path('api/v1/system/errors/', api_enterprise.api_error_logs, name='api_error_logs'),
        path('api/v1/export/', api_enterprise.api_export_data, name='api_export_data'),
        path('api/v1/search/', api_enterprise.api_search, name='api_search'),
        path('api/v1/notifications/', api_enterprise.api_notifications, name='api_notifications'),
        path('api/v1/notifications/<int:notification_id>/read/', api_enterprise.api_mark_notification_read, name='api_mark_notification_read'),
        path('api/v1/sessions/', api_enterprise.api_sessions, name='api_sessions'),
        path('api/v1/keys/', api_enterprise.api_api_keys, name='api_api_keys'),
        path('api/v1/performance/', api_enterprise.api_performance_metrics, name='api_performance_metrics'),
    ]

# Targeted Advertising System
urlpatterns += [
    path('advertisements/', views.AdvertisementListView.as_view(), name='advertisement_list'),
    path('advertisements/<int:ad_id>/', views.AdvertisementDetailView.as_view(), name='advertisement_detail'),
    path('advertisements/create/', views.create_advertisement, name='create_advertisement'),
    path('advertisements/<int:ad_id>/update/', views.update_advertisement, name='update_advertisement'),
    path('advertisements/<int:ad_id>/delete/', views.delete_advertisement, name='delete_advertisement'),
    path('advertisements/<int:ad_id>/respond/', views.respond_to_advertisement, name='respond_to_advertisement'),
    path('advertisements/<int:ad_id>/responses/', views.advertisement_responses, name='advertisement_responses'),
    path('advertisements/responses/<int:response_id>/handle/', views.handle_response, name='handle_response'),
    path('advertisements/<int:ad_id>/matches/', views.advertisement_matches, name='advertisement_matches'),
    path('my-advertisements/', views.user_advertisements, name='user_advertisements'),
    path('advertisements/notification-settings/', views.notification_settings, name='notification_settings'),
]

# Enhanced Channel System
urlpatterns += [
]

# AI-Powered Features
urlpatterns += [
    # Budget Search - ماذا أستطيع شراء بميزانيتي
    
    # Investment Calculator - استثمر أموالك
    
    # Region Comparison - قارن منطقتين
    
    # Smart Property Score - نظام التقييم الذكي
    
    # AI Property Agent - وكلاء العقارات الذكي
    
    # AI Price Watch - مراقبة الأسعار الذكية
    
    # Smart Alerts - التنبيهات الذكية
    
    # Discover Map - خريطة اكتشف حولك
    
    # Unified Marketplace - Marketplace موحد للبحث
]
