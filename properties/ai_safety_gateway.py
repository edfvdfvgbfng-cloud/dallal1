"""
Safety Gateway
Validates and controls AI agent actions before execution
"""

from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions that require safety checks"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    PUBLISH = "publish"
    SEND = "send"
    CONTACT = "contact"
    UPLOAD = "upload"
    MODIFY = "modify"
    EXECUTE = "execute"


class RiskLevel(Enum):
    """Risk levels for actions"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SafetyCheck:
    """Result of a safety check"""
    passed: bool = True
    risk_level: RiskLevel = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    requires_confirmation: bool = False
    blocked: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'passed': self.passed,
            'risk_level': self.risk_level.value,
            'warnings': self.warnings,
            'errors': self.errors,
            'requires_confirmation': self.requires_confirmation,
            'blocked': self.blocked
        }


@dataclass
class ActionRequest:
    """Request for an action to be executed"""
    action_id: str = None
    action_type: ActionType = None
    user_id: int = None
    agent_type: str = None
    tool_name: str = None
    parameters: Dict = None
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'action_id': self.action_id,
            'action_type': self.action_type.value,
            'user_id': self.user_id,
            'agent_type': self.agent_type,
            'tool_name': self.tool_name,
            'parameters': self.parameters,
            'timestamp': self.timestamp
        }


class SafetyGateway:
    """
    Validates AI agent actions before execution
    Enforces security policies and permissions
    """
    
    def __init__(self):
        self.action_history: List[Dict] = []
        self.user_permissions: Dict[int, List[str]] = {}
        self.agent_permissions: Dict[str, List[str]] = {}
        self.risk_thresholds = {
            RiskLevel.SAFE: 0.0,
            RiskLevel.LOW: 0.3,
            RiskLevel.MEDIUM: 0.6,
            RiskLevel.HIGH: 0.8,
            RiskLevel.CRITICAL: 1.0
        }
        self.rate_limits: Dict[str, Dict] = {}
    
    def check_action(self, action_request: ActionRequest) -> SafetyCheck:
        """
        Perform comprehensive safety check on action
        
        Args:
            action_request: Action to check
            
        Returns:
            SafetyCheck result
        """
        check = SafetyCheck(passed=True, risk_level=RiskLevel.SAFE)
        
        try:
            # 1. Check user permissions
            user_check = self._check_user_permissions(action_request)
            if not user_check:
                check.passed = False
                check.blocked = True
                check.errors.append("User does not have permission for this action")
                return check
            
            # 2. Check agent permissions
            agent_check = self._check_agent_permissions(action_request)
            if not agent_check:
                check.passed = False
                check.blocked = True
                check.errors.append("Agent does not have permission for this tool")
                return check
            
            # 3. Assess risk level
            risk_level = self._assess_risk(action_request)
            check.risk_level = risk_level
            
            # 4. Check rate limits
            rate_check = self._check_rate_limit(action_request)
            if not rate_check:
                check.passed = False
                check.blocked = True
                check.errors.append("Rate limit exceeded")
                return check
            
            # 5. Validate parameters
            param_check = self._validate_parameters(action_request)
            if not param_check['valid']:
                check.passed = False
                check.errors.extend(param_check['errors'])
                return check
            
            # 6. Check for sensitive actions
            if self._is_sensitive_action(action_request):
                check.requires_confirmation = True
                check.warnings.append("This action requires user confirmation")
            
            # 7. High risk actions require confirmation
            if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                check.requires_confirmation = True
                check.warnings.append(f"High risk action ({risk_level.value}) requires confirmation")
            
            # Log the check
            self._log_action_check(action_request, check)
            
            return check
            
        except Exception as e:
            logger.error(f"Error in safety check: {str(e)}")
            check.passed = False
            check.errors.append(f"Safety check error: {str(e)}")
            return check
    
    def _check_user_permissions(self, action: ActionRequest) -> bool:
        """Check if user has permission for action"""
        user_perms = self.user_permissions.get(action.user_id, [])
        
        # Default permissions if none set
        if not user_perms:
            # Allow read and low-risk actions by default
            if action.action_type in [ActionType.READ]:
                return True
            return False
        
        # Check if user has permission for this action type
        required_perm = f"{action.action_type.value}:{action.tool_name}"
        return required_perm in user_perms or f"{action.action_type.value}:*" in user_perms
    
    def _check_agent_permissions(self, action: ActionRequest) -> bool:
        """Check if agent has permission for tool"""
        agent_perms = self.agent_permissions.get(action.agent_type, [])
        
        # Default agent permissions
        if not agent_perms:
            # General agent can use basic tools
            if action.agent_type == "general":
                basic_tools = ['search', 'retrieve', 'analyze']
                return action.tool_name in basic_tools
            return False
        
        return action.tool_name in agent_perms or "*" in agent_perms
    
    def _assess_risk(self, action: ActionRequest) -> RiskLevel:
        """Assess risk level of action"""
        # Base risk by action type
        risk_map = {
            ActionType.READ: RiskLevel.SAFE,
            ActionType.WRITE: RiskLevel.LOW,
            ActionType.MODIFY: RiskLevel.MEDIUM,
            ActionType.UPLOAD: RiskLevel.MEDIUM,
            ActionType.SEND: RiskLevel.MEDIUM,
            ActionType.CONTACT: RiskLevel.HIGH,
            ActionType.PUBLISH: RiskLevel.HIGH,
            ActionType.DELETE: RiskLevel.CRITICAL,
            ActionType.EXECUTE: RiskLevel.CRITICAL
        }
        
        base_risk = risk_map.get(action.action_type, RiskLevel.MEDIUM)
        
        # Adjust based on tool
        if action.tool_name in ['delete_property', 'delete_user', 'delete_listing']:
            return RiskLevel.CRITICAL
        elif action.tool_name in ['publish_listing', 'send_message', 'contact_agent']:
            return RiskLevel.HIGH
        elif action.tool_name in ['modify_property', 'update_user']:
            return RiskLevel.MEDIUM
        
        return base_risk
    
    def _check_rate_limit(self, action: ActionRequest) -> bool:
        """Check if action is within rate limits"""
        key = f"{action.user_id}:{action.action_type.value}"
        
        if key not in self.rate_limits:
            self.rate_limits[key] = {'count': 0, 'window_start': time.time()}
        
        limit_info = self.rate_limits[key]
        current_time = time.time()
        
        # Reset window if expired (60 seconds)
        if current_time - limit_info['window_start'] > 60:
            limit_info['count'] = 0
            limit_info['window_start'] = current_time
        
        # Set limits based on action type
        limits = {
            ActionType.READ: 100,
            ActionType.WRITE: 30,
            ActionType.SEND: 10,
            ActionType.CONTACT: 5,
            ActionType.PUBLISH: 3
        }
        
        max_requests = limits.get(action.action_type, 20)
        
        if limit_info['count'] >= max_requests:
            return False
        
        limit_info['count'] += 1
        return True
    
    def _validate_parameters(self, action: ActionRequest) -> Dict:
        """Validate action parameters"""
        result = {'valid': True, 'errors': []}
        
        # Check for required parameters based on tool
        required_params = {
            'search': ['query'],
            'publish_listing': ['property_id'],
            'contact_agent': ['agent_id', 'message'],
            'delete_property': ['property_id']
        }
        
        required = required_params.get(action.tool_name, [])
        for param in required:
            if param not in action.parameters or action.parameters[param] is None:
                result['valid'] = False
                result['errors'].append(f"Missing required parameter: {param}")
        
        # Check for dangerous parameters
        if 'sql' in str(action.parameters).lower():
            result['valid'] = False
            result['errors'].append("Direct SQL not allowed")
        
        if 'eval' in str(action.parameters).lower():
            result['valid'] = False
            result['errors'].append("Code execution not allowed")
        
        return result
    
    def _is_sensitive_action(self, action: ActionRequest) -> bool:
        """Check if action is sensitive and requires confirmation"""
        sensitive_actions = [
            ActionType.PUBLISH,
            ActionType.DELETE,
            ActionType.SEND,
            ActionType.CONTACT,
            ActionType.EXECUTE
        ]
        
        return action.action_type in sensitive_actions
    
    def _log_action_check(self, action: ActionRequest, check: SafetyCheck):
        """Log action check for audit"""
        self.action_history.append({
            'timestamp': datetime.now().isoformat(),
            'action_id': action.action_id,
            'user_id': action.user_id,
            'agent_type': action.agent_type,
            'tool_name': action.tool_name,
            'action_type': action.action_type.value,
            'passed': check.passed,
            'risk_level': check.risk_level.value,
            'blocked': check.blocked,
            'requires_confirmation': check.requires_confirmation
        })
    
    def set_user_permissions(self, user_id: int, permissions: List[str]):
        """Set permissions for a user"""
        self.user_permissions[user_id] = permissions
        logger.info(f"Set permissions for user {user_id}: {permissions}")
    
    def set_agent_permissions(self, agent_type: str, permissions: List[str]):
        """Set permissions for an agent type"""
        self.agent_permissions[agent_type] = permissions
        logger.info(f"Set permissions for agent {agent_type}: {permissions}")
    
    def get_action_history(self, user_id: int = None, limit: int = 100) -> List[Dict]:
        """Get action history"""
        history = self.action_history
        
        if user_id:
            history = [h for h in history if h['user_id'] == user_id]
        
        return history[-limit:]
    
    def get_safety_statistics(self) -> Dict:
        """Get safety gateway statistics"""
        total_checks = len(self.action_history)
        passed = sum(1 for h in self.action_history if h['passed'])
        blocked = sum(1 for h in self.action_history if h['blocked'])
        required_confirmation = sum(1 for h in self.action_history if h['requires_confirmation'])
        
        risk_distribution = {}
        for h in self.action_history:
            risk = h['risk_level']
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
        
        return {
            'total_checks': total_checks,
            'passed': passed,
            'blocked': blocked,
            'required_confirmation': required_confirmation,
            'pass_rate': passed / total_checks if total_checks > 0 else 0,
            'risk_distribution': risk_distribution
        }


# Global instance
safety_gateway = SafetyGateway()