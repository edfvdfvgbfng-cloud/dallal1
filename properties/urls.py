from django.urls import path
from django.views.generic import RedirectView
from django.http import FileResponse
from django.shortcuts import render
from django.conf import settings
from pathlib import Path

from . import views, api, broker_views, dallal_views, otp_views, channel_views, ai_chatbot_views, ai_admin_views, api_views, ai_gateway_api
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
    path('properties-outside-iraq/', views.properties_outside_iraq_view, name='properties_outside_iraq'),
    path('search/', views.unified_search_view, name='unified_search'),
    path('services-categories/', views.service_categories_view, name='service_categories'),
    path('navigation-error/', views.navigation_error_view, name='navigation_error'),
    # Job opportunities
    path('jobs/', views.jobs_view, name='jobs'),
    path('jobs/post/', views.job_create, name='job_post'),
    path('jobs/create/', RedirectView.as_view(url='/jobs/post/', permanent=False)),
    path('jobs/<str:slug>/', views.job_detail_view, name='job_detail'),
    path('jobs/<str:slug>/apply/', views.job_apply_view, name='job_apply'),
    # Channel pages
    path('channels/', channel_views.ChannelListView.as_view(), name='channel_list'),
    path('channel/brokers/', views.channel_brokers_view, name='channel_brokers'),
    path('channel/users/', views.channel_users_view, name='channel_users'),
    path('channel/admin/', views.channel_admin_view, name='channel_admin'),
    path('channel/broker/<int:channel_id>/', views.broker_channel_detail, name='broker_channel_detail'),
    # Broker Channels
    path('broker-channels/', views.channels_list_view, name='channels_list'),
    path('broker-channel/<slug:slug>/', views.channel_detail_view, name='channel_detail'),
    path('broker-channel/<int:channel_id>/follow/', views.follow_channel_view, name='follow_channel'),
    path('broker-channel/<int:channel_id>/save/', views.save_channel_view, name='save_channel'),
    # New Channel Features
    path('broker-channel/<int:channel_id>/detail/', broker_views.channel_detail, name='broker_channel_detail'),
    path('broker-channel/<int:channel_id>/follow-new/', broker_views.channel_follow, name='channel_follow'),
    path('broker-channel/<int:channel_id>/save-new/', broker_views.channel_save, name='channel_save'),
    path('broker-channel/<int:channel_id>/share/', broker_views.channel_share, name='channel_share'),
    path('broker-channel/review/', broker_views.channel_review, name='channel_review'),
    path('broker-channel/review/<int:review_id>/helpful/', broker_views.channel_review_helpful, name='channel_review_helpful'),
    path('broker-channel/review/<int:review_id>/reply/', broker_views.channel_review_reply, name='channel_review_reply'),
    path('channels/search/', broker_views.channel_search, name='channel_search'),
    path('brokers/search/', broker_views.public_broker_search, name='public_broker_search'),
    path('broker-channel/management/', broker_views.channel_management, name='channel_management'),
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
    path('broker/auctions/', views.broker_auctions, name='broker_auctions'),
    path('d/<slug:slug>/', views.broker_standalone_page, name='broker_standalone_page'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-change/', views.password_change, name='password_change'),
    # OTP Verification
    path('otp/send/', otp_views.send_otp_view, name='send_otp'),
    path('otp/verify/', otp_views.verify_otp_view, name='verify_otp'),
    path('otp/verification/', otp_views.otp_verification_page, name='otp_verification'),
    path('otp/resend/', otp_views.resend_otp_view, name='resend_otp'),
    # Admin Panel
    path('admin-panel/', views.admin_panel_enhanced, name='admin_panel'),
    path('admin-panel/legacy/', views.admin_panel, name='admin_panel_legacy'),
    path('admin-panel/enhanced/', views.admin_dashboard_enhanced, name='admin_dashboard_enhanced'),
    path('admin-panel/brokers/', views.admin_brokers_management, name='admin_brokers_management'),
    path('admin-panel/contact/', views.admin_contact_view, name='admin_contact'),
    path('admin-panel/contact/quick-search/', views.quick_search_users, name='quick_search_users'),
    path('admin-panel/users/', views.admin_users_list, name='admin_users_list'),
    path('admin-panel/properties/', views.admin_properties_advanced, name='admin_properties_list'),
    path('admin-panel/subscriptions/', views.admin_subscriptions_advanced, name='admin_subscriptions_list'),
    path('admin-panel/notifications/', views.admin_notifications_advanced, name='admin_notifications_list'),
    path('admin-panel/monitoring/', views.admin_realtime_monitoring, name='admin_realtime_monitoring'),
    path('admin-panel/analytics/', views.admin_analytics_panel, name='admin_analytics_panel'),
    path('admin-panel/reports/', views.admin_reports_panel, name='admin_reports_panel'),
    # API endpoints for admin
    path('api/users/<int:user_id>/toggle-status/', views.api_toggle_user_status, name='api_toggle_user_status'),
    path('api/users/<int:user_id>/delete/', views.api_delete_user, name='api_delete_user'),
    path('api/users/bulk-actions/', views.api_bulk_user_actions, name='api_bulk_user_actions'),
    path('api/properties/<int:property_id>/approve/', views.api_approve_property, name='api_approve_property'),
    path('api/properties/<int:property_id>/toggle-featured/', views.api_toggle_featured_property, name='api_toggle_featured_property'),
    path('api/properties/<int:property_id>/delete/', views.api_delete_property, name='api_delete_property'),
    path('api/monitoring/realtime/', views.api_realtime_monitoring, name='api_realtime_monitoring'),
    path('api/brokers/<int:broker_id>/verify/', views.api_broker_verify, name='api_broker_verify'),
    path('api/brokers/<int:broker_id>/delete/', views.api_broker_delete, name='api_broker_delete'),
    path('api/brokers/<int:broker_id>/toggle-status/', views.api_broker_toggle_status, name='api_broker_toggle_status'),
    
    # API endpoints for messaging
    path('api/users/search/', views.api_user_search, name='api_user_search'),
    path('api/users/<int:user_id>/profile/', views.api_user_profile, name='api_user_profile'),
    path('api/conversations/check/', views.api_check_conversation, name='api_check_conversation'),
    path('api/conversations/create/', views.api_create_conversation, name='api_create_conversation'),
    path('api/conversations/<uuid:conversation_id>/send/', views.api_send_message, name='api_send_message'),
    path('api/conversations/<int:conversation_id>/export/', views.api_export_conversation, name='api_export_conversation'),
    path('api/calls/signaling/', views.api_call_signaling, name='api_call_signaling'),
    path('api/translate/', views.api_translate_message, name='api_translate_message'),
    path('api/location/share/', views.api_share_location, name='api_share_location'),
    path('api/messages/upload-attachments/', views.api_upload_attachments, name='api_upload_attachments'),
    path('api/properties/search/', views.api_search_properties, name='api_search_properties'),
    path('api/ratings/submit/', views.api_submit_rating, name='api_submit_rating'),
    path('api/appointments/create/', views.api_create_appointment, name='api_create_appointment'),
    path('api/appointments/<int:appointment_id>/', views.api_appointment_detail, name='api_appointment_detail'),
    path('api/appointments/<int:appointment_id>/confirm/', views.api_appointment_confirm, name='api_appointment_confirm'),
    path('api/appointments/<int:appointment_id>/cancel/', views.api_appointment_cancel, name='api_appointment_cancel'),
    path('api/appointments/<int:appointment_id>/reschedule/', views.api_appointment_reschedule, name='api_appointment_reschedule'),
    path('api/appointments/<int:appointment_id>/delete/', views.api_appointment_delete, name='api_appointment_delete'),
    path('api/users/', views.api_users_list, name='api_users_list'),
    path('api/brokers/list/', views.api_brokers_list, name='api_brokers_list'),
    path('api/media/upload/', views.api_media_upload, name='api_media_upload'),
    path('api/media/delete/', views.api_media_delete, name='api_media_delete'),
    path('admin-panel/bulk-messaging/', views.admin_bulk_messaging, name='admin_bulk_messaging'),
    # Messaging System
    path('messages/', views.conversations_list, name='conversations_list'),
    path('messages/<uuid:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('messages/start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('messages/send/', views.send_message, name='send_message'),
    path('messages/<uuid:conversation_id>/archive/', views.conversation_archive, name='conversation_archive'),
    path('messages/<uuid:conversation_id>/delete/', views.conversation_delete, name='conversation_delete'),
    path('admin-panel/users/create/', views.admin_create_user, name='admin_create_user'),
    path('admin-panel/users/<int:user_id>/edit/', views.admin_edit_user, name='admin_edit_user'),
    path('admin-panel/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('admin-panel/users/<int:user_id>/toggle/', views.admin_toggle_user, name='admin_toggle_user'),
    path('admin-panel/users/<int:user_id>/reset-password/', views.admin_reset_password, name='admin_reset_password'),
    path('admin-panel/users/<int:user_id>/change-type/', views.admin_change_user_type, name='admin_change_user_type'),
    path('settings/', views.user_settings, name='user_settings'),
    path('settings/enhanced/', views.settings_hub_enhanced_view, name='settings_enhanced'),
    path('settings/profile/', views.user_settings_profile, name='user_settings_profile'),
    path('settings/security/', views.user_settings_security, name='user_settings_security'),
    path('settings/security/revoke-device/<int:device_id>/', views.revoke_device_access, name='revoke_device'),
    path('settings/social/', views.social_settings, name='social_settings'),
    path('settings/notifications/', views.user_settings_notifications, name='user_settings_notifications'),
    path('settings/privacy/', views.user_settings_privacy, name='user_settings_privacy'),
    path('settings/preferences/', views.user_settings_preferences, name='user_settings_preferences'),
    path('settings/favorites/', views.user_settings_favorites, name='user_settings_favorites'),
    path('settings/messages/', views.user_settings_messages, name='user_settings_messages'),
    path('settings/messages/block/', views.block_user_settings, name='block_user'),
    path('settings/messages/unblock/<int:blocked_user_id>/', views.unblock_user_settings, name='unblock_user'),
    path('settings/activity/', views.user_settings_activity, name='user_settings_activity'),
    path('settings/account/', views.user_settings_account, name='user_settings_account'),
    path('chat/', views.chat_view, name='chat'),
    path('join-broker/', broker_views.broker_join, name='broker_join'),
    path('subscription-plans/', views.subscription_plans, name='subscription_plans'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/my-posts/', views.my_posts, name='my_posts'),
    path('dashboard/advanced-reports/', views.advanced_reports, name='advanced_reports'),
    path('dashboard/platform-stats/', views.platform_comprehensive_stats, name='platform_comprehensive_stats'),
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
    path('admin-panel/content-moderation/', views.content_moderation_view, name='content_moderation'),
    path('admin-panel/content-moderation/channel/<int:channel_id>/approve/', views.approve_channel, name='approve_channel'),
    path('admin-panel/content-moderation/channel/<int:channel_id>/reject/', views.reject_channel, name='reject_channel'),
    path('admin-panel/content-moderation/channel/<int:channel_id>/suspend/', views.suspend_channel, name='suspend_channel'),
    path('admin-panel/content-moderation/channel/<int:channel_id>/unsuspend/', views.unsuspend_channel, name='unsuspend_channel'),
    path('admin-panel/content-moderation/post/<int:post_id>/approve/', views.approve_post, name='approve_post'),
    path('admin-panel/content-moderation/post/<int:post_id>/reject/', views.reject_post, name='reject_post'),
    path('admin-panel/content-moderation/video/<int:video_id>/approve/', views.approve_video, name='approve_video'),
    path('admin-panel/content-moderation/video/<int:video_id>/reject/', views.reject_video, name='reject_video'),
    path('admin-panel/content-moderation/broker/<int:broker_id>/suspend/', views.suspend_broker, name='suspend_broker'),
    path('admin-panel/content-moderation/broker/<int:broker_id>/unsuspend/', views.unsuspend_broker, name='unsuspend_broker'),
    # User Monitoring
    path('admin-panel/user-monitoring/', views.user_monitoring_view, name='user_monitoring'),
    path('admin-panel/user-monitoring/<int:user_id>/details/', views.user_details_api, name='user_details_api'),
    path('admin-panel/user-monitoring/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('admin-panel/user-monitoring/<int:user_id>/suspend/', views.suspend_user, name='suspend_user'),
    path('admin-panel/user-monitoring/<int:user_id>/unsuspend/', views.unsuspend_user, name='unsuspend_user'),
    path('admin-panel/user-monitoring/<int:user_id>/restrict/', views.restrict_user, name='restrict_user'),
    path('admin-panel/user-monitoring/<int:user_id>/unrestrict/', views.unrestrict_user, name='unrestrict_user'),
    path('admin-panel/user-monitoring/<int:user_id>/warn/', views.warn_user, name='warn_user'),

    # Auctions
    path('broker/auctions/create/', views.broker_create_auction, name='broker_create_auction'),
    path('auction/<int:auction_id>/', views.auction_detail, name='auction_detail'),
    path('auction/<int:auction_id>/join/', views.auction_join, name='auction_join'),
    path('auction/<int:auction_id>/live/', views.auction_live, name='auction_live'),
    path('auction/<int:auction_id>/bid/', views.place_bid, name='place_bid'),
    path('auction/<int:auction_id>/access/', views.auction_access_code, name='auction_access_code'),
    path('auction/<int:auction_id>/invitations/', views.auction_invitations, name='auction_invitations'),
    path('auction/<int:auction_id>/invite/', views.create_auction_invitation, name='create_auction_invitation'),
    path('admin-panel/auctions/', views.admin_auctions, name='admin_auctions'),
    path('admin-panel/auctions/<int:auction_id>/approve/', views.admin_approve_auction, name='admin_approve_auction'),
    path('admin-panel/auctions/<int:auction_id>/reject/', views.admin_reject_auction, name='admin_reject_auction'),
    path('admin-panel/auctions/<int:auction_id>/winner/', views.determine_auction_winner, name='determine_auction_winner'),
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
    path('api/user/<int:user_id>/toggle-status/', views.toggle_user_status_api, name='toggle_user_status_api'),
    # Subscription plan management API
    path('api/subscription-plan/<int:plan_id>/details/', views.subscription_plan_details_api, name='subscription_plan_details_api'),
    path('api/subscription-plan/create/', views.subscription_plan_create_api, name='subscription_plan_create_api'),
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
    path('api/brokers/bulk-verify/', views.api_broker_bulk_verify, name='api_broker_bulk_verify'),
    path('api/brokers/bulk-activate/', views.api_broker_bulk_activate, name='api_broker_bulk_activate'),
    path('api/brokers/bulk-deactivate/', views.api_broker_bulk_deactivate, name='api_broker_bulk_deactivate'),
    # AI Chatbot API - Redirected to AI Gateway for unification
    path('api/chatbot/', ai_gateway_api.ai_chat, name='ai_chatbot_api'),
    path('api/chatbot/confirmation/', ai_chatbot_views.ai_confirmation_api, name='ai_confirmation_api'),
    path('api/chatbot/feedback/', ai_chatbot_views.ai_feedback_api, name='ai_feedback_api'),
    path('api/chatbot/correction/', ai_chatbot_views.ai_correction_api, name='ai_correction_api'),
    path('api/chatbot/statistics/', ai_chatbot_views.ai_statistics_api, name='ai_statistics_api'),
    
    # Production AI API
    path('api/ai/chat/', api_views.ai_chat_production_api, name='ai_chat_production_api'),
    path('api/ai/conversations/', api_views.ai_conversation_history_api, name='ai_conversation_history_api'),
    path('api/ai/conversation/persist/', api_views.ai_conversation_persistence_api, name='ai_conversation_persistence_api'),
    path('api/ai/conversation/restore/', api_views.ai_conversation_restore_api, name='ai_conversation_restore_api'),
    path('api/ai/saved-search/', api_views.ai_saved_search_api, name='ai_saved_search_api'),
    path('api/ai/saved-searches/', api_views.ai_saved_searches_api, name='ai_saved_searches_api'),
    path('api/ai/property-alert/', api_views.ai_property_alert_api, name='ai_property_alert_api'),
    path('api/ai/user-analytics/', api_views.ai_user_analytics_api, name='ai_user_analytics_api'),
    path('api/ai/property-comparison/', api_views.ai_property_comparison_api, name='ai_property_comparison_api'),
    path('api/ai/buyer-profile/', api_views.ai_buyer_profile_create_api, name='ai_buyer_profile_create_api'),
    path('api/ai/buyer-profile/get/', api_views.ai_buyer_profile_get_api, name='ai_buyer_profile_get_api'),
    path('api/ai/recommendations/', api_views.ai_recommendations_api, name='ai_recommendations_api'),
    
    # AI Admin
    path('admin/ai/', ai_admin_views.ai_admin_dashboard, name='ai_admin_dashboard'),
    path('admin/ai/training-examples/', ai_admin_views.ai_training_examples, name='ai_training_examples'),
    path('admin/ai/review-examples/', ai_admin_views.ai_review_examples, name='ai_review_examples'),
    path('admin/ai/unknown-queries/', ai_admin_views.ai_unknown_queries, name='ai_unknown_queries'),
    path('admin/ai/model-versions/', ai_admin_views.ai_model_versions, name='ai_model_versions'),
    path('admin/ai/knowledge-base/', ai_admin_views.ai_knowledge_base, name='ai_knowledge_base'),
    path('api/ai/analytics/', ai_admin_views.ai_analytics_api, name='ai_analytics_api'),
    path('api/ai/dataset-export/', ai_admin_views.ai_dataset_export_api, name='ai_dataset_export_api'),
    path('api/ai/train-model/', ai_admin_views.ai_train_model_api, name='ai_train_model_api'),
    path('api/ai/health/', ai_admin_views.ai_health_check_api, name='ai_health_check_api'),
    path('api/ai/user-correction/', ai_admin_views.ai_user_correction_api, name='ai_user_correction_api'),
    path('api/ai/data-augmentation/', ai_admin_views.ai_data_augmentation_api, name='ai_data_augmentation_api'),
    path('api/ai/model-evaluation/', ai_admin_views.ai_model_evaluation_api, name='ai_model_evaluation_api'),
    path('api/ai/debug-mode/', ai_admin_views.ai_debug_mode_api, name='ai_debug_mode_api'),
    path('api/ai/debug-data/', ai_admin_views.ai_debug_data_api, name='ai_debug_data_api'),
    path('api/ai/ab-testing/', ai_admin_views.ai_ab_testing_config_api, name='ai_ab_testing_config_api'),
    path('dashboard/settings/payments/', views.settings_payments, name='settings_payments'),
    path('dashboard/settings/security/', views.settings_security, name='settings_security'),
    path('dashboard/settings/reports/', views.settings_reports, name='settings_reports'),
    path('dashboard/settings/backup/', views.settings_backup, name='settings_backup'),
    path('dashboard/settings/seo/', views.settings_seo, name='settings_seo'),
    path('dashboard/settings/api/', views.settings_api, name='settings_api'),
    path('dashboard/settings/system/', views.settings_system, name='settings_system'),
    path('dashboard/settings/maintenance/', views.settings_maintenance, name='settings_maintenance'),
    path('dashboard/settings/oauth-diagnostics/', views.social_auth_diagnostics, name='social_auth_diagnostics'),
    path('dashboard/add/', views.add_property, name='add_property'),
    path('dashboard/add/enhanced/', views.enhanced_add_property, name='enhanced_add_property'),
    path('dashboard/add/outside/enhanced/', views.enhanced_add_outside_property, name='enhanced_add_outside_property'),
    path('dashboard/edit/<int:property_id>/', views.edit_property, name='edit_property'),
    path('dashboard/delete/<int:property_id>/', views.delete_property, name='delete_property'),
    path('dashboard/statistics/', views.property_statistics, name='property_statistics'),
    path('dashboard/image/delete/<int:image_id>/', views.delete_property_image, name='delete_property_image'),
    path('dashboard/message/<int:message_id>/read/', views.mark_legacy_message_read, name='mark_message_read_legacy'),
    # Sub-broker routes
    path('sub-broker/panel/', broker_views.sub_broker_panel, name='sub_broker_panel'),
    path('sub-broker/commissions/', broker_views.sub_broker_commissions, name='sub_broker_commissions'),
    path('sub-broker/properties/', broker_views.sub_broker_properties, name='sub_broker_properties'),
    path('sub-broker/settings/', broker_views.sub_broker_settings, name='sub_broker_settings'),
    # User messaging routes
    path('messages/', views.user_messages, name='user_messages'),
    path('messages/<int:message_id>/', views.user_message_detail, name='user_message_detail'),
    path('messages/send/', views.send_user_message, name='send_user_message'),
    path('messages/send/<int:broker_id>/', views.send_user_message, name='send_user_message_to_broker'),
    path('messages/delete/<int:message_id>/', views.delete_user_message, name='delete_user_message'),
    # Broker conversation routes
    path('broker-conversations/', views.broker_conversation_list, name='broker_conversation_list'),
    path('broker-conversations/<uuid:conversation_id>/', views.broker_conversation_detail, name='broker_conversation_detail'),
    path('broker-conversations/start/<int:broker_id>/', views.start_broker_conversation, name='start_broker_conversation'),
    path('broker-messages/', views.broker_message_list, name='broker_message_list'),
    path('broker-messages/<uuid:conversation_id>/', views.broker_message_detail, name='broker_message_detail'),
    # Property view commissions
    path('dashboard/commissions/view/', broker_views.property_view_commissions, name='property_view_commissions'),
    path('dashboard/commissions/view/pay/<int:property_id>/', broker_views.pay_property_view_commission, name='pay_property_view_commission'),
    path('dashboard/notes/add/', views.add_note, name='add_note'),
    path('dashboard/notes/<int:note_id>/toggle/', views.toggle_note_complete, name='toggle_note_complete'),
    path('dashboard/notes/<int:note_id>/delete/', views.delete_note, name='delete_note'),
    path('dashboard/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('dashboard/notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('dashboard/property/<int:property_id>/virtual-tour/add/', views.add_virtual_tour, name='add_virtual_tour'),
    path('dashboard/virtual-tour/<int:tour_id>/delete/', views.delete_virtual_tour, name='delete_virtual_tour'),
    path('dashboard/property/<int:property_id>/auction/add/', views.add_auction, name='add_auction'),
    path('dashboard/auction/<int:auction_id>/edit/', views.edit_auction, name='edit_auction'),
    path('dashboard/auction/<int:auction_id>/delete/', views.delete_auction, name='delete_auction'),
    path('auctions/', views.auctions_list, name='auctions_list'),
    path('auction/<int:auction_id>/', views.auction_detail_view, name='auction_detail'),
    path('auction/<int:auction_id>/bid/', views.place_bid_view, name='place_bid'),
    path('auction/<int:auction_id>/join/', views.join_auction_view, name='join_auction'),
    path('auction/create/', views.create_auction_view, name='create_auction'),
    path('auction/approval/', views.auction_approval_view, name='auction_approval'),
    path('auction-terms/', views.auction_terms, name='auction_terms'),
    path('auction/<int:auction_id>/auto-bid/', views.setup_auto_bid, name='setup_auto_bid'),
    path('auction/<int:auction_id>/auto-bid/toggle/', views.toggle_auto_bid, name='toggle_auto_bid'),
    path('auction/<int:auction_id>/rating/', views.auction_rating, name='auction_rating'),
    path('auction/<int:auction_id>/stats/', views.auction_stats, name='auction_stats'),
    path('auction/<int:auction_id>/live-stream/', views.setup_live_stream, name='setup_live_stream'),
    path('auction/<int:auction_id>/advertisement/create/', views.create_auction_advertisement, name='create_auction_advertisement'),
    path('auction/notifications/', views.auction_notifications, name='auction_notifications'),
    
    # Tourism section
    path('hotels/', views.hotels_list, name='hotels_list'),
    path('hotels/create/', views.hotel_create, name='hotel_create'),
    path('hotels/create/inside-iraq/', views.hotel_create_inside_iraq, name='hotel_create_inside_iraq'),
    path('hotels/create/outside-iraq/', views.hotel_create_outside_iraq, name='hotel_create_outside_iraq'),
    path('hotels/<int:hotel_id>/update/', views.hotel_update, name='hotel_update'),
    path('hotels/<int:hotel_id>/delete/', views.hotel_delete, name='hotel_delete'),
    path('resorts/', views.resorts_list, name='resorts_list'),
    path('resorts/create/', views.resort_create, name='resort_create'),
    path('resorts/<slug:slug>/', views.resort_detail, name='resort_detail'),
    path('resorts/<slug:slug>/update/', views.resort_update, name='resort_update'),
    path('resorts/<slug:slug>/delete/', views.resort_delete, name='resort_delete'),
    path('resorts/<slug:slug>/booking/', views.resort_booking, name='resort_booking'),
    path('resorts/<slug:slug>/review/', views.resort_review, name='resort_review'),
    path('resorts/<slug:slug>/like/', views.resort_like, name='resort_like'),
    path('resorts/my-resorts/', views.resort_my_resorts, name='resort_my_resorts'),
    path('resorts/my-bookings/', views.resort_my_bookings, name='resort_my_bookings'),
    
    # New category views
    path('category/inside-iraq/', views.properties_inside_iraq_view, name='category_inside_iraq'),
    path('category/hotels/', views.hotels_category_view, name='category_hotels'),
    path('category/hotels-outside/', views.hotels_outside_category_view, name='category_hotels_outside'),
    path('category/resorts/', views.resorts_category_view, name='category_resorts'),
    path('category/outside-iraq/', views.outside_iraq_category_view, name='category_outside_iraq'),
    
    # Travel companies
    path('travel-companies/', views.travel_companies_view, name='travel_companies'),
    path('travel-companies/<int:pk>/', views.travel_company_detail, name='travel_company_detail'),
    
    # Travel packages
    path('travel-packages/', views.travel_package_list, name='travel_packages'),
    path('travel-packages/<int:pk>/<slug:slug>/', views.travel_package_detail, name='travel_package_detail'),
    path('travel-packages/create/<int:company_id>/', views.travel_package_create, name='travel_package_create'),
    path('travel-packages/<int:pk>/update/', views.travel_package_update, name='travel_package_update'),
    path('travel-packages/<int:pk>/delete/', views.travel_package_delete, name='travel_package_delete'),
    
    # Resorts inside Iraq
    path('resorts-inside-iraq/', views.resorts_inside_iraq_view, name='resorts_inside_iraq'),
    path('resorts-inside-iraq/create/', views.resort_create_inside_iraq, name='resort_create_inside_iraq'),
    path('resorts-inside-iraq/<int:pk>/', views.resort_inside_detail, name='resort_inside_detail'),
    
    # Resorts outside Iraq
    path('resorts-outside-iraq/', views.resorts_outside_iraq_view, name='resorts_outside_iraq'),
    path('resorts-outside-iraq/create/', views.resort_create_outside_iraq, name='resort_create_outside_iraq'),
    path('resorts-outside-iraq/<int:pk>/', views.resort_outside_detail, name='resort_outside_detail'),
    
    # Dynamic property addition
    path('add/dynamic/', views.dynamic_add_property, name='dynamic_add_property'),
    
    path('dashboard/financial/', views.financial_dashboard, name='financial_dashboard'),
    path('dashboard/financial/transaction/add/', views.add_financial_transaction, name='add_financial_transaction'),
    path('dashboard/financial/expense/add/', views.add_expense, name='add_expense'),
    path('dashboard/financial/profit/add/', views.add_profit, name='add_profit'),
    path('dashboard/financial/payment/add/<int:transaction_id>/', views.add_payment, name='add_payment'),
    path('dashboard/financial/wallet/', views.wallet_details, name='wallet_details'),
    path('dashboard/financial/reports/', views.financial_reports, name='financial_reports'),

    # Service Providers
    path('service-provider/register/', views.service_provider_register, name='service_provider_register'),
    path('service-provider/dashboard/', views.service_provider_dashboard, name='service_provider_dashboard'),
    path('service-provider/advertisement/create/', views.create_service_advertisement, name='create_service_advertisement'),
    path('service-provider/advertisement/<int:ad_id>/edit/', views.edit_service_advertisement, name='edit_service_advertisement'),
    path('service-provider/advertisement/<int:ad_id>/delete/', views.delete_service_advertisement, name='delete_service_advertisement'),
    path('services/', views.public_service_advertisements, name='public_service_advertisements'),
    path('services/<int:ad_id>/', views.service_advertisement_detail, name='service_advertisement_detail'),
    path('services/<int:ad_id>/contact/', views.contact_service_provider, name='contact_service_provider'),

    
    # Jobs / Employment
    path('jobs/', views.jobs_list, name='jobs_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/my/', views.my_jobs, name='my_jobs'),
    path('jobs/<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('jobs/<int:pk>/delete/', views.job_delete, name='job_delete'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),

    path('send-message/', views.send_message, name='send_message'),
    path('report/', views.submit_report, name='submit_report'),
    path('dashboard/reports/', views.report_list, name='report_list'),
    path('dashboard/reports/<int:report_id>/', views.report_detail, name='report_detail'),
    path('dashboard/messages/', views.broker_messages_list, name='broker_messages'),
    path('dashboard/messages/create/', views.create_conversation_view, name='create_conversation'),
    path('dashboard/messages/send/', views.send_message_view, name='send_message'),
    path('subscription/renewal/', views.subscription_renewal_request, name='subscription_renewal_request'),
    path('admin-panel/subscription-renewals/', views.subscription_renewal_requests_list, name='subscription_renewal_requests_list'),
    path('api/subscription-renewal/<int:request_id>/approve/', views.approve_subscription_renewal, name='approve_subscription_renewal'),
    path('api/subscription-renewal/<int:request_id>/reject/', views.reject_subscription_renewal, name='reject_subscription_renewal'),
    path('api/statistics/', views.statistics_api, name='statistics_api'),
    path('api/chart/growth/', views.chart_growth_data, name='chart_growth_data'),
    path('api/chart/property-distribution/', views.chart_property_distribution, name='chart_property_distribution'),
    path('api/chart/broker-performance/', views.chart_broker_performance, name='chart_broker_performance'),
    path('api/chart/revenue/', views.chart_revenue, name='chart_revenue'),
    path('api/chart/geographic/', views.chart_geographic, name='chart_geographic'),
    path('api/chart/user-activity/', views.chart_user_activity, name='chart_user_activity'),
    path('api/users/all/', views.all_users_api, name='all_users_api'),
    path('api/conversations/check/', views.api_check_conversation, name='api_check_conversation'),
    path('api/conversations/create/', views.api_create_conversation, name='api_create_conversation'),
    path('api/notifications/unread/', views.api_notifications_unread, name='api_notifications_unread'),
    
    # Developer Panel APIs
    path('api/developer/environment-info/', views.developer_environment_info, name='developer_environment_info'),
    path('api/developer/run-migrations/', views.developer_run_migrations, name='developer_run_migrations'),
    path('api/developer/collect-static/', views.developer_collect_static, name='developer_collect_static'),
    path('api/developer/clear-sessions/', views.developer_clear_sessions, name='developer_clear_sessions'),
    path('api/developer/test-database/', views.developer_test_database, name='developer_test_database'),
    path('api/developer/clear-cache/', views.developer_clear_cache, name='developer_clear_cache'),
    path('api/developer/create-superuser/', views.developer_create_superuser, name='developer_create_superuser'),
    path('api/developer/system-logs/', views.developer_system_logs, name='developer_system_logs'),
    path('api/developer/restart-server/', views.developer_restart_server, name='developer_restart_server'),
    path('admin-panel/user-monitoring-panel/', views.user_monitoring_panel, name='user_monitoring_panel'),
    path('admin-panel/subscription-renewals/', views.subscription_renewal_requests_list, name='subscription_renewal_requests_list'),
    path('admin-panel/user-monitoring-panel/<int:user_id>/', views.user_monitoring_detail, name='user_monitoring_detail'),
    path('dashboard/messages/<int:message_id>/', views.broker_message_detail, name='broker_message_detail'),
    path('dashboard/messages/<int:message_id>/archive/', views.archive_message, name='archive_message'),
    path('dashboard/messages/send/', views.send_broker_message, name='send_broker_message'),
    path('dashboard/messages/send/<int:broker_id>/', views.send_broker_message, name='send_broker_message_to'),
    path('dashboard/messages/create-group/', views.create_group_chat, name='create_group_chat'),
    path('dashboard/messages/<int:message_id>/react/', views.add_message_reaction, name='add_message_reaction'),
    path('dashboard/messages/<int:message_id>/edit/', views.edit_message, name='edit_message'),
    path('dashboard/messages/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('dashboard/messages/<int:message_id>/read/', views.mark_message_read, name='mark_message_read'),
    path('dashboard/messages/<int:message_id>/forward/', views.forward_message, name='forward_message'),
    path('dashboard/bulk-messaging/', views.broker_bulk_messaging, name='broker_bulk_messaging'),
    path('dashboard/users/<int:user_id>/mute/', views.mute_user, name='mute_user'),
    path('dashboard/users/<int:user_id>/unmute/', views.unmute_user, name='unmute_user'),
    path('dashboard/users/<int:user_id>/block/', views.block_user_dashboard, name='block_user_dashboard'),
    path('dashboard/users/<int:user_id>/unblock/', views.unblock_user_dashboard, name='unblock_user_dashboard'),
    path('dashboard/messaging/', views.messaging_dashboard, name='messaging_dashboard'),
    path('api/conversations/', views.api_conversations_list, name='api_conversations_list'),
    path('api/conversations/<uuid:conversation_id>/', views.api_conversation_detail, name='api_conversation_detail'),
    path('api/conversations/<uuid:conversation_id>/star/', views.api_conversation_star, name='api_conversation_star'),
    path('api/conversations/<uuid:conversation_id>/archive/', views.api_conversation_archive, name='api_conversation_archive'),
    path('api/conversations/<uuid:conversation_id>/messages/', views.api_send_message, name='api_send_message_uuid'),
    path('api/upload-attachment/', views.api_upload_attachment, name='api_upload_attachment'),
    path('api/attach-property/', views.api_attach_property, name='api_attach_property'),
    path('dashboard/settings/message-notifications/', views.message_notification_settings, name='message_notification_settings'),
    path('dashboard/account/security/', views.security_settings, name='security_settings'),
    path('dashboard/settings/privacy/', views.privacy_settings, name='privacy_settings'),
    path('dashboard/settings/preferences/', views.preferences_settings, name='preferences_settings'),
    path('dashboard/settings/account/', views.account_management, name='account_management'),
    path('dashboard/user-settings/', views.settings_hub, name='settings_hub'),
    path('dashboard/activity/', views.activity_page, name='activity_page'),
    path('dashboard/bulk-messages/create/', views.bulk_message_create, name='bulk_message_create'),
    path('dashboard/bulk-messages/', views.bulk_message_list, name='bulk_message_list'),
    path('dashboard/broker-statistics/', views.broker_statistics_view, name='broker_statistics'),

    # Notifications
    path('dashboard/notifications/', broker_views.notifications_view, name='notifications'),
    
    # New Notification System
    path('notifications/', views.notification_center, name='notification_center'),
    path('notifications/<int:notification_id>/', views.notification_detail, name='notification_detail'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/<int:notification_id>/clicked/', views.mark_notification_clicked, name='mark_notification_clicked'),
    path('notifications/<int:notification_id>/archive/', views.archive_notification, name='archive_notification'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('notifications/mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('api/notifications/unread-count/', views.get_unread_count, name='get_unread_count'),
    
    # Admin Notifications
    path('admin-panel/notifications/', views.admin_notification_panel, name='admin_notification_panel'),
    path('admin-panel/notifications/create/', views.admin_create_notification, name='admin_create_notification'),
    path('admin-panel/notifications/<int:notification_id>/', views.admin_notification_detail, name='admin_notification_detail'),
    path('admin-panel/notifications/<int:notification_id>/edit/', views.admin_edit_notification, name='admin_edit_notification'),
    path('admin-panel/notifications/<int:notification_id>/resend/', views.admin_resend_notification, name='admin_resend_notification'),
    path('admin-panel/notifications/<int:notification_id>/delete/', views.admin_delete_notification, name='admin_delete_notification'),

    # Broker system routes
    path('dashboard/broker/', broker_views.broker_panel, name='broker_panel'),
    path('dashboard/brokers/', broker_views.broker_list, name='broker_list'),
    path('dashboard/brokers/create/', broker_views.broker_create, name='broker_create'),
    path('dashboard/brokers/<int:broker_id>/edit/', broker_views.broker_edit, name='broker_edit'),
    path('dashboard/brokers/<int:broker_id>/toggle/', broker_views.broker_toggle_active, name='broker_toggle_active'),
    path('dashboard/brokers/<int:broker_id>/delete/', broker_views.broker_delete, name='broker_delete'),
    path('dashboard/brokers/<int:broker_id>/renew/', broker_views.broker_renew_subscription, name='broker_renew_subscription'),
    path('dashboard/brokers/export/', broker_views.export_brokers, name='export_brokers'),
    path('dashboard/brokers/activity-log/', broker_views.activity_log, name='activity_log'),
    path('dashboard/brokers/statistics/', broker_views.broker_statistics, name='broker_statistics_admin'),
    path('dashboard/brokers/messaging/', broker_views.broker_messaging, name='broker_messaging'),
    path('dashboard/brokers/main-panel/', views.main_broker_panel, name='main_broker_panel'),
    # Broker channel management
    path('dashboard/broker/channel/settings/', broker_views.broker_channel_settings, name='broker_channel_settings'),
    path('dashboard/broker/channel/stats/', broker_views.broker_channel_stats, name='broker_channel_stats'),
    path('broker-channel/<int:channel_id>/settings/', broker_views.update_channel_settings, name='update_channel_settings'),
    path('dashboard/subscription-plans/', views.subscription_plans_list, name='subscription_plans_list'),
    path('dashboard/subscription-plans/create/', views.subscription_plan_create, name='subscription_plan_create'),
    path('dashboard/subscription-plans/<int:plan_id>/edit/', views.subscription_plan_edit, name='subscription_plan_edit'),
    path('dashboard/subscription-plans/<int:plan_id>/delete/', views.subscription_plan_delete, name='subscription_plan_delete'),
    path('dashboard/map/', broker_views.properties_map, name='properties_map'),
    path('dashboard/map/api/properties/', broker_views.map_api_properties, name='map_api_properties'),
    path('dashboard/map/api/nearby-places/', broker_views.map_api_nearby_places, name='map_api_nearby_places'),
    path('dashboard/map/api/directions/', broker_views.map_api_directions, name='map_api_directions'),
    path('dashboard/map/api/offices/', broker_views.map_api_offices, name='map_api_offices'),
    path('dashboard/map/api/brokers/', broker_views.map_api_brokers, name='map_api_brokers'),
    path('dashboard/map/api/favorite-areas/', broker_views.map_api_save_favorite_area, name='map_api_save_favorite_area'),
    path('dashboard/map/api/comparison/', broker_views.map_api_add_to_comparison, name='map_api_add_to_comparison'),
    path('dashboard/map/api/comparison/list/', broker_views.map_api_comparison_list, name='map_api_comparison_list'),
    path('dashboard/map/api/comparison/<int:comparison_id>/remove/', broker_views.map_api_remove_from_comparison, name='map_api_remove_from_comparison'),
    path('dashboard/map/api/update-location/', broker_views.map_api_update_property_location, name='map_api_update_property_location'),
    path('dashboard/map/api/bulk-update-coordinates/', broker_views.map_api_bulk_update_coordinates, name='map_api_bulk_update_coordinates'),
    path('dashboard/map/api/validate-coordinates/', broker_views.map_api_validate_coordinates, name='map_api_validate_coordinates'),
    path('dashboard/join-requests/', broker_views.join_requests_list, name='join_requests_list'),
    path('dashboard/join-requests/<int:request_id>/approve/', broker_views.join_request_approve, name='join_request_approve'),
    path('dashboard/join-requests/<int:request_id>/reject/', broker_views.join_request_reject, name='join_request_reject'),
    path('dashboard/office/', broker_views.office_panel, name='office_panel'),
    path('dashboard/office/presence/', broker_views.office_presence_settings, name='office_presence_settings'),
    path('dashboard/office/presence/update/', broker_views.update_presence_status, name='update_presence_status'),
    path('office/<int:office_id>/presence/', broker_views.get_office_presence, name='get_office_presence'),
    path('office/<int:office_id>/subscribe/', broker_views.subscribe_presence_notification, name='subscribe_presence_notification'),
    path('dashboard/admin/presence/', broker_views.admin_presence_dashboard, name='admin_presence_dashboard'),
    path('dashboard/admin/presence/<int:presence_id>/edit/', broker_views.admin_update_presence, name='admin_update_presence'),
    path('broker/<int:broker_id>/subscribe/', broker_views.toggle_broker_subscription, name='toggle_broker_subscription'),
    path('broker/<int:broker_id>/notification-settings/', broker_views.update_broker_notification_settings, name='update_broker_notification_settings'),
    path('subscriptions/', broker_views.user_subscriptions, name='user_subscriptions'),
    path('dashboard/broker/subscriptions/', broker_views.broker_subscription_stats, name='broker_subscription_stats'),
    path('dashboard/admin/broker-subscriptions/', broker_views.admin_broker_subscriptions, name='admin_broker_subscriptions'),
    
    # Backup routes
    path('api/backup/create/', views.create_backup, name='create_backup'),
    path('api/backup/import/', views.import_backup, name='import_backup'),
    path('api/backup/<int:backup_id>/restore/', views.restore_backup, name='restore_backup'),
    path('api/backup/<int:backup_id>/download/', views.download_backup, name='download_backup'),
    path('api/backup/<int:backup_id>/delete/', views.delete_backup, name='delete_backup'),
    path('api/backup/<int:backup_id>/verify/', views.verify_backup, name='verify_backup'),
    path('api/backup/<int:backup_id>/protect/', views.protect_backup, name='protect_backup'),
    path('api/backup/<int:backup_id>/detail/', views.backup_detail, name='backup_detail'),
    path('api/backup/list/', views.backup_list, name='backup_list'),
    
    # System Settings routes
    path('api/system/settings/', views.system_settings, name='system_settings'),
    path('api/system/clear_cache/', views.clear_cache, name='clear_cache'),
    path('api/system/restart_server/', views.restart_server, name='restart_server'),
    path('api/system/advanced_settings/', views.advanced_settings, name='advanced_settings'),
    path('api/system/diagnostics/', views.system_diagnostics, name='system_diagnostics'),
    path('api/system/emergency_shutdown/', views.emergency_shutdown, name='emergency_shutdown'),

    # User management routes
    path('api/users/<int:user_id>/toggle_status/', views.toggle_user_status, name='toggle_user_status'),
    path('api/users/<int:user_id>/details/', views.user_details_api, name='user_details_api'),
    path('api/users/export/', views.export_users, name='export_users'),

    # Property management routes
    path('api/properties/<int:property_id>/approve/', views.approve_property_api, name='approve_property_api'),
    path('api/properties/<int:property_id>/reject/', views.reject_property_api, name='reject_property_api'),

    # Analytics routes
    path('api/analytics/growth/', views.analytics_growth_data, name='analytics_growth'),
    path('api/analytics/property-distribution/', views.analytics_property_distribution, name='analytics_property_distribution'),
    path('api/analytics/broker-performance/', views.analytics_broker_performance, name='analytics_broker_performance'),
    path('api/analytics/revenue/', views.analytics_revenue, name='analytics_revenue'),
    path('api/analytics/geographic/', views.analytics_geographic, name='analytics_geographic'),
    path('api/analytics/user-activity/', views.analytics_user_activity, name='analytics_user_activity'),
    path('api/analytics/performance/', views.analytics_performance, name='analytics_performance'),

    # Dashboard stats routes
    path('api/dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('api/dashboard/recent-activity/', views.recent_activity, name='recent_activity'),
    
    # Dedicated dashboard APIs for each user type
    path('api/dashboard/admin/', views.admin_dashboard_api, name='admin_dashboard_api'),
    path('api/dashboard/broker/', views.broker_dashboard_api, name='broker_dashboard_api'),
    path('api/dashboard/user/', views.user_dashboard_api, name='user_dashboard_api'),

    # Advanced features routes
    path('api/notifications/advanced/', views.advanced_notifications, name='advanced_notifications'),
    path('api/performance/monitoring/', views.performance_monitoring, name='performance_monitoring'),
    path('api/financial/reports/', views.financial_reports, name='financial_reports'),
    path('api/support/tickets/', views.support_tickets, name='support_tickets'),
    path('api/audit/log/', views.audit_log, name='audit_log'),
    path('api/api-keys/', views.api_keys_management, name='api_keys_management'),
    path('api/developer/tools/', views.developer_tools, name='developer_tools'),
    path('api/search/advanced/', views.advanced_search, name='advanced_search'),

    # New advanced features routes
    path('api/tasks/management/', views.task_management, name='task_management'),
    path('api/reports/scheduling/', views.report_scheduling, name='report_scheduling'),
    path('api/files/management/', views.file_management, name='file_management'),
    path('api/server/logs/', views.server_logs, name='server_logs'),
    path('api/database/management/', views.database_management, name='database_management'),
    path('api/security/monitoring/', views.security_monitoring, name='security_monitoring'),
    path('api/subscriptions/advanced/', views.subscription_management_advanced, name='subscription_management_advanced'),
    path('api/data/analytics/', views.data_analytics, name='data_analytics'),

    # New advanced features routes (round 2)
    path('api/media/management/', views.media_management, name='media_management'),
    path('api/messaging/advanced/', views.advanced_messaging, name='advanced_messaging'),
    path('api/email/management/', views.email_management, name='email_management'),
    path('api/access/control/', views.access_control, name='access_control'),
    path('api/crm/management/', views.crm_management, name='crm_management'),
    path('api/automation/management/', views.automation_management, name='automation_management'),
    path('api/integrations/management/', views.integrations_management, name='integrations_management'),
    path('api/performance/reports/', views.performance_reports, name='performance_reports'),

    # New advanced features routes (round 3)
    path('api/surveys/management/', views.survey_management, name='survey_management'),
    path('api/queue/management/', views.queue_management, name='queue_management'),
    path('api/invoices/management/', views.invoice_management, name='invoice_management'),
    path('api/inventory/management/', views.inventory_management, name='inventory_management'),
    path('api/transportation/management/', views.transportation_management, name='transportation_management'),
    path('api/contracts/management/', views.contract_management, name='contract_management'),
    path('api/documents/management/', views.document_management, name='document_management'),
    path('api/events/management/', views.event_management, name='event_management'),

    # Real Estate Specific routes
    path('api/real-estate/properties/', views.property_management_advanced, name='property_management_advanced'),
    path('api/real-estate/clients/', views.clients_management, name='clients_management'),
    path('api/real-estate/offers/', views.offers_management, name='offers_management'),
    path('api/real-estate/auctions/', views.live_auctions_management, name='live_auctions_management'),
    path('api/real-estate/schedules/', views.schedules_management, name='schedules_management'),
    path('api/real-estate/contracts/', views.contracts_real_estate, name='contracts_real_estate'),
    path('api/real-estate/contracts/<int:contract_id>/', views.contract_detail, name='contract_detail'),
    path('api/real-estate/contracts/<int:contract_id>/update/', views.contract_update, name='contract_update'),
    path('api/real-estate/contracts/<int:contract_id>/delete/', views.contract_delete, name='contract_delete'),
    path('api/real-estate/contracts/<int:contract_id>/approve/', views.contract_approve, name='contract_approve'),
    
    # Contract Payments
    path('api/real-estate/contracts/<int:contract_id>/payments/create/', views.contract_payment_create, name='contract_payment_create'),
    path('api/real-estate/payments/<int:payment_id>/update/', views.contract_payment_update, name='contract_payment_update'),
    path('api/real-estate/payments/<int:payment_id>/delete/', views.contract_payment_delete, name='contract_payment_delete'),
    path('api/real-estate/payments/<int:payment_id>/mark-paid/', views.contract_payment_mark_paid, name='contract_payment_mark_paid'),
    
    # Contract Documents
    path('api/real-estate/contracts/<int:contract_id>/documents/create/', views.contract_document_create, name='contract_document_create'),
    path('api/real-estate/documents/<int:document_id>/delete/', views.contract_document_delete, name='contract_document_delete'),
    
    # Contract Reminders
    path('api/real-estate/contracts/<int:contract_id>/reminders/create/', views.contract_reminder_create, name='contract_reminder_create'),
    path('api/real-estate/reminders/<int:reminder_id>/update/', views.contract_reminder_update, name='contract_reminder_update'),
    path('api/real-estate/reminders/<int:reminder_id>/delete/', views.contract_reminder_delete, name='contract_reminder_delete'),
    path('api/real-estate/reminders/<int:reminder_id>/mark-sent/', views.contract_reminder_mark_sent, name='contract_reminder_mark_sent'),
    
    path('api/real-estate/payments/', views.payments_commissions, name='payments_commissions'),
    path('api/real-estate/maps/', views.geographic_maps, name='geographic_maps'),
    path('api/advanced/reports/', views.advanced_reports_management, name='advanced_reports_management'),

    # Real Estate Contracts Page
    path('dashboard/contracts/', views.real_estate_contracts_page, name='real_estate_contracts'),

    # Dallal system routes
    path('dashboard/dallal/settings/', dallal_views.dallal_settings, name='dallal_settings'),
    path('dashboard/dallal/subscriptions/', dallal_views.dallal_subscriptions_list, name='dallal_subscriptions_list'),
    path('dashboard/dallal/subscriptions/create/', dallal_views.dallal_subscription_create, name='dallal_subscription_create'),
    path('dashboard/dallal/subscriptions/<int:subscription_id>/edit/', dallal_views.dallal_subscription_edit, name='dallal_subscription_edit'),
    
    # Dallal travel companies routes
    path('dashboard/dallal/travel-companies/create/', dallal_views.dallal_travel_company_create, name='dallal_travel_company_create'),
    path('dashboard/dallal/travel-companies/<int:company_id>/edit/', dallal_views.dallal_travel_company_edit, name='dallal_travel_company_edit'),
    
    # Travel company reviews routes
    path('travel-companies/<int:company_id>/review/create/', dallal_views.travel_company_review_create, name='travel_company_review_create'),
    path('travel-companies/reviews/<int:review_id>/edit/', dallal_views.travel_company_review_edit, name='travel_company_review_edit'),
    
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
    path('property/<str:slug>/publish/', views.property_publication, name='property_publication'),
    path('property/<str:slug>/payment/', views.property_payment, name='property_payment'),
    path('admin-panel/payment/<int:payment_id>/approve/', views.approve_property_payment, name='approve_property_payment'),
    path('admin-panel/payment/<int:payment_id>/reject/', views.reject_property_payment, name='reject_property_payment'),
    
    # User Moderation System routes
    path('admin-panel/users/', views.user_moderation_panel, name='user_moderation_panel'),
    path('admin-panel/users/<int:user_id>/', views.user_detail_moderation, name='user_moderation_detail'),
    path('admin-panel/users/<int:user_id>/warn/', views.issue_user_warning, name='issue_user_warning'),
    path('admin-panel/users/<int:user_id>/suspend/', views.suspend_user, name='suspend_user'),
    path('admin-panel/users/<int:user_id>/lift-suspension/', views.lift_suspension, name='lift_suspension'),
    path('admin-panel/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    
    # نظام الفنادق والمنتجعات الجديد
    path('hotels/', broker_views.hotel_page_list, name='hotel_page_list'),
    path('hotels/create/', broker_views.hotel_page_create, name='hotel_page_create'),
    path('hotels/<slug:slug>/', broker_views.hotel_page_detail, name='hotel_page_detail'),
    path('hotels/<slug:slug>/follow/', broker_views.hotel_page_follow, name='hotel_page_follow'),
    path('hotels/<slug:slug>/unfollow/', broker_views.hotel_page_unfollow, name='hotel_page_unfollow'),
    path('hotels/<slug:slug>/rate/', broker_views.hotel_rating_create, name='hotel_rating_create'),
    
    # Hotel Posts
    path('hotels/<slug:slug>/posts/create/', broker_views.hotel_post_create, name='hotel_post_create'),
    path('hotels/<slug:slug>/posts/<int:post_id>/edit/', broker_views.hotel_post_edit, name='hotel_post_edit'),
    path('hotels/<slug:slug>/posts/<int:post_id>/delete/', broker_views.hotel_post_delete, name='hotel_post_delete'),
    
    # Hotel Rooms
    path('hotels/<slug:slug>/rooms/create/', broker_views.hotel_room_create, name='hotel_room_create'),
    path('hotels/<slug:slug>/rooms/<int:room_id>/edit/', broker_views.hotel_room_edit, name='hotel_room_edit'),
    path('hotels/<slug:slug>/rooms/<int:room_id>/delete/', broker_views.hotel_room_delete, name='hotel_room_delete'),
    
    # Hotel Offers
    path('hotels/<slug:slug>/offers/create/', broker_views.hotel_offer_create, name='hotel_offer_create'),
    path('hotels/<slug:slug>/offers/<int:offer_id>/edit/', broker_views.hotel_offer_edit, name='hotel_offer_edit'),
    path('hotels/<slug:slug>/offers/<int:offer_id>/delete/', broker_views.hotel_offer_delete, name='hotel_offer_delete'),
    
    # Hotel Bookings
    path('hotels/<slug:slug>/bookings/create/', broker_views.hotel_booking_create, name='hotel_booking_create'),
    path('hotels/<slug:slug>/bookings/<int:booking_id>/edit/', broker_views.hotel_booking_edit, name='hotel_booking_edit'),
    path('hotels/<slug:slug>/bookings/<int:booking_id>/cancel/', broker_views.hotel_booking_cancel, name='hotel_booking_cancel'),
    
    # Service Provider System
    path('service-providers/', broker_views.service_provider_list, name='service_provider_list'),
    path('service-providers/create/', broker_views.service_provider_create, name='service_provider_create'),
    path('service-providers/<slug:slug>/', broker_views.service_provider_detail, name='service_provider_detail'),
    path('service-providers/<slug:slug>/follow/', broker_views.service_provider_follow, name='service_provider_follow'),
    path('service-providers/<slug:slug>/unfollow/', broker_views.service_provider_unfollow, name='service_provider_unfollow'),
    path('service-providers/<slug:slug>/rate/', broker_views.service_provider_rating_create, name='service_provider_rating_create'),
    path('service-providers/<slug:slug>/contact/', broker_views.service_provider_contact, name='service_provider_contact'),
    path('service-providers/<slug:slug>/quote/', broker_views.service_provider_quote, name='service_provider_quote'),
    
    # Support Message System
    path('support/messages/', views.support_message_list, name='support_message_list'),
    path('support/messages/create/', views.support_message_create, name='support_message_create'),
    path('support/messages/<int:message_id>/', views.support_message_detail, name='support_message_detail'),
    path('admin/support/messages/', views.admin_support_message_list, name='admin_support_message_list'),
    path('admin/support/messages/<int:message_id>/', views.admin_support_message_detail, name='admin_support_message_detail'),
    
    # Broker appointments
    path('broker/<int:broker_id>/appointment/book/', views.broker_appointment_booking, name='broker_appointment_booking'),
    path('broker/appointments/', views.broker_appointments_list, name='broker_appointments_list'),
    path('broker/appointments/<int:appointment_id>/', views.broker_appointment_detail, name='broker_appointment_detail'),
    
    # Advanced appointments management
    path('dashboard/appointments/', views.appointments_management, name='appointments_management'),
    path('dashboard/appointments/calendar/', views.appointment_calendar, name='appointment_calendar'),
    path('api/appointments/<int:appointment_id>/reschedule/', views.appointment_reschedule, name='appointment_reschedule'),
    path('dashboard/appointments/slots/', views.appointment_slots_management, name='appointment_slots_management'),
    
    # Customer Management System
    path('dashboard/customers/', views.customers_management, name='customers_management'),
    path('dashboard/customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('dashboard/customers/create/', views.customer_create, name='customer_create'),
    path('dashboard/customers/<int:customer_id>/edit/', views.customer_update, name='customer_update'),
    path('dashboard/customers/<int:customer_id>/delete/', views.customer_delete, name='customer_delete'),
    
    # Agent Management System
    path('dashboard/agents/', views.agents_management, name='agents_management'),
    path('dashboard/agents/<int:agent_id>/', views.agent_detail, name='agent_detail'),
    path('dashboard/agents/create/', views.agent_create, name='agent_create'),
    path('dashboard/agents/<int:agent_id>/edit/', views.agent_update, name='agent_update'),
    path('dashboard/agents/<int:agent_id>/delete/', views.agent_delete, name='agent_delete'),
    
    # Broker profile (must be last as it's a catch-all)
    path('broker/<str:username>/', views.broker_profile, name='broker_profile'),
]

# Enterprise API endpoints (only if available)
if api_enterprise:
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
    path('channels/', channel_views.ChannelListView.as_view(), name='channel_list'),
    path('channels/<int:channel_id>/', channel_views.ChannelDetailView.as_view(), name='channel_detail'),
    path('channels/<int:channel_id>/dashboard/', channel_views.channel_dashboard, name='channel_dashboard'),
    path('channels/<int:channel_id>/content/create/', channel_views.create_channel_content, name='create_channel_content'),
    path('channels/<int:channel_id>/broadcast/create/', channel_views.create_channel_broadcast, name='create_channel_broadcast'),
    path('channels/<int:channel_id>/subscription/', channel_views.manage_channel_subscription, name='manage_channel_subscription'),
    path('channels/collaboration/create/', channel_views.create_channel_collaboration, name='create_channel_collaboration'),
    path('channels/<int:channel_id>/advertisement/create/', channel_views.create_channel_advertisement, name='create_channel_advertisement'),
    path('channels/<int:channel_id>/follow/', channel_views.follow_channel, name='follow_channel'),
    path('channels/content/<int:content_id>/like/', channel_views.like_channel_content, name='like_channel_content'),
]
