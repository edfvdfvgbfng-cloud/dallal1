"""
Smart Notifications System
Sends intelligent notifications based on saved searches and property updates
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications"""
    NEW_PROPERTY_MATCH = "new_property_match"
    PRICE_CHANGE = "price_change"
    SIMILAR_PROPERTY = "similar_property"
    MARKET_UPDATE = "market_update"
    AGENT_RECOMMENDATION = "agent_recommendation"


class NotificationPriority(Enum):
    """Priority levels for notifications"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Notification:
    """Represents a notification"""
    notification_id: str
    user_id: int
    notification_type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    data: Dict = field(default_factory=dict)
    read: bool = False
    created_at: str = None
    expires_at: str = None
    sent_at: str = None
    
    def __post_init__(self):
        if not self.notification_id:
            self.notification_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'notification_id': self.notification_id,
            'user_id': self.user_id,
            'notification_type': self.notification_type.value,
            'priority': self.priority.value,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'read': self.read,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'sent_at': self.sent_at
        }


@dataclass
class SavedSearch:
    """Represents a saved search for notifications"""
    search_id: str
    user_id: int
    filters: Dict[str, Any]
    match_threshold: float = 0.7
    enabled: bool = True
    created_at: str = None
    last_matched_at: str = None
    
    def __post_init__(self):
        if not self.search_id:
            import uuid
            self.search_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'search_id': self.search_id,
            'user_id': self.user_id,
            'filters': self.filters,
            'match_threshold': self.match_threshold,
            'enabled': self.enabled,
            'created_at': self.created_at,
            'last_matched_at': self.last_matched_at
        }


class SmartNotificationsSystem:
    """
    Smart notifications system based on saved searches and user preferences
    Only sends notifications if user has enabled them
    """
    
    def __init__(self):
        self.saved_searches: Dict[str, SavedSearch] = {}
        self.notifications: Dict[str, Notification] = {}
        self.notification_preferences: Dict[int, Dict] = {}
        self.notification_history: List[Dict] = []
    
    def create_saved_search(self,
                            user_id: int,
                            filters: Dict,
                            match_threshold: float = 0.7) -> SavedSearch:
        """Create a saved search for notifications"""
        search = SavedSearch(
            user_id=user_id,
            filters=filters,
            match_threshold=match_threshold
        )
        
        self.saved_searches[search.search_id] = search
        logger.info(f"Created saved search {search.search_id} for user {user_id}")
        return search
    
    def check_property_match(self,
                            property_data: Dict,
                            saved_search: SavedSearch) -> Optional[float]:
        """
        Check if property matches saved search criteria
        
        Args:
            property_data: Property data
            saved_search: Saved search to match against
            
        Returns:
            Match score if match, None otherwise
        """
        try:
            score = 0.0
            filters = saved_search.filters
            
            # Check each filter
            if filters.get('governorate'):
                if property_data.get('governorate') == filters['governorate']:
                    score += 0.3
                else:
                    return None  # Filter mismatch
            
            if filters.get('property_type'):
                if property_data.get('property_type') == filters['property_type']:
                    score += 0.2
                else:
                    return None
            
            if filters.get('price_max'):
                if property_data.get('price', float('inf')) <= filters['price_max']:
                    score += 0.3
                else:
                    return None
            
            if filters.get('price_min'):
                if property_data.get('price', 0) >= filters['price_min']:
                    score += 0.2
            
            # Check threshold
            if score >= saved_search.match_threshold:
                return score
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking property match: {str(e)}")
            return None
    
    def create_notification(self,
                         user_id: int,
                         notification_type: NotificationType,
                         title: str,
                         message: str,
                         data: Dict = None,
                         priority: NotificationPriority = NotificationPriority.MEDIUM) -> Notification:
        """Create a notification"""
        # Check if user has notifications enabled
        user_prefs = self.notification_preferences.get(user_id, {})
        if not user_prefs.get('enabled', False):
            logger.info(f"Notifications disabled for user {user_id}")
            return None
        
        # Check specific notification type preference
        type_pref = user_prefs.get('notification_types', {})
        if not type_pref.get(notification_type.value, True):
            logger.info(f"Notification type {notification_type.value} disabled for user {user_id}")
            return None
        
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            data=data or {}
        )
        
        self.notifications[notification.notification_id] = notification
        
        logger.info(f"Created notification {notification.notification_id} for user {user_id}")
        return notification
    
    def check_and_notify_new_properties(self,
                                       new_properties: List[Dict]):
        """Check new properties against saved searches and send notifications"""
        for search_id, saved_search in self.saved_searches.items():
            if not saved_search.enabled:
                continue
            
            for property_data in new_properties:
                match_score = self.check_property_match(property_data, saved_search)
                
                if match_score:
                    # Create notification
                    notification = self.create_notification(
                        user_id=saved_search.user_id,
                        notification_type=NotificationType.NEW_PROPERTY_MATCH,
                        title="عقار جديد مطابق لبحثك",
                        message=f"ظهر عقار جديد في {property_data.get('governorate')} يطابق معايير البحث المحفوظة.",
                        data={
                            'property_id': property_data.get('id'),
                            'match_score': match_score,
                            'search_id': search_id
                        },
                        priority=NotificationPriority.HIGH
                    )
                    
                    if notification:
                        saved_search.last_matched_at = datetime.now().isoformat()
    
    def notify_price_change(self,
                          user_id: int,
                          property_id: int,
                          old_price: float,
                          new_price: float):
        """Notify user about price change for saved property"""
        # Check if user has price change notifications enabled
        user_prefs = self.notification_preferences.get(user_id, {})
        if not user_prefs.get('price_change_alerts', False):
            return
        
        notification = self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.PRICE_CHANGE,
            title="تغيير في سعر عقار محفوظ",
            message=f"تغير سعر العقار من {old_price:,.0f} إلى {new_price:,.0f} دينار.",
            data={
                'property_id': property_id,
                'old_price': old_price,
                'new_price': new_price
            },
            priority=NotificationPriority.MEDIUM
        )
    
    def set_user_notification_preferences(self,
                                       user_id: int,
                                       enabled: bool = True,
                                       notification_types: Dict = None,
                                       price_change_alerts: bool = True):
        """Set user notification preferences"""
        self.notification_preferences[user_id] = {
            'enabled': enabled,
            'notification_types': notification_types or {},
            'price_change_alerts': price_change_alerts
        }
        
        logger.info(f"Updated notification preferences for user {user_id}")
    
    def get_user_notifications(self, user_id: int, unread_only: bool = True) -> List[Notification]:
        """Get notifications for a user"""
        user_notifications = [
            notif for notif in self.notifications.values()
            if notif.user_id == user_id
        ]
        
        if unread_only:
            user_notifications = [n for n in user_notifications if not n.read]
        
        # Sort by created_at descending
        user_notifications.sort(key=lambda x: x.created_at, reverse=True)
        
        return user_notifications
    
    def mark_notification_read(self, notification_id: str):
        """Mark notification as read"""
        if notification_id in self.notifications:
            self.notifications[notification_id].read = True
            logger.info(f"Marked notification {notification_id} as read")
    
    def delete_notification(self, notification_id: str):
        """Delete a notification"""
        if notification_id in self.notifications:
            del self.notifications[notification_id]
            logger.info(f"Deleted notification {notification_id}")
    
    def delete_old_notifications(self, days: int = 30):
        """Delete notifications older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_delete = []
        for notif_id, notif in self.notifications.items():
            notif_date = datetime.fromisoformat(notif.created_at)
            if notif_date < cutoff_date:
                to_delete.append(notif_id)
        
        for notif_id in to_delete:
            del self.notifications[notif_id]
        
        logger.info(f"Deleted {len(to_delete)} old notifications")
    
    def get_notification_statistics(self) -> Dict:
        """Get notification statistics"""
        total = len(self.notifications)
        unread = sum(1 for n in self.notifications.values() if not n.read)
        
        type_counts = {}
        for notif in self.notifications.values():
            notif_type = notif.notification_type.value
            type_counts[notif_type] = type_counts.get(notif_type, 0) + 1
        
        return {
            'total_notifications': total,
            'unread_notifications': unread,
            'type_counts': type_counts,
            'saved_searches_count': len(self.saved_searches),
            'users_with_notifications': len(self.notification_preferences)
        }


# Global instance
smart_notifications_system = SmartNotificationsSystem()