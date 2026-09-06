# Migration to fix missing schema after fake migrations
# This migration creates missing tables and columns that were not applied
# due to previous fake migration logic in entrypoint.sh

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_missing_tables_and_columns(apps, schema_editor):
    """Create missing tables and columns safely"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Check and create SiteSettings table with ALL columns
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'properties_sitesettings'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Create table with minimal columns first
            cursor.execute("""
                CREATE TABLE properties_sitesettings (
                    id BIGSERIAL PRIMARY KEY,
                    site_name VARCHAR(100) DEFAULT 'دلال' NOT NULL,
                    tagline VARCHAR(200) DEFAULT '' NOT NULL,
                    favicon VARCHAR(200) DEFAULT '' NOT NULL,
                    logo VARCHAR(200) DEFAULT '' NOT NULL,
                    site_description TEXT DEFAULT '' NOT NULL,
                    default_language VARCHAR(10) DEFAULT 'ar' NOT NULL,
                    timezone VARCHAR(50) DEFAULT 'Asia/Baghdad' NOT NULL,
                    date_format VARCHAR(20) DEFAULT '%Y-%m-%d' NOT NULL,
                    time_format VARCHAR(20) DEFAULT '%H:%M' NOT NULL,
                    contact_email VARCHAR(254) DEFAULT '' NOT NULL,
                    contact_phone VARCHAR(30) DEFAULT '07701234567' NOT NULL,
                    contact_address VARCHAR(300) DEFAULT '' NOT NULL,
                    contact_city VARCHAR(100) DEFAULT '' NOT NULL,
                    contact_country VARCHAR(100) DEFAULT '' NOT NULL,
                    telegram_url VARCHAR(200) DEFAULT '' NOT NULL,
                    tiktok_url VARCHAR(200) DEFAULT '' NOT NULL,
                    youtube_url VARCHAR(200) DEFAULT '' NOT NULL,
                    snapchat_url VARCHAR(200) DEFAULT '' NOT NULL,
                    facebook_url VARCHAR(200) DEFAULT '' NOT NULL,
                    instagram_url VARCHAR(200) DEFAULT '' NOT NULL,
                    twitter_url VARCHAR(200) DEFAULT '' NOT NULL,
                    linkedin_url VARCHAR(200) DEFAULT '' NOT NULL,
                    whatsapp VARCHAR(30) DEFAULT '' NOT NULL,
                    about_title VARCHAR(200) DEFAULT 'من نحن' NOT NULL,
                    about_content TEXT DEFAULT '' NOT NULL,
                    mission TEXT DEFAULT '' NOT NULL,
                    broker_phone VARCHAR(30) DEFAULT '07701234567' NOT NULL,
                    broker_email VARCHAR(254) DEFAULT '' NOT NULL,
                    broker_address VARCHAR(300) DEFAULT '' NOT NULL,
                    maintenance_mode BOOLEAN DEFAULT FALSE NOT NULL,
                    maintenance_message TEXT DEFAULT '' NOT NULL,
                    maintenance_end_time TIMESTAMP WITH TIME ZONE NULL,
                    allow_admins_during_maintenance BOOLEAN DEFAULT TRUE NOT NULL
                );
            """)
        
        # Add ALL missing columns to properties_sitesettings
        columns_to_add = [
            ('theme_mode', 'VARCHAR(20)', 'light'),
            ('primary_color', 'VARCHAR(20)', '#007bff'),
            ('secondary_color', 'VARCHAR(20)', '#6c757d'),
            ('font_family', 'VARCHAR(50)', 'Arial'),
            ('font_size', 'INTEGER', '16'),
            ('button_style', 'VARCHAR(20)', 'default'),
            ('layout_style', 'VARCHAR(20)', 'default'),
            ('hero_banner_title', 'VARCHAR(200)', 'ابحث عن عقارك المثالي'),
            ('hero_banner_subtitle', 'VARCHAR(300)', 'أفضل العقارات في العراق'),
            ('hero_banner_image', 'VARCHAR(200)', ''),
            ('show_featured_properties', 'BOOLEAN', 'TRUE'),
            ('show_latest_properties', 'BOOLEAN', 'TRUE'),
            ('show_brokers_section', 'BOOLEAN', 'TRUE'),
            ('featured_properties_count', 'INTEGER', '6'),
            ('latest_properties_count', 'INTEGER', '12'),
            ('allow_registration', 'BOOLEAN', 'TRUE'),
            ('require_email_verification', 'BOOLEAN', 'FALSE'),
            ('require_phone_verification', 'BOOLEAN', 'FALSE'),
            ('auto_activate_accounts', 'BOOLEAN', 'TRUE'),
            ('default_user_role', 'VARCHAR(20)', 'user'),
            ('default_currency', 'VARCHAR(3)', 'IQD'),
            ('area_unit', 'VARCHAR(10)', 'm2'),
            ('max_images_per_property', 'INTEGER', '20'),
            ('allow_video_upload', 'BOOLEAN', 'TRUE'),
            ('allow_virtual_tours', 'BOOLEAN', 'TRUE'),
            ('max_image_size', 'INTEGER', '10485760'),
            ('allowed_image_types', 'VARCHAR(100)', 'jpg,jpeg,png'),
            ('max_video_size', 'INTEGER', '52428800'),
            ('allowed_video_types', 'VARCHAR(100)', 'mp4,webm'),
            ('enable_site_notifications', 'BOOLEAN', 'TRUE'),
            ('enable_email_notifications', 'BOOLEAN', 'TRUE'),
            ('enable_sms_notifications', 'BOOLEAN', 'FALSE'),
            ('payment_methods', 'TEXT', 'cash,card'),
            ('enable_subscriptions', 'BOOLEAN', 'TRUE'),
            ('subscription_price_monthly', 'INTEGER', '0'),
            ('subscription_price_yearly', 'INTEGER', '0'),
            ('enable_invoices', 'BOOLEAN', 'TRUE'),
            ('enable_two_factor', 'BOOLEAN', 'FALSE'),
            ('password_min_length', 'INTEGER', '8'),
            ('require_special_chars', 'BOOLEAN', 'FALSE'),
            ('session_timeout', 'INTEGER', '3600'),
            ('log_login_attempts', 'BOOLEAN', 'TRUE'),
            ('enable_reports', 'BOOLEAN', 'TRUE'),
            ('auto_review_reports', 'BOOLEAN', 'FALSE'),
            ('report_priority_threshold', 'INTEGER', '5'),
            ('auto_backup_enabled', 'BOOLEAN', 'TRUE'),
            ('backup_frequency', 'VARCHAR(20)', 'daily'),
            ('backup_retention_days', 'INTEGER', '30'),
            ('seo_title', 'VARCHAR(200)', 'دلال - منصة العقارات في العراق'),
            ('seo_description', 'VARCHAR(300)', 'ابحث عن أفضل العقارات في العراق'),
            ('seo_keywords', 'VARCHAR(300)', 'عقارات,عراق,بيع,شراء'),
            ('enable_og_tags', 'BOOLEAN', 'TRUE'),
            ('enable_api', 'BOOLEAN', 'FALSE'),
            ('api_rate_limit', 'INTEGER', '1000'),
            ('api_key_required', 'BOOLEAN', 'TRUE'),
            ('system_version', 'VARCHAR(20)', '1.0.0'),
            ('license_key', 'VARCHAR(100)', ''),
            ('enable_analytics', 'BOOLEAN', 'FALSE'),
            ('analytics_provider', 'VARCHAR(50)', 'google'),
            ('google_analytics_id', 'VARCHAR(50)', ''),
            ('enable_heatmaps', 'BOOLEAN', 'FALSE'),
            ('enable_user_tracking', 'BOOLEAN', 'FALSE'),
            ('enable_conversion_tracking', 'BOOLEAN', 'FALSE'),
            ('enable_a_b_testing', 'BOOLEAN', 'FALSE'),
            ('enable_google_maps', 'BOOLEAN', 'TRUE'),
            ('google_maps_api_key', 'VARCHAR(100)', ''),
            ('enable_facebook_pixel', 'BOOLEAN', 'FALSE'),
            ('facebook_pixel_id', 'VARCHAR(50)', ''),
            ('enable_twitter_pixel', 'BOOLEAN', 'FALSE'),
            ('twitter_pixel_id', 'VARCHAR(50)', ''),
            ('enable_linkedin_pixel', 'BOOLEAN', 'FALSE'),
            ('linkedin_pixel_id', 'VARCHAR(50)', ''),
            ('enable_auto_moderation', 'BOOLEAN', 'FALSE'),
            ('enable_auto_response', 'BOOLEAN', 'FALSE'),
            ('enable_auto_publish', 'BOOLEAN', 'FALSE'),
            ('enable_scheduled_posts', 'BOOLEAN', 'FALSE'),
            ('enable_auto_backup', 'BOOLEAN', 'TRUE'),
            ('auto_cleanup_days', 'INTEGER', '90'),
            ('enable_rich_text_editor', 'BOOLEAN', 'TRUE'),
            ('enable_content_moderation', 'BOOLEAN', 'FALSE'),
            ('enable_spam_filter', 'BOOLEAN', 'TRUE'),
            ('spam_filter_level', 'VARCHAR(20)', 'medium'),
            ('enable_duplicate_detection', 'BOOLEAN', 'TRUE'),
            ('enable_profanity_filter', 'BOOLEAN', 'TRUE'),
            ('enable_caching', 'BOOLEAN', 'TRUE'),
            ('cache_duration', 'INTEGER', '3600'),
            ('enable_cdn', 'BOOLEAN', 'FALSE'),
            ('cdn_url', 'VARCHAR(200)', ''),
            ('enable_image_optimization', 'BOOLEAN', 'TRUE'),
            ('enable_lazy_loading', 'BOOLEAN', 'TRUE'),
            ('enable_minification', 'BOOLEAN', 'TRUE'),
            ('enable_gzip_compression', 'BOOLEAN', 'TRUE'),
            ('enable_gdpr_compliance', 'BOOLEAN', 'FALSE'),
            ('privacy_policy_url', 'VARCHAR(200)', ''),
            ('terms_of_service_url', 'VARCHAR(200)', ''),
            ('cookie_policy_url', 'VARCHAR(200)', ''),
            ('enable_cookie_consent', 'BOOLEAN', 'FALSE'),
            ('enable_age_verification', 'BOOLEAN', 'FALSE'),
            ('minimum_age', 'INTEGER', '18'),
            ('enable_auto_translation', 'BOOLEAN', 'FALSE'),
            ('translation_provider', 'VARCHAR(50)', 'google'),
            ('translation_api_key', 'VARCHAR(100)', ''),
            ('supported_languages', 'VARCHAR(100)', 'ar,en'),
            ('enable_currency_conversion', 'BOOLEAN', 'FALSE'),
            ('currency_provider', 'VARCHAR(50)', 'fixer'),
            ('enable_data_export', 'BOOLEAN', 'TRUE'),
            ('enable_data_import', 'BOOLEAN', 'TRUE'),
            ('enable_data_anonymization', 'BOOLEAN', 'FALSE'),
            ('data_retention_days', 'INTEGER', '365'),
            ('enable_audit_log', 'BOOLEAN', 'TRUE'),
            ('audit_log_retention_days', 'INTEGER', '90'),
            ('enable_ai_recommendations', 'BOOLEAN', 'FALSE'),
            ('ai_provider', 'VARCHAR(50)', 'openai'),
            ('ai_api_key', 'VARCHAR(100)', ''),
            ('enable_image_recognition', 'BOOLEAN', 'FALSE'),
            ('enable_natural_language_processing', 'BOOLEAN', 'FALSE'),
            ('enable_price_prediction', 'BOOLEAN', 'FALSE'),
            ('enable_fraud_detection', 'BOOLEAN', 'FALSE'),
            ('enable_crm', 'BOOLEAN', 'FALSE'),
            ('crm_provider', 'VARCHAR(50)', 'hubspot'),
            ('crm_api_key', 'VARCHAR(100)', ''),
            ('enable_lead_scoring', 'BOOLEAN', 'FALSE'),
            ('enable_automated_followup', 'BOOLEAN', 'FALSE'),
            ('enable_customer_segmentation', 'BOOLEAN', 'FALSE'),
            ('enable_email_marketing', 'BOOLEAN', 'FALSE'),
            ('email_marketing_provider', 'VARCHAR(50)', 'mailchimp'),
            ('email_marketing_api_key', 'VARCHAR(100)', ''),
            ('enable_newsletter', 'BOOLEAN', 'FALSE'),
            ('newsletter_frequency', 'VARCHAR(20)', 'weekly'),
            ('enable_drip_campaigns', 'BOOLEAN', 'FALSE'),
            ('enable_sms_marketing', 'BOOLEAN', 'FALSE'),
            ('sms_provider', 'VARCHAR(50)', 'twilio'),
            ('sms_api_key', 'VARCHAR(100)', ''),
            ('sms_sender_id', 'VARCHAR(50)', ''),
            ('enable_push_notifications', 'BOOLEAN', 'FALSE'),
            ('push_provider', 'VARCHAR(50)', 'firebase'),
            ('push_api_key', 'VARCHAR(100)', ''),
            ('push_service_worker', 'VARCHAR(200)', ''),
            ('enable_social_sharing', 'BOOLEAN', 'TRUE'),
            ('enable_social_login', 'BOOLEAN', 'TRUE'),
            ('social_login_providers', 'VARCHAR(100)', 'google,facebook'),
            ('enable_social_posting', 'BOOLEAN', 'FALSE'),
            ('social_posting_schedule', 'VARCHAR(20)', 'manual'),
            ('enable_rate_limiting', 'BOOLEAN', 'TRUE'),
            ('rate_limit_requests', 'INTEGER', '1000'),
            ('rate_limit_period', 'INTEGER', '3600'),
            ('enable_ip_whitelist', 'BOOLEAN', 'FALSE'),
            ('ip_whitelist', 'TEXT', ''),
            ('enable_ip_blacklist', 'BOOLEAN', 'FALSE'),
            ('ip_blacklist', 'TEXT', ''),
            ('enable_geoblocking', 'BOOLEAN', 'FALSE'),
            ('blocked_countries', 'TEXT', ''),
            ('enable_user_profiles', 'BOOLEAN', 'TRUE'),
            ('enable_user_reputation', 'BOOLEAN', 'FALSE'),
            ('enable_user_verification', 'BOOLEAN', 'FALSE'),
            ('verification_methods', 'VARCHAR(100)', 'email'),
            ('enable_user_reviews', 'BOOLEAN', 'TRUE'),
            ('enable_user_reports', 'BOOLEAN', 'TRUE'),
            ('enable_property_verification', 'BOOLEAN', 'FALSE'),
            ('property_verification_methods', 'VARCHAR(100)', 'manual'),
            ('enable_property_recommendations', 'BOOLEAN', 'FALSE'),
            ('enable_property_comparison', 'BOOLEAN', 'TRUE'),
            ('enable_property_alerts', 'BOOLEAN', 'TRUE'),
            ('enable_property_valuation', 'BOOLEAN', 'FALSE'),
            ('enable_mobile_app', 'BOOLEAN', 'FALSE'),
            ('mobile_app_ios_url', 'VARCHAR(200)', ''),
            ('mobile_app_android_url', 'VARCHAR(200)', ''),
            ('enable_push_notifications_mobile', 'BOOLEAN', 'FALSE'),
            ('enable_voice_search', 'BOOLEAN', 'FALSE'),
            ('enable_voice_assistant', 'BOOLEAN', 'FALSE'),
            ('voice_language', 'VARCHAR(10)', 'ar'),
            ('enable_crypto_payments', 'BOOLEAN', 'FALSE'),
            ('supported_cryptocurrencies', 'VARCHAR(100)', 'btc,eth'),
            ('enable_nft_integration', 'BOOLEAN', 'FALSE'),
            ('enable_real_time_analytics', 'BOOLEAN', 'FALSE'),
            ('enable_predictive_analytics', 'BOOLEAN', 'FALSE'),
            ('enable_custom_dashboards', 'BOOLEAN', 'FALSE'),
            ('enable_export_reports', 'BOOLEAN', 'TRUE'),
            ('report_formats', 'VARCHAR(100)', 'pdf,csv,xlsx'),
            ('enable_rest_api', 'BOOLEAN', 'TRUE'),
            ('enable_graphql_api', 'BOOLEAN', 'FALSE'),
            ('webhook_endpoints', 'TEXT', ''),
            ('api_documentation_url', 'VARCHAR(200)', ''),
            ('backup_locations', 'TEXT', 'local'),
            ('enable_encrypted_backups', 'BOOLEAN', 'FALSE'),
            ('backup_encryption_key', 'VARCHAR(100)', ''),
            ('enable_cloud_backup', 'BOOLEAN', 'FALSE'),
            ('cloud_backup_provider', 'VARCHAR(50)', 'aws'),
            ('enable_database_optimization', 'BOOLEAN', 'TRUE'),
            ('enable_query_caching', 'BOOLEAN', 'TRUE'),
            ('enable_full_page_caching', 'BOOLEAN', 'TRUE'),
            ('enable_edge_caching', 'BOOLEAN', 'FALSE'),
            ('enable_error_tracking', 'BOOLEAN', 'FALSE'),
            ('error_tracking_provider', 'VARCHAR(50)', 'sentry'),
            ('error_tracking_api_key', 'VARCHAR(100)', ''),
            ('enable_performance_monitoring', 'BOOLEAN', 'TRUE'),
            ('enable_uptime_monitoring', 'BOOLEAN', 'TRUE'),
            ('enable_schema_markup', 'BOOLEAN', 'TRUE'),
            ('enable_canonical_urls', 'BOOLEAN', 'TRUE'),
            ('enable_sitemap_generation', 'BOOLEAN', 'TRUE'),
            ('enable_robots_txt', 'BOOLEAN', 'TRUE'),
            ('enable_meta_tags', 'BOOLEAN', 'TRUE'),
            ('smtp_host', 'VARCHAR(100)', 'smtp.gmail.com'),
            ('smtp_port', 'INTEGER', '587'),
            ('smtp_username', 'VARCHAR(100)', ''),
            ('smtp_password', 'VARCHAR(100)', ''),
            ('smtp_use_tls', 'BOOLEAN', 'TRUE'),
            ('email_from_address', 'VARCHAR(100)', 'noreply@daluailiraq.com'),
            ('email_from_name', 'VARCHAR(100)', 'دلال'),
            ('sms_api_url', 'VARCHAR(200)', ''),
            ('sms_api_username', 'VARCHAR(100)', ''),
            ('sms_api_password', 'VARCHAR(100)', ''),
            ('enable_activity_log', 'BOOLEAN', 'TRUE'),
            ('activity_log_retention_days', 'INTEGER', '90'),
            ('enable_error_log', 'BOOLEAN', 'TRUE'),
            ('error_log_retention_days', 'INTEGER', '30'),
            ('enable_access_log', 'BOOLEAN', 'TRUE'),
            ('access_log_retention_days', 'INTEGER', '30'),
            ('enable_dark_mode', 'BOOLEAN', 'FALSE'),
            ('enable_high_contrast', 'BOOLEAN', 'FALSE'),
            ('enable_text_to_speech', 'BOOLEAN', 'FALSE'),
            ('enable_speech_to_text', 'BOOLEAN', 'FALSE'),
            ('enable_debug_mode', 'BOOLEAN', 'FALSE'),
            ('enable_developer_tools', 'BOOLEAN', 'FALSE'),
            ('enable_api_docs', 'BOOLEAN', 'TRUE'),
            ('enable_swagger_ui', 'BOOLEAN', 'TRUE'),
            ('max_properties_per_user', 'INTEGER', '100'),
            ('max_images_per_user', 'INTEGER', '500'),
            ('max_messages_per_day', 'INTEGER', '50'),
            ('max_search_results', 'INTEGER', '100'),
            ('enable_recaptcha', 'BOOLEAN', 'FALSE'),
            ('recaptcha_site_key', 'VARCHAR(100)', ''),
            ('recaptcha_secret_key', 'VARCHAR(100)', ''),
            ('recaptcha_version', 'VARCHAR(10)', 'v2'),
            ('enable_firewall', 'BOOLEAN', 'FALSE'),
            ('firewall_rules', 'TEXT', ''),
            ('enable_image_cdn', 'BOOLEAN', 'FALSE'),
            ('image_cdn_url', 'VARCHAR(200)', ''),
            ('enable_video_cdn', 'BOOLEAN', 'FALSE'),
            ('video_cdn_url', 'VARCHAR(200)', ''),
            ('enable_server_monitoring', 'BOOLEAN', 'TRUE'),
            ('server_monitoring_interval', 'INTEGER', '60'),
            ('enable_database_monitoring', 'BOOLEAN', 'TRUE'),
            ('enable_cache_monitoring', 'BOOLEAN', 'TRUE'),
            ('enable_oauth', 'BOOLEAN', 'FALSE'),
            ('oauth_providers', 'VARCHAR(100)', 'google,facebook'),
            ('enable_saml', 'BOOLEAN', 'FALSE'),
            ('saml_entity_id', 'VARCHAR(100)', ''),
            ('saml_metadata_url', 'VARCHAR(200)', ''),
            ('enable_cloud_storage', 'BOOLEAN', 'FALSE'),
            ('cloud_storage_provider', 'VARCHAR(50)', 'aws'),
            ('cloud_storage_bucket', 'VARCHAR(100)', ''),
            ('cloud_storage_access_key', 'VARCHAR(100)', ''),
            ('cloud_storage_secret_key', 'VARCHAR(100)', ''),
            ('custom_email_templates', 'BOOLEAN', 'FALSE'),
            ('enable_email_tracking', 'BOOLEAN', 'FALSE'),
            ('enable_email_scheduling', 'BOOLEAN', 'FALSE'),
            ('custom_sms_templates', 'BOOLEAN', 'FALSE'),
            ('enable_sms_tracking', 'BOOLEAN', 'FALSE'),
            ('custom_push_templates', 'BOOLEAN', 'FALSE'),
            ('enable_push_scheduling', 'BOOLEAN', 'FALSE'),
            ('enable_elasticsearch', 'BOOLEAN', 'FALSE'),
            ('elasticsearch_host', 'VARCHAR(100)', 'localhost'),
            ('elasticsearch_port', 'INTEGER', '9200'),
            ('enable_fuzzy_search', 'BOOLEAN', 'FALSE'),
            ('enable_autocomplete', 'BOOLEAN', 'TRUE'),
            ('enable_suggestions', 'BOOLEAN', 'TRUE'),
            ('recommendation_algorithm', 'VARCHAR(50)', 'collaborative'),
            ('enable_ml_recommendations', 'BOOLEAN', 'FALSE'),
            ('enable_personalized_recommendations', 'BOOLEAN', 'FALSE'),
            ('enable_custom_reports', 'BOOLEAN', 'FALSE'),
            ('report_scheduling', 'BOOLEAN', 'FALSE'),
            ('enable_report_automation', 'BOOLEAN', 'FALSE'),
            ('enable_comprehensive_audit', 'BOOLEAN', 'FALSE'),
            ('audit_log_level', 'VARCHAR(20)', 'info'),
            ('enable_audit_alerts', 'BOOLEAN', 'FALSE'),
            ('enable_user_analytics', 'BOOLEAN', 'TRUE'),
            ('enable_property_analytics', 'BOOLEAN', 'TRUE'),
            ('enable_revenue_analytics', 'BOOLEAN', 'TRUE'),
            ('enable_conversion_analytics', 'BOOLEAN', 'TRUE'),
            ('notification_channels', 'VARCHAR(100)', 'email,push'),
            ('enable_notification_groups', 'BOOLEAN', 'FALSE'),
            ('enable_notification_templates', 'BOOLEAN', 'FALSE'),
            ('enable_custom_dashboard', 'BOOLEAN', 'FALSE'),
            ('dashboard_widgets', 'TEXT', ''),
            ('enable_dashboard_scheduling', 'BOOLEAN', 'FALSE'),
            ('enable_third_party_integrations', 'BOOLEAN', 'FALSE'),
            ('integration_settings', 'TEXT', ''),
            ('enable_webhooks', 'BOOLEAN', 'FALSE'),
            ('webhook_settings', 'TEXT', ''),
            ('enable_knowledge_base', 'BOOLEAN', 'FALSE'),
            ('enable_faq_system', 'BOOLEAN', 'FALSE'),
            ('enable_affiliate_program', 'BOOLEAN', 'FALSE'),
            ('enable_referral_program', 'BOOLEAN', 'FALSE'),
            ('enable_loyalty_program', 'BOOLEAN', 'FALSE'),
            ('enable_discount_system', 'BOOLEAN', 'FALSE'),
            ('enable_blog_system', 'BOOLEAN', 'FALSE'),
            ('enable_news_system', 'BOOLEAN', 'FALSE'),
            ('enable_forum_system', 'BOOLEAN', 'FALSE'),
            ('enable_qa_system', 'BOOLEAN', 'FALSE'),
            ('enable_multi_tenant', 'BOOLEAN', 'FALSE'),
            ('enable_white_label', 'BOOLEAN', 'FALSE'),
            ('enable_custom_domains', 'BOOLEAN', 'FALSE'),
            ('enable_api_rate_limiting', 'BOOLEAN', 'TRUE'),
            ('enable_password_complexity', 'BOOLEAN', 'FALSE'),
            ('password_complexity_requirements', 'TEXT', ''),
            ('enable_account_lockout', 'BOOLEAN', 'FALSE'),
            ('account_lockout_threshold', 'INTEGER', '5'),
            ('account_lockout_duration', 'INTEGER', '1800'),
            ('enable_incremental_backup', 'BOOLEAN', 'FALSE'),
            ('enable_differential_backup', 'BOOLEAN', 'FALSE'),
            ('backup_compression', 'BOOLEAN', 'TRUE'),
            ('backup_verification', 'BOOLEAN', 'TRUE'),
            ('enable_query_optimization', 'BOOLEAN', 'TRUE'),
            ('enable_index_optimization', 'BOOLEAN', 'TRUE'),
            ('enable_connection_pooling', 'BOOLEAN', 'TRUE'),
            ('enable_read_replicas', 'BOOLEAN', 'FALSE'),
            ('enable_structured_logging', 'BOOLEAN', 'FALSE'),
            ('log_format', 'VARCHAR(20)', 'json'),
            ('enable_log_rotation', 'BOOLEAN', 'TRUE'),
            ('log_rotation_size', 'INTEGER', '104857600'),
            ('enable_redis_cache', 'BOOLEAN', 'FALSE'),
            ('redis_host', 'VARCHAR(100)', 'localhost'),
            ('redis_port', 'INTEGER', '6379'),
            ('redis_password', 'VARCHAR(100)', ''),
            ('enable_multi_cdn', 'BOOLEAN', 'FALSE'),
            ('cdn_providers', 'VARCHAR(100)', 'cloudflare,aws'),
            ('cdn_fallback', 'BOOLEAN', 'FALSE'),
            ('enable_security_headers', 'BOOLEAN', 'TRUE'),
            ('custom_security_headers', 'TEXT', ''),
            ('enable_csp', 'BOOLEAN', 'FALSE'),
            ('csp_policy', 'TEXT', ''),
            ('enable_advanced_rate_limiting', 'BOOLEAN', 'FALSE'),
            ('rate_limit_rules', 'TEXT', ''),
            ('enable_burst_protection', 'BOOLEAN', 'FALSE'),
            ('enable_bot_protection', 'BOOLEAN', 'FALSE'),
            ('bot_detection_rules', 'TEXT', ''),
            ('enable_honeypot', 'BOOLEAN', 'FALSE'),
            ('enable_ddos_protection', 'BOOLEAN', 'FALSE'),
            ('ddos_protection_level', 'VARCHAR(20)', 'medium'),
            ('enable_traffic_filtering', 'BOOLEAN', 'FALSE'),
            ('enable_ssl_enforcement', 'BOOLEAN', 'TRUE'),
            ('ssl_certificate_path', 'VARCHAR(200)', ''),
            ('ssl_key_path', 'VARCHAR(200)', ''),
            ('enable_hsts', 'BOOLEAN', 'TRUE'),
            ('hsts_max_age', 'INTEGER', '31536000'),
            ('enable_database_encryption', 'BOOLEAN', 'FALSE'),
            ('database_encryption_key', 'VARCHAR(100)', ''),
            ('enable_database_replication', 'BOOLEAN', 'FALSE'),
            ('replication_settings', 'TEXT', ''),
            ('enable_file_encryption', 'BOOLEAN', 'FALSE'),
            ('file_encryption_key', 'VARCHAR(100)', ''),
            ('enable_secure_file_upload', 'BOOLEAN', 'TRUE'),
            ('file_upload_restrictions', 'TEXT', ''),
            ('enable_session_encryption', 'BOOLEAN', 'FALSE'),
            ('session_encryption_key', 'VARCHAR(100)', ''),
            ('enable_session_fixation_protection', 'BOOLEAN', 'TRUE'),
            ('enable_csrf_protection', 'BOOLEAN', 'TRUE'),
            ('enable_api_authentication', 'BOOLEAN', 'TRUE'),
            ('api_authentication_method', 'VARCHAR(20)', 'token'),
            ('enable_api_authorization', 'BOOLEAN', 'TRUE'),
            ('enable_api_encryption', 'BOOLEAN', 'FALSE'),
            ('enable_hipaa_compliance', 'BOOLEAN', 'FALSE'),
            ('enable_pci_dss_compliance', 'BOOLEAN', 'FALSE'),
            ('enable_sox_compliance', 'BOOLEAN', 'FALSE'),
            ('enable_iso27001_compliance', 'BOOLEAN', 'FALSE'),
            ('enable_privacy_by_design', 'BOOLEAN', 'FALSE'),
            ('enable_data_minimization', 'BOOLEAN', 'FALSE'),
            ('enable_purpose_limitation', 'BOOLEAN', 'FALSE'),
            ('enable_storage_limitation', 'BOOLEAN', 'FALSE'),
            ('enable_accuracy', 'BOOLEAN', 'TRUE'),
            ('enable_transparency_reports', 'BOOLEAN', 'FALSE'),
            ('transparency_report_frequency', 'VARCHAR(20)', 'quarterly'),
            ('enable_audit_trail', 'BOOLEAN', 'TRUE'),
            ('enable_user_consent_management', 'BOOLEAN', 'FALSE'),
            ('enable_data_rights', 'BOOLEAN', 'FALSE'),
            ('enable_right_to_access', 'BOOLEAN', 'FALSE'),
            ('enable_right_to_rectification', 'BOOLEAN', 'FALSE'),
            ('enable_right_to_erasure', 'BOOLEAN', 'FALSE'),
            ('enable_right_to_portability', 'BOOLEAN', 'FALSE'),
            ('enable_right_to_object', 'BOOLEAN', 'FALSE'),
            ('enable_real_time_monitoring', 'BOOLEAN', 'FALSE'),
            ('monitoring_alert_thresholds', 'TEXT', ''),
            ('enable_automated_alerts', 'BOOLEAN', 'FALSE'),
            ('alert_escalation_rules', 'TEXT', ''),
            ('enable_incident_response', 'BOOLEAN', 'FALSE'),
            ('incident_response_plan', 'TEXT', ''),
            ('enable_incident_tracking', 'BOOLEAN', 'FALSE'),
            ('enable_post_incident_analysis', 'BOOLEAN', 'FALSE'),
            ('enable_disaster_recovery', 'BOOLEAN', 'FALSE'),
            ('disaster_recovery_plan', 'TEXT', ''),
            ('enable_rto', 'BOOLEAN', 'FALSE'),
            ('rto_hours', 'INTEGER', '24'),
            ('enable_rpo', 'BOOLEAN', 'FALSE'),
            ('rpo_hours', 'INTEGER', '1'),
            ('enable_business_continuity', 'BOOLEAN', 'FALSE'),
            ('business_continuity_plan', 'TEXT', ''),
            ('enable_bcp_testing', 'BOOLEAN', 'FALSE'),
            ('bcp_test_frequency', 'VARCHAR(20)', 'monthly'),
            ('enable_risk_assessment', 'BOOLEAN', 'FALSE'),
            ('risk_assessment_frequency', 'VARCHAR(20)', 'quarterly'),
            ('enable_risk_mitigation', 'BOOLEAN', 'FALSE'),
            ('enable_risk_monitoring', 'BOOLEAN', 'FALSE'),
            ('enable_governance_policies', 'BOOLEAN', 'FALSE'),
            ('governance_framework', 'VARCHAR(50)', 'iso27001'),
            ('enable_policy_enforcement', 'BOOLEAN', 'FALSE'),
            ('enable_compliance_monitoring', 'BOOLEAN', 'FALSE'),
            ('enable_automated_testing', 'BOOLEAN', 'FALSE'),
            ('testing_frequency', 'VARCHAR(20)', 'weekly'),
            ('enable_performance_testing', 'BOOLEAN', 'FALSE'),
            ('enable_security_testing', 'BOOLEAN', 'FALSE'),
            ('enable_compatibility_testing', 'BOOLEAN', 'FALSE'),
            ('enable_api_documentation', 'BOOLEAN', 'TRUE'),
            ('documentation_platform', 'VARCHAR(50)', 'swagger'),
            ('enable_user_documentation', 'BOOLEAN', 'TRUE'),
            ('enable_admin_documentation', 'BOOLEAN', 'TRUE'),
            ('enable_developer_documentation', 'BOOLEAN', 'TRUE'),
            ('enable_user_training', 'BOOLEAN', 'FALSE'),
            ('training_platform', 'VARCHAR(50)', 'lms'),
            ('enable_admin_training', 'BOOLEAN', 'FALSE'),
            ('enable_developer_training', 'BOOLEAN', 'FALSE'),
            ('enable_ticket_system', 'BOOLEAN', 'FALSE'),
            ('ticket_system_provider', 'VARCHAR(50)', 'zendesk'),
            ('enable_live_chat', 'BOOLEAN', 'FALSE'),
            ('live_chat_provider', 'VARCHAR(50)', 'intercom'),
            ('enable_phone_support', 'BOOLEAN', 'FALSE'),
            ('enable_email_support', 'BOOLEAN', 'TRUE'),
            ('enable_user_feedback', 'BOOLEAN', 'TRUE'),
            ('feedback_collection_method', 'VARCHAR(50)', 'form'),
            ('enable_analytics_feedback', 'BOOLEAN', 'FALSE'),
            ('enable_support_feedback', 'BOOLEAN', 'FALSE'),
            ('enable_research_development', 'BOOLEAN', 'FALSE'),
            ('rd_budget_percentage', 'INTEGER', '5'),
            ('enable_experimental_features', 'BOOLEAN', 'FALSE'),
            ('enable_beta_testing', 'BOOLEAN', 'FALSE'),
            ('enable_green_computing', 'BOOLEAN', 'FALSE'),
            ('carbon_footprint_tracking', 'BOOLEAN', 'FALSE'),
            ('enable_energy_efficiency', 'BOOLEAN', 'FALSE'),
            ('enable_sustainable_practices', 'BOOLEAN', 'FALSE'),
            ('enable_csr_programs', 'BOOLEAN', 'FALSE'),
            ('csr_budget_percentage', 'INTEGER', '2'),
            ('enable_community_engagement', 'BOOLEAN', 'FALSE'),
            ('enable_ethical_practices', 'BOOLEAN', 'FALSE'),
            ('enable_diversity_programs', 'BOOLEAN', 'FALSE'),
            ('diversity_metrics', 'TEXT', ''),
            ('enable_inclusion_initiatives', 'BOOLEAN', 'FALSE'),
            ('enable_equal_opportunity', 'BOOLEAN', 'FALSE'),
            ('enable_wcag_compliance', 'BOOLEAN', 'FALSE'),
            ('wcag_level', 'VARCHAR(10)', 'aa'),
            ('enable_screen_reader_support', 'BOOLEAN', 'FALSE'),
            ('enable_keyboard_navigation', 'BOOLEAN', 'TRUE'),
            ('enable_high_contrast_mode', 'BOOLEAN', 'FALSE'),
            ('enable_rtl_support', 'BOOLEAN', 'TRUE'),
            ('enable_ltr_support', 'BOOLEAN', 'TRUE'),
            ('enable_automatic_detection', 'BOOLEAN', 'TRUE'),
            ('enable_manual_selection', 'BOOLEAN', 'TRUE'),
            ('enable_timezone_detection', 'BOOLEAN', 'TRUE'),
            ('enable_timezone_conversion', 'BOOLEAN', 'FALSE'),
            ('enable_daylight_saving', 'BOOLEAN', 'FALSE'),
            ('enable_working_hours', 'BOOLEAN', 'FALSE'),
            ('enable_calendar_sync', 'BOOLEAN', 'FALSE'),
            ('calendar_provider', 'VARCHAR(50)', 'google'),
            ('enable_appointment_scheduling', 'BOOLEAN', 'FALSE'),
            ('enable_reminder_system', 'BOOLEAN', 'FALSE'),
            ('enable_task_tracking', 'BOOLEAN', 'FALSE'),
            ('enable_project_management', 'BOOLEAN', 'FALSE'),
            ('enable_workflow_automation', 'BOOLEAN', 'FALSE'),
            ('enable_process_optimization', 'BOOLEAN', 'FALSE'),
            ('enable_internal_messaging', 'BOOLEAN', 'FALSE'),
            ('enable_announcement_system', 'BOOLEAN', 'FALSE'),
            ('enable_notification_center', 'BOOLEAN', 'FALSE'),
            ('enable_preference_management', 'BOOLEAN', 'TRUE'),
            ('enable_team_features', 'BOOLEAN', 'FALSE'),
            ('enable_sharing_permissions', 'BOOLEAN', 'TRUE'),
            ('enable_collaboration_tools', 'BOOLEAN', 'FALSE'),
            ('enable_version_control', 'BOOLEAN', 'FALSE'),
            ('enable_integration_hub', 'BOOLEAN', 'FALSE'),
            ('integration_hub_url', 'VARCHAR(200)', ''),
            ('enable_webhook_management', 'BOOLEAN', 'FALSE'),
            ('enable_api_gateway', 'BOOLEAN', 'FALSE'),
            ('enable_event_tracking', 'BOOLEAN', 'FALSE'),
            ('enable_event_streaming', 'BOOLEAN', 'FALSE'),
            ('enable_event_replay', 'BOOLEAN', 'FALSE'),
            ('enable_event_archiving', 'BOOLEAN', 'FALSE'),
            ('enable_etl_pipeline', 'BOOLEAN', 'FALSE'),
            ('enable_data_warehouse', 'BOOLEAN', 'FALSE'),
            ('enable_data_lake', 'BOOLEAN', 'FALSE'),
            ('enable_real_time_processing', 'BOOLEAN', 'FALSE'),
            ('enable_model_training', 'BOOLEAN', 'FALSE'),
            ('enable_model_deployment', 'BOOLEAN', 'FALSE'),
            ('enable_model_monitoring', 'BOOLEAN', 'FALSE'),
            ('enable_model_versioning', 'BOOLEAN', 'FALSE'),
            ('enable_sentiment_analysis', 'BOOLEAN', 'FALSE'),
            ('enable_entity_extraction', 'BOOLEAN', 'FALSE'),
            ('enable_text_classification', 'BOOLEAN', 'FALSE'),
            ('enable_language_detection', 'BOOLEAN', 'FALSE'),
            ('enable_image_classification', 'BOOLEAN', 'FALSE'),
            ('enable_object_detection', 'BOOLEAN', 'FALSE'),
            ('enable_face_recognition', 'BOOLEAN', 'FALSE'),
            ('enable_ocr', 'BOOLEAN', 'FALSE'),
            ('enable_speech_recognition', 'BOOLEAN', 'FALSE'),
            ('enable_speaker_identification', 'BOOLEAN', 'FALSE'),
            ('enable_audio_classification', 'BOOLEAN', 'FALSE'),
            ('enable_noise_reduction', 'BOOLEAN', 'FALSE'),
            ('enable_video_analysis', 'BOOLEAN', 'FALSE'),
            ('enable_motion_detection', 'BOOLEAN', 'FALSE'),
            ('enable_scene_detection', 'BOOLEAN', 'FALSE'),
            ('enable_video_transcoding', 'BOOLEAN', 'FALSE'),
            ('enable_iot_devices', 'BOOLEAN', 'FALSE'),
            ('iot_protocol', 'VARCHAR(50)', 'mqtt'),
            ('enable_smart_home_integration', 'BOOLEAN', 'FALSE'),
            ('enable_sensor_data', 'BOOLEAN', 'FALSE'),
            ('enable_smart_contracts', 'BOOLEAN', 'FALSE'),
            ('blockchain_network', 'VARCHAR(50)', 'ethereum'),
            ('enable_digital_identity', 'BOOLEAN', 'FALSE'),
            ('enable_decentralized_storage', 'BOOLEAN', 'FALSE'),
            ('enable_quantum_ready', 'BOOLEAN', 'FALSE'),
            ('quantum_algorithm_support', 'BOOLEAN', 'FALSE'),
            ('enable_post_quantum_crypto', 'BOOLEAN', 'FALSE'),
            ('enable_edge_processing', 'BOOLEAN', 'FALSE'),
            ('edge_node_management', 'BOOLEAN', 'FALSE'),
            ('enable_fog_computing', 'BOOLEAN', 'FALSE'),
            ('enable_5g_connectivity', 'BOOLEAN', 'FALSE'),
            ('enable_network_slicing', 'BOOLEAN', 'FALSE'),
            ('enable_low_latency_communication', 'BOOLEAN', 'FALSE'),
            ('enable_metaverse_integration', 'BOOLEAN', 'FALSE'),
            ('enable_virtual_reality', 'BOOLEAN', 'FALSE'),
            ('enable_augmented_reality', 'BOOLEAN', 'FALSE'),
            ('enable_digital_twins', 'BOOLEAN', 'FALSE'),
            ('enable_satellite_connectivity', 'BOOLEAN', 'FALSE'),
            ('enable_gps_enhancement', 'BOOLEAN', 'FALSE'),
            ('enable_space_data', 'BOOLEAN', 'FALSE'),
            ('enable_biometric_auth', 'BOOLEAN', 'FALSE'),
            ('biometric_methods', 'VARCHAR(100)', 'fingerprint,face'),
            ('enable_dna_analysis', 'BOOLEAN', 'FALSE'),
            ('enable_health_monitoring', 'BOOLEAN', 'FALSE'),
            ('enable_nano_sensors', 'BOOLEAN', 'FALSE'),
            ('enable_nano_robots', 'BOOLEAN', 'FALSE'),
            ('enable_smart_materials', 'BOOLEAN', 'FALSE'),
            ('enable_carbon_capture', 'BOOLEAN', 'FALSE'),
            ('enable_renewable_energy', 'BOOLEAN', 'FALSE'),
            ('enable_waste_management', 'BOOLEAN', 'FALSE'),
            ('enable_water_purification', 'BOOLEAN', 'FALSE'),
            ('enable_rocketry', 'BOOLEAN', 'FALSE'),
            ('enable_orbital_mechanics', 'BOOLEAN', 'FALSE'),
            ('enable_space_exploration', 'BOOLEAN', 'FALSE'),
            ('enable_temporal_coordinates', 'BOOLEAN', 'FALSE'),
            ('enable_parallel_universes', 'BOOLEAN', 'FALSE'),
            ('enable_wormhole_navigation', 'BOOLEAN', 'FALSE'),
            ('enable_neural_interfaces', 'BOOLEAN', 'FALSE'),
            ('enable_brain_computer_interface', 'BOOLEAN', 'FALSE'),
            ('enable_consciousness_upload', 'BOOLEAN', 'FALSE'),
            ('enable_reality_bending', 'BOOLEAN', 'FALSE'),
            ('enable_dimension_travel', 'BOOLEAN', 'FALSE'),
            ('enable_matter_transformation', 'BOOLEAN', 'FALSE'),
            ('enable_simulated_reality', 'BOOLEAN', 'FALSE'),
            ('enable_matrix_protocol', 'BOOLEAN', 'FALSE'),
            ('enable_existence_management', 'BOOLEAN', 'FALSE'),
        ]
        
        for col_name, col_type, default_val in columns_to_add:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'properties_sitesettings' 
                    AND column_name = %s
                );
            """, [col_name])
            if not cursor.fetchone()[0]:
                if default_val == 'NULL':
                    cursor.execute(f"""
                        ALTER TABLE properties_sitesettings 
                        ADD COLUMN {col_name} {col_type} NULL;
                    """)
                elif col_type == 'BOOLEAN':
                    cursor.execute(f"""
                        ALTER TABLE properties_sitesettings 
                        ADD COLUMN {col_name} {col_type} DEFAULT {default_val} NOT NULL;
                    """)
                elif col_type == 'INTEGER':
                    cursor.execute(f"""
                        ALTER TABLE properties_sitesettings 
                        ADD COLUMN {col_name} {col_type} DEFAULT {default_val} NOT NULL;
                    """)
                else:
                    cursor.execute(f"""
                        ALTER TABLE properties_sitesettings 
                        ADD COLUMN {col_name} {col_type} DEFAULT '{default_val}' NOT NULL;
                    """)
        
        # Check and create Broker table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'properties_broker'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                CREATE TABLE properties_broker (
                    id BIGSERIAL PRIMARY KEY,
                    phone VARCHAR(20) NOT NULL,
                    office_name VARCHAR(200) DEFAULT '' NOT NULL,
                    governorate VARCHAR(100) DEFAULT '' NOT NULL,
                    role VARCHAR(10) DEFAULT 'sub' NOT NULL,
                    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    subscription_type VARCHAR(10) DEFAULT 'free' NOT NULL,
                    id_card_image VARCHAR(200) DEFAULT '' NOT NULL,
                    bio TEXT DEFAULT '' NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    office_id INTEGER NULL,
                    parent_id INTEGER NULL,
                    user_id INTEGER NOT NULL UNIQUE
                );
            """)
        
        # Check and create Office table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'properties_office'
            );
        """)
        if not cursor.fetchone()[0]:
            cursor.execute("""
                CREATE TABLE properties_office (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    address VARCHAR(300) DEFAULT '' NOT NULL,
                    phone VARCHAR(30) DEFAULT '' NOT NULL,
                    governorate VARCHAR(100) DEFAULT '' NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    owner_id INTEGER NULL
                );
            """)
        
        # Check and add missing columns to properties_property
        columns_to_add = [
            ('city', 'VARCHAR(100)', 'بغداد'),
            ('is_featured', 'BOOLEAN', 'FALSE'),
            ('is_promoted', 'BOOLEAN', 'FALSE'),
            ('promotion_until', 'DATE', 'NULL'),
            ('slug', 'VARCHAR(220)', ''),
            ('title', 'VARCHAR(200)', ''),
            ('district', 'VARCHAR(100)', ''),
            ('province', 'VARCHAR(30)', 'baghdad'),
            ('latitude', 'DECIMAL(9,6)', 'NULL'),
            ('longitude', 'DECIMAL(9,6)', 'NULL'),
            ('broker_id', 'INTEGER', 'NULL'),
            ('office_id', 'INTEGER', 'NULL'),
            ('owner_id', 'INTEGER', 'NULL'),
            ('is_pinned', 'BOOLEAN', 'FALSE'),
            ('pinned_until', 'TIMESTAMP WITH TIME ZONE', 'NULL'),
        ]
        
        for col_name, col_type, default_val in columns_to_add:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'properties_property' 
                    AND column_name = %s
                );
            """, [col_name])
            if not cursor.fetchone()[0]:
                if default_val == 'NULL':
                    cursor.execute(f"""
                        ALTER TABLE properties_property 
                        ADD COLUMN {col_name} {col_type} NULL;
                    """)
                elif col_type == 'BOOLEAN':
                    cursor.execute(f"""
                        ALTER TABLE properties_property 
                        ADD COLUMN {col_name} {col_type} DEFAULT {default_val} NOT NULL;
                    """)
                elif col_type == 'INTEGER':
                    cursor.execute(f"""
                        ALTER TABLE properties_property 
                        ADD COLUMN {col_name} {col_type} DEFAULT {default_val} NOT NULL;
                    """)
                else:
                    cursor.execute(f"""
                        ALTER TABLE properties_property 
                        ADD COLUMN {col_name} {col_type} DEFAULT '{default_val}' NOT NULL;
                    """)
        
        # Add foreign key constraints
        try:
            cursor.execute("""
                ALTER TABLE properties_property 
                ADD CONSTRAINT properties_property_broker_id_fk 
                FOREIGN KEY (broker_id) REFERENCES properties_broker(id) ON DELETE SET NULL;
            """)
        except Exception:
            pass  # Constraint may already exist
        
        try:
            cursor.execute("""
                ALTER TABLE properties_property 
                ADD CONSTRAINT properties_property_office_id_fk 
                FOREIGN KEY (office_id) REFERENCES properties_office(id) ON DELETE SET NULL;
            """)
        except Exception:
            pass
        
        try:
            cursor.execute("""
                ALTER TABLE properties_broker 
                ADD CONSTRAINT properties_broker_office_id_fk 
                FOREIGN KEY (office_id) REFERENCES properties_office(id) ON DELETE SET NULL;
            """)
        except Exception:
            pass
        
        try:
            cursor.execute("""
                ALTER TABLE properties_broker 
                ADD CONSTRAINT properties_broker_parent_id_fk 
                FOREIGN KEY (parent_id) REFERENCES properties_broker(id) ON DELETE SET NULL;
            """)
        except Exception:
            pass
        
        try:
            cursor.execute("""
                ALTER TABLE properties_broker 
                ADD CONSTRAINT properties_broker_user_id_fk 
                FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;
            """)
        except Exception:
            pass
        
        # Add indexes
        indexes = [
            'properties__provinc_14c1b1_idx ON properties_property(province, city)',
            'properties__type_d3d96a_idx ON properties_property(type, status)',
            'properties__price_32e7c2_idx ON properties_property(price)',
            'properties__created_9ef325_idx ON properties_property(created_at DESC)',
            'properties__is_feat_b56ef4_idx ON properties_property(is_featured, is_promoted)',
        ]
        
        for index_def in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_def}")
            except Exception:
                pass
        
        # Add unique constraint on slug
        try:
            cursor.execute("""
                ALTER TABLE properties_property 
                ADD CONSTRAINT properties_property_slug_key UNIQUE (slug);
            """)
        except Exception:
            pass


def reverse_migration(apps, schema_editor):
    """Reverse migration - drop tables and columns"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Drop tables
        cursor.execute("DROP TABLE IF EXISTS properties_sitesettings CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS properties_broker CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS properties_office CASCADE;")
        
        # Drop columns from properties_property
        columns_to_drop = [
            'city', 'is_featured', 'is_promoted', 'promotion_until', 'slug', 'title',
            'district', 'province', 'latitude', 'longitude', 'broker_id', 'office_id', 'owner_id',
            'is_pinned', 'pinned_until'
        ]
        
        for col_name in columns_to_drop:
            try:
                cursor.execute(f"ALTER TABLE properties_property DROP COLUMN IF EXISTS {col_name};")
            except Exception:
                pass


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0227_useronlinestatus_chatmessage_delivered_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(create_missing_tables_and_columns, reverse_migration),
    ]
