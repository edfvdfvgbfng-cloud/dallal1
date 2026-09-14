"""
AI UI Actions Integration
Allows AI to control UI elements safely through predefined actions
"""

from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class UIActionType(Enum):
    """Types of safe UI actions"""
    NAVIGATE = "navigate"
    APPLY_FILTER = "apply_filter"
    SORT_RESULTS = "sort_results"
    SELECT_RESULT = "select_result"
    OPEN_MODAL = "open_modal"
    CLOSE_MODAL = "close_modal"
    SCROLL_TO = "scroll_to"
    TOGGLE_ELEMENT = "toggle_element"
    UPDATE_STATE = "update_state"
    SUBMIT_FORM = "submit_form"


@dataclass
class UIAction:
    """Represents a safe UI action"""
    action_type: UIActionType
    parameters: Dict[str, Any]
    action_id: str = None
    target_element: str = None
    requires_confirmation: bool = False
    confirmation_message: str = None
    allowed: bool = True
    
    def __post_init__(self):
        if not self.action_id:
            import uuid
            self.action_id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'action_id': self.action_id,
            'action_type': self.action_type.value,
            'parameters': self.parameters,
            'target_element': self.target_element,
            'requires_confirmation': self.requires_confirmation,
            'confirmation_message': self.confirmation_message,
            'allowed': self.allowed
        }


class UIActionManager:
    """
    Manages safe UI actions that AI can execute
    Only predefined, approved actions are allowed
    """
    
    def __init__(self):
        self.allowed_actions = self._initialize_allowed_actions()
        self.action_history: List[Dict] = []
        self.action_handlers: Dict[UIActionType, Callable] = {}
        self._register_default_handlers()
    
    def create_action(self, 
                    action_type: UIActionType,
                    parameters: Dict,
                    target_element: str = None,
                    requires_confirmation: bool = False) -> UIAction:
        """
        Create a UI action
        
        Args:
            action_type: Type of action
            parameters: Action parameters
            target_element: Target UI element
            requires_confirmation: Whether user confirmation is needed
            
        Returns:
            UIAction object
        """
        action = UIAction(
            action_type=action_type,
            parameters=parameters,
            target_element=target_element,
            requires_confirmation=requires_confirmation
        )
        
        # Check if action is allowed
        if action_type not in self.allowed_actions:
            action.allowed = False
            logger.warning(f"Action type {action_type.value} not allowed")
        
        return action
    
    def execute_action(self, action: UIAction, user_id: int = None) -> Tuple[bool, Any]:
        """
        Execute a UI action
        
        Args:
            action: UIAction to execute
            user_id: User ID (for authorization)
            
        Returns:
            (success, result)
        """
        try:
            # Check if action is allowed
            if not action.allowed:
                return False, "Action not allowed"
            
            # Check if confirmation is required
            if action.requires_confirmation:
                return False, f"Confirmation required: {action.confirmation_message}"
            
            # Get handler for action type
            handler = self.action_handlers.get(action.action_type)
            if not handler:
                return False, f"No handler for action type {action.action_type.value}"
            
            # Execute action
            result = handler(action)
            
            # Log action
            self.action_history.append({
                'timestamp': self._get_timestamp(),
                'action_id': action.action_id,
                'action_type': action.action_type.value,
                'parameters': action.parameters,
                'target_element': action.target_element,
                'user_id': user_id,
                'success': True
            })
            
            logger.info(f"Executed action {action.action_id}: {action.action_type.value}")
            return True, result
            
        except Exception as e:
            logger.error(f"Error executing action {action.action_id}: {str(e)}")
            self.action_history.append({
                'timestamp': self._get_timestamp(),
                'action_id': action.action_id,
                'action_type': action.action_type.value,
                'parameters': action.parameters,
                'user_id': user_id,
                'success': False,
                'error': str(e)
            })
            return False, str(e)
    
    def register_handler(self, action_type: UIActionType, handler: Callable):
        """Register a custom handler for an action type"""
        self.action_handlers[action_type] = handler
        logger.info(f"Registered handler for action type: {action_type.value}")
    
    def _initialize_allowed_actions(self) -> set:
        """Initialize allowed action types"""
        return {
            UIActionType.NAVIGATE,
            UIActionType.APPLY_FILTER,
            UIActionType.SORT_RESULTS,
            UIActionType.SELECT_RESULT,
            UIActionType.OPEN_MODAL,
            UIActionType.CLOSE_MODAL,
            UIActionType.SCROLL_TO,
            UIActionType.TOGGLE_ELEMENT,
            UIActionType.UPDATE_STATE
        }
    
    def _register_default_handlers(self):
        """Register default action handlers"""
        self.action_handlers = {
            UIActionType.NAVIGATE: self._handle_navigate,
            UIActionType.APPLY_FILTER: self._handle_apply_filter,
            UIActionType.SORT_RESULTS: self._handle_sort_results,
            UIActionType.SELECT_RESULT: self._handle_select_result,
            UIActionType.OPEN_MODAL: self._handle_open_modal,
            UIActionType.CLOSE_MODAL: self._handle_close_modal,
            UIActionType.SCROLL_TO: self._handle_scroll_to,
            UIActionType.TOGGLE_ELEMENT: self._handle_toggle_element,
            UIActionType.UPDATE_STATE: self._handle_update_state
        }
    
    def _handle_navigate(self, action: UIAction) -> Dict:
        """Handle navigation action"""
        url = action.parameters.get('url')
        page = action.parameters.get('page')
        
        if url:
            return {'action': 'navigate', 'url': url, 'method': 'url_navigation'}
        elif page:
            return {'action': 'navigate', 'page': page, 'method': 'page_navigation'}
        
        return {'action': 'navigate', 'error': 'No URL or page specified'}
    
    def _handle_apply_filter(self, action: UIAction) -> Dict:
        """Handle filter application action"""
        filters = action.parameters.get('filters', {})
        target = action.target_element
        
        return {
            'action': 'apply_filter',
            'filters': filters,
            'target': target,
            'method': 'filter_application'
        }
    
    def _handle_sort_results(self, action: UIAction) -> Dict:
        """Handle sort action"""
        sort_by = action.parameters.get('sort_by', 'default')
        sort_order = action.parameters.get('order', 'asc')
        target = action.target_element
        
        return {
            'action': 'sort',
            'sort_by': sort_by,
            'order': sort_order,
            'target': target,
            'method': 'sort_application'
        }
    
    def _handle_select_result(self, action: UIAction) -> Dict:
        """Handle result selection action"""
        result_id = action.parameters.get('result_id')
        result_index = action.parameters.get('result_index')
        
        return {
            'action': 'select_result',
            'result_id': result_id,
            'result_index': result_index,
            'method': 'result_selection'
        }
    
    def _handle_open_modal(self, action: UIAction) -> Dict:
        """Handle modal open action"""
        modal_type = action.parameters.get('modal_type')
        modal_data = action.parameters.get('data')
        
        return {
            'action': 'open_modal',
            'modal_type': modal_type,
            'data': modal_data,
            'method': 'modal_open'
        }
    
    def _handle_close_modal(self, action: UIAction) -> Dict:
        """Handle modal close action"""
        modal_id = action.parameters.get('modal_id')
        
        return {
            'action': 'close_modal',
            'modal_id': modal_id,
            'method': 'modal_close'
        }
    
    def _handle_scroll_to(self, action: UIAction) -> Dict:
        """Handle scroll action"""
        target = action.target_element
        position = action.parameters.get('position', 'top')
        
        return {
            'action': 'scroll',
            'target': target,
            'position': position,
            'method': 'scroll_action'
        }
    
    def _handle_toggle_element(self, action: UIAction) -> Dict:
        """Handle element toggle action"""
        target = action.target_element
        state = action.parameters.get('state')
        
        return {
            'action': 'toggle',
            'target': target,
            'state': state,
            'method': 'element_toggle'
        }
    
    def _handle_update_state(self, action: UIAction) -> Dict:
        """Handle state update action"""
        state_key = action.parameters.get('key')
        state_value = action.parameters.get('value')
        
        return {
            'action': 'update_state',
            'key': state_key,
            'value': state_value,
            'method': 'state_update'
        }
    
    def create_navigate_action(self, url: str) -> UIAction:
        """Create navigation action"""
        return self.create_action(
            action_type=UIActionType.NAVIGATE,
            parameters={'url': url}
        )
    
    def create_filter_action(self, filters: Dict, target: str = "results") -> UIAction:
        """Create filter action"""
        return self.create_action(
            action_type=UIActionType.APPLY_FILTER,
            parameters={'filters': filters},
            target_element=target
        )
    
    def create_sort_action(self, sort_by: str, order: str = "asc", target: str = "results") -> UIAction:
        """Create sort action"""
        return self.create_action(
            action_type=UIActionType.SORT_RESULTS,
            parameters={'sort_by': sort_by, 'order': order},
            target_element=target
        )
    
    def create_select_action(self, result_id: int, result_index: int = None) -> UIAction:
        """Create selection action"""
        return self.create_action(
            action_type=UIActionType.SELECT_RESULT,
            parameters={'result_id': result_id, 'result_index': result_index}
        )
    
    def parse_natural_language_command(self, command: str, context: Dict) -> Optional[UIAction]:
        """
        Parse natural language command into UI action
        
        Args:
            command: Natural language command
            context: Current UI context
            
        Returns:
            UIAction if successful, None otherwise
        """
        command_lower = command.strip().lower()
        
        # Navigation commands
        if any(word in command_lower for word in ['افتح', 'اذهب', 'روح', 'انتقل']):
            return self._parse_navigation_command(command, context)
        
        # Sort commands
        if any(word in command_lower for word in ['رتب', 'من الأرخص', 'من الأغلى', 'الأحدث']):
            return self._parse_sort_command(command, context)
        
        # Filter commands
        if any(word in command_lower for word in ['فلتر', 'اعرض', 'خلي', 'فقط']):
            return self._parse_filter_command(command, context)
        
        return None
    
    def _parse_navigation_command(self, command: str, context: Dict) -> Optional[UIAction]:
        """Parse navigation command"""
        command_lower = command.strip().lower()
        
        # Extract destination
        destinations = {
            'العقارات': '/properties',
            'الوظائف': '/jobs',
            'الفنادق': '/hotels',
            'المزادات': '/auctions',
            'دخول': '/login',
            'التسجيل': '/register'
        }
        
        for dest, url in destinations.items():
            if dest in command_lower:
                return self.create_navigate_action(url)
        
        return None
    
    def _parse_sort_command(self, command: str, context: Dict) -> Optional[UIAction]:
        """Parse sort command"""
        command_lower = command.strip().lower()
        
        sort_mapping = {
            'من الأرخص': ('price', 'asc'),
            'من الأغلى': ('price', 'desc'),
            'الأحدث': ('created_at', 'desc'),
            'الأقدم': ('created_at', 'asc'),
            'الأكبر': ('area', 'desc'),
            'الأصغر': ('area', 'asc')
        }
        
        for phrase, (sort_by, order) in sort_mapping.items():
            if phrase in command_lower:
                return self.create_sort_action(sort_by, order)
        
        return None
    
    def _parse_filter_command(self, command: str, context: Dict) -> Optional[UIAction]:
        """Parse filter command"""
        # Simple filter parsing
        command_lower = command.strip().lower()
        
        filters = {}
        
        # Extract numeric filters
        import re
        numbers = re.findall(r'(\d+)', command)
        if numbers:
            filters['price_max'] = int(numbers[0]) * 1000000  # Assume millions
        
        return self.create_filter_action(filters) if filters else None
    
    def generate_action_confirmation(self, action: UIAction) -> str:
        """Generate confirmation message for action"""
        if action.action_type == UIActionType.NAVIGATE:
            url = action.parameters.get('url', 'صفحة غير محددة')
            return f"هل تريد الانتقال إلى {url}؟"
        
        elif action.action_type == UIActionType.APPLY_FILTER:
            filters = action.parameters.get('filters', {})
            return f"هل تريد تطبيق الفلاتر: {filters}؟"
        
        elif action.action_type == UIActionType.SORT_RESULTS:
            sort_by = action.parameters.get('sort_by', 'افتراضي')
            order = action.parameters.get('order', 'تصاعدي')
            return f"هل تريد ترتيب النتائج حسب {sort_by} ({order})؟"
        
        return f"هل تريد تنفيذ هذا الإجراء؟"
    
    def get_action_summary(self, action: UIAction) -> str:
        """Get human-readable summary of action"""
        action_descriptions = {
            UIActionType.NAVIGATE: "الانتقال إلى صفحة",
            UIActionType.APPLY_FILTER: "تطبيق فلاتر",
            UIActionType.SORT_RESULTS: "ترتيب النتائج",
            UIActionType.SELECT_RESULT: "اختيار نتيجة",
            UIActionType.OPEN_MODAL: "فتح نافذة",
            UIActionType.CLOSE_MODAL: "إغلاق نافذة",
            UIActionType.SCROLL_TO: "التمرير إلى",
            UIActionType.TOGGLE_ELEMENT: "تبديل حالة عنصر",
            UIActionType.UPDATE_STATE: "تحديث الحالة"
        }
        
        description = action_descriptions.get(action.action_type, "إجراء غير محدد")
        
        if action.target_element:
            return f"{description} {action.target_element}"
        
        return description
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# Global instance
ui_action_manager = UIActionManager()