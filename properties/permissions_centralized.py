"""
Centralized Permissions Module for IDOR Protection and Object-Level Authorization
"""

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required as django_login_required
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


def login_required(view_func):
    """
    Enhanced login_required decorator with activity logging
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            logger.warning(f'Unauthorized access attempt to {view_func.__name__}')
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def permission_required(perm, login_url=None):
    """
    Enhanced permission_required decorator with logging
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_perm(perm):
                logger.warning(f'Permission denied for user {request.user.username} on {view_func.__name__}: requires {perm}')
                raise PermissionDenied(f'ليس لديك الصلاحية اللازمة: {perm}')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def object_permission_required(model_class, lookup_field='pk', permission_field='user'):
    """
    Decorator for object-level authorization (IDOR protection)
    
    Args:
        model_class: The Django model class
        lookup_field: The field to look up the object (default: 'pk')
        permission_field: The field that should contain the user (default: 'user')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            lookup_value = kwargs.get(lookup_field)
            if not lookup_value:
                logger.error(f'Missing lookup value {lookup_field} in {view_func.__name__}')
                return HttpResponseForbidden('المعرف غير موجود')
            
            try:
                obj = model_class.objects.get(**{lookup_field: lookup_value})
            except model_class.DoesNotExist:
                logger.warning(f'Object not found for {lookup_field}={lookup_value} in {view_func.__name__}')
                return HttpResponseForbidden('الكائن غير موجود')
            
            # Check if user has permission
            user = getattr(obj, permission_field, None)
            
            # Allow superusers to access everything
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check if user is the owner
            if user == request.user:
                return view_func(request, object=obj, *args, **kwargs)
            
            # Check if object has can_view/can_edit methods
            if hasattr(obj, 'can_view') and callable(obj.can_view):
                if obj.can_view(request.user):
                    return view_func(request, object=obj, *args, **kwargs)
            
            # Check if object has can_edit method
            if hasattr(obj, 'can_edit') and callable(obj.can_edit):
                if obj.can_edit(request.user):
                    return view_func(request, object=obj, *args, **kwargs)
            
            # Additional checks for staff users
            if request.user.is_staff and hasattr(obj, 'created_by'):
                if obj.created_by == request.user:
                    return view_func(request, object=obj, *args, **kwargs)
            
            logger.warning(f'Authorization denied for user {request.user.username} on {model_class.__name__} {lookup_value}')
            return HttpResponseForbidden('ليس لديك صلاحية للوصول إلى هذا الكائن')
            
        return _wrapped_view
    return decorator


def property_owner_required(view_func):
    """Decorator for property owner authorization"""
    from .models import Property
    return object_permission_required(Property, permission_field='owner')(view_func)


def property_broker_required(view_func):
    """Decorator for property broker authorization"""
    from .models import Property
    return object_permission_required(Property, permission_field='broker')(view_func)


def auction_owner_required(view_func):
    """Decorator for auction owner authorization"""
    from .models import Auction
    return object_permission_required(Auction, permission_field='created_by')(view_func)


def broker_owner_required(view_func):
    """Decorator for broker profile authorization"""
    from .models import Broker
    return object_permission_required(Broker, permission_field='user')(view_func)


def conversation_participant_required(view_func):
    """Decorator for conversation participant authorization"""
    from .models import Conversation
    return object_permission_required(Conversation, permission_field='user')(view_func)


def message_sender_required(view_func):
    """Decorator for message sender authorization"""
    from .models import Message
    return object_permission_required(Message, permission_field='sender')(view_func)


def offer_participant_required(view_func):
    """Decorator for offer participant authorization"""
    from .models import Offer
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, offer_id, *args, **kwargs):
        try:
            offer = Offer.objects.get(id=offer_id)
        except Offer.DoesNotExist:
            return HttpResponseForbidden('العرض غير موجود')
        
        # Allow offer participants: buyer, seller, and broker
        if (offer.buyer == request.user or 
            offer.property.owner == request.user or
            (offer.property.broker and offer.property.broker.user == request.user) or
            request.user.is_superuser):
            return view_func(request, offer=offer, *args, **kwargs)
        
        logger.warning(f'Authorization denied for user {request.username} on offer {offer_id}')
        return HttpResponseForbidden('ليس لديك صلاحية للوصول إلى هذا العرض')
    return decorator


def auction_participant_required(view_func):
    """Decorator for auction participant authorization"""
    from .models import Auction, AuctionParticipant
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, auction_id, *args, **kwargs):
        try:
            auction = Auction.objects.get(id=auction_id)
        except Auction.DoesNotExist:
            return HttpResponseForbidden('المزاد غير موجود')
        
        # Allow auction creator and participants
        if (auction.created_by == request.user or
            AuctionParticipant.objects.filter(auction=auction, user=request.user).exists() or
            request.user.is_superuser):
            return view_func(request, auction=auction, *args, **kwargs)
        
        logger.warning(f'Authorization denied for user {request.username} on auction {auction_id}')
        return HttpResponseForbidden('ليس لديك صلاحية للوصول إلى هذا المزاد')
    return decorator


def booking_owner_required(view_func):
    """Decorator for booking owner authorization"""
    from .models import Booking
    return object_permission_required(Booking, permission_field='user')(view_func)


def contract_owner_required(view_func):
    """Decorator for contract owner authorization"""
    from .models import RealEstateContract
    return object_permission_required(RealEstateContract, permission_field='created_by')(view_func)


def require_post(view_func):
    """Decorator to require POST method"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.method != 'POST':
            return HttpResponseForbidden('يجب استخدام طلب POST')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def require_ajax(view_func):
    """Decorator to require AJAX request"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponseForbidden('يجب استخدام طلب AJAX')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def csrf_protected(view_func):
    """Decorator to ensure CSRF protection"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Django's CSRF middleware already handles this
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def rate_limit(max_requests=10, period=60):
    """
    Rate limiting decorator using cache
    max_requests: Maximum number of requests
    period: Time period in seconds
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            from django.core.cache import cache
            from django.utils import timezone
            import time
            
            client_ip = get_client_ip(request)
            cache_key = f'rate_limit_{client_ip}_{view_func.__name__}'
            
            # Get current request count
            request_count = cache.get(cache_key, 0)
            
            if request_count >= max_requests:
                logger.warning(f'Rate limit exceeded for {client_ip} on {view_func.__name__}')
                return HttpResponseForbidden('تجاوزت الحد المسموح. يرجى المحاولة لاحقاً')
            
            # Increment request count
            cache.set(cache_key, request_count + 1, period)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def get_client_ip(request):
    """Get client IP address considering proxies"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_activity(action, model_type=None, description=''):
    """
    Decorator to log user activity
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            result = view_func(request, *args, **kwargs)
            
            # Log activity
            from .models import ActivityLog
            ActivityLog.log(
                user=request.user,
                action=action,
                model_type=model_type,
                object_id=kwargs.get('pk') or kwargs.get('id'),
                object_repr=str(kwargs.get('pk') or kwargs.get('id', '')),
                description=description,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            
            return result
        return _wrapped_view
    return decorator