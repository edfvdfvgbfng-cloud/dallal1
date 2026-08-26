"""
User Preference Center
Manages user preferences for AI features, notifications, and personalization
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class FeatureType(Enum):
    """Types of AI features"""
    AI_ASSISTANT = "ai_assistant"
    VOICE = "voice"
    MEMORY = "memory"
    PERSONALIZATION = "personalization"
    PROPERTY_ALERTS = "property_alerts"
    JOB_ALERTS = "job_alerts"
    PRICE_ALERTS = "price_alerts"
    MARKETING = "marketing"
    NOTIFICATIONS = "notifications"
    DATA_USAGE = "data_usage"


class CommunicationStyle(Enum):
    """User communication style preferences"""
    FORMAL_ARABIC = "formal_arabic"
    IRAQI_ARABIC = "iraqi_arabic"
    MIXED = "mixed"
    CONCISE = "concise"
    DETAILED = "detailed"


@dataclass
class UserPreference:
    """Represents a user preference"""
    user_id: int = None
    feature_type: FeatureType = None
    enabled: bool = True
    metadata: Dict = field(default_factory=dict)
    updated_at: str = None
    
    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'feature_type': self.feature_type.value,
            'enabled': self.enabled,
            'metadata': self.metadata,
            'updated_at': self.updated_at
        }


@dataclass
class UserCommunicationPreferences:
    """User communication style preferences"""
    user_id: int = None
    style: CommunicationStyle = None
    language: str = "ar"
    timezone: str = "Asia/Baghdad"
    quiet_hours: str = None  # Format: "22:00-08:00"
    notification_schedule: Dict = field(default_factory=dict)
    updated_at: str = None
    
    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'style': self.style.value,
            'language': self.language,
            'timezone': self.timezone,
            'quiet_hours': self.quiet_hours,
            'notification_schedule': self.notification_schedule,
            'updated_at': self.updated_at
        }


class UserPreferenceCenter:
    """
    Manages user preferences for AI features
    Provides control over AI behavior and personalization
    """
    
    def __init__(self):
        self.user_preferences: Dict[int, Dict[FeatureType, UserPreference]] = {}
        self.communication_preferences: Dict[int, UserCommunicationPreferences] = {}
        self.memory_controls: Dict[int, Dict] = {}
    
    def set_feature_preference(self,
                               user_id: int,
                               feature_type: FeatureType,
                               enabled: bool,
                               metadata: Dict = None) -> UserPreference:
        """
        Set preference for a specific feature
        
        Args:
            user_id: User ID
            feature_type: Feature type
            enabled: Whether feature is enabled
            metadata: Additional metadata
            
        Returns:
            Created preference
        """
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        
        preference = UserPreference(
            user_id=user_id,
            feature_type=feature_type,
            enabled=enabled,
            metadata=metadata or {}
        )
        
        self.user_preferences[user_id][feature_type] = preference
        logger.info(f"Set preference for user {user_id}: {feature_type.value} = {enabled}")
        return preference
    
    def get_feature_preference(self, user_id: int, feature_type: FeatureType) -> Optional[UserPreference]:
        """Get preference for a specific feature"""
        if user_id in self.user_preferences:
            return self.user_preferences[user_id].get(feature_type)
        return None
    
    def is_feature_enabled(self, user_id: int, feature_type: FeatureType) -> bool:
        """Check if a feature is enabled for a user"""
        preference = self.get_feature_preference(user_id, feature_type)
        if preference:
            return preference.enabled
        # Default to enabled for most features
        return True
    
    def get_all_preferences(self, user_id: int) -> Dict[FeatureType, UserPreference]:
        """Get all preferences for a user"""
        return self.user_preferences.get(user_id, {})
    
    def delete_feature_preference(self, user_id: int, feature_type: FeatureType):
        """Delete a specific preference"""
        if user_id in self.user_preferences and feature_type in self.user_preferences[user_id]:
            del self.user_preferences[user_id][feature_type]
            logger.info(f"Deleted preference for user {user_id}: {feature_type.value}")
    
    def delete_all_preferences(self, user_id: int):
        """Delete all preferences for a user"""
        if user_id in self.user_preferences:
            del self.user_preferences[user_id]
            logger.info(f"Deleted all preferences for user {user_id}")
    
    def set_communication_preferences(self,
                                      user_id: int,
                                      style: CommunicationStyle,
                                      language: str = "ar",
                                      timezone: str = "Asia/Baghdad",
                                      quiet_hours: str = None,
                                      notification_schedule: Dict = None) -> UserCommunicationPreferences:
        """
        Set communication preferences for a user
        
        Args:
            user_id: User ID
            style: Communication style
            language: Preferred language
            timezone: User timezone
            quiet_hours: Quiet hours for notifications
            notification_schedule: Notification schedule
            
        Returns:
            Created communication preferences
        """
        prefs = UserCommunicationPreferences(
            user_id=user_id,
            style=style,
            language=language,
            timezone=timezone,
            quiet_hours=quiet_hours,
            notification_schedule=notification_schedule or {}
        )
        
        self.communication_preferences[user_id] = prefs
        logger.info(f"Set communication preferences for user {user_id}")
        return prefs
    
    def get_communication_preferences(self, user_id: int) -> Optional[UserCommunicationPreferences]:
        """Get communication preferences for a user"""
        return self.communication_preferences.get(user_id)
    
    def set_memory_controls(self,
                          user_id: int,
                          allow_long_term_memory: bool = True,
                          allow_session_memory: bool = True,
                          allow_preference_learning: bool = True,
                          data_retention_days: int = 90):
        """
        Set memory controls for a user
        
        Args:
            user_id: User ID
            allow_long_term_memory: Allow long-term memory storage
            allow_session_memory: Allow session memory
            allow_preference_learning: Allow learning preferences
            data_retention_days: Days to retain data
        """
        controls = {
            'allow_long_term_memory': allow_long_term_memory,
            'allow_session_memory': allow_session_memory,
            'allow_preference_learning': allow_preference_learning,
            'data_retention_days': data_retention_days,
            'updated_at': datetime.now().isoformat()
        }
        
        self.memory_controls[user_id] = controls
        logger.info(f"Set memory controls for user {user_id}")
    
    def get_memory_controls(self, user_id: int) -> Dict:
        """Get memory controls for a user"""
        if user_id not in self.memory_controls:
            # Default controls
            return {
                'allow_long_term_memory': True,
                'allow_session_memory': True,
                'allow_preference_learning': True,
                'data_retention_days': 90
            }
        return self.memory_controls[user_id]
    
    def clear_memory(self, user_id: int, memory_type: str = "all"):
        """
        Clear user memory
        
        Args:
            user_id: User ID
            memory_type: Type of memory to clear ('all', 'long_term', 'session', 'preferences')
        """
        controls = self.get_memory_controls(user_id)
        
        if memory_type == "all":
            controls['allow_long_term_memory'] = False
            controls['allow_session_memory'] = False
            controls['allow_preference_learning'] = False
        elif memory_type == "long_term":
            controls['allow_long_term_memory'] = False
        elif memory_type == "session":
            controls['allow_session_memory'] = False
        elif memory_type == "preferences":
            controls['allow_preference_learning'] = False
        
        self.memory_controls[user_id] = controls
        logger.info(f"Cleared {memory_type} memory for user {user_id}")
    
    def get_user_summary(self, user_id: int) -> Dict:
        """
        Get summary of user preferences and settings
        
        Args:
            user_id: User ID
            
        Returns:
            User preference summary
        """
        feature_prefs = self.get_all_preferences(user_id)
        comm_prefs = self.get_communication_preferences(user_id)
        memory_controls = self.get_memory_controls(user_id)
        
        enabled_features = [ft.value for ft, pref in feature_prefs.items() if pref.enabled]
        disabled_features = [ft.value for ft, pref in feature_prefs.items() if not pref.enabled]
        
        return {
            'user_id': user_id,
            'enabled_features': enabled_features,
            'disabled_features': disabled_features,
            'communication_style': comm_prefs.style.value if comm_prefs else None,
            'language': comm_prefs.language if comm_prefs else None,
            'memory_controls': memory_controls,
            'total_features': len(feature_prefs)
        }
    
    def apply_forget_request(self, user_id: int, forget_type: str = "all"):
        """
        Apply user forget request
        
        Args:
            user_id: User ID
            forget_type: Type of forget ('all', 'conversation', 'preferences', 'memory')
        """
        if forget_type in ["all", "memory"]:
            self.clear_memory(user_id, "all")
        
        if forget_type in ["all", "preferences"]:
            self.delete_all_preferences(user_id)
        
        logger.info(f"Applied forget request for user {user_id}: {forget_type}")


# Global instance
user_preference_center = UserPreferenceCenter()