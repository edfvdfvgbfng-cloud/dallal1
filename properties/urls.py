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


def placeholder_view(request, *args, **kwargs):
    """Generic placeholder view for unimplemented routes"""
    from django.http import HttpResponse
    html = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Feature Coming Soon</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                max-width: 600px;
                margin: 20px;
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                text-align: center;
            }
            h1 {
                color: #333;
                margin-bottom: 20px;
                font-size: 28px;
            }
            p {
                color: #666;
                font-size: 18px;
                margin-bottom: 30px;
                line-height: 1.6;
            }
            .btn {
                display: inline-block;
                padding: 12px 30px;
                background: #FF7A00;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                transition: background 0.3s;
            }
            .btn:hover {
                background: #ff9500;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Feature Coming Soon</h1>
            <p>This feature is under development. Please check back later.</p>
            <a href="/" class="btn">العودة للصفحة الرئيسية</a>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)


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
    path('dashboard/add/', placeholder_view, name='dashboard_add'),
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
    path('category/inside-iraq/', views.unified_search_view, name='category_inside_iraq'),
    path('category/outside-iraq/', views.unified_search_view, name='category_outside_iraq'),
    
    # Auction routes
    path('auctions/', views.unified_search_view, name='auctions_list'),
    
    # Hotel/Resort/Travel routes (placeholder)
    path('category/hotels/', views.unified_search_view, name='category_hotels'),
    path('category/hotels-outside/', views.unified_search_view, name='category_hotels_outside'),
    path('resorts/inside-iraq/', views.unified_search_view, name='resorts_inside_iraq'),
    path('resorts/outside-iraq/', views.unified_search_view, name='resorts_outside_iraq'),
    path('travel-companies/', views.unified_search_view, name='travel_companies'),
    path('advertisements/public/', views.unified_search_view, name='public_service_advertisements'),
    
    # Channel routes
    path('channels/', views.admin_channels_list, name='channels_list'),
    
    # Catch-all placeholder for missing routes (redirect to home)
    # This will be updated as specific views are implemented
    path('brokers/search/', views.unified_search_view, name='public_broker_search'),
    
    # Travel companies
    
    # Travel packages
    
    # Resorts inside Iraq
    
    # Resorts outside Iraq



    # Dynamic property addition
    path('add/dynamic/', views.dynamic_add_property_view, name='add_dynamic'),
    path('dynamic-add/', views.dynamic_add_property_view, name='dynamic_add_property'),
    

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
    path('api/notifications/unread-count/', views.api_notifications_unread, name='api_notifications_unread_count'),
    
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

# Catch-all placeholder for missing routes (add at the end)
# This handles URLs that are referenced in templates but not yet implemented
placeholder_routes = [
    # Admin routes
    path('admin/panel/', placeholder_view, name='admin_panel'),
    path('admin/analytics/', placeholder_view, name='admin_analytics_panel'),
    path('admin/appointments/', placeholder_view, name='admin_appointment_booking'),
    path('admin/chat/', placeholder_view, name='admin_chat'),
    path('admin/presence/', placeholder_view, name='admin_presence_dashboard'),
    path('admin/presence/update/', placeholder_view, name='admin_update_presence'),
    path('admin/reports/', placeholder_view, name='admin_reports_panel'),
    path('admin/users/toggle/', placeholder_view, name='admin_toggle_user'),
    path('admin/warnings/', placeholder_view, name='issue_user_warning'),
    
    # Broker routes
    path('brokers/join/', placeholder_view, name='broker_join'),
    path('brokers/search/', placeholder_view, name='public_broker_search'),
    path('brokers/appointments/', placeholder_view, name='broker_appointments_list'),
    path('brokers/appointments/booking/', placeholder_view, name='broker_appointment_booking'),
    path('brokers/appointments/<int:id>/', placeholder_view, name='broker_appointment_detail'),
    path('brokers/auctions/', placeholder_view, name='broker_auctions'),
    path('brokers/bulk-messaging/', placeholder_view, name='broker_bulk_messaging'),
    path('brokers/channel/<int:id>/', placeholder_view, name='broker_channel_detail'),
    path('brokers/channel/<int:id>/settings/', placeholder_view, name='broker_channel_settings'),
    path('brokers/channel/<int:id>/stats/', placeholder_view, name='broker_channel_stats'),
    path('brokers/conversations/', placeholder_view, name='broker_conversation_list'),
    path('brokers/conversations/<int:id>/', placeholder_view, name='broker_conversation_detail'),
    path('brokers/hotels/', placeholder_view, name='broker_hotels'),
    path('brokers/hotels-outside/', placeholder_view, name='broker_hotels_outside'),
    path('brokers/messages/', placeholder_view, name='broker_messages'),
    path('brokers/messaging/', placeholder_view, name='broker_messaging'),
    path('brokers/resorts/', placeholder_view, name='broker_resorts'),
    path('brokers/resorts-outside/', placeholder_view, name='broker_resorts_outside'),
    path('brokers/statistics/', placeholder_view, name='broker_statistics'),
    path('brokers/travel-companies/', placeholder_view, name='broker_travel_companies'),
    
    # Channel routes
    path('channels/search/', placeholder_view, name='channel_search'),
    
    # Contract routes
    path('contracts/', placeholder_view, name='contract_list'),
    path('contracts/create/', placeholder_view, name='contract_create'),
    path('contracts/<int:id>/', placeholder_view, name='contract_detail'),
    path('contracts/<int:id>/edit/', placeholder_view, name='contract_edit'),
    path('contracts/<int:id>/delete/', placeholder_view, name='contract_delete'),
    path('contracts/<int:id>/archive/', placeholder_view, name='contract_archive'),
    path('contracts/<int:id>/documents/add/', placeholder_view, name='contract_document_add'),
    path('contracts/<int:id>/documents/<int:doc_id>/delete/', placeholder_view, name='contract_document_delete'),
    path('contracts/<int:id>/documents/<int:doc_id>/', placeholder_view, name='contract_document_view'),
    path('contracts/<int:id>/parties/add/', placeholder_view, name='contract_party_add'),
    path('contracts/statistics/', placeholder_view, name='contract_statistics'),
    
    # CRM routes
    path('crm/', placeholder_view, name='crm_dashboard'),
    path('crm/management/', placeholder_view, name='crm_management'),
    path('crm/contacts/<int:id>/', placeholder_view, name='crm_contact_detail'),
    path('crm/customers/', placeholder_view, name='customers_management'),
    path('crm/customers/create/', placeholder_view, name='customer_create'),
    path('crm/customers/<int:id>/', placeholder_view, name='customer_detail'),
    path('crm/agents/', placeholder_view, name='agents_management'),
    path('crm/agents/create/', placeholder_view, name='agent_create'),
    path('crm/agents/<int:id>/', placeholder_view, name='agent_detail'),
    
    # Dallal routes
    path('dallal/settings/', placeholder_view, name='dallal_settings'),
    path('dallal/subscriptions/', placeholder_view, name='dallal_subscriptions_list'),
    path('dallal/subscriptions/create/', placeholder_view, name='dallal_subscription_create'),
    path('dallal/subscriptions/<int:id>/edit/', placeholder_view, name='dallal_subscription_edit'),
    path('dallal/hotels/create/', placeholder_view, name='dallal_hotel_create'),
    path('dallal/hotels/<int:id>/edit/', placeholder_view, name='dallal_hotel_edit'),
    path('dallal/hotels-outside/create/', placeholder_view, name='dallal_hotel_outside_create'),
    path('dallal/hotels-outside/<int:id>/edit/', placeholder_view, name='dallal_hotel_outside_edit'),
    path('dallal/hotels-outside/<int:id>/delete/', placeholder_view, name='dallal_hotel_outside_delete'),
    path('dallal/resorts/create/', placeholder_view, name='dallal_resort_create'),
    path('dallal/resorts/<int:id>/edit/', placeholder_view, name='dallal_resort_edit'),
    path('dallal/resorts/<int:id>/delete/', placeholder_view, name='dallal_resort_delete'),
    path('dallal/resorts-outside/create/', placeholder_view, name='dallal_resort_outside_create'),
    path('dallal/resorts-outside/<int:id>/edit/', placeholder_view, name='dallal_resort_outside_edit'),
    path('dallal/resorts-outside/<int:id>/delete/', placeholder_view, name='dallal_resort_outside_delete'),
    path('dallal/travel-companies/create/', placeholder_view, name='dallal_travel_company_create'),
    path('dallal/travel-companies/<int:id>/edit/', placeholder_view, name='dallal_travel_company_edit'),
    path('dallal/travel-companies/<int:id>/delete/', placeholder_view, name='dallal_travel_company_delete'),
    
    # Discovery routes
    path('discover/', placeholder_view, name='discover'),
    
    # Financial routes
    path('financial/', placeholder_view, name='financial_dashboard'),
    path('financial/reports/', placeholder_view, name='financial_reports'),
    path('financial/add-transaction/', placeholder_view, name='add_financial_transaction'),
    path('financial/add-expense/', placeholder_view, name='add_expense'),
    path('financial/add-profit/', placeholder_view, name='add_profit'),
    
    # Hotel routes
    path('hotels/', placeholder_view, name='hotels_list'),
    path('hotels/create-inside/', placeholder_view, name='hotel_create_inside_iraq'),
    path('hotels/create-outside/', placeholder_view, name='hotel_create_outside_iraq'),
    path('hotels/<str:slug>/', placeholder_view, name='hotel_detail'),
    path('hotels/<int:id>/', placeholder_view, name='hotel_page_detail_by_id'),
    path('hotels/<int:id>/follow/', placeholder_view, name='hotel_page_follow'),
    path('hotels/<int:id>/unfollow/', placeholder_view, name='hotel_page_unfollow'),
    path('hotels/list/', placeholder_view, name='hotel_page_list'),
    path('hotels/<int:id>/post/', placeholder_view, name='hotel_post_create'),
    path('hotels-outside/<int:id>/post/', placeholder_view, name='hotel_outside_post_create'),
    path('hotels/<int:id>/rating/', placeholder_view, name='hotel_rating_create'),
    
    # Job routes
    path('jobs/', placeholder_view, name='jobs'),
    path('jobs/post/', placeholder_view, name='job_post'),
    path('jobs/<int:id>/apply/', placeholder_view, name='job_apply'),
    
    # Message routes
    path('messages/', placeholder_view, name='message_notification_settings'),
    path('messages/create/', placeholder_view, name='message_create'),
    path('messages/send/', placeholder_view, name='send_message'),
    path('messages/user/', placeholder_view, name='send_user_message'),
    path('messages/broker/', placeholder_view, name='send_broker_message'),
    path('messages/<int:id>/', placeholder_view, name='message_notification_settings'),
    path('conversations/', placeholder_view, name='conversations_list'),
    path('conversations/<int:id>/', placeholder_view, name='conversation_detail'),
    path('conversations/<int:id>/archive/', placeholder_view, name='conversation_archive'),
    path('conversations/<int:id>/delete/', placeholder_view, name='conversation_delete'),
    path('conversations/broker/<int:id>/', placeholder_view, name='broker_conversation_detail'),
    path('conversations/broker/start/', placeholder_view, name='start_broker_conversation'),
    path('conversations/user/<int:id>/', placeholder_view, name='user_message_detail'),
    path('user-messages/', placeholder_view, name='user_messages'),
    path('user-messages/<int:id>/', placeholder_view, name='user_message_detail'),
    path('user-messages/<int:id>/delete/', placeholder_view, name='delete_user_message'),
    path('broker-messages/', placeholder_view, name='broker_message_list'),
    path('broker-messages/<int:id>/', placeholder_view, name='broker_message_detail'),
    
    # Notification routes
    path('notifications/', placeholder_view, name='notifications'),
    path('notifications/center/', placeholder_view, name='notification_center'),
    path('notifications/settings/', placeholder_view, name='notification_settings'),
    
    # Property routes
    path('properties/create/', placeholder_view, name='property_create'),
    path('properties/map/', placeholder_view, name='properties_map'),
    path('properties/contracts/', placeholder_view, name='property_contracts'),
    path('properties/<int:id>/contracts/', placeholder_view, name='real_estate_contracts'),
    path('properties/verification/', placeholder_view, name='property_verification_admin'),
    path('properties/<int:id>/verification/', placeholder_view, name='property_verification_admin_detail'),
    path('properties/<int:id>/verify/', placeholder_view, name='property_verify'),
    path('properties/<int:id>/commissions/', placeholder_view, name='property_view_commissions'),
    path('properties/<int:id>/statistics/', placeholder_view, name='property_statistics'),
    path('properties/<int:id>/publication/', placeholder_view, name='property_publication'),
    
    # Resort routes
    path('resorts/', placeholder_view, name='resorts_list'),
    path('resorts/create-inside/', placeholder_view, name='resort_create_inside_iraq'),
    path('resorts/create-outside/', placeholder_view, name='resort_create_outside_iraq'),
    path('resorts/<int:id>/', placeholder_view, name='resort_detail'),
    path('resorts/inside/<int:id>/', placeholder_view, name='resort_inside_detail'),
    path('resorts/outside/<int:id>/', placeholder_view, name='resort_outside_detail'),
    path('resorts/<int:id>/post/', placeholder_view, name='resort_post_create'),
    path('resorts/outside/<int:id>/post/', placeholder_view, name='resort_outside_post_create'),
    path('resorts/<int:id>/booking/', placeholder_view, name='resort_booking'),
    path('resorts/<int:id>/review/', placeholder_view, name='resort_review'),
    
    # Service provider routes
    path('services/', placeholder_view, name='service_categories'),
    path('services/providers/', placeholder_view, name='service_provider_list'),
    path('services/providers/create/', placeholder_view, name='service_provider_create'),
    path('services/providers/<int:id>/', placeholder_view, name='service_provider_detail'),
    path('services/providers/<int:id>/follow/', placeholder_view, name='service_provider_follow'),
    path('services/providers/<int:id>/unfollow/', placeholder_view, name='service_provider_unfollow'),
    path('services/providers/<int:id>/quote/', placeholder_view, name='service_provider_quote'),
    path('services/providers/<int:id>/contact/', placeholder_view, name='service_provider_contact'),
    path('services/providers/<int:id>/rating/', placeholder_view, name='service_provider_rating_create'),
    path('services/providers/dashboard/', placeholder_view, name='service_provider_dashboard'),
    path('services/advertisements/', placeholder_view, name='public_service_advertisements'),
    path('services/advertisements/create/', placeholder_view, name='create_service_advertisement'),
    path('services/advertisements/<int:id>/', placeholder_view, name='service_advertisement_detail'),
    path('services/advertisements/<int:id>/edit/', placeholder_view, name='edit_service_advertisement'),
    path('services/advertisements/<int:id>/delete/', placeholder_view, name='delete_service_advertisement'),
    path('services/<int:id>/', placeholder_view, name='service_detail'),
    
    # Settings routes
    path('settings/hub/', placeholder_view, name='settings_hub'),
    
    # Sub-broker routes
    path('sub-brokers/', placeholder_view, name='sub_broker_panel'),
    path('sub-brokers/properties/', placeholder_view, name='sub_broker_properties'),
    path('sub-brokers/commissions/', placeholder_view, name='sub_broker_commissions'),
    path('sub-brokers/settings/', placeholder_view, name='sub_broker_settings'),
    
    # Subscription routes
    path('subscriptions/', placeholder_view, name='subscription_plans_list'),
    path('subscriptions/plans/', placeholder_view, name='subscription_plans'),
    path('subscriptions/plans/create/', placeholder_view, name='subscription_plan_create'),
    path('subscriptions/plans/<int:id>/edit/', placeholder_view, name='subscription_plan_edit'),
    path('subscriptions/plans/<int:id>/delete/', placeholder_view, name='subscription_plan_delete'),
    path('subscriptions/renewals/', placeholder_view, name='subscription_renewal_requests_list'),
    path('subscriptions/renewals/create/', placeholder_view, name='subscription_renewal_request'),
    path('subscriptions/renewals/<int:id>/approve/', placeholder_view, name='approve_subscription_renewal'),
    path('subscriptions/renewals/<int:id>/reject/', placeholder_view, name='reject_subscription_renewal'),
    
    # Support routes
    path('support/', placeholder_view, name='support_message_list'),
    path('support/create/', placeholder_view, name='support_message_create'),
    path('support/<int:id>/', placeholder_view, name='support_message_detail'),
    
    # Travel routes
    path('travel/', placeholder_view, name='travel_companies'),
    path('travel/companies/', placeholder_view, name='travel_companies'),
    path('travel/companies/<int:id>/', placeholder_view, name='travel_company_detail'),
    path('travel/companies/<int:id>/post/', placeholder_view, name='travel_company_post_create'),
    path('travel/companies/<int:id>/post/<int:post_id>/edit/', placeholder_view, name='travel_company_post_edit'),
    path('travel/companies/<int:id>/post/<int:post_id>/delete/', placeholder_view, name='travel_company_post_delete'),
    path('travel/packages/', placeholder_view, name='travel_packages'),
    path('travel/packages/create/', placeholder_view, name='travel_package_create'),
    path('travel/packages/<int:id>/', placeholder_view, name='travel_package_detail'),
    
    # User routes
    path('user/settings/', placeholder_view, name='user_settings'),
    path('user/settings/account/', placeholder_view, name='user_settings_account'),
    path('user/settings/activity/', placeholder_view, name='user_settings_activity'),
    path('user/settings/favorites/', placeholder_view, name='user_settings_favorites'),
    path('user/settings/messages/', placeholder_view, name='user_settings_messages'),
    path('user/settings/notifications/', placeholder_view, name='user_settings_notifications'),
    path('user/settings/preferences/', placeholder_view, name='user_settings_preferences'),
    path('user/settings/privacy/', placeholder_view, name='user_settings_privacy'),
    path('user/settings/profile/', placeholder_view, name='user_settings_profile'),
    path('user/settings/security/', placeholder_view, name='user_settings_security'),
    path('user/monitoring/', placeholder_view, name='user_monitoring_panel'),
    path('user/monitoring/<int:id>/', placeholder_view, name='user_monitoring_detail'),
    path('user/moderation/', placeholder_view, name='user_moderation_panel'),
    path('user/moderation/<int:id>/', placeholder_view, name='user_moderation_detail'),
    
    # Wallet routes
    path('wallet/', placeholder_view, name='wallet_details'),
    
    # Additional missing routes
    path('add-property/', placeholder_view, name='add_property'),
    path('account/', placeholder_view, name='account_management'),
    path('activity/', placeholder_view, name='activity_log'),
    path('activity-page/', placeholder_view, name='activity_page'),
    path('block/', placeholder_view, name='block_user'),
    path('unblock/', placeholder_view, name='unblock_user'),
    path('restrict/', placeholder_view, name='restrict_user'),
    path('unrestrict/', placeholder_view, name='unrestrict_user'),
    path('suspend/', placeholder_view, name='suspend_user'),
    path('unsuspend/', placeholder_view, name='unsuspend_user'),
    path('unsuspend-broker/', placeholder_view, name='unsuspend_broker'),
    path('unsuspend-channel/', placeholder_view, name='unsuspend_channel'),
    path('verify-otp/', placeholder_view, name='verify_otp'),
    path('broker/create/', placeholder_view, name='broker_create'),
    path('broker/delete/', placeholder_view, name='broker_delete'),
    path('broker/edit/', placeholder_view, name='broker_edit'),
    path('broker/list/', placeholder_view, name='broker_list'),
    path('broker/toggle-active/', placeholder_view, name='broker_toggle_active'),
    path('broker/panel/', placeholder_view, name='broker_panel'),
    path('channel/dashboard/', placeholder_view, name='channel_dashboard'),
    path('channel/detail/', placeholder_view, name='channel_detail'),
    path('channel/list/', placeholder_view, name='channel_list'),
    path('channel/search/', placeholder_view, name='channel_search'),
    path('channels/', placeholder_view, name='channels'),
    path('contact/', placeholder_view, name='contact'),
    path('content-moderation/', placeholder_view, name='content_moderation'),
    path('conversation/archive/', placeholder_view, name='conversation_archive'),
    path('conversation/delete/', placeholder_view, name='conversation_delete'),
    path('conversation/detail/', placeholder_view, name='conversation_detail'),
    path('conversations/list/', placeholder_view, name='conversations_list'),
    path('advertisement/detail/', placeholder_view, name='advertisement_detail'),
    path('advertisement/list/', placeholder_view, name='advertisement_list'),
    path('advertisement/matches/', placeholder_view, name='advertisement_matches'),
    path('advertisement/responses/', placeholder_view, name='advertisement_responses'),
    path('advertisement/create/', placeholder_view, name='create_advertisement'),
    path('advertisement/<int:id>/update/', placeholder_view, name='update_advertisement'),
    path('advertisement/<int:id>/delete/', placeholder_view, name='delete_advertisement'),
    path('advertisement/<int:id>/respond/', placeholder_view, name='respond_to_advertisement'),
    path('advertisement/<int:id>/responses/', placeholder_view, name='advertisement_responses'),
    path('advertisement/<int:id>/matches/', placeholder_view, name='advertisement_matches'),
    path('appointment/booking/', placeholder_view, name='appointment_booking_landing'),
    path('appointment/calendar/', placeholder_view, name='appointment_calendar'),
    path('appointment/slots/', placeholder_view, name='appointment_slots_management'),
    path('appointments/', placeholder_view, name='appointments_management'),
    path('approve/channel/', placeholder_view, name='approve_channel'),
    path('approve/post/', placeholder_view, name='approve_post'),
    path('approve/property-api/', placeholder_view, name='approve_property_api'),
    path('approve/property-payment/', placeholder_view, name='approve_property_payment'),
    path('approve/subscription-renewal/', placeholder_view, name='approve_subscription_renewal'),
    path('approve/video/', placeholder_view, name='approve_video'),
    path('approve-auction/', placeholder_view, name='admin_approve_auction'),
    path('approve-auction/<int:id>/', placeholder_view, name='approve_auction'),
    path('auction/approval/', placeholder_view, name='auction_approval'),
    path('auction/detail/', placeholder_view, name='auction_detail'),
    path('auction/invitations/', placeholder_view, name='auction_invitations'),
    path('auction/live/', placeholder_view, name='auction_live'),
    path('auction/<int:id>/detail/', placeholder_view, name='auction_detail'),
    path('auction/<int:id>/join/', placeholder_view, name='join_auction'),
    path('auction/<int:id>/bid/', placeholder_view, name='place_bid'),
    path('auction/<int:id>/winner/', placeholder_view, name='determine_auction_winner'),
    path('auctions/', placeholder_view, name='admin_auctions'),
    path('auctions/create/', placeholder_view, name='create_auction'),
    path('auctions/create-advertisement/', placeholder_view, name='create_auction_advertisement'),
    path('auctions/create-invitation/', placeholder_view, name='create_auction_invitation'),
    path('broker/create-auction/', placeholder_view, name='broker_create_auction'),
    path('auctions/join/', placeholder_view, name='join_auction'),
    path('auctions/join-requests/', placeholder_view, name='join_requests_list'),
    path('auctions/join-requests/<int:id>/approve/', placeholder_view, name='join_request_approve'),
    path('auctions/join-requests/<int:id>/reject/', placeholder_view, name='join_request_reject'),
    path('auctions/<int:id>/bid/', placeholder_view, name='place_bid'),
    path('auctions/<int:id>/winner/', placeholder_view, name='determine_auction_winner'),
    path('auctions/<int:id>/delete/', placeholder_view, name='delete_auction'),
    path('auctions/<int:id>/detail/', placeholder_view, name='auction_detail'),
    path('auctions/<int:id>/invitations/', placeholder_view, name='auction_invitations'),
    path('auctions/<int:id>/live/', placeholder_view, name='auction_live'),
    path('auctions/approval/', placeholder_view, name='auction_approval'),
    path('auctions/<int:id>/rating/', placeholder_view, name='auction_rating_create'),
    path('auctions/<int:id>/live-stream/', placeholder_view, name='auction_live_stream'),
    path('auctions/<int:id>/advertisement/', placeholder_view, name='create_auction_advertisement'),
    path('auctions/join-requests/', placeholder_view, name='join_requests_list'),
    path('auctions/join-requests/<int:id>/approve/', placeholder_view, name='join_request_approve'),
    path('auctions/join-requests/<int:id>/reject/', placeholder_view, name='join_request_reject'),
    path('auctions/<int:id>/delete/', placeholder_view, name='delete_auction'),
    path('archive/notification/', placeholder_view, name='archive_notification'),
    path('budget-search/', placeholder_view, name='budget_search'),
    path('bulk-message/create/', placeholder_view, name='bulk_message_create'),
    path('bulk-message/list/', placeholder_view, name='bulk_message_list'),
    path('channel/list/', placeholder_view, name='channel_list'),
    path('dashboard/brokers/', placeholder_view, name='admin_brokers_management'),
    path('dashboard/brokers/<int:id>/toggle/', placeholder_view, name='api_broker_toggle_status'),
    path('dashboard/brokers/<int:id>/verify/', placeholder_view, name='api_broker_verify'),
    path('dashboard/brokers/<int:id>/delete/', placeholder_view, name='api_broker_delete'),
    path('discover/', placeholder_view, name='discover'),
    path('download/backup/', placeholder_view, name='download_backup'),
    path('edit-property/', placeholder_view, name='edit_property'),
    path('edit-service-advertisement/', placeholder_view, name='edit_service_advertisement'),
    path('edit-virtual-tour/', placeholder_view, name='edit_virtual_tour'),
    path('export/brokers/', placeholder_view, name='export_brokers'),
    path('investment-calculator/', placeholder_view, name='investment_calculator'),
    path('lift-suspension/', placeholder_view, name='lift_suspension'),
    path('main-broker-panel/', placeholder_view, name='main_broker_panel'),
    path('manage/channel/subscription/', placeholder_view, name='manage_channel_subscription'),
    path('mark/message/read/', placeholder_view, name='mark_message_read'),
    path('media/dashboard/', placeholder_view, name='media_dashboard'),
    path('media/management/', placeholder_view, name='media_management'),
    path('my-channel/', placeholder_view, name='my_channel'),
    path('my-jobs/', placeholder_view, name='my_jobs'),
    path('notification/center/', placeholder_view, name='notification_center'),
    path('office/presence/settings/', placeholder_view, name='office_presence_settings'),
    path('pay/property-view-commission/', placeholder_view, name='pay_property_view_commission'),
    path('platform/stats/', placeholder_view, name='platform_comprehensive_stats'),
    path('property/create/', placeholder_view, name='property_create'),
    path('property/contracts/', placeholder_view, name='property_contracts'),
    path('property/<int:id>/edit/', placeholder_view, name='edit_property'),
    path('property/<int:id>/delete/', placeholder_view, name='delete_property'),
    path('property/<int:id>/delete-image/', placeholder_view, name='delete_property_image'),
    path('public/service-advertisements/', placeholder_view, name='public_service_advertisements'),
    path('real-estate/contracts/', placeholder_view, name='real_estate_contracts'),
    path('region-comparison/', placeholder_view, name='region_comparison'),
    path('reject/channel/', placeholder_view, name='reject_channel'),
    path('reject/post/', placeholder_view, name='reject_post'),
    path('reject/property-api/', placeholder_view, name='reject_property_api'),
    path('reject/property-payment/', placeholder_view, name='reject_property_payment'),
    path('reject/subscription-renewal/', placeholder_view, name='reject_subscription_renewal'),
    path('reject/video/', placeholder_view, name='reject_video'),
    path('reject-auction/', placeholder_view, name='admin_reject_auction'),
    path('report/detail/', placeholder_view, name='report_detail'),
    path('report/list/', placeholder_view, name='report_list'),
    path('resort/booking/', placeholder_view, name='resort_booking'),
    path('resort/create-inside/', placeholder_view, name='resort_create_inside_iraq'),
    path('resort/create-outside/', placeholder_view, name='resort_create_outside_iraq'),
    path('resort/detail/', placeholder_view, name='resort_detail'),
    path('resort/inside/detail/', placeholder_view, name='resort_inside_detail'),
    path('resort/outside/detail/', placeholder_view, name='resort_outside_detail'),
    path('resort/<int:id>/post/', placeholder_view, name='resort_post_create'),
    path('resort/outside/<int:id>/post/', placeholder_view, name='resort_outside_post_create'),
    path('resort/<int:id>/review/', placeholder_view, name='resort_review'),
    path('respond-to-advertisement/', placeholder_view, name='respond_to_advertisement'),
    path('service/advertisement/detail/', placeholder_view, name='service_advertisement_detail'),
    path('service/categories/', placeholder_view, name='service_categories'),
    path('service/detail/', placeholder_view, name='service_detail'),
    path('service/provider/contact/', placeholder_view, name='service_provider_contact'),
    path('service/provider/create/', placeholder_view, name='service_provider_create'),
    path('service/provider/dashboard/', placeholder_view, name='service_provider_dashboard'),
    path('service/provider/detail/', placeholder_view, name='service_provider_detail'),
    path('service/provider/follow/', placeholder_view, name='service_provider_follow'),
    path('service/provider/list/', placeholder_view, name='service_provider_list'),
    path('service/provider/quote/', placeholder_view, name='service_provider_quote'),
    path('service/provider/rating/', placeholder_view, name='service_provider_rating_create'),
    path('service/provider/unfollow/', placeholder_view, name='service_provider_unfollow'),
    path('social/begin/', placeholder_view, name='social_begin'),
    path('social/disconnect/', placeholder_view, name='social_disconnect'),
    path('start/broker/conversation/', placeholder_view, name='start_broker_conversation'),
    path('support/message/create/', placeholder_view, name='support_message_create'),
    path('support/message/detail/', placeholder_view, name='support_message_detail'),
    path('support/message/list/', placeholder_view, name='support_message_list'),
    path('toggle/advertisement/status/', placeholder_view, name='toggle_advertisement_status'),
    path('toggle/note/complete/', placeholder_view, name='toggle_note_complete'),
    path('travel/company/detail/', placeholder_view, name='travel_company_detail'),
    path('travel/company/post/create/', placeholder_view, name='travel_company_post_create'),
    path('travel/company/post/delete/', placeholder_view, name='travel_company_post_delete'),
    path('travel/company/post/edit/', placeholder_view, name='travel_company_post_edit'),
    path('travel/package/create/', placeholder_view, name='travel_package_create'),
    path('travel/package/detail/', placeholder_view, name='travel_package_detail'),
    path('travel/packages/', placeholder_view, name='travel_packages'),
    path('user/message/detail/', placeholder_view, name='user_message_detail'),
    path('user/messages/', placeholder_view, name='user_messages'),
    path('user/moderation/detail/', placeholder_view, name='user_moderation_detail'),
    path('user/moderation/panel/', placeholder_view, name='user_moderation_panel'),
    path('user/monitoring/', placeholder_view, name='user_monitoring'),
    path('user/monitoring/detail/', placeholder_view, name='user_monitoring_detail'),
    path('user/monitoring/panel/', placeholder_view, name='user_monitoring_panel'),
    path('user/settings/', placeholder_view, name='user_settings'),
    path('user/settings/account/', placeholder_view, name='user_settings_account'),
    path('user/settings/activity/', placeholder_view, name='user_settings_activity'),
    path('user/settings/favorites/', placeholder_view, name='user_settings_favorites'),
    path('user/settings/messages/', placeholder_view, name='user_settings_messages'),
    path('user/settings/notifications/', placeholder_view, name='user_settings_notifications'),
    path('user/settings/preferences/', placeholder_view, name='user_settings_preferences'),
    path('user/settings/privacy/', placeholder_view, name='user_settings_privacy'),
    path('user/settings/profile/', placeholder_view, name='user_settings_profile'),
    path('user/settings/security/', placeholder_view, name='user_settings_security'),
    path('wallet/details/', placeholder_view, name='wallet_details'),
    path('warn/user/', placeholder_view, name='warn_user'),
    path('notification/archive/', placeholder_view, name='archive_notification'),
    path('notification/delete/', placeholder_view, name='delete_notification'),
    path('notification/edit/', placeholder_view, name='admin_edit_notification'),
    path('notification/create/', placeholder_view, name='admin_create_notification'),
    path('notification/detail/', placeholder_view, name='admin_notification_detail'),
    path('notification/panel/', placeholder_view, name='admin_notification_panel'),
    path('notification/resend/', placeholder_view, name='admin_resend_notification'),
    path('admin/presence/', placeholder_view, name='admin_presence_dashboard'),
    path('admin/presence/update/', placeholder_view, name='admin_update_presence'),
    path('admin/reports/', placeholder_view, name='admin_reports_panel'),
    path('admin/users/toggle/', placeholder_view, name='admin_toggle_user'),
    path('admin/warnings/', placeholder_view, name='issue_user_warning'),
    path('admin/chat/', placeholder_view, name='admin_chat'),
    path('admin/contact/', placeholder_view, name='admin_contact'),
    path('admin/auctions/', placeholder_view, name='admin_auctions'),
    path('admin/appointments/', placeholder_view, name='admin_appointment_booking'),
    path('admin/bulk-messaging/', placeholder_view, name='admin_bulk_messaging'),
    path('admin/change-user-type/', placeholder_view, name='admin_change_user_type'),
    path('admin/create-notification/', placeholder_view, name='admin_create_notification'),
    path('admin/create-user/', placeholder_view, name='admin_create_user'),
    path('admin/delete-notification/', placeholder_view, name='admin_delete_notification'),
    path('admin/delete-user/', placeholder_view, name='admin_delete_user'),
    path('admin/edit-notification/', placeholder_view, name='admin_edit_notification'),
    path('admin/edit-user/', placeholder_view, name='admin_edit_user'),
    path('admin/notification-detail/', placeholder_view, name='admin_notification_detail'),
    path('admin/notification-panel/', placeholder_view, name='admin_notification_panel'),
    path('admin/reject-auction/', placeholder_view, name='admin_reject_auction'),
    path('admin/resend-notification/', placeholder_view, name='admin_resend_notification'),
    path('admin/reset-password/', placeholder_view, name='admin_reset_password'),
    path('admin/support-message-detail/', placeholder_view, name='admin_support_message_detail'),
    path('admin/support-message-list/', placeholder_view, name='admin_support_message_list'),
    path('admin/toggle-user/', placeholder_view, name='admin_toggle_user'),
    path('admin/update-presence/', placeholder_view, name='admin_update_presence'),
    path('admin/users-list/', placeholder_view, name='admin_users_list'),
    path('approve-auction/', placeholder_view, name='admin_approve_auction'),
    path('reject-auction/', placeholder_view, name='admin_reject_auction'),
    path('add-note/', placeholder_view, name='add_note'),
    path('delete-note/', placeholder_view, name='delete_note'),
    path('delete-property-image/', placeholder_view, name='delete_property_image'),
    path('delete-property/', placeholder_view, name='delete_property'),
    path('delete-notification/', placeholder_view, name='delete_notification'),
    path('delete-user/', placeholder_view, name='delete_user'),
    path('dynamic-add/', placeholder_view, name='dynamic_add_property'),
    path('edit-property/', placeholder_view, name='edit_property'),
    path('office-panel/', placeholder_view, name='office_panel'),
    path('office-presence/', placeholder_view, name='office_presence_settings'),
    path('preferences/', placeholder_view, name='preferences_settings'),
    path('privacy/', placeholder_view, name='privacy_settings'),
    path('property-verification/', placeholder_view, name='property_verify'),
    path('security/', placeholder_view, name='security_settings'),
    path('social-auth/', placeholder_view, name='social_settings'),
    path('unified-search/', placeholder_view, name='unified_search'),
]

urlpatterns += placeholder_routes
