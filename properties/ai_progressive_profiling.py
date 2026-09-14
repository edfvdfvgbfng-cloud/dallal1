"""
Progressive Profiling System
Gradually collects user preferences through conversation
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class ProfilingStage(Enum):
    """Stages of progressive profiling"""
    INITIAL = "initial"  # Basic info (location, budget)
    ENHANCED = "enhanced"  # Additional info (area, rooms)
    DETAILED = "detailed"  # Detailed preferences
    COMPLETE = "complete"  # All information collected


@dataclass
class ProfileQuestion:
    """Represents a profiling question"""
    question_id: str
    question_text: str
    field_name: str
    stage: ProfilingStage
    priority: int
    required: bool = False
    context_dependent: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'question_id': self.question_id,
            'question_text': self.question_text,
            'field_name': self.field_name,
            'stage': self.stage.value,
            'priority': self.priority,
            'required': self.required,
            'context_dependent': self.context_dependent
        }


@dataclass
class UserProfile:
    """User profile with collected information"""
    user_id: int
    stage: ProfilingStage = ProfilingStage.INITIAL
    collected_data: Dict = field(default_factory=dict)
    questions_asked: List[str] = field(default_factory=list)
    last_updated: str = None
    
    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'stage': self.stage.value,
            'collected_data': self.collected_data,
            'questions_asked_count': len(self.questions_asked),
            'last_updated': self.last_updated
        }


class ProgressiveProfilingSystem:
    """
    Gradually collects user preferences through conversation
    Avoids overwhelming users with long forms
    """
    
    def __init__(self):
        self.user_profiles: Dict[int, UserProfile] = {}
        self.profiling_questions = self._initialize_questions()
        self.profiling_history: List[Dict] = []
    
    def _initialize_questions(self) -> List[ProfileQuestion]:
        """Initialize profiling questions by stage"""
        return [
            # Initial stage - most important
            ProfileQuestion(
                question_id="q1",
                question_text="وين تريد العقار؟ (المحافظة)",
                field_name="governorate",
                stage=ProfilingStage.INITIAL,
                priority=1,
                required=True
            ),
            ProfileQuestion(
                question_id="q2",
                question_text="شنو ميزانيتك؟",
                field_name="budget",
                stage=ProfilingStage.INITIAL,
                priority=2,
                required=True
            ),
            ProfileQuestion(
                question_id="q3",
                question_text="أي نوع عقار تريد؟ (بيت، شقة، أرض)",
                field_name="property_type",
                stage=ProfilingStage.INITIAL,
                priority=3,
                required=True
            ),
            # Enhanced stage - after initial search
            ProfileQuestion(
                question_id="q4",
                question_text="شنو المساحة اللي تحتاجها؟",
                field_name="area",
                stage=ProfilingStage.ENHANCED,
                priority=1,
                required=False
            ),
            ProfileQuestion(
                question_id="q5",
                question_text="كم غرفة تريد؟",
                field_name="rooms",
                stage=ProfilingStage.ENHANCED,
                priority=2,
                required=False
            ),
            ProfileQuestion(
                question_id="q6",
                question_text="تحتاج منطقة معينة بالمحافظة؟",
                field_name="district",
                stage=ProfilingStage.ENHANCED,
                priority=3,
                required=False
            ),
            # Detailed stage - after seeing results
            ProfileQuestion(
                question_id="q7",
                question_text="تحتاج مواقف سيارات؟",
                field_name="parking",
                stage=ProfilingStage.DETAILED,
                priority=1,
                required=False
            ),
            ProfileQuestion(
                question_id="q8",
                question_text="تحتاج حديقة؟",
                field_name="garden",
                stage=ProfilingStage.DETAILED,
                priority=2,
                required=False
            ),
            ProfileQuestion(
                question_id="q9",
                question_text="الطابق الي تحبه؟",
                field_name="floor",
                stage=ProfilingStage.DETAILED,
                priority=3,
                required=False
            )
        ]
    
    def get_user_profile(self, user_id: int) -> UserProfile:
        """Get or create user profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id=user_id)
        
        return self.user_profiles[user_id]
    
    def update_profile(self, user_id: int, field_name: str, value: Any):
        """Update user profile with new information"""
        profile = self.get_user_profile(user_id)
        profile.collected_data[field_name] = value
        profile.last_updated = datetime.now().isoformat()
        
        # Update stage based on completeness
        self._update_profile_stage(profile)
        
        logger.info(f"Updated profile for user {user_id}: {field_name} = {value}")
    
    def _update_profile_stage(self, profile: UserProfile):
        """Update profiling stage based on collected data"""
        initial_fields = ['governorate', 'budget', 'property_type']
        enhanced_fields = ['area', 'rooms', 'district']
        
        collected = set(profile.collected_data.keys())
        
        if collected.issuperset(initial_fields):
            if collected.issuperset(enhanced_fields):
                profile.stage = ProfilingStage.DETAILED
            else:
                profile.stage = ProfilingStage.ENHANCED
        else:
            profile.stage = ProfilingStage.INITIAL
    
    def get_next_question(self, user_id: int, context: Dict = None) -> Optional[ProfileQuestion]:
        """
        Get next profiling question to ask
        
        Args:
            user_id: User ID
            context: Conversation context
            
        Returns:
            Next question to ask, or None if no more questions
        """
        profile = self.get_user_profile(user_id)
        
        # Get questions for current stage
        stage_questions = [q for q in self.profiling_questions if q.stage == profile.stage]
        
        # Filter out already asked questions
        unasked_questions = [q for q in stage_questions if q.question_id not in profile.questions_asked]
        
        if not unasked_questions:
            # Move to next stage
            if profile.stage == ProfilingStage.INITIAL:
                profile.stage = ProfilingStage.ENHANCED
            elif profile.stage == ProfilingStage.ENHANCED:
                profile.stage = ProfilingStage.DETAILED
            elif profile.stage == ProfilingStage.DETAILED:
                profile.stage = ProfilingStage.COMPLETE
                return None
            
            # Get questions for new stage
            stage_questions = [q for q in self.profiling_questions if q.stage == profile.stage]
            unasked_questions = [q for q in stage_questions if q.question_id not in profile.questions_asked]
        
        if not unasked_questions:
            return None
        
        # Sort by priority
        unasked_questions.sort(key=lambda x: x.priority)
        
        return unasked_questions[0]
    
    def mark_question_asked(self, user_id: int, question_id: str):
        """Mark question as asked"""
        profile = self.get_user_profile(user_id)
        if question_id not in profile.questions_asked:
            profile.questions_asked.append(question_id)
    
    def get_profile_completeness(self, user_id: int) -> Dict:
        """Get profile completeness statistics"""
        profile = self.get_user_profile(user_id)
        
        total_questions = len(self.profiling_questions)
        answered_questions = len(profile.questions_asked)
        
        # Count by stage
        stage_counts = {}
        for stage in ProfilingStage:
            stage_questions = [q for q in self.profiling_questions if q.stage == stage]
            answered_in_stage = sum(1 for q in stage_questions if q.question_id in profile.questions_asked)
            stage_counts[stage.value] = {
                'total': len(stage_questions),
                'answered': answered_in_stage,
                'percentage': (answered_in_stage / len(stage_questions) * 100) if stage_questions else 0
            }
        
        return {
            'user_id': user_id,
            'current_stage': profile.stage.value,
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'completeness_percentage': (answered_questions / total_questions * 100) if total_questions > 0 else 0,
            'stage_breakdown': stage_counts
        }
    
    def is_profile_complete(self, user_id: int) -> bool:
        """Check if user profile is complete"""
        profile = self.get_user_profile(user_id)
        return profile.stage == ProfilingStage.COMPLETE
    
    def should_ask_question(self, user_id: int, context: Dict = None) -> bool:
        """Determine if a question should be asked"""
        profile = self.get_user_profile(user_id)
        
        # Don't ask if profile is complete
        if profile.stage == ProfilingStage.COMPLETE:
            return False
        
        # Check if context indicates good time to ask
        if context:
            # Ask after search results
            if context.get('after_search_results'):
                return True
            
            # Ask if user is exploring
            if context.get('user_exploring'):
                return True
        
        # Ask if initial stage and not enough info
        if profile.stage == ProfilingStage.INITIAL:
            required_fields = ['governorate', 'budget', 'property_type']
            collected = set(profile.collected_data.keys())
            if not required_fields.issubset(collected):
                return True
        
        return False
    
    def reset_profile(self, user_id: int):
        """Reset user profile"""
        if user_id in self.user_profiles:
            del self.user_profiles[user_id]
        logger.info(f"Reset profile for user {user_id}")
    
    def get_profiling_statistics(self) -> Dict:
        """Get profiling statistics"""
        stage_counts = {}
        for profile in self.user_profiles.values():
            stage = profile.stage.value
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        
        return {
            'total_users': len(self.user_profiles),
            'stage_distribution': stage_counts,
            'average_questions_asked': sum(len(p.questions_asked) for p in self.user_profiles.values()) / len(self.user_profiles) if self.user_profiles else 0
        }


# Global instance
progressive_profiling_system = ProgressiveProfilingSystem()