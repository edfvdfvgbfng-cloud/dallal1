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


class HealthCheckMiddleware(MiddlewareMixin):
    """
    Middleware to handle health check requests
    """
    
    def process_request(self, request):
        """
        Handle health check endpoint
        """
        if request.path == '/health/' or request.path == '/health':
            from django.http import JsonResponse
            return JsonResponse({'status': 'healthy'})
        return None


class BaseURLMiddleware(MiddlewareMixin):
    """
    Middleware to handle base URL configuration
    """
    
    def process_request(self, request):
        """
        Set base URL for the request
        """
        request.base_url = getattr(settings, 'BASE_URL', 'https://daluailiraq.com')
        return None


class MaintenanceModeMiddleware(MiddlewareMixin):
    """
    Middleware to handle maintenance mode
    """
    
    def process_request(self, request):
        """
        Check if maintenance mode is enabled
        """
        if getattr(settings, 'MAINTENANCE_MODE', False):
            from django.http import JsonResponse
            # Allow health checks and admin to bypass maintenance mode
            if request.path.startswith('/health') or request.path.startswith('/admin'):
                return None
            return JsonResponse({
                'status': 'maintenance',
                'message': getattr(settings, 'MAINTENANCE_MESSAGE', 'الموقع قيد الصيانة - سنعود قريباً')
            }, status=503)
        return None


class SubscriptionCheckMiddleware(MiddlewareMixin):
    """
    Middleware to check user subscription status
    """
    
    def process_request(self, request):
        """
        Check if user has active subscription for premium features
        """
        # Skip subscription check for non-authenticated users or admin
        if not request.user.is_authenticated or request.user.is_staff:
            return None
        
        # Skip for public pages
        public_paths = ['/login/', '/register/', '/about/', '/contact/']
        if any(request.path.startswith(path) for path in public_paths):
            return None
        
        # Set subscription status on request
        request.has_subscription = getattr(request.user, 'has_active_subscription', False)
        return None