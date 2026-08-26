"""
Feature Flags System for Production-Grade Rollouts
Allows gradual feature rollout without full system deployment
"""

from django.core.cache import cache
from django.conf import settings
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class FeatureFlags:
    """
    Feature flags management system
    Allows enabling/disabling features dynamically
    """
    
    # Default feature flags
    DEFAULT_FLAGS = {
        'voice_ai': True,  # Voice AI functionality
        'property_ai': True,  # Property intelligence features
        'recommendations': True,  # AI recommendations
        'rag': True,  # RAG knowledge base
        'saved_search': True,  # Saved search functionality
        'auto_notifications': False,  # Automatic notifications
        'new_model': False,  # New AI model (for testing)
        'semantic_search': True,  # Semantic search capabilities
        'vector_search': True,  # Vector database search
        'buyer_profile': True,  # Buyer profile system
        'property_comparison': True,  # Property comparison
        'ai_listing_assistant': True,  # AI listing assistant
        'image_analysis': False,  # Property image analysis
        'price_analysis': True,  # Price comparison and analysis
        'data_quality_scoring': True,  # Property data quality scoring
        'personalized_ranking': True,  # Personalized result ranking
        'streaming_responses': False,  # Streaming AI responses
        'advanced_voice_commands': True,  # Advanced voice commands
        'offline_mode': False,  # Offline functionality
    }
    
    @classmethod
    def is_enabled(cls, feature_name: str, user=None) -> bool:
        """
        Check if a feature is enabled for the given user
        
        Args:
            feature_name: Name of the feature flag
            user: User object (optional, for user-specific flags)
            
        Returns:
            True if feature is enabled, False otherwise
        """
        try:
            # Check cache first
            cache_key = f"feature_flag_{feature_name}"
            cached_value = cache.get(cache_key)
            
            if cached_value is not None:
                return cached_value
            
            # Check environment variable override
            env_key = f"FEATURE_{feature_name.upper()}"
            env_value = getattr(settings, env_key, None)
            
            if env_value is not None:
                return env_value.lower() in ('true', '1', 'yes', 'on')
            
            # Check user-specific flags if user provided
            if user and cls._has_user_specific_flag(user, feature_name):
                return cls._get_user_specific_flag(user, feature_name)
            
            # Use default value
            return cls.DEFAULT_FLAGS.get(feature_name, False)
            
        except Exception as e:
            logger.error(f"Error checking feature flag {feature_name}: {str(e)}")
            return False
    
    @classmethod
    def enable_feature(cls, feature_name: str, ttl=None):
        """
        Enable a feature flag dynamically
        
        Args:
            feature_name: Name of the feature to enable
            ttl: Time to live in seconds (optional)
        """
        try:
            cache_key = f"feature_flag_{feature_name}"
            cache.set(cache_key, True, timeout=ttl)
            logger.info(f"Feature flag enabled: {feature_name}")
        except Exception as e:
            logger.error(f"Error enabling feature flag {feature_name}: {str(e)}")
    
    @classmethod
    def disable_feature(cls, feature_name: str, ttl=None):
        """
        Disable a feature flag dynamically
        
        Args:
            feature_name: Name of the feature to disable
            ttl: Time to live in seconds (optional)
        """
        try:
            cache_key = f"feature_flag_{feature_name}"
            cache.set(cache_key, False, timeout=ttl)
            logger.info(f"Feature flag disabled: {feature_name}")
        except Exception as e:
            logger.error(f"Error disabling feature flag {feature_name}: {str(e)}")
    
    @classmethod
    def set_user_specific_flag(cls, user, feature_name: str, enabled: bool):
        """
        Set a feature flag for a specific user
        
        Args:
            user: User object
            feature_name: Name of the feature
            enabled: Whether to enable the feature
        """
        try:
            cache_key = f"user_feature_{user.id}_{feature_name}"
            cache.set(cache_key, enabled, timeout=86400)  # 24 hours
            logger.info(f"User-specific flag set: user={user.id}, feature={feature_name}, enabled={enabled}")
        except Exception as e:
            logger.error(f"Error setting user-specific flag: {str(e)}")
    
    @classmethod
    def _has_user_specific_flag(cls, user, feature_name: str) -> bool:
        """Check if user has a specific flag override"""
        cache_key = f"user_feature_{user.id}_{feature_name}"
        return cache.get(cache_key) is not None
    
    @classmethod
    def _get_user_specific_flag(cls, user, feature_name: str) -> bool:
        """Get user-specific flag value"""
        cache_key = f"user_feature_{user.id}_{feature_name}"
        return cache.get(cache_key, False)
    
    @classmethod
    def get_all_flags(cls, user=None) -> Dict[str, bool]:
        """
        Get all feature flags and their current status
        
        Args:
            user: User object (optional, for user-specific flags)
            
        Returns:
            Dictionary of feature names and their enabled status
        """
        flags = {}
        
        for feature_name in cls.DEFAULT_FLAGS:
            flags[feature_name] = cls.is_enabled(feature_name, user)
        
        return flags
    
    @classmethod
    def get_user_flags(cls, user) -> Dict[str, bool]:
        """
        Get all feature flags for a specific user
        
        Args:
            user: User object
            
        Returns:
            Dictionary of feature names and their enabled status for this user
        """
        return cls.get_all_flags(user)


# Global instance
feature_flags = FeatureFlags()