"""
Context Engine - Conversation Context Management
Handles conversation state, context awareness, and information tracking
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.core.cache import cache
import json

logger = logging.getLogger('properties')


class ConversationContext:
    """
    Manages conversation context and state
    Tracks user information across multiple turns
    """
    
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.context = self._load_context()
        self.max_context_age = timedelta(hours=2)  # Context expires after 2 hours
    
    def _load_context(self) -> Dict:
        """Load conversation context from cache or create new"""
        cached_context = cache.get(f"conversation_context_{self.conversation_id}")
        if cached_context:
            return cached_context
        
        return {
            'conversation_id': self.conversation_id,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'turn_count': 0,
            'intent': None,
            'entities': {},
            'previous_intents': [],
            'previous_entities': [],
            'user_corrections': [],
            'missing_fields': [],
            'search_history': [],
            'user_preferences': {},
            'conversation_state': 'active'
        }
    
    def _save_context(self):
        """Save conversation context to cache"""
        self.context['last_updated'] = datetime.now().isoformat()
        cache.set(
            f"conversation_context_{self.conversation_id}",
            self.context,
            timeout=int(self.max_context_age.total_seconds())
        )
    
    def update_intent(self, intent: str, confidence: float):
        """Update current intent with confidence"""
        # Store previous intent
        if self.context['intent']:
            self.context['previous_intents'].append({
                'intent': self.context['intent'],
                'confidence': self.context.get('intent_confidence', 0.0),
                'turn': self.context['turn_count']
            })
        
        self.context['intent'] = intent
        self.context['intent_confidence'] = confidence
        self._save_context()
    
    def update_entities(self, entities: Dict[str, Any], replace: bool = False):
        """Update entities in context"""
        if replace:
            self.context['entities'] = entities
        else:
            # Merge with existing entities, new values take precedence
            self.context['entities'].update(entities)
        
        self._save_context()
    
    def add_user_correction(self, correction_type: str, original_value: str, corrected_value: str):
        """Record user correction for learning"""
        self.context['user_corrections'].append({
            'type': correction_type,
            'original': original_value,
            'corrected': corrected_value,
            'turn': self.context['turn_count'],
            'timestamp': datetime.now().isoformat()
        })
        self._save_context()
    
    def increment_turn(self):
        """Increment conversation turn counter"""
        self.context['turn_count'] += 1
        self._save_context()
    
    def add_search_history(self, search_params: Dict, results_count: int):
        """Add search to history"""
        self.context['search_history'].append({
            'params': search_params,
            'results_count': results_count,
            'turn': self.context['turn_count'],
            'timestamp': datetime.now().isoformat()
        })
        self._save_context()
    
    def update_user_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences"""
        self.context['user_preferences'].update(preferences)
        self._save_context()
    
    def get_missing_fields(self, required_fields: List[str]) -> List[str]:
        """Get list of missing required fields"""
        missing = []
        for field in required_fields:
            if field not in self.context['entities'] or not self.context['entities'][field]:
                missing.append(field)
        
        self.context['missing_fields'] = missing
        self._save_context()
        return missing
    
    def get_complete_context(self) -> Dict:
        """Get complete conversation context"""
        return self.context.copy()
    
    def get_relevant_entities(self, intent: str) -> Dict[str, Any]:
        """Get entities relevant to current intent"""
        # Filter entities based on intent relevance
        intent_entity_mapping = {
            'buy_property': ['property_type', 'governorate', 'district', 'area', 'budget', 'rooms'],
            'sell_property': ['property_type', 'governorate', 'district', 'area', 'budget'],
            'find_job': ['job_type', 'location', 'salary'],
            'find_hotel': ['location', 'room_type', 'duration'],
            'travel': ['destination', 'time_preference']
        }
        
        relevant_fields = intent_entity_mapping.get(intent, [])
        relevant_entities = {
            field: self.context['entities'].get(field) 
            for field in relevant_fields 
            if field in self.context['entities']
        }
        
        return relevant_entities
    
    def get_conversation_summary(self) -> str:
        """Get human-readable summary of conversation"""
        summary_parts = []
        
        if self.context['intent']:
            summary_parts.append(f"النية: {self.context['intent']}")
        
        if self.context['entities']:
            entity_summary = ", ".join([
                f"{k}: {v}" for k, v in self.context['entities'].items()
            ])
            summary_parts.append(f"المعلومات: {entity_summary}")
        
        summary_parts.append(f"عدد الأدوار: {self.context['turn_count']}")
        
        return " | ".join(summary_parts)
    
    def is_expired(self) -> bool:
        """Check if conversation context has expired"""
        last_updated = datetime.fromisoformat(self.context['last_updated'])
        return datetime.now() - last_updated > self.max_context_age
    
    def reset_context(self):
        """Reset conversation context"""
        self.context = self._load_context()
        self._save_context()
    
    def end_conversation(self):
        """Mark conversation as ended"""
        self.context['conversation_state'] = 'ended'
        self.context['ended_at'] = datetime.now().isoformat()
        self._save_context()


class ContextManager:
    """
    Manages multiple conversation contexts
    Provides factory for creating and managing contexts
    """
    
    def __init__(self):
        self.active_contexts = {}
    
    def get_context(self, conversation_id: str) -> ConversationContext:
        """Get or create conversation context"""
        if conversation_id not in self.active_contexts:
            self.active_contexts[conversation_id] = ConversationContext(conversation_id)
        
        context = self.active_contexts[conversation_id]
        
        # Check if expired
        if context.is_expired():
            context.reset_context()
        
        return context
    
    def end_context(self, conversation_id: str):
        """End a conversation context"""
        if conversation_id in self.active_contexts:
            self.active_contexts[conversation_id].end_conversation()
            del self.active_contexts[conversation_id]
    
    def get_active_contexts_count(self) -> int:
        """Get number of active contexts"""
        return len(self.active_contexts)
    
    def cleanup_expired_contexts(self):
        """Clean up expired conversation contexts"""
        expired_ids = [
            conv_id for conv_id, context in self.active_contexts.items()
            if context.is_expired()
        ]
        
        for conv_id in expired_ids:
            self.end_context(conv_id)
        
        logger.info(f"Cleaned up {len(expired_ids)} expired contexts")


class SmartQuestionGenerator:
    """
    Generates smart follow-up questions based on context and missing information
    Uses context awareness to ask only relevant questions
    """
    
    def __init__(self):
        self.question_templates = {
            'governorate': [
                "في أي محافظة تبحث؟",
                "أين تريد العقار؟",
                "الموقع المفضل لديك؟"
            ],
            'property_type': [
                "ما نوع العقار الذي تبحث عنه؟",
                "تفضل بيت، شقة، أم أرض؟",
                "أي نوع عقار تريد؟"
            ],
            'budget': [
                "ما هي ميزانيتك؟",
                "وشكد عندك من المال؟",
                "كم تريد أن تنفق؟"
            ],
            'area': [
                "كم مساحة العقار التي تريدها؟",
                "ما المساحة المطلوبة؟",
                "تحتاج مساحة كم؟"
            ],
            'district': [
                "في أي منطقة تبحث؟",
                "الحي المفضل لديك؟",
                "أي منطقة تفضل؟"
            ],
            'job_type': [
                "ما نوع الوظيفة التي تبحث عنها؟",
                "ما المجال المفضل لديك؟",
                "ما الخبرة التي لديك؟"
            ],
            'salary': [
                "ما الراتب المتوقع؟",
                "وشكد تريد بالراتب؟",
                "الراتب المطلوب؟"
            ],
            'location': [
                "في أي مدينة؟",
                "الموقع المفضل؟",
                "أين تريد العمل؟"
            ]
        }
        
        self.field_priority = {
            'buy_property': ['property_type', 'governorate', 'budget', 'area', 'district'],
            'sell_property': ['property_type', 'governorate', 'budget', 'area'],
            'find_job': ['job_type', 'location', 'salary'],
            'find_hotel': ['location', 'room_type', 'duration'],
            'travel': ['destination', 'time_preference']
        }
    
    def generate_next_question(self, context: ConversationContext, intent: str) -> Optional[str]:
        """
        Generate smart next question based on context
        
        Args:
            context: Conversation context
            intent: Current intent
            
        Returns:
            Next question string or None if no question needed
        """
        entities = context.get_complete_context()['entities']
        
        # Get required fields for current intent
        required_fields = self.field_priority.get(intent, [])
        
        # Find missing fields
        missing_fields = []
        for field in required_fields:
            if field not in entities or not entities[field]:
                missing_fields.append(field)
        
        if not missing_fields:
            return None  # All required information is present
        
        # Get the most important missing field
        next_field = missing_fields[0]
        
        # Generate question for that field
        question = self._generate_question_for_field(next_field, context)
        
        return question
    
    def _generate_question_for_field(self, field: str, context: ConversationContext) -> str:
        """Generate question for a specific field"""
        templates = self.question_templates.get(field, ["معلومات إضافية عن " + field])
        
        # Select random template
        import random
        question = random.choice(templates)
        
        # Add context if available
        if field == 'budget' and 'property_type' in context.context['entities']:
            prop_type = context.context['entities']['property_type']
            question = f"ما هي ميزانيتك للـ {prop_type}؟"
        
        return question
    
    def should_ask_question(self, context: ConversationContext, intent: str) -> bool:
        """
        Determine if we should ask a question or proceed with search
        
        Args:
            context: Conversation context
            intent: Current intent
            
        Returns:
            True if should ask question, False if should proceed
        """
        entities = context.get_complete_context()['entities']
        required_fields = self.field_priority.get(intent, [])
        
        # Check if we have minimum required information
        minimum_required = required_fields[:2]  # First 2 fields are minimum
        has_minimum = all(
            field in entities and entities[field] 
            for field in minimum_required
        )
        
        # If we have minimum info, we can proceed with search
        # Otherwise, ask for more information
        return not has_minimum


class ConversationFlowManager:
    """
    Manages conversation flow and state transitions
    Ensures smooth conversation progression
    """
    
    def __init__(self):
        self.flow_states = {
            'initial': 'initial',
            'collecting_info': 'collecting_info',
            'searching': 'searching',
            'presenting_results': 'presenting_results',
            'clarifying': 'clarifying',
            'completed': 'completed'
        }
    
    def determine_next_state(self, current_state: str, context: ConversationContext, intent: str) -> str:
        """
        Determine next state in conversation flow
        
        Args:
            current_state: Current conversation state
            context: Conversation context
            intent: Current intent
            
        Returns:
            Next state
        """
        if current_state == 'initial':
            if context.context['intent']:
                return 'collecting_info'
            else:
                return 'clarifying'
        
        elif current_state == 'collecting_info':
            # Check if we have enough information
            question_generator = SmartQuestionGenerator()
            if question_generator.should_ask_question(context, intent):
                return 'collecting_info'
            else:
                return 'searching'
        
        elif current_state == 'searching':
            return 'presenting_results'
        
        elif current_state == 'presenting_results':
            # Check if user wants to continue searching
            return 'completed'
        
        elif current_state == 'clarifying':
            if context.context['intent']:
                return 'collecting_info'
            else:
                return 'clarifying'
        
        elif current_state == 'completed':
            return 'initial'  # Ready for new conversation
        
        return current_state
    
    def get_state_description(self, state: str) -> str:
        """Get human-readable state description"""
        descriptions = {
            'initial': 'بداية المحادثة',
            'collecting_info': 'جمع المعلومات',
            'searching': 'البحث في البيانات',
            'presenting_results': 'عرض النتائج',
            'clarifying': 'توضيح النية',
            'completed': 'اكتملت المحادثة'
        }
        return descriptions.get(state, state)


# Global instances
context_manager = ContextManager()
question_generator = SmartQuestionGenerator()
flow_manager = ConversationFlowManager()