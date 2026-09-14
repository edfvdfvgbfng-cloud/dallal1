"""
Unified Multimodal AI Pipeline
Integrates all multimodal components with existing AI Agent
Text, Voice, Image, Document, Location → Single AI Pipeline
"""

from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime

from .ai_multimodal_input import (
    MultimodalInputManager, MultimodalInput, InputType,
    ImageData, DocumentData, VoiceData, LocationData
)
from .ai_image_analysis import PropertyImageAnalyzer, ImageObservation, ImageQuality
from .ai_cv_intelligence import CVIntelligenceSystem, CVProfile
from .ai_document_processing import DocumentProcessingSystem, DocumentExtraction
from .ai_location_intelligence import LocationIntelligenceSystem, LocationConstraint
from .ai_asset_storage import AssetStorageManager, StoredAsset
from .ai_multimodal_memory import MultimodalMemory, AssetReference
from .ai_advanced_orchestrator import AdvancedAIOrchestrator
from .ai_goal_understanding import UserGoal, GoalType
from .ai_evidence_response import EvidenceBasedResponseSystem

logger = logging.getLogger(__name__)


class UnifiedMultimodalAIPipeline:
    """
    Unified pipeline for processing multimodal inputs
    Integrates with existing AI Agent for consistent intelligence
    """
    
    def __init__(self):
        # Multimodal components
        self.input_manager = MultimodalInputManager()
        self.image_analyzer = PropertyImageAnalyzer()
        self.cv_system = CVIntelligenceSystem()
        self.document_processor = DocumentProcessingSystem()
        self.location_system = LocationIntelligenceSystem()
        self.asset_storage = AssetStorageManager()
        self.multimodal_memory = MultimodalMemory()
        
        # Existing AI components
        self.ai_orchestrator = AdvancedAIOrchestrator()
        self.evidence_system = EvidenceBasedResponseSystem()
    
    def process_multimodal_query(self,
                                text: str = None,
                                images: List[ImageData] = None,
                                documents: List[DocumentData] = None,
                                voice_data: VoiceData = None,
                                location_data: LocationData = None,
                                conversation_id: str = None,
                                user_id: int = None) -> Dict:
        """
        Process multimodal query through unified pipeline
        
        Args:
            text: Text input
            images: List of images
            documents: List of documents
            voice_data: Voice/audio data
            location_data: Location data
            conversation_id: Conversation identifier
            user_id: User ID
            
        Returns:
            Comprehensive response with multimodal intelligence
        """
        try:
            # Step 1: Create multimodal input
            multimodal_input = self.input_manager.create_multimodal_input(
                text=text,
                images=images or [],
                documents=documents or [],
                voice_data=voice_data,
                location_data=location_data,
                metadata={'conversation_id': conversation_id, 'user_id': user_id}
            )
            
            # Step 2: Process multimodal input
            processed_input = self.input_manager.process_input(multimodal_input)
            
            # Step 3: Store assets
            stored_assets = self._store_assets(processed_input, user_id)
            
            # Step 4: Store asset references in memory
            self._store_asset_references(processed_input, conversation_id, user_id)
            
            # Step 5: Analyze components
            analysis_results = self._analyze_components(processed_input)
            
            # Step 6: Build enhanced context
            enhanced_context = self._build_enhanced_context(
                processed_input, analysis_results, conversation_id
            )
            
            # Step 7: Process through AI orchestrator
            ai_response = self._process_with_ai(processed_input, enhanced_context, user_id)
            
            # Step 8: Verify response with evidence
            verified_response = self._verify_multimodal_response(
                ai_response, analysis_results, enhanced_context
            )
            
            # Step 9: Build final response
            final_response = self._build_final_response(
                verified_response, analysis_results, stored_assets
            )
            
            logger.info(f"Processed multimodal query for conversation {conversation_id}")
            return final_response
            
        except Exception as e:
            logger.error(f"Error processing multimodal query: {str(e)}")
            return self._create_error_response(str(e))
    
    def _store_assets(self, 
                     multimodal_input: MultimodalInput,
                     user_id: int) -> Dict[str, StoredAsset]:
        """Store assets in secure storage"""
        stored_assets = {}
        
        # Store images
        for image in multimodal_input.images:
            try:
                asset = self.asset_storage.store_image(image, user_id)
                stored_assets[image.image_id] = asset
            except Exception as e:
                logger.error(f"Error storing image {image.image_id}: {str(e)}")
        
        # Store documents
        for document in multimodal_input.documents:
            try:
                asset = self.asset_storage.store_document(document, user_id)
                stored_assets[document.document_id] = asset
            except Exception as e:
                logger.error(f"Error storing document {document.document_id}: {str(e)}")
        
        # Store audio
        if multimodal_input.voice_data:
            try:
                asset = self.asset_storage.store_audio(multimodal_input.voice_data, user_id)
                stored_assets[multimodal_input.voice_data.audio_id] = asset
            except Exception as e:
                logger.error(f"Error storing audio {multimodal_input.voice_data.audio_id}: {str(e)}")
        
        return stored_assets
    
    def _store_asset_references(self,
                               multimodal_input: MultimodalInput,
                               conversation_id: str,
                               user_id: int):
        """Store asset references in multimodal memory"""
        for image in multimodal_input.images:
            self.multimodal_memory.store_image_reference(image, conversation_id, user_id)
        
        for document in multimodal_input.documents:
            self.multimodal_memory.store_document_reference(document, conversation_id, user_id)
        
        if multimodal_input.location_data:
            self.multimodal_memory.store_location_reference(
                multimodal_input.location_data, conversation_id, user_id
            )
    
    def _analyze_components(self, 
                          multimodal_input: MultimodalInput) -> Dict:
        """Analyze each multimodal component"""
        analysis = {
            'images': [],
            'documents': [],
            'location': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Analyze images
        for image in multimodal_input.images:
            observations, quality = self.image_analyzer.analyze_property_image(image)
            analysis['images'].append({
                'image_id': image.image_id,
                'observations': [obs.to_dict() for obs in observations],
                'quality': quality.to_dict(),
                'category': self.image_analyzer.categorize_image(image).value
            })
        
        # Analyze documents
        for document in multimodal_input.documents:
            if document.document_type.value == 'cv':
                cv_profile = self.cv_system.analyze_cv(document)
                analysis['documents'].append({
                    'document_id': document.document_id,
                    'type': 'cv',
                    'profile': cv_profile.to_dict()
                })
            else:
                extraction = self.document_processor.process_document(document)
                analysis['documents'].append({
                    'document_id': document.document_id,
                    'type': 'document',
                    'extraction': extraction.to_dict()
                })
        
        # Analyze location
        if multimodal_input.location_data:
            processed_location = self.location_system.process_location_input(
                multimodal_input.location_data
            )
            analysis['location'] = processed_location.to_dict()
        
        return analysis
    
    def _build_enhanced_context(self,
                               multimodal_input: MultimodalInput,
                               analysis_results: Dict,
                               conversation_id: str) -> Dict:
        """Build enhanced context for AI processing"""
        context = {
            'conversation_id': conversation_id,
            'input_type': multimodal_input.input_type.value,
            'has_text': multimodal_input.text is not None,
            'has_images': len(multimodal_input.images) > 0,
            'has_documents': len(multimodal_input.documents) > 0,
            'has_location': multimodal_input.location_data is not None,
            'image_count': len(multimodal_input.images),
            'document_count': len(multimodal_input.documents),
            'analysis': analysis_results
        }
        
        # Add text content
        if multimodal_input.text:
            context['text'] = multimodal_input.text
        
        # Add image insights
        if analysis_results['images']:
            context['image_insights'] = [
                {
                    'category': img['category'],
                    'visible_elements': [obs['element'] for obs in img['observations']],
                    'quality': img['quality']['overall_quality']
                }
                for img in analysis_results['images']
            ]
        
        # Add document insights
        if analysis_results['documents']:
            context['document_insights'] = [
                {
                    'type': doc['type'],
                    'content_available': len(doc.get('extraction', {}).get('full_text', '')) > 0
                }
                for doc in analysis_results['documents']
            ]
        
        # Add location insights
        if analysis_results['location']:
            context['location_insights'] = {
                'governorate': analysis_results['location'].get('governorate'),
                'district': analysis_results['location'].get('district'),
                'nearby_services': analysis_results['location'].get('nearby_services', [])
            }
        
        return context
    
    def _process_with_ai(self,
                        multimodal_input: MultimodalInput,
                        enhanced_context: Dict,
                        user_id: int) -> Dict:
        """Process through existing AI orchestrator"""
        # Use text from multimodal input
        text = multimodal_input.text or self._generate_contextual_text(enhanced_context)
        
        # Process through AI orchestrator
        response = self.ai_orchestrator.process_advanced_query(
            user_input=text,
            conversation_id=enhanced_context['conversation_id'],
            user_id=user_id,
            is_voice=multimodal_input.voice_data is not None
        )
        
        return response
    
    def _generate_contextual_text(self, context: Dict) -> str:
        """Generate contextual text when no explicit text provided"""
        parts = []
        
        if context.get('has_images'):
            parts.append("المستخدم رفع صورة عقار")
        
        if context.get('has_documents'):
            parts.append("المستخدم رفع مستند")
        
        if context.get('has_location'):
            parts.append("المستخدم حدد موقعًا")
        
        if parts:
            return " ".join(parts) + ". كيف أستطيع مساعدتك؟"
        
        return "مرحباً، كيف أستطيع مساعدتك؟"
    
    def _verify_multimodal_response(self,
                                   ai_response: Dict,
                                   analysis_results: Dict,
                                   context: Dict) -> Dict:
        """Verify AI response with multimodal evidence"""
        # Get tool results from AI response
        tool_results = ai_response.get('tool_results', {})
        
        # Add multimodal evidence to tool results
        if analysis_results['images']:
            tool_results['image_evidence'] = analysis_results['images']
        
        if analysis_results['documents']:
            tool_results['document_evidence'] = analysis_results['documents']
        
        if analysis_results['location']:
            tool_results['location_evidence'] = analysis_results['location']
        
        # Verify response
        verified = self.evidence_system.verify_response(
            ai_response.get('text', ''),
            tool_results,
            context
        )
        
        return verified.to_dict()
    
    def _build_final_response(self,
                            verified_response: Dict,
                            analysis_results: Dict,
                            stored_assets: Dict) -> Dict:
        """Build final comprehensive response"""
        final_response = {
            'text': verified_response.get('verified_response'),
            'confidence': verified_response.get('overall_confidence'),
            'confidence_level': verified_response.get('confidence_level'),
            'evidence_summary': verified_response.get('evidence_summary'),
            'warnings': verified_response.get('warnings', []),
            'multimodal_analysis': analysis_results,
            'stored_assets': {
                asset_id: asset.to_dict()
                for asset_id, asset in stored_assets.items()
            },
            'metadata': {
                'input_type': analysis_results.get('timestamp'),
                'image_count': len(analysis_results.get('images', [])),
                'document_count': len(analysis_results.get('documents', [])),
                'has_location': analysis_results.get('location') is not None
            }
        }
        
        return final_response
    
    def _create_error_response(self, error: str) -> Dict:
        """Create error response"""
        return {
            'text': f"حدث خطأ أثناء معالجة طلبك: {error}",
            'confidence': 0.1,
            'confidence_level': 'very_low',
            'error': error,
            'multimodal_analysis': None,
            'stored_assets': {}
        }
    
    def process_image_similarity_search(self,
                                      query_image: ImageData,
                                      property_data: List[Dict],
                                      constraints: Dict = None) -> Dict:
        """
        Process image similarity search
        Find properties visually similar to query image
        """
        try:
            # Analyze query image
            observations, quality = self.image_analyzer.analyze_property_image(query_image)
            
            # Get similar images from properties
            # This would integrate with visual search
            similar_properties = []
            
            # Apply constraints
            if constraints:
                # Filter by constraints
                similar_properties = [
                    prop for prop in similar_properties
                    if self._matches_constraints(prop, constraints)
                ]
            
            return {
                'query_image_analysis': {
                    'observations': [obs.to_dict() for obs in observations],
                    'quality': quality.to_dict()
                },
                'similar_properties': similar_properties,
                'total_results': len(similar_properties)
            }
            
        except Exception as e:
            logger.error(f"Error in image similarity search: {str(e)}")
            return {'error': str(e)}
    
    def _matches_constraints(self, property_data: Dict, constraints: Dict) -> bool:
        """Check if property matches constraints"""
        # Simple constraint matching
        if constraints.get('governorate'):
            if property_data.get('governorate') != constraints['governorate']:
                return False
        
        if constraints.get('max_price'):
            if property_data.get('price', 0) > constraints['max_price']:
                return False
        
        return True
    
    def process_cv_job_matching(self,
                               cv_document: DocumentData,
                               job_listings: List[Dict]) -> Dict:
        """
        Process CV and match with job listings
        """
        try:
            # Analyze CV
            cv_profile = self.cv_system.analyze_cv(cv_document)
            
            # Match with jobs
            matches = self.cv_system.match_with_jobs(cv_profile, job_listings)
            
            # Generate explanations
            match_explanations = []
            for job, score in matches[:5]:  # Top 5
                explanation = self.cv_system.generate_match_explanation(cv_profile, job, score)
                match_explanations.append({
                    'job': job,
                    'match_score': score,
                    'explanation': explanation
                })
            
            return {
                'cv_profile': cv_profile.to_dict(),
                'matches': match_explanations,
                'total_matches': len(matches)
            }
            
        except Exception as e:
            logger.error(f"Error in CV job matching: {str(e)}")
            return {'error': str(e)}
    
    def process_document_qa(self,
                           document: DocumentData,
                           question: str) -> Dict:
        """
        Process document question answering
        """
        try:
            # Process document
            extraction = self.document_processor.process_document(document)
            
            # Answer question
            answer = self.document_processor.answer_document_question(extraction, question)
            
            return {
                'answer': answer,
                'document_id': document.document_id,
                'extraction_confidence': extraction.extraction_confidence
            }
            
        except Exception as e:
            logger.error(f"Error in document QA: {str(e)}")
            return {'error': str(e)}
    
    def get_pipeline_statistics(self) -> Dict:
        """Get pipeline statistics"""
        return {
            'asset_storage': self.asset_storage.get_storage_statistics(),
            'multimodal_memory': self.multimodal_memory.get_memory_statistics(),
            'semantic_memory': self.multimodal_memory.semantic_memory.get_memory_statistics()
        }


# Global instance
unified_multimodal_pipeline = UnifiedMultimodalAIPipeline()