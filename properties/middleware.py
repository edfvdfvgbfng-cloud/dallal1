"""
Custom Middleware for Production-Grade Security and Performance
"""

import time
import logging
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Rate limiting middleware to prevent API abuse
    Configurable limits per endpoint and user type
    """
    
    RATE_LIMITS = {
        'default': {'requests': 100, 'window': 60},  # 100 requests per minute
        'ai_chat': {'requests': 30, 'window': 60},  # 30 AI requests per minute
        'voice': {'requests': 20, 'window': 60},  # 20 voice requests per minute
        'search': {'requests': 50, 'window': 60},  # 50 search requests per minute
        'upload': {'requests': 10, 'window': 60},  # 10 uploads per minute
        'contact': {'requests': 20, 'window': 60},  # 20 contact requests per minute
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip rate limiting for authenticated admin users
        if request.user.is_authenticated and request.user.is_staff:
            return self.get_response(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Determine rate limit based on endpoint
        endpoint_type = self._get_endpoint_type(request)
        rate_limit = self.RATE_LIMITS.get(endpoint_type, self.RATE_LIMITS['default'])
        
        # Check rate limit
        if self._is_rate_limited(client_id, endpoint_type, rate_limit):
            return JsonResponse({
                'error': 'rate_limit_exceeded',
                'message': f'عدد الطلبات تجاوز الحد المسموح. يرجى المحاولة بعد {rate_limit["window"]} ثانية.',
                'retry_after': rate_limit['window']
            }, status=429)
        
        response = self.get_response(request)
        
        # Update rate limit counter
        self._update_rate_limit(client_id, endpoint_type, rate_limit)
        
        return response
    
    def _get_client_id(self, request):
        """Get unique client identifier"""
        if request.user.is_authenticated:
            return f"user_{request.user.id}"
        return f"anon_{request.META.get('REMOTE_ADDR', 'unknown')}"
    
    def _get_endpoint_type(self, request):
        """Determine endpoint type for rate limiting"""
        path = request.path
        
        if '/api/chatbot/' in path:
            return 'ai_chat'
        elif '/api/voice' in path:
            return 'voice'
        elif '/search' in path or '/api/properties' in path:
            return 'search'
        elif '/upload' in path:
            return 'upload'
        elif '/contact' in path:
            return 'contact'
        
        return 'default'
    
    def _is_rate_limited(self, client_id, endpoint_type, rate_limit):
        """Check if client has exceeded rate limit"""
        cache_key = f"rate_limit_{endpoint_type}_{client_id}"
        
        current_count = cache.get(cache_key, 0)
        return current_count >= rate_limit['requests']
    
    def _update_rate_limit(self, client_id, endpoint_type, rate_limit):
        """Update rate limit counter with sliding window"""
        cache_key = f"rate_limit_{endpoint_type}_{client_id}"
        
        # Use cache increment with expiration
        current_count = cache.get(cache_key, 0)
        cache.set(cache_key, current_count + 1, timeout=rate_limit['window'])


class AICostControlMiddleware:
    """
    AI usage tracking and cost control
    Monitors token usage, voice minutes, and model requests
    """
    
    COST_LIMITS = {
        'default': {
            'tokens_per_day': 100000,
            'voice_minutes_per_day': 30,
            'requests_per_day': 500
        },
        'user': {
            'tokens_per_day': 50000,
            'voice_minutes_per_day': 15,
            'requests_per_day': 200
        },
        'premium': {
            'tokens_per_day': 500000,
            'voice_minutes_per_day': 120,
            'requests_per_day': 2000
        }
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip cost control for admin users
        if request.user.is_authenticated and request.user.is_staff:
            return self.get_response(request)
        
        # Get user tier
        user_tier = self._get_user_tier(request)
        limits = self.COST_LIMITS.get(user_tier, self.COST_LIMITS['default'])
        
        # Check AI-specific endpoints
        if self._is_ai_endpoint(request):
            if self._is_ai_usage_exceeded(request.user, limits):
                return JsonResponse({
                    'error': 'ai_usage_exceeded',
                    'message': 'تجاوزت الحد اليومي لاستخدام الذكاء الاصطناعي. يرجى المحاولة غداً.',
                    'limit': limits
                }, status=429)
        
        response = self.get_response(request)
        
        # Track AI usage
        if self._is_ai_endpoint(request):
            self._track_ai_usage(request.user, request.path)
        
        return response
    
    def _get_user_tier(self, request):
        """Determine user tier based on subscription or role"""
        if not request.user.is_authenticated:
            return 'default'
        
        # Check for premium features (customize based on your subscription system)
        if hasattr(request.user, 'subscription') and request.user.subscription.tier == 'premium':
            return 'premium'
        
        return 'user'
    
    def _is_ai_endpoint(self, request):
        """Check if request is to an AI endpoint"""
        ai_endpoints = ['/api/chatbot/', '/api/ai/', '/api/voice/']
        return any(endpoint in request.path for endpoint in ai_endpoints)
    
    def _is_ai_usage_exceeded(self, user, limits):
        """Check if user has exceeded AI usage limits"""
        if not user.is_authenticated:
            user_id = 'anonymous'
        else:
            user_id = user.id
        
        # Check token usage
        cache_key = f"ai_tokens_{user_id}"
        token_usage = cache.get(cache_key, 0)
        
        if token_usage >= limits['tokens_per_day']:
            return True
        
        # Check request count
        request_key = f"ai_requests_{user_id}"
        request_count = cache.get(request_key, 0)
        
        if request_count >= limits['requests_per_day']:
            return True
        
        return False
    
    def _track_ai_usage(self, user, endpoint):
        """Track AI usage for cost monitoring"""
        if not user.is_authenticated:
            user_id = 'anonymous'
        else:
            user_id = user.id
        
        # Increment request counter
        request_key = f"ai_requests_{user_id}"
        cache.incr(request_key)
        cache.expire(request_key, 86400)  # 24 hours
        
        # Estimate token usage (rough estimate)
        estimated_tokens = 100  # Default estimate
        token_key = f"ai_tokens_{user_id}"
        cache.incr(token_key, estimated_tokens)
        cache.expire(token_key, 86400)  # 24 hours


class SecurityHeadersMiddleware:
    """
    Enhanced security headers for production
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Remove sensitive headers in production
        if not settings.DEBUG:
            response.pop('Server', None)
            response.pop('X-Powered-By', None)
        
        return response


class RequestLoggingMiddleware:
    """
    Structured request logging for monitoring and debugging
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Generate request ID
        request_id = self._generate_request_id()
        request.request_id = request_id
        
        # Log request start
        logger.info(f"Request started: {request_id} - {request.method} {request.path}")
        
        response = self.get_response(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log request completion
        logger.info(
            f"Request completed: {request_id} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration_ms:.2f}ms - "
            f"User: {request.user.id if request.user.is_authenticated else 'anonymous'}"
        )
        
        # Add timing header
        response['X-Request-ID'] = request_id
        response['X-Response-Time'] = f"{duration_ms:.2f}ms"
        
        return response
    
    def _generate_request_id(self):
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())[:8]


class ErrorTrackingMiddleware:
    """
    Centralized error tracking with structured logging
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as e:
            # Log structured error
            error_id = self._generate_error_id()
            
            logger.error(
                f"Error occurred: {error_id} - "
                f"Path: {request.path} - "
                f"Method: {request.method} - "
                f"User: {request.user.id if request.user.is_authenticated else 'anonymous'} - "
                f"Error: {str(e)}",
                exc_info=True,
                extra={
                    'error_id': error_id,
                    'request_path': request.path,
                    'request_method': request.method,
                    'user_id': request.user.id if request.user.is_authenticated else None
                }
            )
            
            # Return user-friendly error response
            if settings.DEBUG:
                # Detailed error in development
                return JsonResponse({
                    'error': 'internal_server_error',
                    'error_id': error_id,
                    'message': str(e),
                    'debug': True
                }, status=500)
            else:
                # Generic error in production
                return JsonResponse({
                    'error': 'internal_server_error',
                    'error_id': error_id,
                    'message': 'حدث خطأ في الخادم. يرجى المحاولة مرة أخرى.'
                }, status=500)
    
    def _generate_error_id(self):
        """Generate unique error ID"""
        import uuid
        return str(uuid.uuid4())[:8]