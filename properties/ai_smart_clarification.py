"""
Smart Clarification System with Information Gain
Intelligently selects the most informative questions to ask users
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass
from collections import defaultdict
import math

from .ai_goal_understanding import UserGoal, GoalType
from .ai_constraint_engine import ConstraintEngine, ConstraintType

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Types of clarification questions"""
    LOCATION = "location"
    BUDGET = "budget"
    PROPERTY_TYPE = "property_type"
    PURPOSE = "purpose"
    PREFERENCES = "preferences"
    TIMING = "timing"
    CONTACT = "contact"
    NAVIGATION = "navigation"


class InformationGainCalculator:
    """Calculates information gain for potential questions"""
    
    def __init__(self):
        self.field_entropy_cache = {}
        self.result_count_cache = {}
    
    def calculate_information_gain(self, 
                                   field: str, 
                                   current_context: Dict, 
                                   total_estimated_results: int) -> float:
        """
        Calculate information gain for asking about a specific field
        
        Args:
            field: Field to ask about
            current_context: Current known information
            total_estimated_results: Current estimated result count
            
        Returns:
            Information gain score (0-1)
        """
        try:
            # Get entropy reduction if this field is known
            current_entropy = self._calculate_field_entropy(field, current_context)
            
            # Estimate entropy after knowing this field
            hypothetical_context = current_context.copy()
            hypothetical_context[field] = 'known'  # Simulate knowing this field
            new_entropy = self._calculate_field_entropy(field, hypothetical_context)
            
            # Information gain = entropy reduction
            information_gain = current_entropy - new_entropy
            
            # Normalize to 0-1 range
            max_possible_gain = self._get_max_possible_entropy(field)
            normalized_gain = information_gain / max_possible_gain if max_possible_gain > 0 else 0
            
            # Apply result count factor
            result_factor = self._calculate_result_count_factor(field, total_estimated_results)
            
            final_score = normalized_gain * result_factor
            
            return min(final_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating information gain for {field}: {str(e)}")
            return 0.0
    
    def _calculate_field_entropy(self, field: str, context: Dict) -> float:
        """Calculate entropy for a specific field given current context"""
        # Field-specific entropy calculations
        field_entropy_map = {
            'governorate': self._calculate_location_entropy,
            'price': self._calculate_price_entropy,
            'property_type': self._calculate_type_entropy,
            'district': self._calculate_district_entropy,
            'area': self._calculate_area_entropy
        }
        
        calculator = field_entropy_map.get(field, self._calculate_generic_entropy)
        return calculator(context)
    
    def _calculate_location_entropy(self, context: Dict) -> float:
        """Calculate entropy for location field"""
        if context.get('governorate'):
            return 0.1  # Low entropy if governorate known
        return 0.9  # High entropy if location unknown
    
    def _calculate_price_entropy(self, context: Dict) -> float:
        """Calculate entropy for price field"""
        if context.get('price'):
            return 0.2
        return 0.8
    
    def _calculate_type_entropy(self, context: Dict) -> float:
        """Calculate entropy for property type field"""
        if context.get('property_type'):
            return 0.1
        return 0.7
    
    def _calculate_district_entropy(self, context: Dict) -> float:
        """Calculate entropy for district field"""
        if context.get('district'):
            return 0.1
        # Lower priority if governorate not known
        if not context.get('governorate'):
            return 0.3
        return 0.6
    
    def _calculate_area_entropy(self, context: Dict) -> float:
        """Calculate entropy for area field"""
        if context.get('area'):
            return 0.2
        return 0.5
    
    def _calculate_generic_entropy(self, context: Dict) -> float:
        """Calculate generic entropy for unknown fields"""
        return 0.5
    
    def _get_max_possible_entropy(self, field: str) -> float:
        """Get maximum possible entropy for a field"""
        max_entropy_map = {
            'governorate': 0.9,
            'price': 0.8,
            'property_type': 0.7,
            'district': 0.6,
            'area': 0.5
        }
        return max_entropy_map.get(field, 0.5)
    
    def _calculate_result_count_factor(self, field: str, current_results: int) -> float:
        """
        Calculate factor based on current result count
        Fields that reduce large result sets get higher priority
        """
        if current_results == 0:
            return 1.0  # Maximum priority when no results
        
        # Logarithmic scaling
        factor = 1.0 - (math.log10(current_results) / math.log10(10000))
        return max(factor, 0.1)
    
    def estimate_result_count(self, query_params: Dict) -> int:
        """Estimate number of results for given query parameters"""
        # This would typically query the database for actual counts
        # For now, use heuristic estimation
        
        base_count = 10000  # Estimated total properties
        
        # Reduce count based on known parameters
        if query_params.get('governorate'):
            base_count = int(base_count * 0.3)  # 30% in one governorate
        if query_params.get('property_type'):
            base_count = int(base_count * 0.4)  # 40% of one type
        if query_params.get('price'):
            base_count = int(base_count * 0.5)  # 50% in price range
        if query_params.get('district'):
            base_count = int(base_count * 0.2)  # 20% in one district
        
        return max(base_count, 1)


@dataclass
class ClarificationQuestion:
    """Represents a clarification question with metadata"""
    question_type: QuestionType
    question_text: str
    information_gain: float
    priority: float
    context_field: str
    user_friendly: bool = True
    optional: bool = False


class SmartClarificationSystem:
    """
    Smart clarification system that selects optimal questions
    based on information gain and context
    """
    
    def __init__(self):
        self.information_gain_calculator = InformationGainCalculator()
        self.question_templates = self._initialize_question_templates()
        self.question_history: List[Dict] = []
    
    def generate_clarification_questions(self, 
                                        user_goal: UserGoal, 
                                        conversation_context: Dict) -> List[ClarificationQuestion]:
        """
        Generate optimal clarification questions based on information gain
        
        Args:
            user_goal: Current user goal
            conversation_context: Conversation context
            
        Returns:
            List of clarification questions sorted by priority
        """
        try:
            # Identify missing information
            missing_fields = self._identify_missing_fields(user_goal)
            
            if not missing_fields:
                return []  # No clarification needed
            
            # Calculate information gain for each potential question
            questions = []
            
            for field in missing_fields:
                question = self._create_question_for_field(field, user_goal, conversation_context)
                if question:
                    # Calculate information gain
                    current_context = self._build_query_context(user_goal, conversation_context)
                    estimated_results = self.information_gain_calculator.estimate_result_count(current_context)
                    
                    information_gain = self.information_gain_calculator.calculate_information_gain(
                        field, current_context, estimated_results
                    )
                    
                    question.information_gain = information_gain
                    question.priority = self._calculate_priority(question, user_goal)
                    
                    questions.append(question)
            
            # Sort by priority
            questions.sort(key=lambda q: q.priority, reverse=True)
            
            # Return top questions (max 3 to avoid overwhelming user)
            return questions[:3]
            
        except Exception as e:
            logger.error(f"Error generating clarification questions: {str(e)}")
            return []
    
    def _identify_missing_fields(self, user_goal: UserGoal) -> List[str]:
        """Identify fields that need clarification"""
        missing_fields = []
        
        # Critical fields for property search
        if user_goal.goal == GoalType.FIND_PROPERTY:
            if not user_goal.entities.get('governorate'):
                missing_fields.append('governorate')
            if not user_goal.entities.get('property_type'):
                missing_fields.append('property_type')
            if not user_goal.entities.get('price'):
                missing_fields.append('price')
            
            # Secondary fields
            if user_goal.entities.get('governorate') and not user_goal.entities.get('district'):
                missing_fields.append('district')
        
        elif user_goal.goal == GoalType.FIND_JOB:
            if not user_goal.entities.get('governorate'):
                missing_fields.append('governorate')
            if not user_goal.entities.get('job_type'):
                missing_fields.append('job_type')
        
        return missing_fields
    
    def _create_question_for_field(self, 
                                  field: str, 
                                  user_goal: UserGoal, 
                                  context: Dict) -> Optional[ClarificationQuestion]:
        """Create a clarification question for a specific field"""
        question_map = {
            'governorate': self._create_location_question,
            'price': self._create_budget_question,
            'property_type': self._create_type_question,
            'district': self._create_district_question,
            'area': self._create_area_question,
            'job_type': self._create_job_type_question
        }
        
        question_creator = question_map.get(field)
        if question_creator:
            return question_creator(user_goal, context)
        
        return None
    
    def _create_location_question(self, user_goal: UserGoal, context: Dict) -> ClarificationQuestion:
        """Create location clarification question"""
        question_text = "في أي محافظة تبحث عن العقار؟"
        
        # Personalize based on context
        if context.get('previous_locations'):
            recent_location = context['previous_locations'][0]
            question_text = f"هل تبحث في {recent_location} أم محافظة أخرى؟"
        
        return ClarificationQuestion(
            question_type=QuestionType.LOCATION,
            question_text=question_text,
            information_gain=0.0,  # Will be calculated
            priority=0.0,  # Will be calculated
            context_field='governorate',
            user_friendly=True,
            optional=False
        )
    
    def _create_budget_question(self, user_goal: UserGoal, context: Dict) -> ClarificationQuestion:
        """Create budget clarification question"""
        question_text = "ما هي ميزانيتك التقريبية؟"
        
        # Check if there's any budget context
        if context.get('budget_range'):
            question_text = f"هل ميزانيتك ضمن {context['budget_range']} أم مختلفة؟"
        
        return ClarificationQuestion(
            question_type=QuestionType.BUDGET,
            question_text=question_text,
            information_gain=0.0,
            priority=0.0,
            context_field='price',
            user_friendly=True,
            optional=False
        )
    
    def _create_type_question(self, user_goal: UserGoal, context: Dict) -> ClarificationQuestion:
        """Create property type clarification question"""
        question_text = "هل تبحث عن بيت، شقة، أرض، أو نوع آخر؟"
        
        # Personalize based on purpose
        if user_goal.purpose == 'family':
            question_text = "هل تفضل بيت للعائلة أم شقة؟"
        elif user_goal.purpose == 'investment':
            question_text = "هل تبحث عن عقار للاستثمار، أي نوع يفضل؟"
        
        return ClarificationQuestion(
            question_type=QuestionType.PROPERTY_TYPE,
            question_text=question_text,
            information_gain=0.0,
            priority=0.0,
            context_field='property_type',
            user_friendly=True,
            optional=False
        )
    
    def _create_district_question(self, user_goal: UserGoal, context: Dict) -> ClarificationQuestion:
        """Create district clarification question"""
        governorate = user_goal.entities.get('governorate', 'المنطقة')
        question_text = f"في أي منطقة من {governorate} تفضل؟"
        
        return ClarificationQuestion(
            question_type=QuestionType.LOCATION,
            question_text=question_text,
            information_gain=0.0,
            priority=0.0,
            context_field='district',
            user_friendly=True,
            optional=True
        )
    
    def _create_area_question(self, user_goal: UserGoal, context: Dict) -> ClarificationQuestion:
        """Create area clarification question"""
        question_text = "هل لديك تفضيل لمساحة العقار؟"
        
        return ClarificationQuestion(
            question_type=QuestionType.PREFERENCES,
            question_text=question_text,
            information_gain=0.0,
            priority=0.0,
            context_field='area',
            user_friendly=True,
            optional=True
        )
    
    def _create_job_type_question(self, user_goal: UserGoal, context: Dict) -> ClarificationQuestion:
        """Create job type clarification question"""
        question_text = "ما نوع الوظيفة التي تبحث عنها؟"
        
        return ClarificationQuestion(
            question_type=QuestionType.PREFERENCES,
            question_text=question_text,
            information_gain=0.0,
            priority=0.0,
            context_field='job_type',
            user_friendly=True,
            optional=False
        )
    
    def _calculate_priority(self, question: ClarificationQuestion, user_goal: UserGoal) -> float:
        """Calculate overall priority for a question"""
        base_priority = question.information_gain * 0.7
        
        # Boost priority for mandatory questions
        if not question.optional:
            base_priority += 0.2
        
        # Boost priority for user-friendly questions
        if question.user_friendly:
            base_priority += 0.1
        
        # Adjust based on user goal confidence
        if user_goal.confidence < 0.5:
            base_priority += 0.1
        
        return min(base_priority, 1.0)
    
    def _build_query_context(self, user_goal: UserGoal, conversation_context: Dict) -> Dict:
        """Build query context for information gain calculation"""
        context = {}
        
        # Add entities from user goal
        context.update(user_goal.entities)
        
        # Add context from conversation
        if conversation_context:
            context.update(conversation_context.get('entities', {}))
        
        return context
    
    def _initialize_question_templates(self) -> Dict:
        """Initialize question templates"""
        return {
            QuestionType.LOCATION: [
                "في أي محافظة تبحث؟",
                "هل تفضل منطقة معينة؟",
                "الموقع المهم بالنسبة لك أين؟"
            ],
            QuestionType.BUDGET: [
                "ما هي ميزانيتك؟",
                "كم تقدر تنفق؟",
                "ما هو السعر المناسب لك؟"
            ],
            QuestionType.PROPERTY_TYPE: [
                "ما نوع العقار الذي تبحث عنه؟",
                "بيت أم شقة؟",
                "هل تبحث عن أرض للبناء؟"
            ]
        }
    
    def select_best_question(self, questions: List[ClarificationQuestion]) -> Optional[ClarificationQuestion]:
        """Select the single best question to ask"""
        if not questions:
            return None
        
        # Sort by priority and return top
        questions.sort(key=lambda q: q.priority, reverse=True)
        return questions[0]
    
    def format_question_response(self, question: ClarificationQuestion) -> str:
        """Format question for user response"""
        response = question.question_text
        
        # Add helpful hints for optional questions
        if question.optional:
            response += " (اختياري)"
        
        return response
    
    def track_question_asked(self, question: ClarificationQuestion, user_response: str):
        """Track question and user response for learning"""
        self.question_history.append({
            'timestamp': self._get_timestamp(),
            'question': question.to_dict() if hasattr(question, 'to_dict') else str(question),
            'user_response': user_response,
            'information_gain': question.information_gain,
            'priority': question.priority
        })
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# Global instance
smart_clarification_system = SmartClarificationSystem()