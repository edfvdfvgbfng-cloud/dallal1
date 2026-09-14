"""
AI Gateway
Single entry point for all AI requests from frontend
Routes requests to appropriate AI subsystems
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AIGateway:
    """
    Central gateway for all AI requests
    Routes to appropriate subsystems based on request type
    """
    
    def __init__(self):
        # Subsystems (lazy loaded to avoid circular imports)
        self._advanced_orchestrator = None
        self._market_orchestrator = None
        self._autonomous_orchestrator = None
        self._multimodal_system = None
        self._proactive_system = None
        self._conversation_state_manager = None
        self._smart_conversation_manager = None
    
    def _get_advanced_orchestrator(self):
        """Lazy load advanced orchestrator"""
        if self._advanced_orchestrator is None:
            from .ai_advanced_orchestrator import advanced_ai_orchestrator
            self._advanced_orchestrator = advanced_ai_orchestrator
        return self._advanced_orchestrator
    
    def _get_market_orchestrator(self):
        """Lazy load market orchestrator"""
        if self._market_orchestrator is None:
            from .ai_market_orchestrator import market_intelligence_orchestrator
            self._market_orchestrator = market_intelligence_orchestrator
        return self._market_orchestrator
    
    def _get_autonomous_orchestrator(self):
        """Lazy load autonomous orchestrator"""
        if self._autonomous_orchestrator is None:
            from .ai_autonomous_orchestrator import autonomous_agent_orchestrator
            self._autonomous_orchestrator = autonomous_agent_orchestrator
        return self._autonomous_orchestrator
    
    def _get_multimodal_system(self):
        """Lazy load multimodal system"""
        if self._multimodal_system is None:
            from .ai_unified_multimodal import unified_multimodal_system
            self._multimodal_system = unified_multimodal_system
        return self._multimodal_system
    
    def _get_proactive_system(self):
        """Lazy load proactive system"""
        if self._proactive_system is None:
            from .ai_proactive_notifications import proactive_notification_system
            self._proactive_system = proactive_notification_system
        return self._proactive_system
    
    def _get_conversation_state_manager(self):
        """Lazy load conversation state manager"""
        if self._conversation_state_manager is None:
            from .ai_conversation_state_manager import conversation_state_manager
            self._conversation_state_manager = conversation_state_manager
        return self._conversation_state_manager
    
    def _get_smart_conversation_manager(self):
        """Lazy load smart conversation manager"""
        if self._smart_conversation_manager is None:
            from .ai_smart_conversation_handler import smart_conversation_manager
            self._smart_conversation_manager = smart_conversation_manager
        return self._smart_conversation_manager
    
    def process_request(self, request_type: str, user_id: int, conversation_id: str, 
                       input_data: Dict, context: Dict = None) -> Dict:
        """
        Process AI request through appropriate subsystem
        
        Args:
            request_type: Type of request (chat, multimodal, market, autonomous, proactive)
            user_id: User ID
            conversation_id: Conversation ID
            input_data: Input data
            context: Additional context
            
        Returns:
            Response from appropriate subsystem
        """
        try:
            # Get or create conversation state
            state_manager = self._get_conversation_state_manager()
            state = state_manager.get_or_create_state(conversation_id, user_id)
            
            # Route based on request type
            if request_type == "chat":
                return self._process_chat_request(user_id, conversation_id, input_data, context, state)
            elif request_type == "smart_assistant":
                return self._process_smart_assistant_request(user_id, conversation_id, input_data, context, state)
            elif request_type == "multimodal":
                return self._process_multimodal_request(user_id, conversation_id, input_data, context, state)
            elif request_type == "market":
                return self._process_market_request(user_id, conversation_id, input_data, context, state)
            elif request_type == "autonomous":
                return self._process_autonomous_request(user_id, conversation_id, input_data, context, state)
            elif request_type == "proactive":
                return self._process_proactive_request(user_id, conversation_id, input_data, context, state)
            else:
                return {
                    'success': False,
                    'error': f'Unknown request type: {request_type}'
                }
                
        except Exception as e:
            logger.error(f"Error processing AI request: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_chat_request(self, user_id: int, conversation_id: str, 
                              input_data: Dict, context: Dict, state: Dict) -> Dict:
        """Process chat request through advanced orchestrator"""
        orchestrator = self._get_advanced_orchestrator()
        
        user_input = input_data.get('input', '')
        
        # Process through advanced orchestrator
        response = orchestrator.process_user_message(
            user_id=user_id,
            conversation_id=conversation_id,
            user_input=user_input,
            context=context or {}
        )
        
        # Update conversation state
        state_manager = self._get_conversation_state_manager()
        state_manager.update_state(conversation_id, {
            'last_input': user_input,
            'last_response': response.get('response', ''),
            'intent': response.get('intent'),
            'entities': response.get('entities', {})
        })
        
        return {
            'success': True,
            'response': response.get('response', ''),
            'intent': response.get('intent'),
            'entities': response.get('entities', {}),
            'state': state
        }
    
    def _process_smart_assistant_request(self, user_id: int, conversation_id: str, 
                                        input_data: Dict, context: Dict, state: Dict) -> Dict:
        """Process smart assistant request with intent detection and search"""
        smart_manager = self._get_smart_conversation_manager()
        
        user_input = input_data.get('input', '')
        
        # Process through smart conversation manager
        response = smart_manager.process_message(
            message=user_input,
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        # Update conversation state
        state_manager = self._get_conversation_state_manager()
        state_manager.update_state(conversation_id, {
            'last_input': user_input,
            'last_response': response.get('response', ''),
            'intent': response.get('metadata', {}).get('intent'),
            'action': response.get('action'),
            'results_count': len(response.get('results', []))
        })
        
        return {
            'success': True,
            'response': response.get('response', ''),
            'action': response.get('action'),
            'results': response.get('results'),
            'rendered_results': response.get('rendered_results'),
            'metadata': response.get('metadata'),
            'state': state
        }
    
    def _process_multimodal_request(self, user_id: int, conversation_id: str,
                                    input_data: Dict, context: Dict, state: Dict) -> Dict:
        """Process multimodal request"""
        system = self._get_multimodal_system()
        
        input_type = input_data.get('input_type', 'text')
        content = input_data.get('content')
        
        # Process through multimodal system
        result = system.process_input(
            input_type=input_type,
            content=content,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        return {
            'success': True,
            'result': result,
            'state': state
        }
    
    def _process_market_request(self, user_id: int, conversation_id: str,
                               input_data: Dict, context: Dict, state: Dict) -> Dict:
        """Process market intelligence request"""
        orchestrator = self._get_market_orchestrator()
        
        query = input_data.get('query', '')
        
        # Process through market orchestrator
        response = orchestrator.process_market_query(
            user_input=query,
            user_id=user_id,
            context=context or {}
        )
        
        return {
            'success': True,
            'response': response,
            'state': state
        }
    
    def _process_autonomous_request(self, user_id: int, conversation_id: str,
                                    input_data: Dict, context: Dict, state: Dict) -> Dict:
        """Process autonomous agent request"""
        orchestrator = self._get_autonomous_orchestrator()
        
        user_input = input_data.get('input', '')
        
        # Process through autonomous orchestrator
        response = orchestrator.process_user_request(
            user_id=user_id,
            conversation_id=conversation_id,
            user_input=user_input,
            context=context or {}
        )
        
        return {
            'success': True,
            'response': response,
            'state': state
        }
    
    def _process_proactive_request(self, user_id: int, conversation_id: str,
                                    input_data: Dict, context: Dict, state: Dict) -> Dict:
        """Process proactive notification request"""
        system = self._get_proactive_system()
        
        event_type = input_data.get('event_type')
        event_data = input_data.get('event_data', {})
        
        # Process event
        notification = system.process_event(
            event_type=event_type,
            user_id=user_id,
            event_data=event_data,
            context=context or {}
        )
        
        return {
            'success': True,
            'notification': notification.to_dict() if notification else None,
            'state': state
        }
    
    def get_conversation_state(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation state"""
        state_manager = self._get_conversation_state_manager()
        return state_manager.get_state(conversation_id)
    
    def clear_conversation_state(self, conversation_id: str):
        """Clear conversation state"""
        state_manager = self._get_conversation_state_manager()
        state_manager.clear_state(conversation_id)


# Global instance
ai_gateway = AIGateway()