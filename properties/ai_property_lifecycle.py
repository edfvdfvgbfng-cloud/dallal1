"""
Property Lifecycle Manager
Manages property statuses and lifecycle transitions
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime

from .ai_market_intelligence import PropertyStatus

logger = logging.getLogger(__name__)


class LifecycleTransition(Enum):
    """Allowed lifecycle transitions"""
    DRAFT_TO_PENDING = "draft_to_pending"
    PENDING_TO_PUBLISHED = "pending_to_published"
    PUBLISHED_TO_ACTIVE = "published_to_active"
    ACTIVE_TO_RESERVED = "active_to_reserved"
    RESERVED_TO_SOLD = "reserved_to_sold"
    ACTIVE_TO_SOLD = "active_to_sold"
    ACTIVE_TO_RENTED = "active_to_rented"
    ACTIVE_TO_EXPIRED = "active_to_expired"
    ACTIVE_TO_HIDDEN = "active_to_hidden"
    PENDING_TO_REJECTED = "pending_to_rejected"
    SOLD_TO_HIDDEN = "sold_to_hidden"


@dataclass
class LifecycleEvent:
    """Represents a lifecycle transition event"""
    event_id: str = None
    property_id: int = None
    from_status: PropertyStatus = None
    to_status: PropertyStatus = None
    transition: LifecycleTransition = None
    timestamp: str = None
    user_id: int = None
    reason: str = None
    
    def __post_init__(self):
        if self.event_id is None:
            import uuid
            self.event_id = str(uuid.uuid4())[:8]
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'event_id': self.event_id,
            'property_id': self.property_id,
            'from_status': self.from_status.value,
            'to_status': self.to_status.value,
            'transition': self.transition.value,
            'timestamp': self.timestamp,
            'user_id': self.user_id,
            'reason': self.reason
        }


class PropertyLifecycleManager:
    """
    Manages property lifecycle transitions
    Ensures only valid transitions are allowed
    """
    
    def __init__(self):
        self.allowed_transitions = self._initialize_allowed_transitions()
        self.property_statuses: Dict[int, PropertyStatus] = {}
        self.lifecycle_history: Dict[int, List[LifecycleEvent]] = {}
    
    def _initialize_allowed_transitions(self) -> Dict[PropertyStatus, List[PropertyStatus]]:
        """Initialize allowed status transitions"""
        return {
            PropertyStatus.DRAFT: [PropertyStatus.PENDING_REVIEW, PropertyStatus.HIDDEN],
            PropertyStatus.PENDING_REVIEW: [PropertyStatus.PUBLISHED, PropertyStatus.REJECTED, PropertyStatus.HIDDEN],
            PropertyStatus.PUBLISHED: [PropertyStatus.ACTIVE, PropertyStatus.HIDDEN],
            PropertyStatus.ACTIVE: [PropertyStatus.RESERVED, PropertyStatus.SOLD, PropertyStatus.RENTED, PropertyStatus.EXPIRED, PropertyStatus.HIDDEN],
            PropertyStatus.RESERVED: [PropertyStatus.ACTIVE, PropertyStatus.SOLD, PropertyStatus.HIDDEN],
            PropertyStatus.SOLD: [PropertyStatus.HIDDEN],
            PropertyStatus.RENTED: [PropertyStatus.HIDDEN],
            PropertyStatus.EXPIRED: [PropertyStatus.ACTIVE, PropertyStatus.HIDDEN],
            PropertyStatus.HIDDEN: [PropertyStatus.ACTIVE, PropertyStatus.PENDING_REVIEW],
            PropertyStatus.REJECTED: [PropertyStatus.DRAFT, PropertyStatus.PENDING_REVIEW]
        }
    
    def set_property_status(self,
                           property_id: int,
                           new_status: PropertyStatus,
                           user_id: int = None,
                           reason: str = None) -> bool:
        """
        Set property status with validation
        
        Args:
            property_id: Property ID
            new_status: New status to set
            user_id: User making the change
            reason: Reason for change
            
        Returns:
            True if transition successful, False otherwise
        """
        try:
            current_status = self.property_statuses.get(property_id, PropertyStatus.DRAFT)
            
            # Validate transition
            if not self._is_transition_allowed(current_status, new_status):
                logger.warning(f"Invalid transition from {current_status.value} to {new_status.value} for property {property_id}")
                return False
            
            # Determine transition type
            transition = self._get_transition_type(current_status, new_status)
            
            # Create lifecycle event
            event = LifecycleEvent(
                property_id=property_id,
                from_status=current_status,
                to_status=new_status,
                transition=transition,
                user_id=user_id,
                reason=reason
            )
            
            # Update status
            self.property_statuses[property_id] = new_status
            
            # Record event
            if property_id not in self.lifecycle_history:
                self.lifecycle_history[property_id] = []
            self.lifecycle_history[property_id].append(event)
            
            logger.info(f"Property {property_id} status changed from {current_status.value} to {new_status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting property status: {str(e)}")
            return False
    
    def _is_transition_allowed(self, from_status: PropertyStatus, to_status: PropertyStatus) -> bool:
        """Check if transition is allowed"""
        allowed_next = self.allowed_transitions.get(from_status, [])
        return to_status in allowed_next
    
    def _get_transition_type(self, from_status: PropertyStatus, to_status: PropertyStatus) -> LifecycleTransition:
        """Get transition type from status change"""
        transition_map = {
            (PropertyStatus.DRAFT, PropertyStatus.PENDING_REVIEW): LifecycleTransition.DRAFT_TO_PENDING,
            (PropertyStatus.PENDING_REVIEW, PropertyStatus.PUBLISHED): LifecycleTransition.PENDING_TO_PUBLISHED,
            (PropertyStatus.PUBLISHED, PropertyStatus.ACTIVE): LifecycleTransition.PUBLISHED_TO_ACTIVE,
            (PropertyStatus.ACTIVE, PropertyStatus.RESERVED): LifecycleTransition.ACTIVE_TO_RESERVED,
            (PropertyStatus.RESERVED, PropertyStatus.SOLD): LifecycleTransition.RESERVED_TO_SOLD,
            (PropertyStatus.ACTIVE, PropertyStatus.SOLD): LifecycleTransition.ACTIVE_TO_SOLD,
            (PropertyStatus.ACTIVE, PropertyStatus.RENTED): LifecycleTransition.ACTIVE_TO_RENTED,
            (PropertyStatus.ACTIVE, PropertyStatus.EXPIRED): LifecycleTransition.ACTIVE_TO_EXPIRED,
            (PropertyStatus.ACTIVE, PropertyStatus.HIDDEN): LifecycleTransition.ACTIVE_TO_HIDDEN,
            (PropertyStatus.PENDING_REVIEW, PropertyStatus.REJECTED): LifecycleTransition.PENDING_TO_REJECTED,
            (PropertyStatus.SOLD, PropertyStatus.HIDDEN): LifecycleTransition.SOLD_TO_HIDDEN
        }
        
        return transition_map.get((from_status, to_status))
    
    def get_property_status(self, property_id: int) -> Optional[PropertyStatus]:
        """Get current status of property"""
        return self.property_statuses.get(property_id)
    
    def get_property_history(self, property_id: int) -> List[LifecycleEvent]:
        """Get lifecycle history for property"""
        return self.lifecycle_history.get(property_id, [])
    
    def get_available_properties(self, property_ids: List[int] = None) -> List[int]:
        """
        Get list of available (active) property IDs
        
        Args:
            property_ids: List of property IDs to filter (optional)
            
        Returns:
            List of available property IDs
        """
        available = []
        
        for prop_id, status in self.property_statuses.items():
            if status == PropertyStatus.ACTIVE:
                if property_ids is None or prop_id in property_ids:
                    available.append(prop_id)
        
        return available
    
    def filter_by_status(self, property_ids: List[int], allowed_statuses: List[PropertyStatus]) -> List[int]:
        """
        Filter property IDs by status
        
        Args:
            property_ids: List of property IDs
            allowed_statuses: Allowed statuses
            
        Returns:
            Filtered list of property IDs
        """
        filtered = []
        
        for prop_id in property_ids:
            status = self.property_statuses.get(prop_id)
            if status in allowed_statuses:
                filtered.append(prop_id)
        
        return filtered
    
    def get_status_statistics(self) -> Dict:
        """Get statistics of property statuses"""
        status_counts = {}
        
        for status in self.property_statuses.values():
            status_counts[status.value] = status_counts.get(status.value, 0) + 1
        
        return {
            'total_properties': len(self.property_statuses),
            'status_counts': status_counts,
            'active_count': status_counts.get(PropertyStatus.ACTIVE.value, 0),
            'sold_count': status_counts.get(PropertyStatus.SOLD.value, 0),
            'rented_count': status_counts.get(PropertyStatus.RENTED.value, 0)
        }


# Global instance
property_lifecycle_manager = PropertyLifecycleManager()