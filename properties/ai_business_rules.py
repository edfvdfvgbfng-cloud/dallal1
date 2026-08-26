"""
Business Rules Engine
Validates actions against business rules and policies
"""

from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Types of business rules"""
    REQUIRED_FIELD = "required_field"
    PERMISSION = "permission"
    VALIDATION = "validation"
    CONDITIONAL = "conditional"
    POLICY = "policy"


class RuleSeverity(Enum):
    """Severity of rule violations"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class BusinessRule:
    """Represents a business rule"""
    rule_id: str = None
    name: str = None
    rule_type: RuleType = None
    entity: str = None  # property, user, listing, etc.
    condition: Callable = None
    severity: RuleSeverity = None
    error_message: str = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'rule_type': self.rule_type.value,
            'entity': self.entity,
            'severity': self.severity.value,
            'error_message': self.error_message,
            'metadata': self.metadata
        }


@dataclass
class RuleEvaluation:
    """Result of rule evaluation"""
    rule_id: str = None
    passed: bool = True
    severity: RuleSeverity = None
    message: str = None
    data: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'rule_id': self.rule_id,
            'passed': self.passed,
            'severity': self.severity.value,
            'message': self.message,
            'data': self.data
        }


class BusinessRulesEngine:
    """
    Validates actions against business rules
    Separates business logic from AI prompts
    """
    
    def __init__(self):
        self.rules: Dict[str, BusinessRule] = {}
        self.evaluation_history: List[Dict] = []
        self._initialize_rules()
    
    def _initialize_rules(self):
        """Initialize business rules"""
        
        # Property Rules
        self.add_rule(BusinessRule(
            rule_id="prop_001",
            name="Property Requires Price",
            rule_type=RuleType.REQUIRED_FIELD,
            entity="property",
            condition=lambda data: data.get('price') is not None and data.get('price') > 0,
            severity=RuleSeverity.ERROR,
            error_message="Property listing requires a valid price"
        ))
        
        self.add_rule(BusinessRule(
            rule_id="prop_002",
            name="Property Requires Area",
            rule_type=RuleType.REQUIRED_FIELD,
            entity="property",
            condition=lambda data: data.get('area') is not None and data.get('area') > 0,
            severity=RuleSeverity.ERROR,
            error_message="Property listing requires a valid area"
        ))
        
        self.add_rule(BusinessRule(
            rule_id="prop_003",
            name="Property Requires Location",
            rule_type=RuleType.REQUIRED_FIELD,
            entity="property",
            condition=lambda data: data.get('governorate') is not None,
            severity=RuleSeverity.ERROR,
            error_message="Property listing requires a governorate"
        ))
        
        self.add_rule(BusinessRule(
            rule_id="prop_004",
            name="Property Price Reasonable",
            rule_type=RuleType.VALIDATION,
            entity="property",
            condition=lambda data: data.get('price', 0) > 10000,  # Minimum 10,000 IQD
            severity=RuleSeverity.WARNING,
            error_message="Property price seems unusually low"
        ))
        
        # User Rules
        self.add_rule(BusinessRule(
            rule_id="user_001",
            name="User Cannot Contact Blocked User",
            rule_type=RuleType.PERMISSION,
            entity="user",
            condition=lambda data: data.get('target_user_id') not in data.get('blocked_users', []),
            severity=RuleSeverity.ERROR,
            error_message="Cannot contact a blocked user"
        ))
        
        self.add_rule(BusinessRule(
            rule_id="user_002",
            name="User Cannot Modify Others Property",
            rule_type=RuleType.PERMISSION,
            entity="user",
            condition=lambda data: data.get('user_id') == data.get('property_owner_id'),
            severity=RuleSeverity.ERROR,
            error_message="User cannot modify property they don't own"
        ))
        
        # Job Rules
        self.add_rule(BusinessRule(
            rule_id="job_001",
            name="Job Requires CV",
            rule_type=RuleType.CONDITIONAL,
            entity="job",
            condition=lambda data: not data.get('requires_cv') or data.get('cv_id') is not None,
            severity=RuleSeverity.ERROR,
            error_message="Job requires CV but none provided"
        ))
        
        # Listing Rules
        self.add_rule(BusinessRule(
            rule_id="list_001",
            name="Listing Requires Images",
            rule_type=RuleType.REQUIRED_FIELD,
            entity="listing",
            condition=lambda data: len(data.get('images', [])) > 0,
            severity=RuleSeverity.WARNING,
            error_message="Listing without images may receive less attention"
        ))
        
        self.add_rule(BusinessRule(
            rule_id="list_002",
            name="Listing Description Length",
            rule_type=RuleType.VALIDATION,
            entity="listing",
            condition=lambda data: len(data.get('description', '')) >= 50,
            severity=RuleSeverity.WARNING,
            error_message="Listing description should be at least 50 characters"
        ))
    
    def add_rule(self, rule: BusinessRule):
        """Add a business rule"""
        self.rules[rule.rule_id] = rule
        logger.info(f"Added rule {rule.rule_id}: {rule.name}")
    
    def evaluate_rules(self, entity: str, data: Dict) -> List[RuleEvaluation]:
        """
        Evaluate all rules for an entity
        
        Args:
            entity: Entity type (property, user, etc.)
            data: Data to validate
            
        Returns:
            List of rule evaluations
        """
        evaluations = []
        
        for rule_id, rule in self.rules.items():
            if rule.entity != entity:
                continue
            
            try:
                passed = rule.condition(data)
                
                evaluation = RuleEvaluation(
                    rule_id=rule_id,
                    passed=passed,
                    severity=rule.severity,
                    message=rule.error_message if not passed else "Rule passed",
                    data={'entity': entity}
                )
                
                evaluations.append(evaluation)
                
                # Log evaluation
                self.evaluation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'rule_id': rule_id,
                    'entity': entity,
                    'passed': passed,
                    'severity': rule.severity.value
                })
                
            except Exception as e:
                logger.error(f"Error evaluating rule {rule_id}: {str(e)}")
                evaluations.append(RuleEvaluation(
                    rule_id=rule_id,
                    passed=False,
                    severity=RuleSeverity.ERROR,
                    message=f"Rule evaluation error: {str(e)}"
                ))
        
        return evaluations
    
    def validate_action(self, action: str, entity: str, data: Dict) -> Dict:
        """
        Validate an action against business rules
        
        Args:
            action: Action being performed
            entity: Entity type
            data: Action data
            
        Returns:
            Validation result
        """
        evaluations = self.evaluate_rules(entity, data)
        
        errors = [e for e in evaluations if not e.passed and e.severity == RuleSeverity.ERROR]
        warnings = [e for e in evaluations if not e.passed and e.severity == RuleSeverity.WARNING]
        
        is_valid = len(errors) == 0
        
        return {
            'valid': is_valid,
            'errors': [e.message for e in errors],
            'warnings': [e.message for e in warnings],
            'evaluations': [e.to_dict() for e in evaluations]
        }
    
    def get_rule(self, rule_id: str) -> Optional[BusinessRule]:
        """Get rule by ID"""
        return self.rules.get(rule_id)
    
    def get_rules_for_entity(self, entity: str) -> List[BusinessRule]:
        """Get all rules for an entity type"""
        return [rule for rule in self.rules.values() if rule.entity == entity]
    
    def get_evaluation_statistics(self) -> Dict:
        """Get evaluation statistics"""
        total_evaluations = len(self.evaluation_history)
        passed = sum(1 for e in self.evaluation_history if e['passed'])
        
        severity_counts = {}
        for e in self.evaluation_history:
            severity = e['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_evaluations': total_evaluations,
            'passed': passed,
            'failed': total_evaluations - passed,
            'pass_rate': passed / total_evaluations if total_evaluations > 0 else 0,
            'severity_distribution': severity_counts,
            'total_rules': len(self.rules)
        }


# Global instance
business_rules_engine = BusinessRulesEngine()