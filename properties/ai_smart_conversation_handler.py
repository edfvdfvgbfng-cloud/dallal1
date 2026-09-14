"""
AI Smart Conversation Manager
Manages conversation state for the smart AI assistant
Handles gradual information collection and context tracking
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
from django.core.cache import cache

from .ai_smart_intent_detection import Intent, intent_detector
from .ai_smart_request_parser import ai_request_parser
from .ai_unified_search_service import ai_search_service

logger = logging.getLogger(__name__)


class SmartConversationState:
    """Represents the state of a smart AI conversation"""
    
    def __init__(self, conversation_id: str, user_id: Optional[int] = None):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.current_intent = None
        self.collected_filters = {}
        self.missing_fields = []
        self.conversation_history = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.awaiting_confirmation = False
        self.pending_action = None
        self.pending_data = None
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to conversation history"""
        self.conversation_history.append({
            'role': role,
            'content': content,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def update_filters(self, new_filters: Dict):
        """Update collected filters with new data"""
        self.collected_filters.update(new_filters)
        self.updated_at = datetime.now()
    
    def set_awaiting_confirmation(self, action: str, data: Dict):
        """Set conversation to await user confirmation"""
        self.awaiting_confirmation = True
        self.pending_action = action
        self.pending_data = data
        self.updated_at = datetime.now()
    
    def clear_confirmation(self):
        """Clear confirmation state"""
        self.awaiting_confirmation = False
        self.pending_action = None
        self.pending_data = None
        self.updated_at = datetime.now()
    
    def reset(self):
        """Reset conversation state"""
        self.current_intent = None
        self.collected_filters = {}
        self.missing_fields = []
        self.awaiting_confirmation = False
        self.pending_action = None
        self.pending_data = None
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'current_intent': self.current_intent,
            'collected_filters': self.collected_filters,
            'missing_fields': self.missing_fields,
            'conversation_history': self.conversation_history,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'awaiting_confirmation': self.awaiting_confirmation,
            'pending_action': self.pending_action,
            'pending_data': self.pending_data,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SmartConversationState':
        """Create instance from dictionary"""
        state = cls(data['conversation_id'], data.get('user_id'))
        state.current_intent = data.get('current_intent')
        state.collected_filters = data.get('collected_filters', {})
        state.missing_fields = data.get('missing_fields', [])
        state.conversation_history = data.get('conversation_history', [])
        state.created_at = datetime.fromisoformat(data['created_at'])
        state.updated_at = datetime.fromisoformat(data['updated_at'])
        state.awaiting_confirmation = data.get('awaiting_confirmation', False)
        state.pending_action = data.get('pending_action')
        state.pending_data = data.get('pending_data')
        return state


class SmartConversationManager:
    """
    Manages smart AI conversations
    Handles gradual information collection and context tracking
    """
    
    CACHE_TIMEOUT = 3600  # 1 hour
    
    def __init__(self):
        self.cache_prefix = 'smart_conversation_'
    
    def get_or_create_state(self, conversation_id: str, user_id: Optional[int] = None) -> SmartConversationState:
        """Get existing conversation state or create new one"""
        cache_key = f"{self.cache_prefix}{conversation_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return SmartConversationState.from_dict(cached_data)
        
        return SmartConversationState(conversation_id, user_id)
    
    def save_state(self, state: SmartConversationState):
        """Save conversation state to cache"""
        cache_key = f"{self.cache_prefix}{state.conversation_id}"
        cache.set(cache_key, state.to_dict(), self.CACHE_TIMEOUT)
    
    def process_message(self, message: str, conversation_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Process user message and generate appropriate response
        
        Args:
            message: User message
            conversation_id: Conversation ID
            user_id: User ID
            
        Returns:
            Dict containing:
            - response: AI response text
            - action: Suggested action (if any)
            - results: Search results (if any)
            - metadata: Additional metadata
        """
        # Get conversation state
        state = self.get_or_create_state(conversation_id, user_id)
        
        # Add user message to history
        state.add_message('user', message)
        
        # Check if awaiting confirmation
        if state.awaiting_confirmation:
            return self._handle_confirmation(state, message)
        
        # Check for clear conversation command
        if self._is_clear_command(message):
            state.reset()
            state.add_message('assistant', 'تم بدء محادثة جديدة. كيف يمكنني مساعدتك؟')
            self.save_state(state)
            return {
                'response': 'تم بدء محادثة جديدة. كيف يمكنني مساعدتك؟',
                'action': None,
                'results': None,
                'metadata': {'conversation_reset': True}
            }
        
        # Parse user request
        parsed = ai_request_parser.parse_request(message, user_id)
        
        # Update intent if detected
        if parsed['intent'] != Intent.GENERAL_QUESTION:
            state.current_intent = parsed['intent']
        
        # Update filters
        state.update_filters(parsed['filters'])
        
        # Update missing fields
        state.missing_fields = parsed['missing_fields']
        
        # Generate response based on state
        response_data = self._generate_response(state, parsed)
        
        # Add assistant response to history
        state.add_message('assistant', response_data['response'], response_data.get('metadata'))
        
        # Save state
        self.save_state(state)
        
        return response_data
    
    def _handle_confirmation(self, state: SmartConversationState, message: str) -> Dict[str, Any]:
        """Handle user confirmation response"""
        message_lower = message.lower().strip()
        
        # Check for positive confirmation
        if any(word in message_lower for word in ['نعم', 'أجل', 'متابعة', 'yes', 'ok', 'continue']):
            state.clear_confirmation()
            
            # Execute pending action
            if state.pending_action == 'create_listing':
                return self._execute_create_listing(state)
            elif state.pending_action == 'contact_broker':
                return self._execute_contact_broker(state)
            elif state.pending_action == 'save_search':
                return self._execute_save_search(state)
            
            # Default: perform search
            return self._perform_search(state)
        
        # Check for negative confirmation
        elif any(word in message_lower for word in ['لا', 'إلغاء', 'لا', 'cancel', 'no']):
            state.clear_confirmation()
            state.add_message('assistant', 'تم إلغاء العملية. هل تريد البحث عن شيء آخر؟')
            return {
                'response': 'تم إلغاء العملية. هل تريد البحث عن شيء آخر؟',
                'action': None,
                'results': None,
                'metadata': {'cancelled': True}
            }
        
        # Check for edit request
        elif any(word in message_lower for word in ['تعديل', 'تغيير', 'edit', 'change', 'modify']):
            state.clear_confirmation()
            state.add_message('assistant', 'حسناً، ما الذي تريد تعديله؟')
            return {
                'response': 'حسناً، ما الذي تريد تعديله؟',
                'action': 'edit',
                'results': None,
                'metadata': {'edit_mode': True}
            }
        
        # Unknown response
        return {
            'response': 'لم أفهم ردك. هل تريد المتابعة (نعم) أو الإلغاء (لا)؟',
            'action': None,
            'results': None,
            'metadata': {'awaiting_confirmation': True}
        }
    
    def _generate_response(self, state: SmartConversationState, parsed: Dict) -> Dict[str, Any]:
        """Generate appropriate response based on conversation state"""
        intent = parsed['intent']
        missing_fields = parsed['missing_fields']
        
        # Handle greetings
        if intent == Intent.GREETING:
            return {
                'response': 'أهلاً بك! 👋 أنا مساعدك الذكي. يمكنني مساعدتك في البحث عن عقارات، فنادق، وظائف، خدمات، والمزيد. كيف يمكنني مساعدتك اليوم؟',
                'action': None,
                'results': None,
                'metadata': {'intent': 'greeting'}
            }
        
        # Handle help
        if intent == Intent.HELP:
            return {
                'response': '''يمكنني مساعدتك في:
🏠 البحث عن عقارات للشراء أو الإيجار
🏨 البحث عن فنادق ومنتجعات
💼 البحث عن وظائف
🔧 البحث عن خدمات
🔨 البحث عن مزادات
🤝 التواصل مع الدلالين

فقط أخبرني بما تريد، وسأساعدك في العثور عليه!''',
                'action': None,
                'results': None,
                'metadata': {'intent': 'help'}
            }
        
        # Handle sell intent
        if intent == Intent.SELL_PROPERTY:
            return self._handle_sell_intent(state, parsed)
        
        # If there are missing fields, ask for them gradually
        if missing_fields:
            return self._ask_for_missing_field(state, missing_fields[0])
        
        # If all required fields are present, perform search
        return self._perform_search(state)
    
    def _handle_sell_intent(self, state: SmartConversationState, parsed: Dict) -> Dict[str, Any]:
        """Handle sell property intent"""
        missing_fields = parsed['missing_fields']
        
        if missing_fields:
            return self._ask_for_missing_field(state, missing_fields[0])
        
        # All information collected, ask for confirmation
        filters = state.collected_filters
        summary = self._generate_listing_summary(filters)
        
        state.set_awaiting_confirmation('create_listing', filters)
        
        return {
            'response': f'''حسناً، سأنشئ إعلان بيع عقار لك. إليك ملخص المعلومات:

{summary}

هل تريد المتابعة؟''',
            'action': 'confirm_create_listing',
            'results': None,
            'metadata': {
                'pending_action': 'create_listing',
                'listing_data': filters
            }
        }
    
    def _generate_listing_summary(self, filters: Dict) -> str:
        """Generate human-readable summary of listing data"""
        summary_lines = []
        
        if filters.get('property_type'):
            summary_lines.append(f"نوع العقار: {filters['property_type']}")
        
        if filters.get('location'):
            summary_lines.append(f"الموقع: {filters['location']}")
        
        if filters.get('area'):
            summary_lines.append(f"المساحة: {filters['area']} م²")
        
        if filters.get('rooms'):
            summary_lines.append(f"الغرف: {filters['rooms']}")
        
        if filters.get('price'):
            price = filters['price']
            value = price.get('value', 0)
            currency = price.get('currency', 'IQD')
            summary_lines.append(f"السعر: {value:,} {currency}")
        
        return '\n'.join(summary_lines) if summary_lines else 'المعلومات الأساسية'
    
    def _ask_for_missing_field(self, state: SmartConversationState, field: str) -> Dict[str, Any]:
        """Ask user for a specific missing field"""
        field_questions = {
            'location': '📍 في أي محافظة أو مدينة تريد؟',
            'price': '💰 ما هي ميزانيتك التقريبية؟',
            'property_type': '🏠 ما نوع العقار الذي تبحث عنه؟ (بيت، شقة، فيلا، إلخ)',
            'service_type': '🔧 ما نوع الخدمة التي تحتاجها؟',
            'job_title': '💼 ما نوع الوظيفة التي تبحث عنها؟',
        }
        
        question = field_questions.get(field, f'من فضلك، أخبرني بـ {field}')
        
        return {
            'response': question,
            'action': 'collect_info',
            'results': None,
            'metadata': {
                'collecting_field': field,
                'current_filters': state.collected_filters
            }
        }
    
    def _perform_search(self, state: SmartConversationState) -> Dict[str, Any]:
        """Perform search with collected filters"""
        intent = state.current_intent
        filters = state.collected_filters
        
        # Execute search
        search_results = ai_search_service.search(intent, filters, state.user_id)
        
        # Generate response
        if not search_results['results']:
            return {
                'response': 'لم أجد نتائج مطابقة حالياً. هل تريد أن أوسع البحث بتغيير بعض المعايير؟',
                'action': 'suggest_alternatives',
                'results': [],
                'metadata': search_results['metadata']
            }
        
        # Generate results summary
        result_count = len(search_results['results'])
        total_count = search_results['total_count']
        
        response = f'وجدت {result_count} نتيجة (من أصل {total_count}) 🎉\n\n'
        
        # Add top results summary
        for i, result in enumerate(search_results['results'][:3], 1):
            item = result['item']
            score = result['score']
            response += f'{i}. {self._get_item_title(item)} - مطابقة: {score:.0%}\n'
        
        if total_count > result_count:
            response += f'\nو {total_count - result_count} نتيجة أخرى...'
        
        return {
            'response': response,
            'action': 'show_results',
            'results': search_results['results'],
            'metadata': search_results['metadata']
        }
    
    def _get_item_title(self, item: Any) -> str:
        """Get display title for search result item"""
        try:
            if hasattr(item, 'title'):
                return item.title
            elif hasattr(item, 'name'):
                return item.name
            elif hasattr(item, 'display_title'):
                return item.display_title
            else:
                return str(item)
        except:
            return 'عنصر'
    
    def _execute_create_listing(self, state: SmartConversationState) -> Dict[str, Any]:
        """Execute create listing action"""
        # This would integrate with the actual listing creation system
        return {
            'response': 'تم تجهيز إعلان البيع. يرجى الانتقال إلى صفحة إنشاء الإعلان لإكمال التفاصيل وإضافة الصور.',
            'action': 'redirect_to_create',
            'results': None,
            'metadata': {
                'redirect_url': '/properties/create/',
                'listing_data': state.pending_data
            }
        }
    
    def _execute_contact_broker(self, state: SmartConversationState) -> Dict[str, Any]:
        """Execute contact broker action"""
        # This would integrate with the messaging system
        return {
            'response': 'تم فتح المحادثة مع الدلال.',
            'action': 'open_messaging',
            'results': None,
            'metadata': {
                'broker_id': state.pending_data.get('broker_id'),
                'conversation_url': f'/messages/{state.pending_data.get("broker_id")}/'
            }
        }
    
    def _execute_save_search(self, state: SmartConversationState) -> Dict[str, Any]:
        """Execute save search action"""
        # This would integrate with the saved search system
        return {
            'response': 'تم حفظ البحث. سأخطرك عندما تتوفر نتائج جديدة.',
            'action': 'search_saved',
            'results': None,
            'metadata': {
                'search_filters': state.collected_filters
            }
        }
    
    def _is_clear_command(self, message: str) -> bool:
        """Check if message is a clear conversation command"""
        clear_patterns = [
            r'ابدأ.*من.*جديد',
            r'محادثة.*جديدة',
            r'بدء.*جديد',
            r'clear',
            r'reset',
            r'new.*conversation',
        ]
        
        import re
        for pattern in clear_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        return False


# Global instance
smart_conversation_manager = SmartConversationManager()
