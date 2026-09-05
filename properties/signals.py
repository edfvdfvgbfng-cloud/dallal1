"""
Cache Invalidation Signals
Automatically invalidate cache when models are modified
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Property, PropertyImage, HotelPage
from .cache_utils import (
    invalidate_property_cache,
    invalidate_category_cache,
    invalidate_location_cache,
    CACHE_KEYS
)


@receiver(post_save, sender=Property)
@receiver(post_delete, sender=Property)
def invalidate_property_related_cache(sender, instance, **kwargs):
    """
    Invalidate cache when a property is saved or deleted
    """
    # Invalidate specific property cache
    if instance.id:
        invalidate_property_cache(instance.id)
    
    # Invalidate category cache
    if instance.category:
        invalidate_category_cache(instance.category)
    
    # Invalidate location caches
    if instance.governorate:
        invalidate_location_cache('governorate', instance.governorate)
    if instance.city:
        invalidate_location_cache('city', instance.city)
    
    # Invalidate general property caches
    cache.delete_many([
        CACHE_KEYS['featured_properties'],
        CACHE_KEYS['latest_properties'],
        'dynamic:properties_count',
        'dynamic:published_properties',
    ])


@receiver(post_save, sender=PropertyImage)
@receiver(post_delete, sender=PropertyImage)
def invalidate_property_image_cache(sender, instance, **kwargs):
    """
    Invalidate cache when property images are modified
    """
    if instance.property_id:
        invalidate_property_cache(instance.property_id)
        
        # Invalidate property detail cache
        cache.delete(f"property_detail:{instance.property_id}")
        cache.delete(f"property_images:{instance.property_id}")


@receiver(post_save, sender=HotelPage)
@receiver(post_delete, sender=HotelPage)
def invalidate_hotel_cache(sender, instance, **kwargs):
    """
    Invalidate cache when hotels are modified
    """
    # Invalidate specific hotel cache
    cache.delete(f"hotel:{instance.id}")
    cache.delete(f"hotel_detail:{instance.id}")
    
    # Invalidate location caches
    if instance.governorate:
        invalidate_location_cache('governorate', instance.governorate)
    if instance.city:
        invalidate_location_cache('city', instance.city)
    
    # Invalidate general hotel caches
    cache.delete_many([
        'dynamic:featured_hotels',
        'dynamic:latest_hotels',
        'dynamic:hotels_count',
    ])


def invalidate_user_cache(user_id: int):
    """
    Invalidate user-specific cache
    """
    cache.delete_many([
        f"user:{user_id}:favorites",
        f"user:{user_id}:saves",
        f"user:{user_id}:properties",
        f"user:{user_id}:notifications",
    ])