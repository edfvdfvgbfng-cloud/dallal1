"""
Middleware for automatic image optimization and CDN integration
"""

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class ImageOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware to handle image optimization settings
    This middleware sets request-level attributes for image optimization
    """
    
    def process_request(self, request):
        """
        Add image optimization settings to request
        """
        request.image_optimization_enabled = getattr(settings, 'IMAGE_OPTIMIZATION_ENABLED', True)
        request.image_convert_to_webp = getattr(settings, 'IMAGE_CONVERT_TO_WEBP', True)
        request.image_quality = getattr(settings, 'IMAGE_QUALITY', 85)
        request.cdn_enabled = getattr(settings, 'CDN_ENABLED', False)
        
        return None


class CDNMiddleware(MiddlewareMixin):
    """
    Middleware to handle CDN-related headers and settings
    """
    
    def process_response(self, request, response):
        """
        Add CDN-related headers to response
        """
        if getattr(settings, 'CDN_ENABLED', False):
            # Add cache headers for static assets
            if request.path.startswith('/static/') or request.path.startswith('/media/'):
                response['Cache-Control'] = 'public, max-age=31536000, immutable'
                response['X-Content-Type-Options'] = 'nosniff'
        
        return response