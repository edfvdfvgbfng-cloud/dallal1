"""
Query Relaxation Engine
Intelligently relaxes search constraints when no results are found
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass
from collections import OrderedDict

from .ai_constraint_engine import ConstraintEngine, Constraint, ConstraintType
from .ai_goal_understanding import UserGoal

logger = logging.getLogger(__name__)


class RelaxationStrategy(Enum):
    """Strategies for constraint relaxation"""
    BUDGET_SLIGHT = "budget_slight"
    BUDGET_MODERATE = "budget_moderate"
    LOCATION_EXPAND = "location_expand"
    REMOVE_OPTIONAL = "remove_optional"
    CHANGE_TYPE = "change_type"
    DISTRICT_RELAX = "district_relax"


@dataclass
class RelaxationSuggestion:
    """Suggestion for constraint relaxation"""
    strategy: RelaxationStrategy
    description: str
    estimated_result_count: int
    requires_approval: bool
    confidence: float
    original_constraint: Dict
    relaxed_constraint: Dict
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'strategy': self.strategy.value,
            'description': self.description,
            'estimated_result_count': self.estimated_result_count,
            'requires_approval': self.requires_approval,
            'confidence': self.confidence,
            'original_constraint': self.original_constraint,
            'relaxed_constraint': self.relaxed_constraint
        }


class QueryRelaxationEngine:
    """
    Advanced query relaxation engine for handling empty search results
    Provides intelligent constraint relaxation with user approval
    """
    
    def __init__(self):
        self.constraint_engine = ConstraintEngine()
        self.relaxation_priority = self._initialize_relaxation_priority()
        self.relaxation_history: List[Dict] = []
    
    def analyze_empty_results(self, 
                            user_goal: UserGoal,
                            query_params: Dict,
                            estimated_total_count: int = 0) -> List[RelaxationSuggestion]:
        """
        Analyze empty results and suggest relaxation strategies
        
        Args:
            user_goal: User's goal and constraints
            query_params: Query parameters that returned no results
            estimated_total_count: Estimated total available items
            
        Returns:
            List of relaxation suggestions
        """
        try:
            suggestions = []
            
            # Build constraint set from user goal
            constraint_set = self.constraint_engine.build_constraint_set_from_goal(user_goal)
            
            # Analyze which constraints are most restrictive
            constraint_analysis = self._analyze_constraint_restrictiveness(
                constraint_set, query_params, estimated_total_count
            )
            
            # Generate suggestions based on analysis
            for constraint_info in constraint_analysis:
                suggestion = self._generate_relaxation_suggestion(
                    constraint_info, user_goal, estimated_total_count
                )
                if suggestion:
                    suggestions.append(suggestion)
            
            # Sort suggestions by priority and confidence
            suggestions.sort(key=lambda x: (
                self.relaxation_priority.get(x.strategy.value, 5),
                -x.confidence
            ))
            
            # Limit to top suggestions
            return suggestions[:5]
            
        except Exception as e:
            logger.error(f"Error analyzing empty results: {str(e)}")
            return []
    
    def _analyze_constraint_restrictiveness(self, 
                                        constraint_set,
                                        query_params: Dict,
                                        total_count: int) -> List[Dict]:
        """Analyze which constraints are most restrictive"""
        analysis = []
        
        for constraint in constraint_set.constraints:
            if constraint.constraint_type == ConstraintType.MUST_HAVE and not constraint.relaxed:
                restrictiveness = self._calculate_constraint_restrictiveness(
                    constraint, query_params, total_count
                )
                
                analysis.append({
                    'constraint': constraint.to_dict(),
                    'restrictiveness': restrictiveness,
                    'field': constraint.field,
                    'value': constraint.value
                })
        
        # Sort by restrictiveness
        analysis.sort(key=lambda x: x['restrictiveness'], reverse=True)
        
        return analysis
    
    def _calculate_constraint_restrictiveness(self, 
                                            constraint: Constraint,
                                            query_params: Dict,
                                            total_count: int) -> float:
        """Calculate how restrictive a constraint is"""
        restrictiveness = 0.0
        
        # Budget constraints are usually highly restrictive
        if constraint.field == 'budget':
            restrictiveness += 0.9
        
        # Location constraints are highly restrictive
        if constraint.field == 'location':
            restrictiveness += 0.8
        
        # Property type is moderately restrictive
        if constraint.field == 'property_type':
            restrictiveness += 0.6
        
        # District is less restrictive than governorate
        if constraint.field == 'district':
            restrictiveness += 0.4
        
        # Optional constraints have low restrictiveness
        if constraint.constraint_type == ConstraintType.OPTIONAL:
            restrictiveness += 0.2
        
        return restrictiveness
    
    def _generate_relaxation_suggestion(self, 
                                       constraint_info: Dict,
                                       user_goal: UserGoal,
                                       total_count: int) -> Optional[RelaxationSuggestion]:
        """Generate a specific relaxation suggestion"""
        constraint = constraint_info['constraint']
        field = constraint['field']
        value = constraint['value']
        
        # Determine appropriate relaxation strategy
        if field == 'budget':
            return self._generate_budget_relaxation(constraint, user_goal, total_count)
        elif field == 'location':
            return self._generate_location_relaxation(constraint, user_goal, total_count)
        elif field == 'property_type':
            return self._generate_type_relaxation(constraint, user_goal, total_count)
        elif field == 'district':
            return self._generate_district_relaxation(constraint, user_goal, total_count)
        else:
            return self._generate_generic_relaxation(constraint, user_goal, total_count)
    
    def _generate_budget_relaxation(self, 
                                    constraint: Dict,
                                    user_goal: UserGoal,
                                    total_count: int) -> RelaxationSuggestion:
        """Generate budget relaxation suggestion"""
        current_budget = constraint.get('value')
        
        if isinstance(current_budget, dict):
            max_budget = current_budget.get('max')
        else:
            max_budget = current_budget
        
        # Calculate relaxed budget
        if isinstance(max_budget, (int, float)):
            slight_increase = int(max_budget * 1.1)  # 10% increase
            moderate_increase = int(max_budget * 1.2)  # 20% increase
            
            # Estimate results with relaxed budget
            estimated_results = self._estimate_results_with_relaxed_budget(
                user_goal, moderate_increase, total_count
            )
            
            return RelaxationSuggestion(
                strategy=RelaxationStrategy.BUDGET_MODERATE,
                description=f"زيادة الميزانية إلى {moderate_increase:,} دينار (زيادة 20%)",
                estimated_result_count=estimated_results,
                requires_approval=True,
                confidence=0.8,
                original_constraint=constraint,
                relaxed_constraint={'max': moderate_increase}
            )
        
        return None
    
    def _generate_location_relaxation(self, 
                                     constraint: Dict,
                                     user_goal: UserGoal,
                                     total_count: int) -> RelaxationSuggestion:
        """Generate location relaxation suggestion"""
        current_location = constraint.get('value')
        
        # Suggest expanding to nearby governorates
        if isinstance(current_location, str):
            nearby_locations = self._get_nearby_locations(current_location)
            
            if nearby_locations:
                estimated_results = self._estimate_results_with_expanded_location(
                    user_goal, nearby_locations, total_count
                )
                
                return RelaxationSuggestion(
                    strategy=RelaxationStrategy.LOCATION_EXPAND,
                    description=f"التوسع للبحث في {', '.join(nearby_locations[:2])}",
                    estimated_result_count=estimated_results,
                    requires_approval=True,
                    confidence=0.7,
                    original_constraint=constraint,
                    relaxed_constraint={'locations': nearby_locations}
                )
        
        return None
    
    def _generate_type_relaxation(self, 
                                  constraint: Dict,
                                  user_goal: UserGoal,
                                  total_count: int) -> RelaxationSuggestion:
        """Generate property type relaxation suggestion"""
        current_type = constraint.get('value')
        
        # Suggest including other types
        alternative_types = self._get_alternative_types(current_type)
        
        if alternative_types:
            estimated_results = self._estimate_results_with_type_change(
                user_goal, alternative_types, total_count
            )
            
            return RelaxationSuggestion(
                strategy=RelaxationStrategy.CHANGE_TYPE,
                description=f"البحث أيضًا عن {', '.join(alternative_types[:2])}",
                estimated_result_count=estimated_results,
                requires_approval=False,
                confidence=0.6,
                original_constraint=constraint,
                relaxed_constraint={'types': alternative_types}
            )
        
        return None
    
    def _generate_district_relaxation(self, 
                                   constraint: Dict,
                                   user_goal: UserGoal,
                                   total_count: int) -> RelaxationSuggestion:
        """Generate district relaxation suggestion"""
        # District relaxation usually doesn't require approval
        return RelaxationSuggestion(
            strategy=RelaxationStrategy.DISTRICT_RELAX,
            description="إزالة شرط المنطقة المحددة",
            estimated_result_count=int(total_count * 0.3),  # Estimate 30% more results
            requires_approval=False,
            confidence=0.9,
            original_constraint=constraint,
            relaxed_constraint={'district': None}
        )
    
    def _generate_generic_relaxation(self, 
                                    constraint: Dict,
                                    user_goal: UserGoal,
                                    total_count: int) -> RelaxationSuggestion:
        """Generate generic relaxation suggestion"""
        return RelaxationSuggestion(
            strategy=RelaxationStrategy.REMOVE_OPTIONAL,
            description=f"إزالة شرط {constraint.get('field')}",
            estimated_result_count=int(total_count * 0.1),
            requires_approval=False,
            confidence=0.5,
            original_constraint=constraint,
            relaxed_constraint={}
        )
    
    def _get_nearby_locations(self, location: str) -> List[str]:
        """Get nearby governorates"""
        # This would be based on actual geography
        nearby_map = {
            'البصرة': ['ذي قار', 'ميسان', 'المثنى'],
            'بغداد': ['بابل', 'ديالى', 'الأنبار'],
            'البصرة': ['العمارة', 'الناصرية', 'ميسان'],
            'أربيل': ['دهوك', 'السليمانية', 'كرموك'],
            'الموصل': 'نينوى',
            'كركوك': 'السليمانية',
            'النجف': 'كربلاء',
            'كربلاء': 'بابل'
        }
        
        return nearby_map.get(location, [])
    
    def _get_alternative_types(self, current_type: str) -> List[str]:
        """Get alternative property types"""
        type_alternatives = {
            'house': ['apartment', 'villa'],
            'apartment': ['house', 'villa'],
            'villa': ['house', 'apartment'],
            'land': ['house', 'apartment']
        }
        
        return type_alternatives.get(current_type, [])
    
    def _estimate_results_with_relaxed_budget(self, 
                                            user_goal: UserGoal,
                                            relaxed_budget: int,
                                            total_count: int) -> int:
        """Estimate results with relaxed budget"""
        # Simple heuristic: each 10% budget increase adds ~15% more results
        original_budget = user_goal.entities.get('price', {})
        if isinstance(original_budget, dict):
            original_budget = original_budget.get('max', 0)
        
        if original_budget > 0:
            budget_increase_ratio = (relaxed_budget - original_budget) / original_budget
            estimated_increase = budget_increase_ratio * 1.5
            return int(total_count * (1 + estimated_increase))
        
        return int(total_count * 0.2)
    
    def _estimate_results_with_expanded_location(self, 
                                              user_goal: UserGoal,
                                              expanded_locations: List[str],
                                              total_count: int) -> int:
        """Estimate results with expanded location"""
        # Adding nearby locations roughly doubles results
        return int(total_count * len(expanded_locations))
    
    def _estimate_results_with_type_change(self, 
                                          user_goal: UserGoal,
                                          alternative_types: List[str],
                                          total_count: int) -> int:
        """Estimate results with type change"""
        # Adding alternative types adds ~50% more results
        return int(total_count * 1.5)
    
    def apply_relaxation(self, 
                        user_goal: UserGoal,
                        suggestion: RelaxationSuggestion,
                        user_approved: bool = False) -> UserGoal:
        """
        Apply a relaxation suggestion to the user goal
        
        Args:
            user_goal: Original user goal
            suggestion: Relaxation suggestion to apply
            user_approved: Whether user approved the relaxation
            
        Returns:
            Modified user goal
        """
        if not user_approved and suggestion.requires_approval:
            logger.info(f"User did not approve relaxation: {suggestion.strategy.value}")
            return user_goal
        
        # Apply relaxation based on strategy
        if suggestion.strategy == RelaxationStrategy.BUDGET_MODERATE:
            relaxed_budget = suggestion.relaxed_constraint.get('max')
            if relaxed_budget:
                if 'price' not in user_goal.entities:
                    user_goal.entities['price'] = {}
                user_goal.entities['price']['max'] = relaxed_budget
                user_goal.entities['price']['relaxed'] = True
        
        elif suggestion.strategy == RelaxationStrategy.LOCATION_EXPAND:
            expanded_locations = suggestion.relaxed_constraint.get('locations', [])
            if expanded_locations:
                user_goal.entities['expanded_locations'] = expanded_locations
                user_goal.entities['location_relaxed'] = True
        
        elif suggestion.strategy == RelaxationStrategy.CHANGE_TYPE:
            alternative_types = suggestion.relaxed_constraint.get('types', [])
            if alternative_types:
                user_goal.entities['alternative_types'] = alternative_types
                user_goal.entities['type_relaxed'] = True
        
        elif suggestion.strategy == RelaxationStrategy.DISTRICT_RELAX:
            if 'district' in user_goal.entities:
                del user_goal.entities['district']
            user_goal.entities['district_relaxed'] = True
        
        # Record relaxation in history
        self.relaxation_history.append({
            'timestamp': self._get_timestamp(),
            'strategy': suggestion.strategy.value,
            'description': suggestion.description,
            'user_approved': user_approved,
            'estimated_results': suggestion.estimated_result_count
        })
        
        logger.info(f"Applied relaxation: {suggestion.strategy.value}")
        return user_goal
    
    def generate_counterfactual_message(self, 
                                        suggestion: RelaxationSuggestion,
                                        current_results: int) -> str:
        """Generate user-friendly counterfactual message"""
        if suggestion.estimated_result_count > 0:
            return f"إذا {suggestion.description}، تظهر تقريبًا {suggestion.estimated_result_count} نتيجة بدل من {current_results}."
        else:
            return f"جرب {suggestion.description} لمزيد من الخيارات."
    
    def _initialize_relaxation_priority(self) -> Dict[str, int]:
        """Initialize priority for relaxation strategies"""
        return {
            'remove_optional': 1,  # Highest priority (safest)
            'district_relax': 2,
            'change_type': 3,
            'budget_slight': 4,
            'budget_moderate': 5,
            'location_expand': 6
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_relaxation_explanation(self, suggestion: RelaxationSuggestion) -> str:
        """Get detailed explanation for why relaxation is suggested"""
        explanations = {
            RelaxationStrategy.BUDGET_MODERATE: "الميزانية الحالية قد تكون صارمة جدًا. زيادتها بنسبة 20% قد تظهر خيارات إضافية.",
            RelaxationStrategy.LOCATION_EXPAND: "البحث في المحافظة الحالية فقط قد يكون محدودًا. التوسع للمحافظات المجاورة قد يزيد الخيارات.",
            RelaxationStrategy.CHANGE_TYPE: "نوع العقار المحدد قد لا يكون متوفرًا. البحث عن أنواع بديلة قد يظهر نتائج.",
            RelaxationStrategy.DISTRICT_RELAX: "تحديد المنطقة قد يحد الخيارات. إزالة هذا الشرط قد يظهر نتائج في مناطق أخرى.",
            RelaxationStrategy.REMOVE_OPTIONAL: "بعض التفضيلات الاختيارية قد تكون محدودة. إزالتها قد يظهر نتائج إضافية."
        }
        
        return explanations.get(suggestion.strategy, "تخفيف هذا الشرط قد يظهر نتائج إضافية.")


# Global instance
query_relaxation_engine = QueryRelaxationEngine()