"""
Proactive Notification System
Event-driven notifications with smart timing and relevance scoring
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class NotificationEventType(Enum):
    """Types of notification events"""
    NEW_PROPERTY = "new_property"
    PRICE_CHANGE = "price_change"
    PROPERTY_SOLD = "property_sold"
    NEW_JOB = "new_job"
    APPLICATION_UPDATE = "application_update"
    AGENT_REPLY = "agent_reply"
    SAVED_SEARCH_MATCH = "saved_search_match"
    AUCTION_STARTING = "auction_starting"


class NotificationUrgency(Enum):
    """Urgency levels for notifications"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ProactiveNotification:
    """Represents a proactive notification"""
    notification_id: str = None
    user_id: int = None
    event_type: NotificationEventType = None
    title: str = None
    message: str = None
    relevance_score: float = 0.0
    urgency: NotificationUrgency = None
    data: Dict = field(default_factory=dict)
    requires_action: bool = False
    created_at: str = None
    expires_at: str = None
    sent_at: str = None
    digest_group: str = None
    
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
            'event_type': self.event_type.value,
            'title': self.title,
            'message': self.message,
            'relevance_score': self.relevance_score,
            'urgency': self.urgency.value,
            'data': self.data,
            'requires_action': self.requires_action,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'sent_at': self.sent_at,
            'digest_group': self.digest_group
        }


class ProactiveNotificationSystem:
    """
    System for proactive, event-driven notifications
    Uses relevance scoring and smart timing
    """
    
    def __init__(self):
        self.notifications: Dict[str, ProactiveNotification] = {}
        self.user_preferences: Dict[int, Dict] = {}
        self.notification_history: List[Dict] = []
        self.digest_windows: Dict[str, datetime] = {}
        self.digest_window_minutes = 15  # Group notifications within 15 minutes
    
    def create_notification(self,
                           user_id: int,
                           event_type: NotificationEventType,
                           title: str,
                           message: str,
                           relevance_score: float,
                           urgency: NotificationUrgency = NotificationUrgency.MEDIUM,
                           data: Dict = None,
                           requires_action: bool = False) -> ProactiveNotification:
        """
        Create a proactive notification
        
        Args:
            user_id: User ID
            event_type: Type of event
            title: Notification title
            message: Notification message
            relevance_score: How relevant (0-1)
            urgency: Urgency level
            data: Additional data
            requires_action: Whether user needs to take action
            
        Returns:
            Created notification
        """
        notification = ProactiveNotification(
            user_id=user_id,
            event_type=event_type,
            title=title,
            message=message,
            relevance_score=relevance_score,
            urgency=urgency,
            data=data or {},
            requires_action=requires_action
        )
        
        self.notifications[notification.notification_id] = notification
        logger.info(f"Created proactive notification {notification.notification_id} for user {user_id}")
        return notification
    
    def should_send_notification(self, notification: ProactiveNotification) -> bool:
        """
        Determine if notification should be sent based on user preferences and timing
        
        Args:
            notification: Notification to check
            
        Returns:
            True if should send, False otherwise
        """
        # Get user preferences
        user_prefs = self.user_preferences.get(notification.user_id, {})
        
        # Check if notifications are enabled
        if not user_prefs.get('notifications_enabled', True):
            return False
        
        # Check specific event type preference
        event_prefs = user_prefs.get('event_preferences', {})
        if event_type_key := f"{notification.event_type.value}_enabled":
            if event_type_key in event_prefs and not event_prefs[event_type_key]:
                return False
        
        # Check relevance threshold
        relevance_threshold = user_prefs.get('relevance_threshold', 0.5)
        if notification.relevance_score < relevance_threshold:
            return False
        
        # Check quiet hours
        if self._is_quiet_hours(notification.user_id):
            return False
        
        # Check urgency - only send high urgency outside quiet hours
        if self._is_quiet_hours(notification.user_id):
            if notification.urgency not in [NotificationUrgency.CRITICAL, NotificationUrgency.HIGH]:
                return False
        
        return True
    
    def process_event(self,
                     event_type: NotificationEventType,
                     user_id: int,
                     event_data: Dict,
                     context: Dict = None) -> Optional[ProactiveNotification]:
        """
        Process an event and create notification if needed
        
        Args:
            event_type: Type of event
            user_id: User ID
            event_data: Event data
            context: Additional context
            
        Returns:
            Created notification if warranted, None otherwise
        """
        try:
            # Calculate relevance
            relevance = self._calculate_relevance(event_type, user_id, event_data, context)
            
            if relevance < 0.5:
                return None
            
            # Determine urgency
            urgency = self._determine_urgency(event_type, event_data)
            
            # Create notification
            notification = self.create_notification(
                user_id=user_id,
                event_type=event_type,
                title=self._generate_title(event_type, event_data),
                message=self._generate_message(event_type, event_data),
                relevance_score=relevance,
                urgency=urgency,
                data=event_data,
                requires_action=urgency in [NotificationUrgency.CRITICAL, NotificationUrgency.HIGH]
            )
            
            # Check if should send
            if self.should_send_notification(notification):
                return notification
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing event: {str(e)}")
            return None
    
    def _calculate_relevance(self,
                             event_type: NotificationEventType,
                             user_id: int,
                             event_data: Dict,
                             context: Dict = None) -> float:
        """Calculate relevance score for event"""
        # Placeholder - would use saved searches, preferences, etc.
        relevance = 0.5
        
        # Boost relevance if matches saved search
        if event_type == NotificationEventType.SAVED_SEARCH_MATCH:
            relevance += 0.3
        
        # Boost relevance if price change is significant
        if event_type == NotificationEventType.PRICE_CHANGE:
            price_change_percent = event_data.get('price_change_percent', 0)
            if price_change_percent > 0.1:  # More than 10% change
                relevance += 0.2
        
        return min(relevance, 1.0)
    
    def _determine_urgency(self, event_type: NotificationEventType, event_data: Dict) -> NotificationUrgency:
        """Determine urgency level"""
        # Map event types to urgency
        urgency_map = {
            NotificationEventType.AGENT_REPLY: NotificationUrgency.HIGH,
            NotificationEventType.AUCTION_STARTING: NotificationUrgency.HIGH,
            NotificationEventType.APPLICATION_UPDATE: NotificationUrgency.MEDIUM,
            NotificationEventType.PRICE_CHANGE: NotificationUrgency.MEDIUM,
            NotificationEventType.NEW_PROPERTY: NotificationUrgency.LOW,
            NotificationEventType.NEW_JOB: NotificationUrgency.LOW,
            NotificationEventType.SAVED_SEARCH_MATCH: NotificationUrgency.MEDIUM
        }
        
        return urgency_map.get(event_type, NotificationUrgency.MEDIUM)
    
    def _generate_title(self, event_type: NotificationEventType, event_data: Dict) -> str:
        """Generate notification title"""
        title_map = {
            NotificationEventType.NEW_PROPERTY: "عقار جديد",
            NotificationEventType.PRICE_CHANGE: "تغيير في السعر",
            NotificationEventType.SAVED_SEARCH_MATCH: "عقار مطابق لبحثك",
            NotificationEventType.NEW_JOB: "وظيفة جديدة",
            NotificationEventType.APPLICATION_UPDATE: "تحديث على طلبك",
            NotificationEventType.AGENT_REPLY: "رد من الدلال",
            NotificationEventType.AUCTION_STARTING: "مزاد قريب"
        }
        
        return title_map.get(event_type, "إشعار جديد")
    
    def _generate_message(self, event_type: NotificationEventType, event_data: Dict) -> str:
        """Generate notification message"""
        if event_type == NotificationEventType.NEW_PROPERTY:
            return f"ظهر عقار جديد في {event_data.get('location', 'المنطقة')}."
        elif event_type == NotificationEventType.PRICE_CHANGE:
            old_price = event_data.get('old_price', 0)
            new_price = event_data.get('new_price', 0)
            return f"تغير سعر العقار من {old_price:,.0f} إلى {new_price:,.0f} دينار."
        elif event_type == NotificationEventType.SAVED_SEARCH_MATCH:
            return f"وجدت عقار جديد مطابق لبحثك بنسبة {event_data.get('match_score', 0)}%."
        elif event_type == NotificationEventType.AGENT_REPLY:
            return f"الدلال {event_data.get('agent_name', '')} رد على رسالتك."
        
        return "حدث جديد يستحق انتباهك."
    
    def group_notifications_for_digest(self, user_id: int) -> List[List[ProactiveNotification]]:
        """
        Group notifications for digest delivery
        
        Args:
            user_id: User ID
            
        Returns:
            List of notification groups
        """
        user_notifications = [
            n for n in self.notifications.values()
            if n.user_id == user_id and not n.sent_at
        ]
        
        if not user_notifications:
            return []
        
        # Sort by creation time
        user_notifications.sort(key=lambda x: x.created_at)
        
        # Group by time window
        groups = []
        current_group = []
        window_start = None
        
        for notification in user_notifications:
            created_at = datetime.fromisoformat(notification.created_at)
            
            if window_start is None:
                window_start = created_at
                current_group = [notification]
            else:
                time_diff = (created_at - window_start).total_seconds()
                if time_diff <= self.digest_window_minutes * 60:
                    current_group.append(notification)
                else:
                    if current_group:
                        groups.append(current_group)
                    window_start = created_at
                    current_group = [notification]
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def send_digest(self, user_id: int, group: List[ProactiveNotification]) -> str:
        """
        Create digest message for notification group
        
        Args:
            user_id: User ID
            group: Group of notifications
            
        Returns:
            Digest message
        """
        count = len(group)
        
        if count == 1:
            return group[0].message
        
        # Create digest message
        digest = f"عندك {count} إشعارات جديدة:\n"
        
        for i, notification in enumerate(group, 1):
            digest += f"{i}. {notification.title}: {notification.message}\n"
        
        return digest
    
    def _is_quiet_hours(self, user_id: int) -> bool:
        """Check if current time is in user's quiet hours"""
        user_prefs = self.user_preferences.get(user_id, {})
        
        quiet_hours = user_prefs.get('quiet_hours')
        if not quiet_hours:
            return False
        
        # Check current time against quiet hours
        current_time = datetime.now().time()
        
        # Parse quiet hours (format: "22:00-08:00")
        if '-' in quiet_hours:
            start, end = quiet_hours.split('-')
            start_time = datetime.strptime(start, "%H:%M").time()
            end_time = datetime.strptime(end, "%H:%M").time()
            
            if start_time <= end_time:
                # Quiet hours overnight
                if start_time <= current_time <= end_time:
                    return True
            else:
                # Quiet hours across midnight
                if current_time >= start_time or current_time <= end_time:
                    return True
        
        return False
    
    def set_user_preferences(self, user_id: int, preferences: Dict):
        """Set user notification preferences"""
        self.user_preferences[user_id] = preferences
        logger.info(f"Set preferences for user {user_id}")
    
    def get_user_notifications(self, user_id: int, unread_only: bool = True) -> List[ProactiveNotification]:
        """Get notifications for a user"""
        user_notifications = [
            n for n in self.notifications.values()
            if n.user_id == user_id
        ]
        
        if unread_only:
            user_notifications = [n for n in user_notifications if not n.sent_at]
        
        return user_notifications
    
    def mark_as_sent(self, notification_id: str):
        """Mark notification as sent"""
        if notification_id in self.notifications:
            self.notifications[notification_id].sent_at = datetime.now().isoformat()
            logger.info(f"Marked notification {notification_id} as sent")
    
    def get_notification_statistics(self) -> Dict:
        """Get notification statistics"""
        type_counts = {}
        urgency_counts = {}
        
        for notification in self.notifications.values():
            n_type = notification.event_type.value
            n_urgency = notification.urgency.value
            type_counts[n_type] = type_counts.get(n_type, 0) + 1
            urgency_counts[n_urgency] = urgency_counts.get(n_urgency, 0) + 1
        
        return {
            'total_notifications': len(self.notifications),
            'type_distribution': type_counts,
            'urgency_distribution': urgency_counts,
            'users_with_preferences': len(self.user_preferences)
        }


# Global instance
proactive_notification_system = ProactiveNotificationSystem()