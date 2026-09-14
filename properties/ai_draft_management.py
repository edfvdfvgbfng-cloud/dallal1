"""
Draft Management System
Manages incomplete forms and tasks for recovery
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)


class DraftType(Enum):
    """Types of drafts"""
    PROPERTY_LISTING = "property_listing"
    JOB_APPLICATION = "job_application"
    AGENT_APPLICATION = "agent_application"
    SAVED_SEARCH = "saved_search"
    USER_PROFILE = "user_profile"


class DraftStatus(Enum):
    """Draft status"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    ABANDONED = "abandoned"
    SUBMITTED = "submitted"


@dataclass
class Draft:
    """Represents a draft of an incomplete form or task"""
    draft_id: str = None
    user_id: int = None
    draft_type: DraftType = None
    status: DraftStatus = None
    data: Dict = None
    completion_percentage: float = 0.0
    created_at: str = None
    updated_at: str = None
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.draft_id:
            self.draft_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'draft_id': self.draft_id,
            'user_id': self.user_id,
            'draft_type': self.draft_type.value,
            'status': self.status.value,
            'data': self.data,
            'completion_percentage': self.completion_percentage,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata
        }


class DraftManagementSystem:
    """
    Manages incomplete forms and tasks
    Allows recovery of abandoned work
    """
    
    def __init__(self):
        self.drafts: Dict[str, Draft] = {}
        self.user_drafts: Dict[int, List[str]] = {}
    
    def create_draft(self,
                    user_id: int,
                    draft_type: DraftType,
                    data: Dict,
                    completion_percentage: float = 0.0,
                    metadata: Dict = None) -> Draft:
        """
        Create a new draft
        
        Args:
            user_id: User ID
            draft_type: Type of draft
            data: Draft data
            completion_percentage: Completion percentage (0-100)
            metadata: Additional metadata
            
        Returns:
            Created draft
        """
        draft = Draft(
            user_id=user_id,
            draft_type=draft_type,
            status=DraftStatus.DRAFT,
            data=data,
            completion_percentage=completion_percentage,
            metadata=metadata or {}
        )
        
        self.drafts[draft.draft_id] = draft
        
        # Track user drafts
        if user_id not in self.user_drafts:
            self.user_drafts[user_id] = []
        self.user_drafts[user_id].append(draft.draft_id)
        
        logger.info(f"Created draft {draft.draft_id} for user {user_id}")
        return draft
    
    def update_draft(self, draft_id: str, data: Dict = None, completion_percentage: float = None) -> Optional[Draft]:
        """
        Update an existing draft
        
        Args:
            draft_id: Draft ID
            data: Updated data
            completion_percentage: Updated completion percentage
            
        Returns:
            Updated draft
        """
        if draft_id not in self.drafts:
            return None
        
        draft = self.drafts[draft_id]
        
        if data is not None:
            draft.data.update(data)
        
        if completion_percentage is not None:
            draft.completion_percentage = completion_percentage
        
        draft.status = DraftStatus.IN_PROGRESS
        draft.updated_at = datetime.now().isoformat()
        
        logger.info(f"Updated draft {draft_id}")
        return draft
    
    def mark_abandoned(self, draft_id: str):
        """Mark a draft as abandoned"""
        if draft_id in self.drafts:
            self.drafts[draft_id].status = DraftStatus.ABANDONED
            self.drafts[draft_id].updated_at = datetime.now().isoformat()
            logger.info(f"Marked draft {draft_id} as abandoned")
    
    def mark_submitted(self, draft_id: str):
        """Mark a draft as submitted"""
        if draft_id in self.drafts:
            self.drafts[draft_id].status = DraftStatus.SUBMITTED
            self.drafts[draft_id].updated_at = datetime.now().isoformat()
            logger.info(f"Marked draft {draft_id} as submitted")
    
    def delete_draft(self, draft_id: str):
        """Delete a draft"""
        if draft_id in self.drafts:
            user_id = self.drafts[draft_id].user_id
            
            # Remove from user drafts
            if user_id in self.user_drafts and draft_id in self.user_drafts[user_id]:
                self.user_drafts[user_id].remove(draft_id)
            
            del self.drafts[draft_id]
            logger.info(f"Deleted draft {draft_id}")
    
    def get_draft(self, draft_id: str) -> Optional[Draft]:
        """Get draft by ID"""
        return self.drafts.get(draft_id)
    
    def get_user_drafts(self, user_id: int, draft_type: DraftType = None) -> List[Draft]:
        """
        Get all drafts for a user
        
        Args:
            user_id: User ID
            draft_type: Optional filter by draft type
            
        Returns:
            List of drafts
        """
        if user_id not in self.user_drafts:
            return []
        
        draft_ids = self.user_drafts[user_id]
        drafts = [self.drafts[did] for did in draft_ids if did in self.drafts]
        
        if draft_type:
            drafts = [d for d in drafts if d.draft_type == draft_type]
        
        # Sort by updated_at (most recent first)
        drafts.sort(key=lambda x: x.updated_at, reverse=True)
        
        return drafts
    
    def get_abandoned_drafts(self, user_id: int) -> List[Draft]:
        """Get abandoned drafts for a user"""
        drafts = self.get_user_drafts(user_id)
        return [d for d in drafts if d.status == DraftStatus.ABANDONED]
    
    def calculate_completion_score(self, draft_type: DraftType, data: Dict) -> float:
        """
        Calculate completion score for a draft
        
        Args:
            draft_type: Type of draft
            data: Draft data
            
        Returns:
            Completion percentage (0-100)
        """
        required_fields = {
            DraftType.PROPERTY_LISTING: ['title', 'price', 'area', 'governorate', 'district'],
            DraftType.JOB_APPLICATION: ['name', 'email', 'phone', 'cv_id'],
            DraftType.AGENT_APPLICATION: ['name', 'email', 'phone', 'experience'],
            DraftType.SAVED_SEARCH: ['property_type', 'governorate'],
            DraftType.USER_PROFILE: ['name', 'email', 'phone']
        }
        
        fields = required_fields.get(draft_type, [])
        if not fields:
            return 0.0
        
        filled = sum(1 for field in fields if field in data and data[field])
        return (filled / len(fields)) * 100
    
    def get_missing_fields(self, draft_type: DraftType, data: Dict) -> List[str]:
        """
        Get missing required fields for a draft
        
        Args:
            draft_type: Type of draft
            data: Draft data
            
        Returns:
            List of missing field names
        """
        required_fields = {
            DraftType.PROPERTY_LISTING: ['title', 'price', 'area', 'governorate', 'district'],
            DraftType.JOB_APPLICATION: ['name', 'email', 'phone', 'cv_id'],
            DraftType.AGENT_APPLICATION: ['name', 'email', 'phone', 'experience'],
            DraftType.SAVED_SEARCH: ['property_type', 'governorate'],
            DraftType.USER_PROFILE: ['name', 'email', 'phone']
        }
        
        fields = required_fields.get(draft_type, [])
        return [field for field in fields if field not in data or not data[field]]
    
    def cleanup_old_drafts(self, days: int = 30):
        """Clean up drafts older than specified days"""
        cutoff_date = datetime.now() - datetime.timedelta(days=days)
        
        to_delete = []
        for draft_id, draft in self.drafts.items():
            if draft.status in [DraftStatus.SUBMITTED, DraftStatus.ABANDONED]:
                updated_date = datetime.fromisoformat(draft.updated_at)
                if updated_date < cutoff_date:
                    to_delete.append(draft_id)
        
        for draft_id in to_delete:
            self.delete_draft(draft_id)
        
        logger.info(f"Cleaned up {len(to_delete)} old drafts")
    
    def get_draft_statistics(self) -> Dict:
        """Get draft statistics"""
        type_counts = {}
        status_counts = {}
        
        for draft in self.drafts.values():
            d_type = draft.draft_type.value
            d_status = draft.status.value
            type_counts[d_type] = type_counts.get(d_type, 0) + 1
            status_counts[d_status] = status_counts.get(d_status, 0) + 1
        
        return {
            'total_drafts': len(self.drafts),
            'type_distribution': type_counts,
            'status_distribution': status_counts,
            'users_with_drafts': len(self.user_drafts)
        }


# Global instance
draft_management_system = DraftManagementSystem()