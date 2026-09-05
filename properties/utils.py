import logging
from django.db.models import Q
from django.utils import timezone

from .models import Property, PropertyImage, PropertyVideo, Notification
from .cache_utils import cache_query_result

logger = logging.getLogger(__name__)


PUBLIC_STATUSES = ['draft', 'paid', 'pending_approval', 'published', 'renewed', 'ready', 'under-construction', 'rent']


@cache_query_result(timeout=300, key_prefix='public_properties')
def get_public_properties():
    """Get public properties, excluding suspended brokers and expired listings."""
    from .models import Broker

    try:
        now = timezone.now()
        inactive_broker_ids = list(
            Broker.objects.filter(Q(is_active=False) | Q(is_suspended=True)).values_list('id', flat=True)
        )
        standalone_only_ids = list(
            Broker.objects.filter(page_display_mode='standalone_only').values_list('id', flat=True)
        )

        qs = (
            Property.objects.filter(status__in=PUBLIC_STATUSES)
            .exclude(is_frozen=True)
            .filter(Q(publication_end_date__isnull=True) | Q(publication_end_date__gt=now))
            .filter(Q(expiry_date__isnull=True) | Q(expiry_date__gt=now))
            .select_related('broker', 'owner')
            .prefetch_related('gallery_images', 'outside_details')
            .order_by('-is_pinned', '-is_featured', '-is_promoted', '-created_at')
        )

        return list(qs)
    except Exception as e:
        logger.error(f"Error in get_public_properties: {e}")
        # Fallback: return empty list if there's a database schema issue
        return []


def expire_featured_and_publications():
    """Clear featured/pinned flags and archive expired publications (server-side)."""
    today = timezone.now().date()
    now = timezone.now()

    Property.objects.filter(is_featured=True, promotion_until__lt=today).update(is_featured=False)
    Property.objects.filter(is_pinned=True, pinned_until__lt=now).update(is_pinned=False)
    Property.objects.filter(
        status__in=PUBLIC_STATUSES,
        publication_end_date__lt=now,
    ).update(status='expired')
    Property.objects.filter(
        status__in=PUBLIC_STATUSES,
        expiry_date__lt=now,
    ).update(status='expired')


def filter_properties(queryset, params):
    """Apply search filters from GET params dict."""
    
    # Handle list input (from get_public_properties)
    if isinstance(queryset, list):
        q = params.get('q', '').strip()
        city = params.get('city', '').strip()
        governorate = params.get('governorate', '').strip()
        district = params.get('district', '').strip()
        region = params.get('region', '').strip()
        ptype = params.get('type')
        status = params.get('status')
        price_min = params.get('price_min')
        price_max = params.get('price_max')
        area_min = params.get('area_min')
        area_max = params.get('area_max')
        bedrooms = params.get('bedrooms')
        owner_name = params.get('owner_name', '').strip()
        
        filtered = queryset
        if q:
            filtered = [p for p in filtered if q.lower() in (p.title or '').lower() or (p.location and q.lower() in p.location.lower()) or (p.city and q.lower() in p.city.lower()) or (p.district and q.lower() in p.district.lower()) or (getattr(p, 'region', None) and q.lower() in (p.region or '').lower()) or (p.description and q.lower() in p.description.lower())]
        if city:
            filtered = [p for p in filtered if p.city and city.lower() in p.city.lower()]
        if governorate:
            filtered = [p for p in filtered if (p.governorate and governorate.lower() in p.governorate.lower()) or (p.district and governorate.lower() in p.district.lower())]
        if district:
            filtered = [p for p in filtered if p.district and district.lower() in p.district.lower()]
        if region:
            filtered = [p for p in filtered if getattr(p, 'region', None) and region.lower() in (p.region or '').lower()]
        if ptype:
            filtered = [p for p in filtered if p.type == ptype]
        if status:
            filtered = [p for p in filtered if p.status == status]
        if price_min:
            try:
                filtered = [p for p in filtered if p.price and p.price >= int(price_min)]
            except (TypeError, ValueError):
                pass
        if price_max:
            try:
                filtered = [p for p in filtered if p.price and p.price <= int(price_max)]
            except (TypeError, ValueError):
                pass
        if area_min:
            try:
                filtered = [p for p in filtered if p.area and p.area >= int(area_min)]
            except (TypeError, ValueError):
                pass
        if area_max:
            try:
                filtered = [p for p in filtered if p.area and p.area <= int(area_max)]
            except (TypeError, ValueError):
                pass
        if bedrooms:
            try:
                filtered = [p for p in filtered if p.bedrooms and p.bedrooms >= int(bedrooms)]
            except (TypeError, ValueError):
                pass
        if owner_name:
            filtered = [p for p in filtered if p.owner and (owner_name.lower() in p.owner.first_name.lower() or owner_name.lower() in p.owner.last_name.lower() or owner_name.lower() in p.owner.username.lower())]
        if params.get('has_parking'):
            filtered = [p for p in filtered if p.parking]
        if params.get('furnished'):
            filtered = [p for p in filtered if p.furnished]
        if params.get('featured') in ('1', 'true', 'on'):
            filtered = [p for p in filtered if p.is_featured]
        
        return filtered
    
    # Original QuerySet logic
    q = params.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q)
            | Q(location__icontains=q)
            | Q(city__icontains=q)
            | Q(district__icontains=q)
            | Q(description__icontains=q)
        )

    city = params.get('city', '').strip()
    if city:
        queryset = queryset.filter(city__icontains=city)

    governorate = params.get('governorate', '').strip()
    if governorate:
        queryset = queryset.filter(
            Q(broker__governorate__icontains=governorate)
        )

    district = params.get('district', '').strip()
    if district:
        queryset = queryset.filter(district__icontains=district)

    ptype = params.get('type')
    if ptype:
        queryset = queryset.filter(type=ptype)

    status = params.get('status')
    if status:
        queryset = queryset.filter(status=status)

    price_min = params.get('price_min')
    if price_min:
        try:
            queryset = queryset.filter(price__gte=int(price_min))
        except (TypeError, ValueError):
            pass

    price_max = params.get('price_max')
    if price_max:
        try:
            queryset = queryset.filter(price__lte=int(price_max))
        except (TypeError, ValueError):
            pass

    area_min = params.get('area_min')
    if area_min:
        try:
            queryset = queryset.filter(area__gte=int(area_min))
        except (TypeError, ValueError):
            pass

    area_max = params.get('area_max')
    if area_max:
        try:
            queryset = queryset.filter(area__lte=int(area_max))
        except (TypeError, ValueError):
            pass

    bedrooms = params.get('bedrooms')
    if bedrooms:
        try:
            queryset = queryset.filter(bedrooms__gte=int(bedrooms))
        except (TypeError, ValueError):
            pass

    # Search by owner name
    owner_name = params.get('owner_name', '').strip()
    if owner_name:
        queryset = queryset.filter(
            Q(owner__first_name__icontains=owner_name)
            | Q(owner__last_name__icontains=owner_name)
            | Q(owner__username__icontains=owner_name)
        )

    if params.get('has_parking'):
        queryset = queryset.filter(parking=True)
    if params.get('furnished'):
        queryset = queryset.filter(furnished=True)
    if params.get('featured') in ('1', 'true', 'on'):
        queryset = queryset.filter(is_featured=True)

    return queryset


def sort_properties(queryset, sort_key):
    mapping = {
        'newest': ['-created_at'],
        'price_asc': ['price'],
        'price_desc': ['-price'],
        'area_asc': ['area'],
        'area_desc': ['-area'],
        'views': ['-views_count'],
    }
    
    # Handle list input (from get_public_properties)
    if isinstance(queryset, list):
        sort_fields = mapping.get(sort_key, ['-is_featured', '-is_promoted', '-created_at'])
        reverse = False
        if sort_fields[0].startswith('-'):
            reverse = True
            sort_field = sort_fields[0][1:]
        else:
            sort_field = sort_fields[0]
        
        return sorted(queryset, key=lambda x: getattr(x, sort_field, 0), reverse=reverse)
    
    return queryset.order_by(*mapping.get(sort_key, ['-is_featured', '-is_promoted', '-created_at']))


def save_gallery_images(property_obj, files, is_360_list=None):
    """Save multiple uploaded images to PropertyImage with security validation."""
    if not files:
        return
    
    from .file_upload_security import validate_property_image
    
    start_order = property_obj.gallery_images.count()
    for i, f in enumerate(files):
        if not f or not getattr(f, 'name', None):
            continue
        ctype = getattr(f, 'content_type', '') or ''
        if ctype and not ctype.startswith('image/'):
            continue
        
        # Security validation
        try:
            validation_result = validate_property_image(f)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Image validation failed: {str(e)}")
            continue
        
        # Check if this is a 360° image
        is_360 = False
        if is_360_list and i < len(is_360_list):
            is_360 = is_360_list[i]
        
        PropertyImage.objects.create(
            property=property_obj,
            image=f,
            sort_order=start_order + i,
            is_primary=(start_order == 0 and i == 0 and not property_obj.image),
            is_360=is_360,
        )


def save_gallery_videos(property_obj, files):
    """Save multiple uploaded videos to PropertyVideo with security validation."""
    if not files:
        return
    
    from .file_upload_security import validate_video_upload
    
    start_order = property_obj.gallery_videos.count()
    for i, f in enumerate(files):
        if not f or not getattr(f, 'name', None):
            continue
        ctype = getattr(f, 'content_type', '') or ''
        if ctype and not ctype.startswith('video/'):
            continue
        
        # Security validation
        try:
            validation_result = validate_video_upload(f)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Video validation failed: {str(e)}")
            continue
        
        PropertyVideo.objects.create(
            property=property_obj,
            video=f,
            sort_order=start_order + i,
        )


def create_notification(user, notification_type, title, message, link='', metadata=None):
    """Create a notification for a user."""
    if metadata is None:
        metadata = {}
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
        metadata=metadata,
    )


# ==================== Advertising System Utilities ====================

def match_advertisement_with_targets(advertisement):
    """
    مطابقة إعلان البناء مع الأهداف المحتملة (عقارات، دلالين، مستخدمين)
    Match building advertisement with potential targets (properties, brokers, users)
    """
    from .advertising_utils import match_advertisement_with_targets as match_targets
    return match_targets(advertisement)
