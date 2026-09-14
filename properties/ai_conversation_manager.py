"""
Conversation Manager - Main Orchestrator
Integrates all AI components for intelligent conversation handling
Now includes AI Agent integration for tool calling and advanced workflows
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from .ai_nlp_layer import nlp_manager
from .ai_intent_classifier import intent_classifier
from .ai_entity_extraction import entity_extractor, entity_normalizer
from .ai_context_engine import context_manager, question_generator, flow_manager
from .ai_arabic_normalizer import arabic_normalizer, number_parser
from .ai_semantic_search import hybrid_search_engine, conversation_learner
from .ai_agent_loop import ai_agent
from .ai_agent_tools import tool_registry
from .ai_learning_pipeline import data_collector, data_anonymizer, health_checker
from .ai_voice_provider import voice_analytics, voice_command_handler
from .ai_training_models import VoiceInteractionLog
from .models import Property, Broker, HotelPage, ServiceProviderPage, BuildingAdvertisement
from django.contrib.auth.models import User

logger = logging.getLogger('properties')


class ConversationManager:
    """
    Main conversation manager that orchestrates all AI components
    Now integrates AI Agent for advanced tool calling and workflow orchestration
    """
    
    def __init__(self):
        self.nlp_model = nlp_manager.get_current_model()
        self.context_manager = context_manager
        self.question_generator = question_generator
        self.flow_manager = flow_manager
        self.arabic_normalizer = arabic_normalizer
        self.number_parser = number_parser
        self.hybrid_search_engine = hybrid_search_engine
        self.conversation_learner = conversation_learner
        self.ai_agent = ai_agent
        self.tool_registry = tool_registry
        self.data_collector = data_collector
        self.data_anonymizer = data_anonymizer
        self.voice_analytics = voice_analytics
        self.voice_command_handler = voice_command_handler
        self.health_checker = health_checker
        self.confidence_threshold = 0.70
        self.use_agent_mode = True  # Enable AI Agent mode by default
        self.collect_training_data = True  # Enable data collection
        self.voice_enabled = True  # Enable voice features
    
    def process_message(self, message: str, conversation_id: str, user: Optional[User] = None, is_voice: bool = False) -> Dict[str, Any]:
        """
        Process user message and generate intelligent response
        Now uses AI Agent for advanced tool calling and workflow orchestration
        Also collects training data when enabled and tracks voice interactions
        
        Args:
            message: User input message
            conversation_id: Unique conversation identifier
            user: Current user (optional)
            is_voice: Whether the input was voice
            
        Returns:
            Complete response with action, state, and results
        """
        try:
            # Track voice interaction
            if is_voice:
                self.voice_analytics.voice_conversations += 1
                
                # Log voice interaction
                voice_log = VoiceInteractionLog.objects.create(
                    duration_ms=0,  # Will be updated if provided from frontend
                    recognized_text=message,
                    stt_success=True,
                    stt_language='ar-SA',
                    conversation_id=conversation_id,
                    user=user
                )
            
            # Preprocess message with learning pipeline
            preprocessed = self._preprocess_message(message)
            
            # Use AI Agent for advanced processing
            if self.use_agent_mode:
                response = self.ai_agent.process_message(preprocessed['normalized_text'], conversation_id, user)
                
                # Apply entity normalization to response
                if response.get('state', {}).get('entities'):
                    response['state']['entities'] = self._normalize_entities(response['state']['entities'])
                
                # Collect training data if enabled
                if self.collect_training_data and response.get('success'):
                    self._collect_training_data_from_response(preprocessed['normalized_text'], response, conversation_id, user)
                
                # Track voice command if applicable
                if is_voice:
                    command = self.voice_command_handler.recognize_command(preprocessed['normalized_text'])
                    if command:
                        self.voice_analytics.record_voice_command(command)
                        # Update voice log with command
                        if is_voice:
                            voice_log.command_recognized = command
                            voice_log.save()
                
                # Update voice log with response
                if is_voice:
                    voice_log.response_text = response.get('response', '')
                    voice_log.intent_detected = response.get('state', {}).get('intent', '')
                    voice_log.entities_extracted = response.get('state', {}).get('entities', {})
                    voice_log.save()
                
                return response
            
            # Fallback to original processing for simple cases
            return self._process_message_legacy(preprocessed['normalized_text'], conversation_id)
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                'success': False,
                'error': 'حدث خطأ في معالجة الرسالة',
                'response': 'عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.'
            }
    
    def _preprocess_message(self, message: str) -> Dict[str, Any]:
        """Preprocess message with learning pipeline components"""
        try:
            # Normalize text
            normalized_text = self.arabic_normalizer.normalize_text(message)
            
            # Parse money expressions
            money_data = self.data_collector.money_parser.parse_money_expression(message)
            
            # Parse time expressions
            time_data = self.data_collector.time_parser.parse_time_expression(message)
            
            return {
                'original_text': message,
                'normalized_text': normalized_text,
                'money_data': money_data,
                'time_data': time_data
            }
        except Exception as e:
            logger.error(f"Error preprocessing message: {str(e)}")
            return {
                'original_text': message,
                'normalized_text': message,
                'money_data': {},
                'time_data': {}
            }
    
    def _normalize_entities(self, entities: Dict) -> Dict:
        """Normalize entities using learning pipeline"""
        try:
            entity_normalizer = self.data_collector.entity_normalizer
            normalized_entities = {}
            
            for entity_type, value in entities.items():
                if isinstance(value, str):
                    normalized_value = entity_normalizer.normalize_entity(entity_type, value)
                    normalized_entities[entity_type] = normalized_value
                else:
                    normalized_entities[entity_type] = value
            
            return normalized_entities
        except Exception as e:
            logger.error(f"Error normalizing entities: {str(e)}")
            return entities
    
    def _collect_training_data_from_response(self, message: str, response: Dict, 
                                          conversation_id: str, user: Optional[User] = None):
        """Collect training data from successful responses"""
        try:
            # Get understanding from agent if available
            if hasattr(self.ai_agent, 'short_term_memory'):
                intent = self.ai_agent.short_term_memory.get('last_intent')
                entities = self.ai_agent.short_term_memory.get('last_entities')
                confidence = self.ai_agent.short_term_memory.get('last_confidence', 0.5)
            else:
                # Fallback to basic detection
                from .ai_intent_classifier import intent_classifier
                from .ai_entity_extraction import entity_extractor
                from .ai_arabic_normalizer import arabic_normalizer
                
                normalized = arabic_normalizer.normalize_text(message)
                intent_result = intent_classifier.classify_intent(normalized)
                intent = intent_result.category.value
                confidence = intent_result.confidence
                entities = {}  # Placeholder for entities extraction
            
            # Collect training example
            if intent and intent != 'unknown':
                try:
                    self.data_collector.collect_training_example(
                        message, intent, entities, confidence,
                        source='conversation'
                    )
                except Exception as e:
                    logger.error(f"Error collecting training example: {str(e)}")

            
            # Collect training example
            if intent and intent != 'unknown':
                try:
                    self.data_collector.collect_training_example(
                        message, intent, entities, confidence,
                        source='conversation'
                    )
                except Exception as e:
                    logger.error(f"Error collecting training example: {str(e)}")
            
            # Record conversation data
            self.data_collector.collect_conversation_data(conversation_id, user)
            
        except Exception as e:
            logger.error(f"Error collecting training data: {str(e)}")
    
    def handle_confirmation(self, conversation_id: str, confirmed: bool, user: Optional[User] = None) -> Dict[str, Any]:
        """Handle user confirmation response"""
        return self.ai_agent.handle_confirmation(conversation_id, confirmed, user)
    
    def record_feedback(self, conversation_id: str, feedback: str, message: str):
        """Record user feedback for learning"""
        context = self.context_manager.get_context(conversation_id)
        
        # Record in conversation learner
        feedback_type = 'positive' if feedback in ['نعم', 'جيد', 'ممتاز', 'حلو', 'تمام'] else 'negative'
        self.conversation_learner.record_feedback(conversation_id, feedback_type, message, 'اخر رسالة من المساعد')
        
        # Add to context
        context.add_user_correction('response_quality', message, feedback)
        
        logger.info(f"Recorded feedback: {feedback} for message: {message}")
        
        # If negative feedback, ask for clarification
        if feedback_type == 'negative':
            return {
                'success': True,
                'response': 'عذراً على ذلك، شنو الشي اللي ما كان صحيح؟ حتى نحسن في المرة الجاية.',
                'action': 'ask_clarification'
            }
        
        return {
            'success': True,
            'response': 'شكراً لملاحظاتك! سأساعدك بشكل أفضل المرة الجاية.',
            'action': 'acknowledge_feedback'
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get conversation manager statistics"""
        return {
            'active_conversations': self.context_manager.get_active_contexts_count(),
            'intent_stats': intent_classifier.get_classification_statistics(),
            'entity_stats': entity_extractor.get_extraction_statistics(),
            'agent_stats': self.ai_agent.get_agent_statistics(),
            'tool_stats': self._get_tool_statistics()
        }
    
    def _get_tool_statistics(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        tool_stats = {}
        for tool_name, tool in self.tool_registry.get_all_tools().items():
            tool_stats[tool_name] = {
                'usage_count': tool.usage_count,
                'error_count': tool.error_count,
                'success_rate': (tool.usage_count - tool.error_count) / tool.usage_count if tool.usage_count > 0 else 0
            }
        return tool_stats


# Global conversation manager instance
conversation_manager = ConversationManager()