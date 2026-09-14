"""
Multimodal Input Manager
Handles text, voice, images, documents, and location inputs
Converts them to unified format for AI Agent understanding
"""

from typing import Dict, List, Any, Optional, Union
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import base64
import mimetypes

logger = logging.getLogger(__name__)


class InputType(Enum):
    """Types of multimodal inputs"""
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    DOCUMENT = "document"
    PDF = "pdf"
    CV = "cv"
    LOCATION = "location"
    MULTIMODAL = "multimodal"


class ImageCategory(Enum):
    """Categories for property images"""
    EXTERIOR = "exterior"
    INTERIOR = "interior"
    ROOM = "room"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    GARDEN = "garden"
    ROOF = "roof"
    GARAGE = "garage"
    OFFICE = "office"
    SHOP = "shop"
    LAND = "land"
    LIVING_ROOM = "living_room"
    BEDROOM = "bedroom"
    UNCLASSIFIED = "unclassified"


class DocumentType(Enum):
    """Types of documents"""
    CV = "cv"
    CONTRACT = "contract"
    PROPERTY_DOCUMENT = "property_document"
    CERTIFICATE = "certificate"
    INVOICE = "invoice"
    OTHER = "other"


@dataclass
class ImageData:
    """Represents image data with metadata"""
    image_id: str
    data: bytes
    mime_type: str
    filename: str = None
    category: ImageCategory = ImageCategory.UNCLASSIFIED
    confidence: float = 0.0
    width: int = None
    height: int = None
    analysis: Dict = field(default_factory=dict)
    related_property_id: int = None
    upload_timestamp: str = None
    
    def __post_init__(self):
        if not self.image_id:
            self.image_id = str(uuid.uuid4())[:8]
        if not self.upload_timestamp:
            self.upload_timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary (excludes raw data for serialization)"""
        return {
            'image_id': self.image_id,
            'mime_type': self.mime_type,
            'filename': self.filename,
            'category': self.category.value,
            'confidence': self.confidence,
            'width': self.width,
            'height': self.height,
            'analysis': self.analysis,
            'related_property_id': self.related_property_id,
            'upload_timestamp': self.upload_timestamp,
            'data_size': len(self.data)
        }


@dataclass
class DocumentData:
    """Represents document data with metadata"""
    document_id: str
    data: bytes
    mime_type: str
    filename: str
    document_type: DocumentType
    pages: int = 0
    text_content: str = None
    extraction_confidence: float = 0.0
    analysis: Dict = field(default_factory=dict)
    upload_timestamp: str = None
    
    def __post_init__(self):
        if not self.document_id:
            self.document_id = str(uuid.uuid4())[:8]
        if not self.upload_timestamp:
            self.upload_timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary (excludes raw data for serialization)"""
        return {
            'document_id': self.document_id,
            'mime_type': self.mime_type,
            'filename': self.filename,
            'document_type': self.document_type.value,
            'pages': self.pages,
            'text_content': self.text_content,
            'extraction_confidence': self.extraction_confidence,
            'analysis': self.analysis,
            'upload_timestamp': self.upload_timestamp,
            'data_size': len(self.data)
        }


@dataclass
class VoiceData:
    """Represents voice/audio data with metadata"""
    audio_id: str
    data: bytes
    mime_type: str
    duration: float = 0.0
    transcript: str = None
    confidence: float = 0.0
    language: str = None
    upload_timestamp: str = None
    
    def __post_init__(self):
        if not self.audio_id:
            self.audio_id = str(uuid.uuid4())[:8]
        if not self.upload_timestamp:
            self.upload_timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary (excludes raw data for serialization)"""
        return {
            'audio_id': self.audio_id,
            'mime_type': self.mime_type,
            'duration': self.duration,
            'transcript': self.transcript,
            'confidence': self.confidence,
            'language': self.language,
            'upload_timestamp': self.upload_timestamp,
            'data_size': len(self.data)
        }


@dataclass
class LocationData:
    """Represents location data with metadata"""
    location_id: str
    latitude: float
    longitude: float
    address: str = None
    governorate: str = None
    district: str = None
    radius: float = None  # For radius-based search
    nearby_services: List[str] = field(default_factory=list)
    upload_timestamp: str = None
    
    def __post_init__(self):
        if not self.location_id:
            self.location_id = str(uuid.uuid4())[:8]
        if not self.upload_timestamp:
            self.upload_timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'location_id': self.location_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'governorate': self.governorate,
            'district': self.district,
            'radius': self.radius,
            'nearby_services': self.nearby_services,
            'upload_timestamp': self.upload_timestamp
        }


@dataclass
class MultimodalInput:
    """Unified multimodal input representation"""
    input_id: str
    input_type: InputType
    text: str = None
    voice_data: VoiceData = None
    images: List[ImageData] = field(default_factory=list)
    documents: List[DocumentData] = field(default_factory=list)
    location_data: LocationData = None
    metadata: Dict = field(default_factory=dict)
    processed: bool = False
    processing_timestamp: str = None
    
    def __post_init__(self):
        if not self.input_id:
            self.input_id = str(uuid.uuid4())[:8]
        if not self.processing_timestamp:
            self.processing_timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'input_id': self.input_id,
            'input_type': self.input_type.value,
            'text': self.text,
            'voice_data': self.voice_data.to_dict() if self.voice_data else None,
            'images': [img.to_dict() for img in self.images],
            'documents': [doc.to_dict() for doc in self.documents],
            'location_data': self.location_data.to_dict() if self.location_data else None,
            'metadata': self.metadata,
            'processed': self.processed,
            'processing_timestamp': self.processing_timestamp
        }


class MultimodalInputManager:
    """
    Manager for handling multimodal inputs
    Converts various input types to unified format for AI processing
    """
    
    def __init__(self):
        self.max_image_size = 10 * 1024 * 1024  # 10MB
        self.max_document_size = 50 * 1024 * 1024  # 50MB
        self.max_audio_size = 25 * 1024 * 1024  # 25MB
        self.supported_image_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        self.supported_document_types = ['application/pdf', 'text/plain', 'application/msword', 
                                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        self.supported_audio_types = ['audio/wav', 'audio/mpeg', 'audio/ogg', 'audio/webm']
        self.input_history: List[Dict] = []
    
    def create_text_input(self, text: str, metadata: Dict = None) -> MultimodalInput:
        """Create text-only input"""
        return MultimodalInput(
            input_type=InputType.TEXT,
            text=text,
            metadata=metadata or {}
        )
    
    def create_voice_input(self, 
                          audio_data: bytes,
                          mime_type: str,
                          filename: str = None,
                          transcript: str = None) -> MultimodalInput:
        """Create voice input"""
        # Validate audio
        if not self._validate_audio(audio_data, mime_type):
            raise ValueError("Invalid audio data or unsupported format")
        
        voice_data = VoiceData(
            data=audio_data,
            mime_type=mime_type,
            filename=filename,
            transcript=transcript
        )
        
        return MultimodalInput(
            input_type=InputType.VOICE,
            voice_data=voice_data,
            text=transcript,  # Use transcript as text
            metadata={'filename': filename}
        )
    
    def create_image_input(self, 
                          image_data: bytes,
                          mime_type: str,
                          filename: str = None,
                          related_property_id: int = None) -> MultimodalInput:
        """Create image input"""
        # Validate image
        if not self._validate_image(image_data, mime_type):
            raise ValueError("Invalid image data or unsupported format")
        
        image = ImageData(
            data=image_data,
            mime_type=mime_type,
            filename=filename,
            related_property_id=related_property_id
        )
        
        return MultimodalInput(
            input_type=InputType.IMAGE,
            images=[image],
            metadata={'filename': filename, 'property_id': related_property_id}
        )
    
    def create_document_input(self,
                             document_data: bytes,
                             mime_type: str,
                             filename: str,
                             document_type: DocumentType = DocumentType.OTHER) -> MultimodalInput:
        """Create document input"""
        # Validate document
        if not self._validate_document(document_data, mime_type):
            raise ValueError("Invalid document data or unsupported format")
        
        document = DocumentData(
            data=document_data,
            mime_type=mime_type,
            filename=filename,
            document_type=document_type
        )
        
        return MultimodalInput(
            input_type=InputType.DOCUMENT,
            documents=[document],
            metadata={'filename': filename, 'document_type': document_type.value}
        )
    
    def create_cv_input(self,
                       cv_data: bytes,
                       mime_type: str,
                       filename: str) -> MultimodalInput:
        """Create CV input"""
        return self.create_document_input(
            cv_data, mime_type, filename, DocumentType.CV
        )
    
    def create_location_input(self,
                            latitude: float,
                            longitude: float,
                            address: str = None,
                            radius: float = None) -> MultimodalInput:
        """Create location input"""
        location = LocationData(
            latitude=latitude,
            longitude=longitude,
            address=address,
            radius=radius
        )
        
        return MultimodalInput(
            input_type=InputType.LOCATION,
            location_data=location,
            metadata={'address': address, 'radius': radius}
        )
    
    def create_multimodal_input(self,
                                text: str = None,
                                images: List[ImageData] = None,
                                documents: List[DocumentData] = None,
                                voice_data: VoiceData = None,
                                location_data: LocationData = None,
                                metadata: Dict = None) -> MultimodalInput:
        """Create combined multimodal input"""
        # Determine input type based on components
        component_count = sum([
            1 if text else 0,
            1 if images else 0,
            1 if documents else 0,
            1 if voice_data else 0,
            1 if location_data else 0
        ])
        
        input_type = InputType.MULTIMODAL if component_count > 1 else InputType.TEXT
        
        return MultimodalInput(
            input_type=input_type,
            text=text,
            voice_data=voice_data,
            images=images or [],
            documents=documents or [],
            location_data=location_data,
            metadata=metadata or {}
        )
    
    def process_input(self, multimodal_input: MultimodalInput) -> MultimodalInput:
        """
        Process multimodal input to extract actionable information
        
        Args:
            multimodal_input: Input to process
            
        Returns:
            Processed input with extracted information
        """
        try:
            # Process voice (transcribe if needed)
            if multimodal_input.voice_data and not multimodal_input.voice_data.transcript:
                multimodal_input.voice_data.transcript = self._transcribe_audio(
                    multimodal_input.voice_data
                )
                multimodal_input.text = multimodal_input.voice_data.transcript
            
            # Process images (analyze and categorize)
            for image in multimodal_input.images:
                if not image.analysis:
                    image.analysis = self._analyze_image(image)
            
            # Process documents (extract text)
            for document in multimodal_input.documents:
                if not document.text_content:
                    document.text_content = self._extract_document_text(document)
                    document.analysis = self._analyze_document(document)
            
            # Process location (reverse geocode if needed)
            if multimodal_input.location_data and not multimodal_input.location_data.governorate:
                location_info = self._reverse_geocode(multimodal_input.location_data)
                multimodal_input.location_data.governorate = location_info.get('governorate')
                multimodal_input.location_data.district = location_info.get('district')
            
            multimodal_input.processed = True
            multimodal_input.processing_timestamp = datetime.now().isoformat()
            
            # Add to history
            self.input_history.append({
                'timestamp': datetime.now().isoformat(),
                'input_id': multimodal_input.input_id,
                'input_type': multimodal_input.input_type.value,
                'component_count': len(multimodal_input.images) + len(multimodal_input.documents)
            })
            
            logger.info(f"Processed multimodal input {multimodal_input.input_id}")
            return multimodal_input
            
        except Exception as e:
            logger.error(f"Error processing multimodal input: {str(e)}")
            multimodal_input.metadata['processing_error'] = str(e)
            return multimodal_input
    
    def _validate_image(self, data: bytes, mime_type: str) -> bool:
        """Validate image data"""
        if len(data) > self.max_image_size:
            logger.warning(f"Image size exceeds limit: {len(data)} bytes")
            return False
        
        if mime_type not in self.supported_image_types:
            logger.warning(f"Unsupported image type: {mime_type}")
            return False
        
        return True
    
    def _validate_document(self, data: bytes, mime_type: str) -> bool:
        """Validate document data"""
        if len(data) > self.max_document_size:
            logger.warning(f"Document size exceeds limit: {len(data)} bytes")
            return False
        
        if mime_type not in self.supported_document_types:
            logger.warning(f"Unsupported document type: {mime_type}")
            return False
        
        return True
    
    def _validate_audio(self, data: bytes, mime_type: str) -> bool:
        """Validate audio data"""
        if len(data) > self.max_audio_size:
            logger.warning(f"Audio size exceeds limit: {len(data)} bytes")
            return False
        
        if mime_type not in self.supported_audio_types:
            logger.warning(f"Unsupported audio type: {mime_type}")
            return False
        
        return True
    
    def _transcribe_audio(self, voice_data: VoiceData) -> str:
        """Transcribe audio to text (placeholder)"""
        # This would integrate with speech-to-text service
        # For now, return placeholder
        logger.info(f"Transcribing audio {voice_data.audio_id}")
        return f"[Transcription placeholder for {voice_data.audio_id}]"
    
    def _analyze_image(self, image: ImageData) -> Dict:
        """Analyze image content (placeholder)"""
        # This would integrate with vision/AI service
        analysis = {
            'visible_elements': [],
            'confidence': 0.0,
            'quality_score': 0.5,
            'suggested_category': ImageCategory.UNCLASSIFIED.value
        }
        
        logger.info(f"Analyzing image {image.image_id}")
        return analysis
    
    def _extract_document_text(self, document: DocumentData) -> str:
        """Extract text from document (placeholder)"""
        # This would integrate with OCR/PDF extraction service
        # For now, return placeholder
        logger.info(f"Extracting text from document {document.document_id}")
        return f"[Text extraction placeholder for {document.document_id}]"
    
    def _analyze_document(self, document: DocumentData) -> Dict:
        """Analyze document content (placeholder)"""
        analysis = {
            'content_type': 'unknown',
            'key_entities': [],
            'confidence': 0.0
        }
        
        if document.document_type == DocumentType.CV:
            analysis['content_type'] = 'cv'
            analysis['key_entities'] = ['skills', 'experience', 'education']
        
        logger.info(f"Analyzing document {document.document_id}")
        return analysis
    
    def _reverse_geocode(self, location: LocationData) -> Dict:
        """Reverse geocode coordinates to address (placeholder)"""
        # This would integrate with geocoding service
        # For now, return placeholder
        logger.info(f"Reverse geocoding location {location.location_id}")
        return {
            'governorate': None,
            'district': None,
            'address': location.address
        }
    
    def get_input_summary(self, multimodal_input: MultimodalInput) -> Dict:
        """Get summary of multimodal input"""
        return {
            'input_id': multimodal_input.input_id,
            'input_type': multimodal_input.input_type.value,
            'has_text': multimodal_input.text is not None,
            'has_voice': multimodal_input.voice_data is not None,
            'image_count': len(multimodal_input.images),
            'document_count': len(multimodal_input.documents),
            'has_location': multimodal_input.location_data is not None,
            'processed': multimodal_input.processed
        }
    
    def encode_image_base64(self, image_data: ImageData) -> str:
        """Encode image data to base64"""
        return base64.b64encode(image_data.data).decode('utf-8')
    
    def decode_image_base64(self, base64_string: str, mime_type: str) -> ImageData:
        """Decode base64 string to image data"""
        data = base64.b64decode(base64_string)
        return ImageData(
            data=data,
            mime_type=mime_type
        )


# Global instance
multimodal_input_manager = MultimodalInputManager()