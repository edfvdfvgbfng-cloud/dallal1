"""
Document Processing System
Handles PDF and document extraction with grounding
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime

from .ai_multimodal_input import DocumentData, DocumentType

logger = logging.getLogger(__name__)


class ExtractionMethod(Enum):
    """Methods for extracting content from documents"""
    OCR = "ocr"
    PDF_PARSING = "pdf_parsing"
    TEXT_EXTRACTION = "text_extraction"
    MANUAL = "manual"


@dataclass
class DocumentSection:
    """Represents a section within a document"""
    section_id: str
    title: str
    content: str
    page_number: int
    start_char: int
    end_char: int
    confidence: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'section_id': self.section_id,
            'title': self.title,
            'content': self.content,
            'page_number': self.page_number,
            'start_char': self.start_char,
            'end_char': self.end_char,
            'confidence': self.confidence
        }


@dataclass
class DocumentExtraction:
    """Represents extracted content from a document"""
    document_id: str
    full_text: str
    sections: List[DocumentSection]
    extraction_method: ExtractionMethod
    extraction_confidence: float
    extraction_timestamp: str
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'document_id': self.document_id,
            'full_text': self.full_text,
            'sections': [section.to_dict() for section in self.sections],
            'extraction_method': self.extraction_method.value,
            'extraction_confidence': self.extraction_confidence,
            'extraction_timestamp': self.extraction_timestamp,
            'metadata': self.metadata
        }


class DocumentProcessingSystem:
    """
    Processes documents and extracts content with grounding
    Provides source attribution for all extracted information
    """
    
    def __init__(self):
        self.extraction_history: List[Dict] = []
    
    def process_document(self, document: DocumentData) -> DocumentExtraction:
        """
        Process document and extract content
        
        Args:
            document: Document data to process
            
        Returns:
            DocumentExtraction with extracted content
        """
        try:
            # Determine extraction method
            extraction_method = self._determine_extraction_method(document)
            
            # Extract content
            if not document.text_content:
                document.text_content = self._extract_text(document, extraction_method)
            
            # Section the document
            sections = self._section_document(document)
            
            # Create extraction object
            extraction = DocumentExtraction(
                document_id=document.document_id,
                full_text=document.text_content,
                sections=sections,
                extraction_method=extraction_method,
                extraction_confidence=self._calculate_extraction_confidence(document, sections),
                extraction_timestamp=datetime.now().isoformat()
            )
            
            # Update document with extraction
            document.text_content = extraction.full_text
            document.extraction_confidence = extraction.extraction_confidence
            document.analysis = {
                'sections_count': len(sections),
                'extraction_method': extraction_method.value
            }
            
            # Log extraction
            self.extraction_history.append({
                'timestamp': datetime.now().isoformat(),
                'document_id': document.document_id,
                'document_type': document.document_type.value,
                'extraction_method': extraction_method.value,
                'confidence': extraction.extraction_confidence
            })
            
            logger.info(f"Processed document {document.document_id}: {len(sections)} sections")
            return extraction
            
        except Exception as e:
            logger.error(f"Error processing document {document.document_id}: {str(e)}")
            return self._create_error_extraction(document, str(e))
    
    def _determine_extraction_method(self, document: DocumentData) -> ExtractionMethod:
        """Determine best extraction method for document"""
        mime_type = document.mime_type
        
        if mime_type == 'application/pdf':
            return ExtractionMethod.PDF_PARSING
        elif mime_type == 'text/plain':
            return ExtractionMethod.TEXT_EXTRACTION
        elif mime_type in ['image/jpeg', 'image/png']:
            return ExtractionMethod.OCR
        else:
            return ExtractionMethod.MANUAL
    
    def _extract_text(self, document: DocumentData, method: ExtractionMethod) -> str:
        """Extract text from document using specified method"""
        # Placeholder extraction
        # In production, this would integrate with:
        # - PDF parsing libraries (PyPDF2, pdfplumber)
        # - OCR services (Tesseract, Google Vision API)
        # - Document parsing services
        
        logger.info(f"Extracting text from {document.document_id} using {method.value}")
        return f"[Text extraction placeholder for {document.document_id} using {method.value}]"
    
    def _section_document(self, document: DocumentData) -> List[DocumentSection]:
        """Section document into logical parts"""
        sections = []
        
        text = document.text_content
        if not text:
            return sections
        
        # Placeholder sectioning
        # In production, this would use NLP to identify sections
        
        # Create a single section for now
        section = DocumentSection(
            section_id=f"section_0",
            title="Full Content",
            content=text,
            page_number=1,
            start_char=0,
            end_char=len(text),
            confidence=0.8
        )
        sections.append(section)
        
        return sections
    
    def _calculate_extraction_confidence(self, 
                                       document: DocumentData,
                                       sections: List[DocumentSection]) -> float:
        """Calculate confidence in extraction"""
        if not sections:
            return 0.0
        
        # Average section confidence
        avg_section_confidence = sum(s.confidence for s in sections) / len(sections)
        
        # Adjust based on document type
        if document.document_type == DocumentType.CV:
            avg_section_confidence *= 0.9  # CVs may have structured formats
        
        return min(avg_section_confidence, 1.0)
    
    def answer_document_question(self, 
                                extraction: DocumentExtraction,
                                question: str) -> Optional[Dict]:
        """
        Answer a question based on document content
        
        Args:
            extraction: Document extraction
            question: Question to answer
            
        Returns:
            Answer with source attribution
        """
        try:
            # Search for answer in document sections
            answer = self._search_document(extraction, question)
            
            if answer:
                return {
                    'answer': answer['text'],
                    'confidence': answer['confidence'],
                    'source': {
                        'document_id': extraction.document_id,
                        'section_id': answer['section_id'],
                        'page_number': answer['page_number'],
                        'text_span': answer['text_span']
                    },
                    'grounded': True
                }
            else:
                return {
                    'answer': "ما لكيت هذه المعلومة داخل الملف.",
                    'confidence': 0.0,
                    'grounded': False
                }
                
        except Exception as e:
            logger.error(f"Error answering document question: {str(e)}")
            return {
                'answer': "حدث خطأ أثناء البحث في الملف.",
                'confidence': 0.0,
                'grounded': False
            }
    
    def _search_document(self, 
                        extraction: DocumentExtraction,
                        question: str) -> Optional[Dict]:
        """Search document for answer to question"""
        # Placeholder search
        # In production, this would use RAG or question-answering models
        
        question_lower = question.lower()
        
        for section in extraction.sections:
            section_content_lower = section.content.lower()
            
            # Simple keyword matching
            if any(word in section_content_lower for word in question_lower.split()):
                return {
                    'text': section.content[:200] + "...",  # Truncated for demo
                    'confidence': 0.6,
                    'section_id': section.section_id,
                    'page_number': section.page_number,
                    'text_span': {
                        'start': section.start_char,
                        'end': section.start_char + 200
                    }
                }
        
        return None
    
    def extract_property_info(self, extraction: DocumentExtraction) -> Dict:
        """Extract property information from document"""
        # Placeholder extraction
        # In production, this would use pattern matching for property documents
        
        return {
            'property_id': None,
            'price': None,
            'area': None,
            'location': None,
            'confidence': 0.0
        }
    
    def _create_error_extraction(self, document: DocumentData, error: str) -> DocumentExtraction:
        """Create error extraction when processing fails"""
        return DocumentExtraction(
            document_id=document.document_id,
            full_text="",
            sections=[],
            extraction_method=ExtractionMethod.MANUAL,
            extraction_confidence=0.0,
            extraction_timestamp=datetime.now().isoformat(),
            metadata={'error': error}
        )
    
    def get_document_summary(self, extraction: DocumentExtraction) -> Dict:
        """Get summary of document extraction"""
        return {
            'document_id': extraction.document_id,
            'total_length': len(extraction.full_text),
            'sections_count': len(extraction.sections),
            'extraction_method': extraction.extraction_method.value,
            'extraction_confidence': extraction.extraction_confidence
        }


# Global instance
document_processing_system = DocumentProcessingSystem()