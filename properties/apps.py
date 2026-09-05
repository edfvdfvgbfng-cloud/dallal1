from django.apps import AppConfig


class PropertiesConfig(AppConfig):
    name = 'properties'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """تفعيل الإشارات عند بدء التطبيق"""
        try:
            import properties.signals
        except Exception as e:
            # Log error but don't fail startup
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not import signals: {e}")
