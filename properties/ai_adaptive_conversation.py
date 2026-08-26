"""
Adaptive Conversation Logic
Adapts conversation style based on user preferences and context
"""

from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

from .ai_user_preferences import CommunicationStyle

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Context for adaptive conversation"""
    user_id: int = None
    session_id: str = None
    style: CommunicationStyle = None
    language: str = "ar"
    urgency: str = "normal"  # quick, normal, detailed
    complexity: str = "normal"  # simple, normal, complex
    history: List[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'session_id': self.session_id,
            'style': self.style.value,
            'language': self.language,
            'urgency': self.urgency,
            'complexity': self.complexity,
            'history': self.history or []
        }


class AdaptiveConversationLogic:
    """
    Adapts conversation style based on user preferences and context
    Detects urgency and adjusts response accordingly
    """
    
    def __init__(self):
        self.user_contexts: Dict[str, ConversationContext] = {}
    
    def create_context(self,
                      user_id: int,
                      session_id: str,
                      style: CommunicationStyle = CommunicationStyle.MIXED,
                      language: str = "ar") -> ConversationContext:
        """
        Create a conversation context
        
        Args:
            user_id: User ID
            session_id: Session ID
            style: Communication style
            language: Language
            
        Returns:
            Created context
        """
        context = ConversationContext(
            user_id=user_id,
            session_id=session_id,
            style=style,
            language=language,
            urgency="normal",
            complexity="normal",
            history=[]
        )
        
        self.user_contexts[session_id] = context
        logger.info(f"Created conversation context for session {session_id}")
        return context
    
    def detect_urgency(self, user_input: str) -> str:
        """
        Detect urgency from user input
        
        Args:
            user_input: User's input
            
        Returns:
            Urgency level (quick, normal, detailed)
        """
        urgency_keywords = {
            'quick': ['بسرعة', 'عاجل', 'فورا', 'حالا', 'سريع'],
            'detailed': ['فصل', 'تفاصيل', 'اشرح', 'كيف', 'لماذا', 'وين']
        }
        
        for keyword in urgency_keywords['quick']:
            if keyword in user_input:
                return 'quick'
        
        for keyword in urgency_keywords['detailed']:
            if keyword in user_input:
                return 'detailed'
        
        return 'normal'
    
    def adapt_response(self,
                      context: ConversationContext,
                      user_input: str,
                      base_response: str) -> str:
        """
        Adapt response based on context and user input
        
        Args:
            context: Conversation context
            user_input: User's input
            base_response: Base response to adapt
            
        Returns:
            Adapted response
        """
        # Detect urgency
        urgency = self.detect_urgency(user_input)
        context.urgency = urgency
        
        # Adapt based on style
        if context.style == CommunicationStyle.CONCISE:
            base_response = self._make_concise(base_response)
        elif context.style == CommunicationStyle.DETAILED:
            base_response = self._make_detailed(base_response)
        elif context.style == CommunicationStyle.IRAQI_ARABIC:
            base_response = self._make_iraqi(base_response)
        
        # Adapt based on urgency
        if urgency == 'quick':
            base_response = self._make_quick(base_response)
        elif urgency == 'detailed':
            base_response = self._make_detailed(base_response)
        
        return base_response
    
    def _make_concise(self, response: str) -> str:
        """Make response more concise"""
        # Remove filler words and unnecessary details
        concise_patterns = [
            (r'بشكل عام', ''),
            (r'في الواقع', ''),
            (r'من المهم أن نذكر', ''),
            (r'كما نعلم', '')
        ]
        
        for pattern, replacement in concise_patterns:
            response = response.replace(pattern, replacement)
        
        return response.strip()
    
    def _make_detailed(self, response: str) -> str:
        """Make response more detailed"""
        # Add explanation if response is short
        if len(response) < 100:
            response += " هل تريد مزيد من التفاصيل؟"
        
        return response
    
    def _make_quick(self, response: str) -> str:
        """Make response quick and direct"""
        # Get to the point quickly
        sentences = response.split('.')
        if len(sentences) > 2:
            response = sentences[0] + '.'
        
        return response.strip()
    
    def _make_iraqi(self, response: str) -> str:
        """Adapt to Iraqi dialect"""
        iraqi_mappings = {
            'أريد': 'أريد',
            'هل': 'شو',
            'نعم': 'هاي',
            'لا': 'لا',
            'كيف': 'شلون',
            'ماذا': 'شنو',
            'لماذا': 'ليش',
            'أين': 'وين',
            'متى': 'متى',
            'كم': 'شكد'
        }
        
        for formal, informal in iraqi_mappings.items():
            response = response.replace(formal, informal)
        
        return response
    
    def update_style(self, session_id: str, style: CommunicationStyle):
        """Update conversation style for a session"""
        if session_id in self.user_contexts:
            self.user_contexts[session_id].style = style
            logger.info(f"Updated style for session {session_id} to {style.value}")
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context for a session"""
        return self.user_contexts.get(session_id)
    
    def add_to_history(self, session_id: str, user_input: str, response: str):
        """Add interaction to history"""
        if session_id in self.user_contexts:
            self.user_contexts[session_id].history.append({
                'user_input': user_input,
                'response': response,
                'timestamp': None  # Would be datetime
            })
            
            # Keep only last 20 interactions
            if len(self.user_contexts[session_id].history) > 20:
                self.user_contexts[session_id].history = self.user_contexts[session_id].history[-20:]


# Global instance
adaptive_conversation_logic = AdaptiveConversationLogic()