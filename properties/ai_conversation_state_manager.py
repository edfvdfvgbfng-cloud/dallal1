"""
Conversation State Manager
Single source of truth for conversation state
"""

from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    """Represents the state of a conversation"""
    conversation_id: str
    user_id: int
    intent: str = None
    goal: str = None
    entities: Dict = field(default_factory=dict)
    preferences: Dict = field(default_factory=dict)
    active_task: str = None
    active_property_id: int = None
    selected_results: List[int] = field(default_factory=list)
    last_input: str = None
    last_response: str = None
    created_at: str = None
    updated_at: str = None
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.conversation_id:
            self.conversation_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'intent': self.intent,
            'goal': self.goal,
            'entities': self.entities,
            'preferences': self.preferences,
            'active_task': self.active_task,
            'active_property_id': self.active_property_id,
            'selected_results': self.selected_results,
            'last_input': self.last_input,
            'last_response': self.last_response,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata
        }


class ConversationStateManager:
    """
    Single source of truth for conversation state
    Manages intent, goal, entities, preferences, and context
    """
    
    def __init__(self):
        self.states: Dict[str, ConversationState] = {}
        self.user_conversations: Dict[int, List[str]] = {}
    
    def get_or_create_state(self, conversation_id: str, user_id: int) -> ConversationState:
        """
        Get or create conversation state
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            
        Returns:
            Conversation state
        """
        if conversation_id in self.states:
            return self.states[conversation_id]
        
        # Create new state
        state = ConversationState(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        self.states[conversation_id] = state
        
        # Track user conversations
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = []
        self.user_conversations[user_id].append(conversation_id)
        
        logger.info(f"Created conversation state for {conversation_id}")
        return state
    
    def get_state(self, conversation_id: str) -> Optional[ConversationState]:
        """Get conversation state by ID"""
        return self.states.get(conversation_id)
    
    def update_state(self, conversation_id: str, updates: Dict):
        """
        Update conversation state
        
        Args:
            conversation_id: Conversation ID
            updates: Fields to update
        """
        if conversation_id not in self.states:
            return
        
        state = self.states[conversation_id]
        
        for key, value in updates.items():
            if hasattr(state, key):
                setattr(state, key, value)
        
        state.updated_at = datetime.now().isoformat()
        logger.info(f"Updated conversation state for {conversation_id}")
    
    def clear_state(self, conversation_id: str):
        """Clear conversation state"""
        if conversation_id in self.states:
            user_id = self.states[conversation_id].user_id
            
            # Remove from user conversations
            if user_id in self.user_conversations and conversation_id in self.user_conversations[user_id]:
                self.user_conversations[user_id].remove(conversation_id)
            
            del self.states[conversation_id]
            logger.info(f"Cleared conversation state for {conversation_id}")
    
    def get_user_conversations(self, user_id: int) -> List[ConversationState]:
        """Get all conversation states for a user"""
        if user_id not in self.user_conversations:
            return []
        
        conversation_ids = self.user_conversations[user_id]
        return [self.states[cid] for cid in conversation_ids if cid in self.states]
    
    def cleanup_old_states(self, days: int = 7):
        """Clean up states older than specified days"""
        cutoff_date = datetime.now() - datetime.timedelta(days=days)
        
        to_delete = []
        for conversation_id, state in self.states.items():
            updated_date = datetime.fromisoformat(state.updated_at)
            if updated_date < cutoff_date:
                to_delete.append(conversation_id)
        
        for conversation_id in to_delete:
            self.clear_state(conversation_id)
        
        logger.info(f"Cleaned up {len(to_delete)} old conversation states")
    
    def get_state_statistics(self) -> Dict:
        """Get state manager statistics"""
        intent_counts = {}
        for state in self.states.values():
            if state.intent:
                intent_counts[state.intent] = intent_counts.get(state.intent, 0) + 1
        
        return {
            'total_states': len(self.states),
            'total_users': len(self.user_conversations),
            'intent_distribution': intent_counts
        }


# Global instance
conversation_state_manager = ConversationStateManager()