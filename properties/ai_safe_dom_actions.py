"""
Safe DOM Actions
Defines safe, limited actions that AI can perform on UI
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of safe UI actions"""
    NAVIGATE = "navigate"
    OPEN_PROPERTY = "open_property"
    OPEN_JOB = "open_job"
    APPLY_FILTER = "apply_filter"
    CHANGE_SORT = "change_sort"
    OPEN_MODAL = "open_modal"
    CLOSE_MODAL = "close_modal"
    SELECT_RESULT = "select_result"
    FILL_ALLOWED_FIELD = "fill_allowed_field"
    SUBMIT_FORM = "submit_form"


@dataclass
class DOMAction:
    """Represents a safe DOM action"""
    action_id: str = None
    action_type: ActionType = None
    parameters: Dict = None
    requires_confirmation: bool = False
    validation_required: bool = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'action_id': self.action_id,
            'action_type': self.action_type.value,
            'parameters': self.parameters,
            'requires_confirmation': self.requires_confirmation,
            'validation_required': self.validation_required
        }


class SafeDOMActions:
    """
    Defines safe, limited actions that AI can perform
    Never allows arbitrary JavaScript execution
    """
    
    def __init__(self):
        self.action_schemas = {
            ActionType.NAVIGATE: {
                'required_params': ['route'],
                'optional_params': ['params'],
                'requires_confirmation': False
            },
            ActionType.OPEN_PROPERTY: {
                'required_params': ['property_id'],
                'optional_params': [],
                'requires_confirmation': False
            },
            ActionType.OPEN_JOB: {
                'required_params': ['job_id'],
                'optional_params': [],
                'requires_confirmation': False
            },
            ActionType.APPLY_FILTER: {
                'required_params': ['filter_name', 'filter_value'],
                'optional_params': [],
                'requires_confirmation': False
            },
            ActionType.CHANGE_SORT: {
                'required_params': ['sort_by'],
                'optional_params': ['sort_order'],
                'requires_confirmation': False
            },
            ActionType.OPEN_MODAL: {
                'required_params': ['modal_name'],
                'optional_params': ['modal_data'],
                'requires_confirmation': False
            },
            ActionType.CLOSE_MODAL: {
                'required_params': [],
                'optional_params': [],
                'requires_confirmation': False
            },
            ActionType.SELECT_RESULT: {
                'required_params': ['result_index'],
                'optional_params': [],
                'requires_confirmation': False
            },
            ActionType.FILL_ALLOWED_FIELD: {
                'required_params': ['field_name', 'field_value'],
                'optional_params': [],
                'requires_confirmation': False
            },
            ActionType.SUBMIT_FORM: {
                'required_params': [],
                'optional_params': [],
                'requires_confirmation': True
            }
        }
        
        self.allowed_fields = {
            'property_listing': ['title', 'price', 'area', 'governorate', 'district', 'description'],
            'job_application': ['name', 'email', 'phone'],
            'agent_application': ['name', 'email', 'phone', 'experience'],
            'user_profile': ['name', 'email', 'phone']
        }
    
    def create_action(self,
                     action_type: ActionType,
                     parameters: Dict,
                     requires_confirmation: bool = None) -> Optional[DOMAction]:
        """
        Create a DOM action with validation
        
        Args:
            action_type: Type of action
            parameters: Action parameters
            requires_confirmation: Override confirmation requirement
            
        Returns:
            Created action or None if invalid
        """
        schema = self.action_schemas.get(action_type)
        if not schema:
            logger.error(f"Unknown action type: {action_type}")
            return None
        
        # Validate required parameters
        for param in schema['required_params']:
            if param not in parameters:
                logger.error(f"Missing required parameter: {param}")
                return None
        
        # Validate field names for fill actions
        if action_type == ActionType.FILL_ALLOWED_FIELD:
            field_name = parameters.get('field_name')
            form_type = parameters.get('form_type')
            if form_type and field_name:
                if form_type in self.allowed_fields:
                    if field_name not in self.allowed_fields[form_type]:
                        logger.error(f"Field {field_name} not allowed for form {form_type}")
                        return None
        
        # Determine if confirmation is required
        if requires_confirmation is None:
            requires_confirmation = schema['requires_confirmation']
        
        action = DOMAction(
            action_id=f"{action_type.value}_{hash(str(parameters))}",
            action_type=action_type,
            parameters=parameters,
            requires_confirmation=requires_confirmation,
            validation_required=True
        )
        
        logger.info(f"Created safe action: {action_type.value}")
        return action
    
    def validate_action(self, action: DOMAction) -> bool:
        """
        Validate a DOM action
        
        Args:
            action: Action to validate
            
        Returns:
            True if valid, False otherwise
        """
        schema = self.action_schemas.get(action.action_type)
        if not schema:
            return False
        
        # Check for dangerous parameters
        dangerous_keywords = ['javascript:', 'eval(', 'script:', 'onload=', 'onerror=']
        for key, value in action.parameters.items():
            if isinstance(value, str):
                for keyword in dangerous_keywords:
                    if keyword in value.lower():
                        logger.error(f"Dangerous keyword detected: {keyword}")
                        return False
        
        return True
    
    def execute_action(self, action: DOMAction) -> Dict:
        """
        Execute a safe DOM action (placeholder)
        
        Args:
            action: Action to execute
            
        Returns:
            Execution result
        """
        if not self.validate_action(action):
            return {
                'success': False,
                'error': 'Action validation failed'
            }
        
        # Placeholder for actual execution
        logger.info(f"Executing action: {action.action_type.value}")
        
        return {
            'success': True,
            'action': action.to_dict(),
            'message': f"Action {action.action_type.value} executed successfully"
        }
    
    def get_allowed_actions(self) -> List[str]:
        """Get list of allowed action types"""
        return [action.value for action in ActionType]
    
    def get_allowed_fields(self, form_type: str) -> List[str]:
        """Get allowed fields for a form type"""
        return self.allowed_fields.get(form_type, [])


# Global instance
safe_dom_actions = SafeDOMActions()