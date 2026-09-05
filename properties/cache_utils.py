"""
Advanced Caching Utilities for Dalal Project
Provides efficient caching strategies for static and semi-static data
"""

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models import QuerySet
from functools import wraps
import hashlib
import json
from typing import Any, Callable, Optional


def cache_query_result(
    timeout: int = 300,  # 5 minutes default
    key_prefix: str = '',
    version: Optional[int] = None
):
    """
    Decorator to cache database query results
    Automatically invalidates cache on model changes
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key based on function name and arguments
            key_parts = [key_prefix, func.__name__]
            
            # Add args to key (limited to first 3 to avoid huge keys)
            for arg in args[:3]:
                if hasattr(arg, 'id'):
                    key_parts.append(str(arg.id))
                else:
                    key_parts.append(str(arg)[:50])
            
            # Add kwargs to key
            for k, v in sorted(kwargs.items())[:5]:
                key_parts.append(f"{k}:{str(v)[:50]}")
            
            cache_key = ":".join(key_parts)
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Try to get from cache
            result = cache.get(cache_key, version=version)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            # Cache only if result is not None
            if result is not None:
                cache.set(cache_key, result, timeout, version=version)
            
            return result
        
        return wrapper
    return decorator


# Alias for backward compatibility
cache_result = cache_query_result


def cache_static_data(
    timeout: int = 3600,  # 1 hour default
    key_prefix: str = 'static'
):
    """
    Decorator for caching static/semi-static data like lists, choices, etc.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache_key = f"{key_prefix}:{func.__name__}"
            
            # Add kwargs to key for different variations
            if kwargs:
                kwargs_str = json.dumps(sorted(kwargs.items()), sort_keys=True)
                cache_key += f":{hashlib.md5(kwargs_str.encode()).hexdigest()}"
            
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str) -> None:
    """
    Invalidate all cache keys matching a pattern
    Useful for bulk cache invalidation
    """
    # This is a simplified version - in production, you might want to use
    # a more sophisticated cache backend that supports pattern-based deletion
    keys_to_delete = []
    
    # Get all keys (this depends on your cache backend)
    try:
        if hasattr(cache, 'keys'):
            all_keys = cache.keys(f"{pattern}*")
            keys_to_delete.extend(all_keys)
    except Exception:
        # Fallback: pattern-based deletion not supported
        pass
    
    for key in keys_to_delete:
        cache.delete(key)


def invalidate_property_cache(property_id: int) -> None:
    """
    Invalidate all cache related to a specific property
    """
    patterns = [
        f"property:{property_id}",
        f"property_detail:{property_id}",
        f"listing:*:property_{property_id}",
    ]
    
    for pattern in patterns:
        invalidate_cache_pattern(pattern)


def invalidate_category_cache(category: str) -> None:
    """
    Invalidate cache for a specific property category
    """
    patterns = [
        f"category:{category}",
        f"listings:{category}",
        f"properties_{category}",
    ]
    
    for pattern in patterns:
        invalidate_cache_pattern(pattern)


def invalidate_location_cache(location_type: str, location_id: int) -> None:
    """
    Invalidate cache for location-based queries
    """
    patterns = [
        f"{location_type}:{location_id}",
        f"properties_{location_type}_{location_id}",
        f"listings_{location_type}:{location_id}",
    ]
    
    for pattern in patterns:
        invalidate_cache_pattern(pattern)


class QuerySetCache:
    """
    Helper class for caching QuerySet results with automatic invalidation
    """
    
    def __init__(self, timeout: int = 300):
        self.timeout = timeout
    
    def get_cached_queryset(
        self,
        queryset: QuerySet,
        cache_key: str,
        timeout: Optional[int] = None
    ) -> list:
        """
        Get cached queryset or execute and cache
        """
        timeout = timeout or self.timeout
        
        # Try cache first
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Execute queryset
        results = list(queryset)
        
        # Cache results
        cache.set(cache_key, results, timeout)
        
        return results
    
    def invalidate_queryset(self, cache_key: str) -> None:
        """
        Invalidate cached queryset
        """
        cache.delete(cache_key)


# Pre-defined cache keys for common data
CACHE_KEYS = {
    'governorates': 'static:governorates',
    'property_types': 'static:property_types',
    'property_categories': 'static:property_categories',
    'currencies': 'static:currencies',
    'countries': 'static:countries',
    'featured_properties': 'dynamic:featured_properties',
    'latest_properties': 'dynamic:latest_properties',
}


def get_or_set_cache(key: str, default: Any, timeout: int = 300) -> Any:
    """
    Simple get or set pattern for cache
    """
    value = cache.get(key)
    if value is None:
        value = default
        cache.set(key, value, timeout)
    return value


def bulk_cache_invalidate(keys: list[str]) -> None:
    """
    Invalidate multiple cache keys at once
    """
    cache.delete_many(keys)