"""
Asset Storage Manager
Secure storage for images, documents, and other assets
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import os
import hashlib

from .ai_multimodal_input import ImageData, DocumentData, VoiceData

logger = logging.getLogger(__name__)


class AssetType(Enum):
    """Types of assets"""
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    OTHER = "other"


class AccessLevel(Enum):
    """Access levels for assets"""
    PUBLIC = "public"
    PRIVATE = "private"
    RESTRICTED = "restricted"


@dataclass
class StoredAsset:
    """Represents a stored asset"""
    asset_id: str
    asset_type: AssetType
    filename: str
    file_path: str
    size_bytes: int
    mime_type: str
    access_level: AccessLevel
    owner_id: int = None
    related_property_id: int = None
    upload_timestamp: str = None
    expires_at: str = None
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.asset_id:
            self.asset_id = str(uuid.uuid4())[:8]
        if not self.upload_timestamp:
            self.upload_timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'asset_id': self.asset_id,
            'asset_type': self.asset_type.value,
            'filename': self.filename,
            'file_path': self.file_path,
            'size_bytes': self.size_bytes,
            'mime_type': self.mime_type,
            'access_level': self.access_level.value,
            'owner_id': self.owner_id,
            'related_property_id': self.related_property_id,
            'upload_timestamp': self.upload_timestamp,
            'expires_at': self.expires_at,
            'metadata': self.metadata
        }


class AssetStorageManager:
    """
    Manages secure storage of assets
    Handles file operations, access control, and cleanup
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(os.getcwd(), 'assets')
        self.storage_locations = {
            AssetType.IMAGE: os.path.join(self.storage_path, 'images'),
            AssetType.DOCUMENT: os.path.join(self.storage_path, 'documents'),
            AssetType.AUDIO: os.path.join(self.storage_path, 'audio'),
            AssetType.VIDEO: os.path.join(self.storage_path, 'video')
        }
        self.asset_database: Dict[str, StoredAsset] = {}
        self.access_logs: List[Dict] = []
        
        # Create storage directories
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize storage directories"""
        for asset_type, path in self.storage_locations.items():
            os.makedirs(path, exist_ok=True)
            logger.info(f"Initialized storage for {asset_type.value}: {path}")
    
    def store_image(self, 
                   image: ImageData,
                   owner_id: int = None,
                   access_level: AccessLevel = AccessLevel.PRIVATE) -> StoredAsset:
        """Store an image asset"""
        # Determine storage path
        asset_type = AssetType.IMAGE
        storage_dir = self.storage_locations[asset_type]
        
        # Generate unique filename
        file_extension = self._get_file_extension(image.mime_type)
        unique_filename = f"{image.image_id}{file_extension}"
        file_path = os.path.join(storage_dir, unique_filename)
        
        # Save file
        try:
            with open(file_path, 'wb') as f:
                f.write(image.data)
            
            # Create asset record
            asset = StoredAsset(
                asset_id=image.image_id,
                asset_type=asset_type,
                filename=image.filename or unique_filename,
                file_path=file_path,
                size_bytes=len(image.data),
                mime_type=image.mime_type,
                access_level=access_level,
                owner_id=owner_id,
                related_property_id=image.related_property_id,
                metadata={
                    'width': image.width,
                    'height': image.height,
                    'category': image.category.value
                }
            )
            
            # Store in database
            self.asset_database[asset.asset_id] = asset
            
            logger.info(f"Stored image asset {asset.asset_id}")
            return asset
            
        except Exception as e:
            logger.error(f"Error storing image: {str(e)}")
            raise
    
    def store_document(self,
                     document: DocumentData,
                     owner_id: int = None,
                     access_level: AccessLevel = AccessLevel.PRIVATE) -> StoredAsset:
        """Store a document asset"""
        asset_type = AssetType.DOCUMENT
        storage_dir = self.storage_locations[asset_type]
        
        file_extension = self._get_file_extension(document.mime_type)
        unique_filename = f"{document.document_id}{file_extension}"
        file_path = os.path.join(storage_dir, unique_filename)
        
        try:
            with open(file_path, 'wb') as f:
                f.write(document.data)
            
            asset = StoredAsset(
                asset_id=document.document_id,
                asset_type=asset_type,
                filename=document.filename or unique_filename,
                file_path=file_path,
                size_bytes=len(document.data),
                mime_type=document.mime_type,
                access_level=access_level,
                owner_id=owner_id,
                metadata={
                    'document_type': document.document_type.value,
                    'pages': document.pages
                }
            )
            
            self.asset_database[asset.asset_id] = asset
            
            logger.info(f"Stored document asset {asset.asset_id}")
            return asset
            
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            raise
    
    def store_audio(self,
                   audio: VoiceData,
                   owner_id: int = None,
                   access_level: AccessLevel = AccessLevel.PRIVATE) -> StoredAsset:
        """Store an audio asset"""
        asset_type = AssetType.AUDIO
        storage_dir = self.storage_locations[asset_type]
        
        file_extension = self._get_file_extension(audio.mime_type)
        unique_filename = f"{audio.audio_id}{file_extension}"
        file_path = os.path.join(storage_dir, unique_filename)
        
        try:
            with open(file_path, 'wb') as f:
                f.write(audio.data)
            
            asset = StoredAsset(
                asset_id=audio.audio_id,
                asset_type=asset_type,
                filename=audio.filename or unique_filename,
                file_path=file_path,
                size_bytes=len(audio.data),
                mime_type=audio.mime_type,
                access_level=access_level,
                owner_id=owner_id,
                metadata={
                    'duration': audio.duration,
                    'language': audio.language
                }
            )
            
            self.asset_database[asset.asset_id] = asset
            
            logger.info(f"Stored audio asset {asset.asset_id}")
            return asset
            
        except Exception as e:
            logger.error(f"Error storing audio: {str(e)}")
            raise
    
    def get_asset(self, asset_id: str, user_id: int = None) -> Optional[StoredAsset]:
        """Retrieve asset by ID with access check"""
        asset = self.asset_database.get(asset_id)
        
        if not asset:
            logger.warning(f"Asset {asset_id} not found")
            return None
        
        # Check access
        if not self._check_access(asset, user_id):
            logger.warning(f"Access denied for asset {asset_id} by user {user_id}")
            return None
        
        # Log access
        self._log_access(asset_id, user_id, 'retrieval')
        
        return asset
    
    def get_asset_file(self, asset_id: str, user_id: int = None) -> Optional[bytes]:
        """Get actual file data for asset"""
        asset = self.get_asset(asset_id, user_id)
        
        if not asset:
            return None
        
        try:
            with open(asset.file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading asset file: {str(e)}")
            return None
    
    def generate_signed_url(self, 
                          asset_id: str,
                          user_id: int = None,
                          expiration_seconds: int = 3600) -> Optional[str]:
        """Generate a signed URL for temporary access"""
        asset = self.get_asset(asset_id, user_id)
        
        if not asset:
            return None
        
        # In production, this would generate a signed URL with expiration
        # For now, return the file path
        return f"/api/assets/{asset_id}?expires={expiration_seconds}"
    
    def delete_asset(self, asset_id: str, user_id: int = None) -> bool:
        """Delete an asset"""
        asset = self.get_asset(asset_id, user_id)
        
        if not asset:
            return False
        
        try:
            # Delete file
            if os.path.exists(asset.file_path):
                os.remove(asset.file_path)
            
            # Remove from database
            del self.asset_database[asset_id]
            
            # Log deletion
            self._log_access(asset_id, user_id, 'deletion')
            
            logger.info(f"Deleted asset {asset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting asset: {str(e)}")
            return False
    
    def _check_access(self, asset: StoredAsset, user_id: int) -> bool:
        """Check if user has access to asset"""
        # Owner always has access
        if asset.owner_id == user_id:
            return True
        
        # Public assets are accessible to all
        if asset.access_level == AccessLevel.PUBLIC:
            return True
        
        # Otherwise, deny access
        return False
    
    def _log_access(self, asset_id: str, user_id: int, action: str):
        """Log asset access"""
        self.access_logs.append({
            'timestamp': datetime.now().isoformat(),
            'asset_id': asset_id,
            'user_id': user_id,
            'action': action
        })
    
    def _get_file_extension(self, mime_type: str) -> str:
        """Get file extension from mime type"""
        extension_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/webp': '.webp',
            'image/gif': '.gif',
            'application/pdf': '.pdf',
            'text/plain': '.txt',
            'audio/wav': '.wav',
            'audio/mpeg': '.mp3',
            'audio/ogg': '.ogg'
        }
        
        return extension_map.get(mime_type, '.bin')
    
    def calculate_file_hash(self, data: bytes) -> str:
        """Calculate SHA-256 hash of file data"""
        return hashlib.sha256(data).hexdigest()
    
    def get_user_assets(self, user_id: int) -> List[StoredAsset]:
        """Get all assets owned by a user"""
        return [
            asset for asset in self.asset_database.values()
            if asset.owner_id == user_id
        ]
    
    def get_property_assets(self, property_id: int) -> List[StoredAsset]:
        """Get all assets related to a property"""
        return [
            asset for asset in self.asset_database.values()
            if asset.related_property_id == property_id
        ]
    
    def cleanup_expired_assets(self):
        """Remove assets that have expired"""
        now = datetime.now()
        expired_ids = []
        
        for asset_id, asset in self.asset_database.items():
            if asset.expires_at:
                expires_at = datetime.fromisoformat(asset.expires_at)
                if now > expires_at:
                    expired_ids.append(asset_id)
        
        for asset_id in expired_ids:
            self.delete_asset(asset_id)
        
        logger.info(f"Cleaned up {len(expired_ids)} expired assets")
    
    def get_storage_statistics(self) -> Dict:
        """Get storage statistics"""
        total_size = sum(asset.size_bytes for asset in self.asset_database.values())
        
        type_counts = {}
        for asset in self.asset_database.values():
            asset_type = asset.asset_type.value
            type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
        
        return {
            'total_assets': len(self.asset_database),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'type_counts': type_counts,
            'access_logs_count': len(self.access_logs)
        }


# Global instance
asset_storage_manager = AssetStorageManager()