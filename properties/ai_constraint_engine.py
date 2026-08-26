"""
Constraint Engine for Advanced User Requirements
Manages hard filters vs soft preferences and constraint relaxation
"""

from typing import Dict, List, Any, Optional, Set
from enum import Enum
import logging
from dataclasses import dataclass
from collections import defaultdict

from .ai_goal_understanding import ConstraintType, UserGoal

logger = logging.getLogger(__name__)


class Constraint:
    """Individual constraint with metadata"""
    
    def __init__(self, 
                 constraint_type: ConstraintType,
                 field: str,
                 value: Any,
                 source: str = 'explicit',
                 confidence: float = 1.0):
        self.constraint_type = constraint_type
        self.field = field
        self.value = value
        self.source = source
        self.confidence = confidence
        self.relaxed = False
        self.relaxation_reason = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'type': self.constraint_type.value,
            'field': self.field,
            'value': self.value,
            'source': self.source,
            'confidence': self.confidence,
            'relaxed': self.relaxed,
            'relaxation_reason': self.relaxation_reason
        }
    
    def matches(self, item_value: Any) -> bool:
        """Check if item value matches constraint"""
        if self.relaxed:
            return True  # Relaxed constraints always match
        
        if self.value is None:
            return True
        
        if isinstance(self.value, (int, float)):
            if isinstance(item_value, (int, float)):
                return item_value == self.value
            return False
        
        if isinstance(self.value, str):
            if isinstance(item_value, str):
                return self.value.lower() == item_value.lower()
            return False
        
        if isinstance(self.value, list):
            if isinstance(item_value, (list, set)):
                return any(v in item_value for v in self.value)
            return item_value in self.value
        
        return str(self.value) == str(item_value)


class ConstraintSet:
    """Set of constraints with management capabilities"""
    
    def __init__(self):
        self.constraints: List[Constraint] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_constraint(self, constraint: Constraint):
        """Add a constraint to the set"""
        # Remove existing constraint for same field if exists
        self.constraints = [c for c in self.constraints if c.field != constraint.field]
        self.constraints.append(constraint)
    
    def get_constraints_by_type(self, constraint_type: ConstraintType) -> List[Constraint]:
        """Get constraints of specific type"""
        return [c for c in self.constraints if c.constraint_type == constraint_type]
    
    def get_constraint_for_field(self, field: str) -> Optional[Constraint]:
        """Get constraint for specific field"""
        for constraint in self.constraints:
            if constraint.field == field:
                return constraint
        return None
    
    def remove_constraint(self, field: str):
        """Remove constraint for specific field"""
        self.constraints = [c for c in self.constraints if c.field != field]
    
    def relax_constraint(self, field: str, reason: str):
        """Relax a constraint"""
        for constraint in self.constraints:
            if constraint.field == field:
                constraint.relaxed = True
                constraint.relaxation_reason = reason
                break
    
    def restore_constraint(self, field: str):
        """Restore a relaxed constraint"""
        for constraint in self.constraints:
            if constraint.field == field:
                constraint.relaxed = False
                constraint.relaxation_reason = None
                break
    
    def matches_all_hard_constraints(self, item: Dict) -> bool:
        """Check if item matches all hard (must-have) constraints"""
        hard_constraints = self.get_constraints_by_type(ConstraintType.MUST_HAVE)
        
        for constraint in hard_constraints:
            if not constraint.relaxed:
                item_value = item.get(constraint.field)
                if not constraint.matches(item_value):
                    return False
        
        return True
    
    def matches_forbidden_constraints(self, item: Dict) -> bool:
        """Check if item matches forbidden constraints (should be false)"""
        forbidden_constraints = self.get_constraints_by_type(ConstraintType.FORBIDDEN)
        
        for constraint in forbidden_constraints:
            if not constraint.relaxed:
                item_value = item.get(constraint.field)
                if constraint.matches(item_value):
                    return False  # Matches forbidden constraint
        
        return True
    
    def calculate_soft_match_score(self, item: Dict) -> float:
        """Calculate match score based on soft constraints"""
        preferred_constraints = self.get_constraints_by_type(ConstraintType.PREFERRED)
        optional_constraints = self.get_constraints_by_type(ConstraintType.OPTIONAL)
        
        score = 0.0
        total_weight = 0.0
        
        # Preferred constraints have higher weight
        for constraint in preferred_constraints:
            total_weight += 1.0
            item_value = item.get(constraint.field)
            if constraint.matches(item_value):
                score += 1.0 * constraint.confidence
        
        # Optional constraints have lower weight
        for constraint in optional_constraints:
            total_weight += 0.5
            item_value = item.get(constraint.field)
            if constraint.matches(item_value):
                score += 0.5 * constraint.confidence
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'constraints': [c.to_dict() for c in self.constraints],
            'metadata': self.metadata
        }


class ConstraintEngine:
    """
    Advanced constraint management engine
    Handles hard filters, soft preferences, and constraint relaxation
    """
    
    def __init__(self):
        self.active_constraint_set = ConstraintSet()
        self.constraint_history: List[Dict] = []
        self.relaxation_suggestions: List[Dict] = []
    
    def build_constraint_set_from_goal(self, user_goal: UserGoal) -> ConstraintSet:
        """Build constraint set from user goal"""
        constraint_set = ConstraintSet()
        
        # Convert goal constraints to Constraint objects
        for constraint_type, constraints in user_goal.constraints.items():
            for constraint_data in constraints:
                constraint = Constraint(
                    constraint_type=constraint_type,
                    field=constraint_data.get('type'),
                    value=constraint_data.get('value'),
                    source=constraint_data.get('source', 'explicit'),
                    confidence=1.0
                )
                constraint_set.add_constraint(constraint)
        
        # Set as active
        self.active_constraint_set = constraint_set
        
        # Add to history
        self.constraint_history.append({
            'timestamp': self._get_timestamp(),
            'constraint_set': constraint_set.to_dict(),
            'source': 'user_goal'
        })
        
        return constraint_set
    
    def apply_constraints_to_query(self, query_params: Dict) -> Dict:
        """
        Apply constraints to database query parameters
        Only hard constraints are applied as filters
        """
        filtered_params = query_params.copy()
        
        hard_constraints = self.active_constraint_set.get_constraints_by_type(ConstraintType.MUST_HAVE)
        
        for constraint in hard_constraints:
            if not constraint.relaxed:
                if constraint.field == 'budget' and constraint.constraint_type == ConstraintType.MUST_HAVE:
                    if isinstance(constraint.value, dict):
                        if constraint.value.get('max'):
                            filtered_params['price__lte'] = constraint.value['max']
                        if constraint.value.get('min'):
                            filtered_params['price__gte'] = constraint.value['min']
                    else:
                        filtered_params['price'] = constraint.value
                
                elif constraint.field == 'location':
                    if isinstance(constraint.value, dict):
                        if constraint.value.get('governorate'):
                            filtered_params['governorate'] = constraint.value['governorate']
                        if constraint.value.get('district'):
                            filtered_params['district'] = constraint.value['district']
                    else:
                        filtered_params['governorate'] = constraint.value
                
                elif constraint.field == 'property_type':
                    filtered_params['property_type'] = constraint.value
                
                elif constraint.field == 'area':
                    if isinstance(constraint.value, dict):
                        if constraint.value.get('min'):
                            filtered_params['area__gte'] = constraint.value['min']
                        if constraint.value.get('max'):
                            filtered_params['area__lte'] = constraint.value['max']
                    else:
                        filtered_params['area'] = constraint.value
        
        return filtered_params
    
    def filter_results(self, results: List[Dict]) -> List[Dict]:
        """
        Filter results based on hard constraints
        """
        filtered_results = []
        
        for result in results:
            if (self.active_constraint_set.matches_all_hard_constraints(result) and
                self.active_constraint_set.matches_forbidden_constraints(result)):
                filtered_results.append(result)
        
        return filtered_results
    
    def rank_results(self, results: List[Dict]) -> List[tuple]:
        """
        Rank results based on soft constraints
        Returns list of (result, score) tuples
        """
        ranked_results = []
        
        for result in results:
            soft_score = self.active_constraint_set.calculate_soft_match_score(result)
            ranked_results.append((result, soft_score))
        
        # Sort by score descending
        ranked_results.sort(key=lambda x: x[1], reverse=True)
        
        return ranked_results
    
    def suggest_constraint_relaxation(self, empty_results: bool = True) -> List[Dict]:
        """
        Suggest which constraints to relax based on search results
        """
        suggestions = []
        
        if empty_results:
            # Analyze which constraints are most restrictive
            hard_constraints = self.active_constraint_set.get_constraints_by_type(ConstraintType.MUST_HAVE)
            
            for constraint in hard_constraints:
                if not constraint.relaxed:
                    suggestions.append({
                        'constraint': constraint.to_dict(),
                        'reason': 'No results with current constraints',
                        'relaxation_impact': self._estimate_relaxation_impact(constraint),
                        'user_permission_required': self._requires_user_permission(constraint)
                    })
        
        self.relaxation_suggestions = suggestions
        return suggestions
    
    def relax_constraint(self, field: str, reason: str, user_approved: bool = False):
        """
        Relax a specific constraint
        """
        if user_approved or not self._requires_user_permission_for_field(field):
            self.active_constraint_set.relax_constraint(field, reason)
            logger.info(f"Relaxed constraint for field: {field}, reason: {reason}")
        else:
            logger.warning(f"User permission required to relax constraint: {field}")
    
    def restore_all_constraints(self):
        """Restore all relaxed constraints"""
        for constraint in self.active_constraint_set.constraints:
            if constraint.relaxed:
                self.active_constraint_set.restore_constraint(constraint.field)
        logger.info("All constraints restored")
    
    def get_constraint_summary(self) -> Dict:
        """Get summary of current constraints"""
        return {
            'total_constraints': len(self.active_constraint_set.constraints),
            'hard_constraints': len(self.active_constraint_set.get_constraints_by_type(ConstraintType.MUST_HAVE)),
            'preferred_constraints': len(self.active_constraint_set.get_constraints_by_type(ConstraintType.PREFERRED)),
            'optional_constraints': len(self.active_constraint_set.get_constraints_by_type(ConstraintType.OPTIONAL)),
            'forbidden_constraints': len(self.active_constraint_set.get_constraints_by_type(ConstraintType.FORBIDDEN)),
            'relaxed_constraints': len([c for c in self.active_constraint_set.constraints if c.relaxed]),
            'active_fields': [c.field for c in self.active_constraint_set.constraints if not c.relaxed]
        }
    
    def _estimate_relaxation_impact(self, constraint: Constraint) -> str:
        """Estimate the impact of relaxing a constraint"""
        impact_levels = {
            'budget': 'high',
            'governorate': 'high',
            'property_type': 'medium',
            'district': 'medium',
            'area': 'low',
            'amenities': 'low'
        }
        
        return impact_levels.get(constraint.field, 'unknown')
    
    def _requires_user_permission(self, constraint: Constraint) -> bool:
        """Check if relaxing constraint requires user permission"""
        # Budget and location usually require user permission
        permission_required_fields = ['budget', 'governorate']
        return constraint.field in permission_required_fields
    
    def _requires_user_permission_for_field(self, field: str) -> bool:
        """Check if relaxing specific field requires user permission"""
        permission_required_fields = ['budget', 'governorate']
        return field in permission_required_fields
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def create_fallback_constraints(self, primary_type: str, fallback_type: str) -> ConstraintSet:
        """
        Create fallback constraint set (e.g., house -> apartment)
        """
        fallback_set = ConstraintSet()
        
        # Copy all constraints except property type
        for constraint in self.active_constraint_set.constraints:
            if constraint.field != 'property_type':
                fallback_set.add_constraint(constraint)
        
        # Add fallback property type
        fallback_constraint = Constraint(
            constraint_type=ConstraintType.PREFERRED,
            field='property_type',
            value=fallback_type,
            source='fallback',
            confidence=0.7
        )
        fallback_set.add_constraint(fallback_constraint)
        
        return fallback_set
    
    def merge_constraint_sets(self, primary_set: ConstraintSet, secondary_set: ConstraintSet) -> ConstraintSet:
        """
        Merge two constraint sets with conflict resolution
        Primary set takes precedence
        """
        merged_set = ConstraintSet()
        
        # Add all constraints from primary set
        for constraint in primary_set.constraints:
            merged_set.add_constraint(constraint)
        
        # Add constraints from secondary set only if not in primary
        for constraint in secondary_set.constraints:
            if not merged_set.get_constraint_for_field(constraint.field):
                merged_set.add_constraint(constraint)
        
        return merged_set


# Global instance
constraint_engine = ConstraintEngine()