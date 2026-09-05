"""
Advanced User Goal Understanding System
Extracts comprehensive user goals, constraints, preferences, and context from user input
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
import re
from collections import defaultdict

from .ai_intent_classifier import intent_classifier
from .ai_entity_extraction import entity_extractor
from .ai_arabic_normalizer import ArabicNormalizer

logger = logging.getLogger(__name__)


class GoalType(Enum):
    """Types of user goals"""
    FIND_PROPERTY = "find_property"
    FIND_JOB = "find_job"
    FIND_HOTEL = "find_hotel"
    FIND_SERVICE = "find_service"
    SELL_PROPERTY = "sell_property"
    JOIN_AGENT = "join_agent"
    GENERAL_INFO = "general_info"
    NAVIGATION = "navigation"
    COMPARISON = "comparison"
    SAVING = "saving"
    CONTACT = "contact"


class ConstraintType(Enum):
    """Types of constraints"""
    MUST_HAVE = "must_have"
    PREFERRED = "preferred"
    OPTIONAL = "optional"
    FORBIDDEN = "forbidden"


class UserGoal:
    """Comprehensive user goal representation"""
    
    def __init__(self):
        self.intent: str = None
        self.goal: GoalType = None
        self.purpose: str = None
        self.constraints: Dict[ConstraintType, List[Dict]] = defaultdict(list)
        self.preferences: List[str] = []
        self.entities: Dict[str, Any] = {}
        self.actions: List[str] = []
        self.context: Dict[str, Any] = {}
        self.confidence: float = 0.0
        self.ambiguity_score: float = 0.0
        self.missing_information: List[str] = []
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'intent': self.intent,
            'goal': self.goal.value if self.goal else None,
            'purpose': self.purpose,
            'constraints': {
                constraint_type.value: constraints 
                for constraint_type, constraints in self.constraints.items()
            },
            'preferences': self.preferences,
            'entities': self.entities,
            'actions': self.actions,
            'context': self.context,
            'confidence': self.confidence,
            'ambiguity_score': self.ambiguity_score,
            'missing_information': self.missing_information,
            'metadata': self.metadata
        }


class UserGoalUnderstandingSystem:
    """
    Advanced system for understanding user goals beyond simple intent detection
    """
    
    def __init__(self):
        self.arabic_normalizer = ArabicNormalizer()
        self.goal_patterns = self._initialize_goal_patterns()
        self.purpose_patterns = self._initialize_purpose_patterns()
        self.constraint_patterns = self._initialize_constraint_patterns()
        self.preference_patterns = self._initialize_preference_patterns()
    
    def understand_goal(self, user_input: str, conversation_context: Dict = None) -> UserGoal:
        """
        Comprehensive goal understanding from user input
        
        Args:
            user_input: User's text or voice input
            conversation_context: Previous conversation context
            
        Returns:
            UserGoal object with comprehensive understanding
        """
        try:
            # Normalize input
            normalized_input = self.arabic_normalizer.normalize_text(user_input)
            
            # Create goal object
            user_goal = UserGoal()
            
            # Extract basic intent
            intent_result = intent_detector.detect_intent(normalized_input)
            user_goal.intent = intent_result.get('intent', 'unknown')
            user_goal.confidence = intent_result.get('confidence', 0.0)
            
            # Extract entities
            entities = entity_extractor.extract_entities(normalized_input)
            user_goal.entities = entities
            
            # Determine goal type
            user_goal.goal = self._determine_goal_type(normalized_input, user_goal.intent, entities)
            
            # Extract purpose
            user_goal.purpose = self._extract_purpose(normalized_input, entities)
            
            # Extract constraints
            self._extract_constraints(normalized_input, entities, user_goal)
            
            # Extract preferences
            self._extract_preferences(normalized_input, entities, user_goal)
            
            # Extract actions
            user_goal.actions = self._extract_actions(normalized_input, user_goal.intent)
            
            # Build context
            user_goal.context = self._build_context(normalized_input, conversation_context, user_goal)
            
            # Calculate ambiguity
            user_goal.ambiguity_score = self._calculate_ambiguity(user_goal)
            
            # Identify missing information
            user_goal.missing_information = self._identify_missing_information(user_goal)
            
            # Add metadata
            user_goal.metadata = {
                'original_input': user_input,
                'normalized_input': normalized_input,
                'processing_timestamp': self._get_timestamp()
            }
            
            logger.info(f"Goal understood: {user_goal.goal.value} with confidence {user_goal.confidence}")
            return user_goal
            
        except Exception as e:
            logger.error(f"Error understanding user goal: {str(e)}")
            return self._create_error_goal(user_input)
    
    def _determine_goal_type(self, input_text: str, intent: str, entities: Dict) -> GoalType:
        """Determine the specific goal type"""
        # Map intents to goal types
        intent_to_goal = {
            'buy_property': GoalType.FIND_PROPERTY,
            'sell_property': GoalType.SELL_PROPERTY,
            'find_job': GoalType.FIND_JOB,
            'find_hotel': GoalType.FIND_HOTEL,
            'find_service': GoalType.FIND_SERVICE,
            'join_agent': GoalType.JOIN_AGENT
        }
        
        # Check for comparison keywords
        comparison_keywords = ['قارن', 'أي واحد أفضل', 'الفرق بين', 'مقارنة']
        if any(keyword in input_text for keyword in comparison_keywords):
            return GoalType.COMPARISON
        
        # Check for saving keywords
        saving_keywords = ['احفظ', 'خلي احفظ', 'أريد احفظ', 'أضف للمفضلة']
        if any(keyword in input_text for keyword in saving_keywords):
            return GoalType.SAVING
        
        # Check for contact keywords
        contact_keywords = ['اتصل', 'تواصل', 'اريد اتصل', 'أريد رقم']
        if any(keyword in input_text for keyword in contact_keywords):
            return GoalType.CONTACT
        
        # Check for navigation keywords
        navigation_keywords = ['افتح', 'وديني', 'روح', 'اذهب', 'انتقل']
        if any(keyword in input_text for keyword in navigation_keywords):
            return GoalType.NAVIGATION
        
        # Use intent mapping
        return intent_to_goal.get(intent, GoalType.GENERAL_INFO)
    
    def _extract_purpose(self, input_text: str, entities: Dict) -> str:
        """Extract the purpose behind the user's request"""
        purpose_patterns = {
            'family': ['للعائلة', 'للاسرة', 'عائلي', 'أسرية', 'للأطفال'],
            'investment': ['للاستثمار', 'استثمار', 'تجاري', 'مشروع'],
            'personal': ['شخصي', 'سكن شخصي', 'أسكن', 'للسكن'],
            'rental': ['للايجار', 'ايجار', 'تأجير'],
            'business': ['للعمل', 'تجاري', 'مكتب', 'عمل'],
            'vacation': ['للعطلة', 'سياحة', 'قضاء عطلة']
        }
        
        for purpose, keywords in purpose_patterns.items():
            if any(keyword in input_text for keyword in keywords):
                return purpose
        
        # Infer from entities
        if entities.get('property_type') == 'apartment' and 'rent' in input_text:
            return 'rental'
        
        return None
    
    def _extract_constraints(self, input_text: str, entities: Dict, user_goal: UserGoal):
        """Extract constraints and classify them by type"""
        
        # MUST HAVE constraints
        must_have = []
        
        # Location is usually must-have
        if entities.get('governorate'):
            must_have.append({
                'type': 'location',
                'value': entities['governorate'],
                'source': 'explicit'
            })
        
        # Property type is usually must-have
        if entities.get('property_type'):
            must_have.append({
                'type': 'property_type',
                'value': entities['property_type'],
                'source': 'explicit'
            })
        
        # Budget constraints
        if entities.get('price'):
            must_have.append({
                'type': 'budget',
                'value': entities['price'],
                'constraint_type': 'max' if 'أقل من' in input_text or 'حدود' in input_text else 'exact',
                'source': 'explicit'
            })
        
        # FORBIDDEN constraints
        forbidden = []
        
        # Negative patterns
        forbidden_patterns = [
            (r'بدون\s+(\w+)', 'without'),
            (r'لا\s+أريد\s+(\w+)', 'not_want'),
            (r'بدون\s+(\w+)', 'without')
        ]
        
        for pattern, constraint_type in forbidden_patterns:
            matches = re.findall(pattern, input_text)
            for match in matches:
                forbidden.append({
                    'type': constraint_type,
                    'value': match,
                    'source': 'explicit'
                })
        
        # PREFERRED constraints
        preferred = []
        
        # Preferred patterns
        preferred_keywords = ['أفضل', 'أحب', 'يفضل', 'مناسب', 'جيد']
        if any(keyword in input_text for keyword in preferred_keywords):
            if entities.get('district'):
                preferred.append({
                    'type': 'district',
                    'value': entities['district'],
                    'source': 'preference'
                })
        
        # OPTIONAL constraints
        optional = []
        
        # Optional amenities
        amenity_keywords = ['حديقة', 'موقف سيارات', 'مسبح', 'مصعد']
        for amenity in amenity_keywords:
            if amenity in input_text:
                optional.append({
                    'type': 'amenity',
                    'value': amenity,
                    'source': 'mentioned'
                })
        
        # Assign constraints to user goal
        user_goal.constraints[ConstraintType.MUST_HAVE] = must_have
        user_goal.constraints[ConstraintType.PREFERRED] = preferred
        user_goal.constraints[ConstraintType.OPTIONAL] = optional
        user_goal.constraints[ConstraintType.FORBIDDEN] = forbidden
    
    def _extract_preferences(self, input_text: str, entities: Dict, user_goal: UserGoal):
        """Extract user preferences"""
        preference_patterns = {
            'quiet': ['هادئ', 'هدوء', 'منطقة هادئة', 'بعيد عن الضوضاء'],
            'near_schools': ['قريب من المدارس', 'جانب مدرسة', 'قرب مدرسة'],
            'near_services': ['قريب من الخدمات', 'مركزي', 'قرب مركز'],
            'new': ['جديد', 'حديث', 'بناء حديث'],
            'modern': ['عصري', 'تشطيب عصري', 'حديث'],
            'large': ['كبير', 'واسع', 'مساحة كبيرة'],
            'small': ['صغير', 'مقبول', 'بسيط'],
            'affordable': ['رخيص', 'اقتصادي', 'بسعر مناسب'],
            'luxury': ['راقي', 'فاخر', 'مميز', 'عالي الجودة']
        }
        
        for preference, keywords in preference_patterns.items():
            if any(keyword in input_text for keyword in keywords):
                user_goal.preferences.append(preference)
        
        # Contextual preferences from purpose
        if user_goal.purpose == 'family':
            user_goal.preferences.extend(['quiet', 'near_schools', 'large'])
        elif user_goal.purpose == 'investment':
            user_goal.preferences.extend(['good_location', 'high_demand'])
    
    def _extract_actions(self, input_text: str, intent: str) -> List[str]:
        """Extract requested actions"""
        actions = []
        
        action_patterns = {
            'search': ['ابحث', 'دورلي', 'أريد أشوف', 'عرضلي'],
            'save': ['احفظ', 'خلي احفظ', 'أضف للمفضلة'],
            'compare': ['قارن', 'أي واحد أفضل', 'الفرق بين'],
            'contact': ['اتصل', 'تواصل', 'أريد رقم'],
            'navigate': ['افتح', 'وديني', 'روح', 'انتقل'],
            'sort': ['رتب', 'من الأرخص', 'من الأغلى', 'الأحدث']
        }
        
        for action, keywords in action_patterns.items():
            if any(keyword in input_text for keyword in keywords):
                actions.append(action)
        
        return actions
    
    def _build_context(self, input_text: str, conversation_context: Dict, user_goal: UserGoal) -> Dict:
        """Build comprehensive context for the goal"""
        context = {
            'current_input': input_text,
            'conversation_stage': self._determine_conversation_stage(conversation_context),
            'previous_goals': self._extract_previous_goals(conversation_context),
            'active_entities': self._merge_entities(conversation_context, user_goal.entities),
            'conversation_length': self._calculate_conversation_length(conversation_context),
            'user_type': self._determine_user_type(conversation_context)
        }
        
        return context
    
    def _determine_conversation_stage(self, context: Dict) -> str:
        """Determine current stage of conversation"""
        if not context:
            return 'initial'
        
        messages = context.get('messages', [])
        if len(messages) == 0:
            return 'initial'
        elif len(messages) < 3:
            return 'early'
        elif len(messages) < 6:
            return 'middle'
        else:
            return 'advanced'
    
    def _extract_previous_goals(self, context: Dict) -> List[str]:
        """Extract goals from previous conversation turns"""
        if not context:
            return []
        
        previous_goals = []
        messages = context.get('messages', [])
        
        for msg in messages[:-1]:  # Exclude current message
            if msg.get('user_goal'):
                previous_goals.append(msg['user_goal'].get('goal'))
        
        return previous_goals
    
    def _merge_entities(self, context: Dict, current_entities: Dict) -> Dict:
        """Merge entities from context with current entities"""
        if not context:
            return current_entities
        
        merged_entities = current_entities.copy()
        
        # Get entities from context
        context_entities = context.get('entities', {})
        
        # Merge with current entities taking precedence
        for key, value in context_entities.items():
            if key not in merged_entities:
                merged_entities[key] = value
        
        return merged_entities
    
    def _calculate_conversation_length(self, context: Dict) -> int:
        """Calculate conversation length"""
        if not context:
            return 0
        return len(context.get('messages', []))
    
    def _determine_user_type(self, context: Dict) -> str:
        """Determine user type based on behavior"""
        if not context:
            return 'new'
        
        # Check for saved searches, favorites, etc.
        if context.get('has_saved_searches'):
            return 'returning_with_preferences'
        elif context.get('conversation_count', 0) > 5:
            return 'experienced'
        else:
            return 'new'
    
    def _calculate_ambiguity(self, user_goal: UserGoal) -> float:
        """Calculate ambiguity score based on missing information"""
        ambiguity_score = 0.0
        
        # Check for missing critical information
        if user_goal.goal == GoalType.FIND_PROPERTY:
            if not user_goal.entities.get('governorate'):
                ambiguity_score += 0.3
            if not user_goal.entities.get('property_type'):
                ambiguity_score += 0.2
            if not user_goal.entities.get('price'):
                ambiguity_score += 0.2
        
        # Check for conflicting information
        if len(user_goal.constraints[ConstraintType.FORBIDDEN]) > 0:
            ambiguity_score += 0.1
        
        # Normalize
        return min(ambiguity_score, 1.0)
    
    def _identify_missing_information(self, user_goal: UserGoal) -> List[str]:
        """Identify missing critical information"""
        missing = []
        
        if user_goal.goal == GoalType.FIND_PROPERTY:
            if not user_goal.entities.get('governorate'):
                missing.append('المحافظة')
            if not user_goal.entities.get('property_type'):
                missing.append('نوع العقار')
            if not user_goal.entities.get('price'):
                missing.append('الميزانية')
            if not user_goal.entities.get('district') and user_goal.entities.get('governorate'):
                missing.append('المنطقة')
        
        elif user_goal.goal == GoalType.FIND_JOB:
            if not user_goal.entities.get('governorate'):
                missing.append('المحافظة')
            if not user_goal.entities.get('job_type'):
                missing.append('نوع الوظيفة')
        
        return missing
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _create_error_goal(self, user_input: str) -> UserGoal:
        """Create error goal when understanding fails"""
        error_goal = UserGoal()
        error_goal.intent = 'error'
        error_goal.goal = GoalType.GENERAL_INFO
        error_goal.confidence = 0.0
        error_goal.ambiguity_score = 1.0
        error_goal.metadata = {
            'original_input': user_input,
            'error': 'Goal understanding failed',
            'processing_timestamp': self._get_timestamp()
        }
        return error_goal
    
    def _initialize_goal_patterns(self) -> Dict:
        """Initialize goal detection patterns"""
        return {
            GoalType.FIND_PROPERTY: [
                r'أريد\s+(بيت|دار|شقة|عقار|أرض)',
                r'ابحث\s+عن\s+(بيت|دار|شقة|عقار)',
                r'دورلي\s+على\s+(بيت|دار|شقة)'
            ],
            GoalType.FIND_JOB: [
                r'أريد\s+(وظيفة|شغل|عمل)',
                r'ابحث\s+عن\s+(وظيفة|شغل)',
                r'شغل\s+بالبصرة'
            ],
            GoalType.FIND_HOTEL: [
                r'أريد\s+(فندق|سكن|مكان للإقامة)',
                r'فندق\s+في',
                r'سكن\s+في'
            ]
        }
    
    def _initialize_purpose_patterns(self) -> Dict:
        """Initialize purpose detection patterns"""
        return {
            'family': r'للعائلة|للاسرة|عائلي',
            'investment': r'للاستثمار|استثمار|تجاري',
            'personal': r'شخصي|سكن شخصي',
            'rental': r'للايجار|ايجار'
        }
    
    def _initialize_constraint_patterns(self) -> Dict:
        """Initialize constraint detection patterns"""
        return {
            ConstraintType.MUST_HAVE: [
                r'أقل\s+من\s+(\d+)',
                r'حدود\s+(\d+)',
                r'في\s+(\w+)'
            ],
            ConstraintType.FORBIDDEN: [
                r'بدون\s+(\w+)',
                r'لا\s+أريد\s+(\w+)'
            ]
        }
    
    def _initialize_preference_patterns(self) -> Dict:
        """Initialize preference detection patterns"""
        return {
            'quiet': r'هادئ|هدوء',
            'near_schools': r'قريب\s+من\s+المدارس',
            'new': r'جديد|حديث',
            'large': r'كبير|واسع'
        }


# Global instance
user_goal_understanding_system = UserGoalUnderstandingSystem()