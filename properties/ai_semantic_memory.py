"""
Semantic Memory System
Stores and retrieves meaningful information from conversations beyond raw messages
"""

from typing import Dict, List, Any, Optional, Set
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory with different retention policies"""
    EPHEMERAL = "ephemeral"  # Short-term, session-based
    SESSION = "session"  # Current session only
    LONG_TERM = "long_term"  # Persistent across sessions
    PREFERENCE = "preference"  # User preferences
    FACTUAL = "factual"  # Facts about the world
    PROCEDURAL = "procedural"  # How to do things


class MemoryImportance(Enum):
    """Importance levels for memory items"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class MemoryItem:
    """Individual memory item with metadata"""
    memory_id: str
    memory_type: MemoryType
    content: Dict[str, Any]
    importance: MemoryImportance
    created_at: str
    last_accessed: str
    access_count: int = 0
    expiration: str = None
    source: str = "conversation"
    confidence: float = 1.0
    tags: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        if not self.memory_id:
            import uuid
            self.memory_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_accessed:
            self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Check if memory item has expired"""
        if not self.expiration:
            return False
        
        try:
            expiration_time = datetime.fromisoformat(self.expiration)
            return datetime.now() > expiration_time
        except:
            return False
    
    def update_access(self):
        """Update access metadata"""
        self.last_accessed = datetime.now().isoformat()
        self.access_count += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'memory_id': self.memory_id,
            'memory_type': self.memory_type.value,
            'content': self.content,
            'importance': self.importance.value,
            'created_at': self.created_at,
            'last_accessed': self.last_accessed,
            'access_count': self.access_count,
            'expiration': self.expiration,
            'source': self.source,
            'confidence': self.confidence,
            'tags': list(self.tags)
        }


class SemanticMemory:
    """
    Advanced semantic memory system that stores meaningful information
    from conversations with intelligent retrieval and expiration
    """
    
    def __init__(self):
        self.memory_store: Dict[str, MemoryItem] = {}
        self.user_memories: Dict[int, Set[str]] = defaultdict(set)
        self.memory_index: Dict[str, Set[str]] = defaultdict(set)
        self.retention_policies = self._initialize_retention_policies()
    
    def store_memory(self, 
                   content: Dict[str, Any],
                   memory_type: MemoryType,
                   importance: MemoryImportance = MemoryImportance.MEDIUM,
                   user_id: int = None,
                   tags: List[str] = None,
                   source: str = "conversation") -> MemoryItem:
        """
        Store a memory item
        
        Args:
            content: Memory content
            memory_type: Type of memory
            importance: Importance level
            user_id: User ID (optional)
            tags: Tags for indexing
            source: Source of memory
            
        Returns:
            Created MemoryItem
        """
        try:
            # Calculate expiration based on memory type
            expiration = self._calculate_expiration(memory_type, importance)
            
            # Create memory item
            memory_item = MemoryItem(
                memory_type=memory_type,
                content=content,
                importance=importance,
                expiration=expiration,
                source=source,
                tags=set(tags or [])
            )
            
            # Store memory
            self.memory_store[memory_item.memory_id] = memory_item
            
            # Index by user
            if user_id:
                self.user_memories[user_id].add(memory_item.memory_id)
            
            # Index by tags
            for tag in memory_item.tags:
                self.memory_index[tag].add(memory_item.memory_id)
            
            # Index by content fields
            for key, value in content.items():
                index_key = f"{key}:{value}"
                self.memory_index[index_key].add(memory_item.memory_id)
            
            logger.info(f"Stored memory {memory_item.memory_id} of type {memory_type.value}")
            return memory_item
            
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return None
    
    def retrieve_memory(self, 
                      query: Dict[str, Any],
                      user_id: int = None,
                      memory_types: List[MemoryType] = None,
                      limit: int = 10) -> List[MemoryItem]:
        """
        Retrieve memory items based on query
        
        Args:
            query: Query parameters
            user_id: User ID (optional)
            memory_types: Filter by memory types
            limit: Maximum number of results
            
        Returns:
            List of matching MemoryItems
        """
        try:
            candidate_ids = set()
            
            # Search by content fields
            for key, value in query.items():
                index_key = f"{key}:{value}"
                if index_key in self.memory_index:
                    candidate_ids.update(self.memory_index[index_key])
            
            # Filter by user
            if user_id:
                user_memory_ids = self.user_memories.get(user_id, set())
                candidate_ids = candidate_ids.intersection(user_memory_ids)
            
            # Filter by memory type
            if memory_types:
                memory_type_ids = set()
                for memory_id in candidate_ids:
                    memory_item = self.memory_store.get(memory_id)
                    if memory_item and memory_item.memory_type in memory_types:
                        memory_type_ids.add(memory_id)
                candidate_ids = memory_type_ids
            
            # Get memory items
            results = []
            for memory_id in candidate_ids:
                memory_item = self.memory_store.get(memory_id)
                if memory_item and not memory_item.is_expired():
                    memory_item.update_access()
                    results.append(memory_item)
            
            # Sort by importance and access count
            results.sort(key=lambda x: (
                self._importance_score(x.importance),
                x.access_count
            ), reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving memory: {str(e)}")
            return []
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get all preferences for a user"""
        preference_memories = self.retrieve_memory(
            query={},
            user_id=user_id,
            memory_types=[MemoryType.PREFERENCE],
            limit=50
        )
        
        preferences = {}
        for memory in preference_memories:
            preferences.update(memory.content)
        
        return preferences
    
    def update_user_preference(self, 
                              user_id: int,
                              preference_key: str,
                              preference_value: Any):
        """Update or create a user preference"""
        # Check if preference already exists
        existing_memories = self.retrieve_memory(
            query={preference_key: preference_value},
            user_id=user_id,
            memory_types=[MemoryType.PREFERENCE]
        )
        
        if existing_memories:
            # Update existing
            for memory in existing_memories:
                memory.content[preference_key] = preference_value
                memory.update_access()
        else:
            # Create new preference memory
            self.store_memory(
                content={preference_key: preference_value},
                memory_type=MemoryType.PREFERENCE,
                importance=MemoryImportance.HIGH,
                user_id=user_id,
                tags=['preference', preference_key]
            )
    
    def get_session_context(self, user_id: int) -> Dict[str, Any]:
        """Get current session context for a user"""
        session_memories = self.retrieve_memory(
            query={},
            user_id=user_id,
            memory_types=[MemoryType.SESSION, MemoryType.EPHEMERAL],
            limit=20
        )
        
        context = {}
        for memory in session_memories:
            context.update(memory.content)
        
        return context
    
    def clear_expired_memories(self):
        """Remove all expired memory items"""
        expired_ids = []
        
        for memory_id, memory_item in self.memory_store.items():
            if memory_item.is_expired():
                expired_ids.append(memory_id)
        
        for memory_id in expired_ids:
            self._remove_memory(memory_id)
        
        logger.info(f"Cleared {len(expired_ids)} expired memories")
    
    def clear_user_memories(self, user_id: int, memory_types: List[MemoryType] = None):
        """Clear memories for a specific user"""
        user_memory_ids = self.user_memories.get(user_id, set()).copy()
        
        for memory_id in user_memory_ids:
            memory_item = self.memory_store.get(memory_id)
            if memory_item:
                if memory_types is None or memory_item.memory_type in memory_types:
                    self._remove_memory(memory_id)
        
        # Clear user memory set
        if memory_types is None:
            self.user_memories[user_id].clear()
        else:
            self.user_memories[user_id] = {
                mid for mid in self.user_memories[user_id]
                if self.memory_store.get(mid).memory_type not in memory_types
            }
        
        logger.info(f"Cleared memories for user {user_id}")
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get statistics about memory store"""
        memory_counts = defaultdict(int)
        importance_counts = defaultdict(int)
        expired_count = 0
        
        for memory_item in self.memory_store.values():
            memory_counts[memory_item.memory_type.value] += 1
            importance_counts[memory_item.importance.value] += 1
            if memory_item.is_expired():
                expired_count += 1
        
        return {
            'total_memories': len(self.memory_store),
            'memory_counts': dict(memory_counts),
            'importance_counts': dict(importance_counts),
            'expired_count': expired_count,
            'user_count': len(self.user_memories),
            'unique_tags': len(self.memory_index)
        }
    
    def consolidate_memories(self, user_id: int):
        """Consolidate similar memories for a user"""
        # Get all user memories
        user_memory_ids = self.user_memories.get(user_id, set())
        
        # Group by content similarity
        content_groups = defaultdict(list)
        for memory_id in user_memory_ids:
            memory_item = self.memory_store.get(memory_id)
            if memory_item:
                # Create a simple key for grouping
                content_key = frozenset(memory_item.content.items())
                content_groups[content_key].append(memory_item)
        
        # Consolidate groups with multiple memories
        for content_key, memories in content_groups.items():
            if len(memories) > 1:
                # Keep the most recent one
                memories.sort(key=lambda x: x.last_accessed, reverse=True)
                keep_memory = memories[0]
                
                # Remove others
                for memory in memories[1:]:
                    self._remove_memory(memory.memory_id)
                
                logger.info(f"Consolidated {len(memories)} memories into {keep_memory.memory_id}")
    
    def _remove_memory(self, memory_id: str):
        """Remove a memory item and clean up indexes"""
        memory_item = self.memory_store.get(memory_id)
        if not memory_item:
            return
        
        # Remove from user index
        for user_id, memory_ids in self.user_memories.items():
            if memory_id in memory_ids:
                memory_ids.remove(memory_id)
        
        # Remove from tag index
        for tag in memory_item.tags:
            if tag in self.memory_index:
                self.memory_index[tag].discard(memory_id)
        
        # Remove from content index
        for key, value in memory_item.content.items():
            index_key = f"{key}:{value}"
            if index_key in self.memory_index:
                self.memory_index[index_key].discard(memory_id)
        
        # Remove from main store
        del self.memory_store[memory_id]
    
    def _calculate_expiration(self, memory_type: MemoryType, importance: MemoryImportance) -> str:
        """Calculate expiration time based on memory type and importance"""
        now = datetime.now()
        
        # Base retention periods
        retention_periods = {
            MemoryType.EPHEMERAL: timedelta(hours=1),
            MemoryType.SESSION: timedelta(days=1),
            MemoryType.LONG_TERM: timedelta(days=90),
            MemoryType.PREFERENCE: timedelta(days=180),
            MemoryType.FACTUAL: timedelta(days=365),
            MemoryType.PROCEDURAL: timedelta(days=365)
        }
        
        # Importance multipliers
        importance_multipliers = {
            MemoryImportance.CRITICAL: 2.0,
            MemoryImportance.HIGH: 1.5,
            MemoryImportance.MEDIUM: 1.0,
            MemoryImportance.LOW: 0.5
        }
        
        base_period = retention_periods.get(memory_type, timedelta(days=1))
        multiplier = importance_multipliers.get(importance, 1.0)
        
        expiration = now + (base_period * multiplier)
        return expiration.isoformat()
    
    def _importance_score(self, importance: MemoryImportance) -> int:
        """Convert importance to numeric score"""
        scores = {
            MemoryImportance.CRITICAL: 4,
            MemoryImportance.HIGH: 3,
            MemoryImportance.MEDIUM: 2,
            MemoryImportance.LOW: 1
        }
        return scores.get(importance, 0)
    
    def _initialize_retention_policies(self) -> Dict:
        """Initialize retention policies for different memory types"""
        return {
            MemoryType.EPHEMERAL: {
                'max_age_hours': 1,
                'max_items_per_user': 10
            },
            MemoryType.SESSION: {
                'max_age_days': 1,
                'max_items_per_user': 50
            },
            MemoryType.LONG_TERM: {
                'max_age_days': 90,
                'max_items_per_user': 100
            },
            MemoryType.PREFERENCE: {
                'max_age_days': 180,
                'max_items_per_user': 20
            },
            MemoryType.FACTUAL: {
                'max_age_days': 365,
                'max_items_per_user': 200
            },
            MemoryType.PROCEDURAL: {
                'max_age_days': 365,
                'max_items_per_user': 50
            }
        }
    
    def export_user_memories(self, user_id: int) -> str:
        """Export user memories as JSON"""
        user_memory_ids = self.user_memories.get(user_id, set())
        
        memories_data = []
        for memory_id in user_memory_ids:
            memory_item = self.memory_store.get(memory_id)
            if memory_item:
                memories_data.append(memory_item.to_dict())
        
        return json.dumps(memories_data, ensure_ascii=False, indent=2)
    
    def import_user_memories(self, user_id: int, memories_json: str):
        """Import user memories from JSON"""
        try:
            memories_data = json.loads(memories_json)
            
            for memory_data in memories_data:
                memory_item = MemoryItem(
                    memory_id=memory_data.get('memory_id'),
                    memory_type=MemoryType(memory_data.get('memory_type')),
                    content=memory_data.get('content'),
                    importance=MemoryImportance(memory_data.get('importance', 'medium')),
                    created_at=memory_data.get('created_at'),
                    last_accessed=memory_data.get('last_accessed'),
                    access_count=memory_data.get('access_count', 0),
                    expiration=memory_data.get('expiration'),
                    source=memory_data.get('source', 'imported'),
                    confidence=memory_data.get('confidence', 1.0),
                    tags=set(memory_data.get('tags', []))
                )
                
                # Store memory
                self.memory_store[memory_item.memory_id] = memory_item
                self.user_memories[user_id].add(memory_item.memory_id)
                
                # Rebuild indexes
                for tag in memory_item.tags:
                    self.memory_index[tag].add(memory_item.memory_id)
                
                for key, value in memory_item.content.items():
                    index_key = f"{key}:{value}"
                    self.memory_index[index_key].add(memory_item.memory_id)
            
            logger.info(f"Imported {len(memories_data)} memories for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error importing memories: {str(e)}")
    
    def get_memory_by_tags(self, tags: List[str], user_id: int = None) -> List[MemoryItem]:
        """Get memories by tags"""
        candidate_ids = set()
        
        for tag in tags:
            if tag in self.memory_index:
                candidate_ids.update(self.memory_index[tag])
        
        # Filter by user if specified
        if user_id:
            user_memory_ids = self.user_memories.get(user_id, set())
            candidate_ids = candidate_ids.intersection(user_memory_ids)
        
        results = []
        for memory_id in candidate_ids:
            memory_item = self.memory_store.get(memory_id)
            if memory_item and not memory_item.is_expired():
                memory_item.update_access()
                results.append(memory_item)
        
        return results
    
    def forget_information(self, user_id: int, information_type: str):
        """Allow user to forget specific types of information"""
        # Find memories related to the information type
        memories_to_remove = []
        
        for memory_id in self.user_memories.get(user_id, set()):
            memory_item = self.memory_store.get(memory_id)
            if memory_item and information_type in str(memory_item.content).lower():
                memories_to_remove.append(memory_id)
        
        # Remove memories
        for memory_id in memories_to_remove:
            self._remove_memory(memory_id)
        
        logger.info(f"Forgot {len(memories_to_remove)} memories of type '{information_type}' for user {user_id}")


# Global instance
semantic_memory = SemanticMemory()