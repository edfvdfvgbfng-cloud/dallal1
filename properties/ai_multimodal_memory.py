"""
Multimodal Memory System
Stores references to multimodal assets without storing full content in context
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime

from .ai_multimodal_input import ImageData, DocumentData, VoiceData, LocationData
from .ai_semantic_memory import SemanticMemory, MemoryType, MemoryImportance

logger = logging.getLogger(__name__)


class AssetReferenceType(Enum):
    """Types of asset references"""
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    LOCATION = "location"


@dataclass
class AssetReference:
    """Reference to an asset stored in memory"""
    reference_id: str
    asset_type: AssetReferenceType
    asset_id: str
    related_property_id: int = None
    conversation_id: str = None
    metadata: Dict = field(default_factory=dict)
    created_at: str = None
    expires_at: str = None
    
    def __post_init__(self):
        if not self.reference_id:
            import uuid
            self.reference_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'reference_id': self.reference_id,
            'asset_type': self.asset_type.value,
            'asset_id': self.asset_id,
            'related_property_id': self.related_property_id,
            'conversation_id': self.conversation_id,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'expires_at': self.expires_at
        }


class MultimodalMemory:
    """
    Memory system for multimodal assets
    Stores references instead of full content to avoid context bloat
    """
    
    def __init__(self):
        self.semantic_memory = SemanticMemory()
        self.asset_references: Dict[str, AssetReference] = []
        self.conversation_assets: Dict[str, List[str]] = {}  # conversation_id -> [reference_ids]
    
    def store_image_reference(self,
                            image: ImageData,
                            conversation_id: str = None,
                            user_id: int = None) -> AssetReference:
        """Store reference to an image"""
        reference = AssetReference(
            asset_type=AssetReferenceType.IMAGE,
            asset_id=image.image_id,
            related_property_id=image.related_property_id,
            conversation_id=conversation_id,
            metadata={
                'filename': image.filename,
                'category': image.category.value,
                'width': image.width,
                'height': image.height
            }
        )
        
        # Store in semantic memory
        self.semantic_memory.store_memory(
            content={
                'asset_id': image.image_id,
                'asset_type': 'image',
                'category': image.category.value,
                'property_id': image.related_property_id
            },
            memory_type=MemoryType.SESSION,
            importance=MemoryImportance.MEDIUM,
            user_id=user_id,
            tags=['multimodal', 'image', conversation_id] if conversation_id else ['multimodal', 'image']
        )
        
        # Store reference
        self.asset_references[reference.reference_id] = reference
        
        # Link to conversation
        if conversation_id:
            if conversation_id not in self.conversation_assets:
                self.conversation_assets[conversation_id] = []
            self.conversation_assets[conversation_id].append(reference.reference_id)
        
        logger.info(f"Stored image reference {reference.reference_id}")
        return reference
    
    def store_document_reference(self,
                               document: DocumentData,
                               conversation_id: str = None,
                               user_id: int = None) -> AssetReference:
        """Store reference to a document"""
        reference = AssetReference(
            asset_type=AssetReferenceType.DOCUMENT,
            asset_id=document.document_id,
            conversation_id=conversation_id,
            metadata={
                'filename': document.filename,
                'document_type': document.document_type.value,
                'pages': document.pages
            }
        )
        
        # Store in semantic memory
        self.semantic_memory.store_memory(
            content={
                'asset_id': document.document_id,
                'asset_type': 'document',
                'document_type': document.document_type.value
            },
            memory_type=MemoryType.SESSION,
            importance=MemoryImportance.HIGH,
            user_id=user_id,
            tags=['multimodal', 'document', conversation_id] if conversation_id else ['multimodal', 'document']
        )
        
        self.asset_references[reference.reference_id] = reference
        
        if conversation_id:
            if conversation_id not in self.conversation_assets:
                self.conversation_assets[conversation_id] = []
            self.conversation_assets[conversation_id].append(reference.reference_id)
        
        logger.info(f"Stored document reference {reference.reference_id}")
        return reference
    
    def store_location_reference(self,
                               location: LocationData,
                               conversation_id: str = None,
                               user_id: int = None) -> AssetReference:
        """Store reference to a location"""
        reference = AssetReference(
            asset_type=AssetReferenceType.LOCATION,
            asset_id=location.location_id,
            conversation_id=conversation_id,
            metadata={
                'latitude': location.latitude,
                'longitude': location.longitude,
                'address': location.address,
                'governorate': location.governorate,
                'district': location.district
            }
        )
        
        # Store in semantic memory
        self.semantic_memory.store_memory(
            content={
                'asset_id': location.location_id,
                'asset_type': 'location',
                'governorate': location.governorate,
                'district': location.district
            },
            memory_type=MemoryType.EPHEMERAL,
            importance=MemoryImportance.MEDIUM,
            user_id=user_id,
            tags=['multimodal', 'location', conversation_id] if conversation_id else ['multimodal', 'location']
        )
        
        self.asset_references[reference.reference_id] = reference
        
        if conversation_id:
            if conversation_id not in self.conversation_assets:
                self.conversation_assets[conversation_id] = []
            self.conversation_assets[conversation_id].append(reference.reference_id)
        
        logger.info(f"Stored location reference {reference.reference_id}")
        return reference
    
    def get_conversation_assets(self, conversation_id: str) -> List[AssetReference]:
        """Get all asset references for a conversation"""
        reference_ids = self.conversation_assets.get(conversation_id, [])
        return [
            self.asset_references[ref_id]
            for ref_id in reference_ids
            if ref_id in self.asset_references
        ]
    
    def get_reference(self, reference_id: str) -> Optional[AssetReference]:
        """Get asset reference by ID"""
        return self.asset_references.get(reference_id)
    
    def clear_conversation_assets(self, conversation_id: str):
        """Clear all asset references for a conversation"""
        if conversation_id in self.conversation_assets:
            reference_ids = self.conversation_assets[conversation_id]
            
            for ref_id in reference_ids:
                if ref_id in self.asset_references:
                    del self.asset_references[ref_id]
            
            del self.conversation_assets[conversation_id]
            
            logger.info(f"Cleared {len(reference_ids)} asset references for conversation {conversation_id}")
    
    def get_asset_context_summary(self, conversation_id: str) -> Dict:
        """Get summary of assets in conversation context"""
        references = self.get_conversation_assets(conversation_id)
        
        type_counts = {}
        for ref in references:
            asset_type = ref.asset_type.value
            type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
        
        return {
            'conversation_id': conversation_id,
            'total_assets': len(references),
            'type_counts': type_counts,
            'has_images': type_counts.get('image', 0) > 0,
            'has_documents': type_counts.get('document', 0) > 0,
            'has_location': type_counts.get('location', 0) > 0
        }
    
    def cleanup_expired_references(self):
        """Remove expired references"""
        now = datetime.now()
        expired_ids = []
        
        for ref_id, ref in self.asset_references.items():
            if ref.expires_at:
                expires_at = datetime.fromisoformat(ref.expires_at)
                if now > expires_at:
                    expired_ids.append(ref_id)
        
        for ref_id in expired_ids:
            del self.asset_references[ref_id]
        
        logger.info(f"Cleaned up {len(expired_ids)} expired asset references")
    
    def get_memory_statistics(self) -> Dict:
        """Get memory statistics"""
        type_counts = {}
        for ref in self.asset_references.values():
            asset_type = ref.asset_type.value
            type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
        
        return {
            'total_references': len(self.asset_references),
            'type_counts': type_counts,
            'active_conversations': len(self.conversation_assets),
            'semantic_memory_stats': self.semantic_memory.get_memory_statistics()
        }


# Global instance
multimodal_memory = MultimodalMemory()