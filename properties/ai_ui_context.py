"""
UI Context Provider
Provides safe, limited UI context to AI agent
"""

from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UIContext:
    """Safe UI context for AI agent"""
    current_page: str = None
    current_route: str = None
    selected_property_id: Optional[int] = None
    selected_job_id: Optional[int] = None
    current_form: Optional[str] = None
    visible_filters: Dict = None
    active_modal: Optional[str] = None
    user_intent: Optional[str] = None
    ui_state: str = "loaded"  # loading, loaded, empty, error, modal_open, form_active
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'current_page': self.current_page,
            'current_route': self.current_route,
            'selected_property_id': self.selected_property_id,
            'selected_job_id': self.selected_job_id,
            'current_form': self.current_form,
            'visible_filters': self.visible_filters or {},
            'active_modal': self.active_modal,
            'user_intent': self.user_intent,
            'ui_state': self.ui_state
        }


class UIContextProvider:
    """
    Provides safe, limited UI context to AI agent
    Never exposes full DOM or sensitive data
    """
    
    def __init__(self):
        self.contexts: Dict[str, UIContext] = {}
        self.allowed_pages = [
            'home', 'properties', 'property_detail', 'jobs', 'job_detail',
            'sell', 'agent_application', 'profile', 'search'
        ]
        self.allowed_forms = [
            'property_listing', 'job_application', 'agent_application', 'user_profile'
        ]
    
    def create_context(self,
                      session_id: str,
                      current_page: str,
                      current_route: str,
                      **kwargs) -> UIContext:
        """
        Create a UI context for a session
        
        Args:
            session_id: Session ID
            current_page: Current page name
            current_route: Current route
            **kwargs: Additional context data
            
        Returns:
            Created UI context
        """
        # Validate page
        if current_page not in self.allowed_pages:
            logger.warning(f"Page {current_page} not in allowed pages")
            current_page = 'home'
        
        context = UIContext(
            current_page=current_page,
            current_route=current_route,
            selected_property_id=kwargs.get('selected_property_id'),
            selected_job_id=kwargs.get('selected_job_id'),
            current_form=kwargs.get('current_form'),
            visible_filters=kwargs.get('visible_filters', {}),
            active_modal=kwargs.get('active_modal'),
            user_intent=kwargs.get('user_intent'),
            ui_state=kwargs.get('ui_state', 'loaded')
        )
        
        # Validate form
        if context.current_form and context.current_form not in self.allowed_forms:
            context.current_form = None
        
        self.contexts[session_id] = context
        logger.info(f"Created UI context for session {session_id}")
        return context
    
    def get_context(self, session_id: str) -> Optional[UIContext]:
        """Get UI context for a session"""
        return self.contexts.get(session_id)
    
    def update_context(self, session_id: str, updates: Dict):
        """Update UI context"""
        if session_id in self.contexts:
            context = self.contexts[session_id]
            for key, value in updates.items():
                if hasattr(context, key):
                    setattr(context, key, value)
            logger.info(f"Updated UI context for session {session_id}")
    
    def delete_context(self, session_id: str):
        """Delete UI context"""
        if session_id in self.contexts:
            del self.contexts[session_id]
            logger.info(f"Deleted UI context for session {session_id}")
    
    def is_form_active(self, session_id: str) -> bool:
        """Check if a form is currently active"""
        context = self.get_context(session_id)
        return context is not None and context.current_form is not None
    
    def get_form_state(self, session_id: str) -> Optional[Dict]:
        """Get current form state"""
        context = self.get_context(session_id)
        if context and context.current_form:
            return {
                'form_type': context.current_form,
                'visible_filters': context.visible_filters,
                'ui_state': context.ui_state
            }
        return None


# Global instance
ui_context_provider = UIContextProvider()