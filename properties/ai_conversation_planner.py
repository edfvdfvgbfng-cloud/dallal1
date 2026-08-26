"""
Conversation Planning System
Creates and manages dynamic conversation plans based on user goals and context
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .ai_goal_understanding import UserGoal, GoalType
from .ai_constraint_engine import ConstraintEngine
from .ai_smart_clarification import SmartClarificationSystem, ClarificationQuestion

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Status of planning steps"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class StepType(Enum):
    """Types of planning steps"""
    INFORMATION_GATHERING = "information_gathering"
    CLARIFICATION = "clarification"
    SEARCH = "search"
    FILTERING = "filtering"
    RANKING = "ranking"
    SELECTION = "selection"
    ACTION = "action"
    CONFIRMATION = "confirmation"
    NAVIGATION = "navigation"


@dataclass
class PlanningStep:
    """Individual step in conversation plan"""
    step_id: str
    step_type: StepType
    description: str
    status: StepStatus = StepStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    action_function: str = None
    parameters: Dict = field(default_factory=dict)
    result: Any = None
    error: str = None
    timestamp: str = None
    
    def __post_init__(self):
        if not self.step_id:
            self.step_id = str(uuid.uuid4())[:8]
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'step_id': self.step_id,
            'step_type': self.step_type.value,
            'description': self.description,
            'status': self.status.value,
            'dependencies': self.dependencies,
            'required_fields': self.required_fields,
            'optional_fields': self.optional_fields,
            'action_function': self.action_function,
            'parameters': self.parameters,
            'result': self.result,
            'error': self.error,
            'timestamp': self.timestamp
        }


class ConversationPlan:
    """Complete conversation plan with multiple steps"""
    
    def __init__(self, goal: UserGoal):
        self.plan_id = str(uuid.uuid4())
        self.goal = goal
        self.steps: List[PlanningStep] = []
        self.current_step_index = 0
        self.status = "active"
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.metadata: Dict = {}
    
    def add_step(self, step: PlanningStep):
        """Add a step to the plan"""
        self.steps.append(step)
        self.updated_at = datetime.now().isoformat()
    
    def get_current_step(self) -> Optional[PlanningStep]:
        """Get current step"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def advance_step(self):
        """Advance to next step"""
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            self.updated_at = datetime.now().isoformat()
            return True
        return False
    
    def mark_step_completed(self, step_id: str, result: Any = None):
        """Mark a step as completed"""
        for step in self.steps:
            if step.step_id == step_id:
                step.status = StepStatus.COMPLETED
                step.result = result
                step.timestamp = datetime.now().isoformat()
                self.updated_at = datetime.now().isoformat()
                break
    
    def mark_step_failed(self, step_id: str, error: str):
        """Mark a step as failed"""
        for step in self.steps:
            if step.step_id == step_id:
                step.status = StepStatus.FAILED
                step.error = error
                step.timestamp = datetime.now().isoformat()
                self.updated_at = datetime.now().isoformat()
                break
    
    def skip_step(self, step_id: str, reason: str):
        """Skip a step"""
        for step in self.steps:
            if step.step_id == step_id:
                step.status = StepStatus.SKIPPED
                step.error = reason
                step.timestamp = datetime.now().isoformat()
                self.updated_at = datetime.now().isoformat()
                break
    
    def get_next_executable_step(self) -> Optional[PlanningStep]:
        """Get next step that can be executed (dependencies met)"""
        for i in range(self.current_step_index, len(self.steps)):
            step = self.steps[i]
            if step.status == StepStatus.PENDING:
                # Check dependencies
                dependencies_met = all(
                    self._get_step_status(dep_id) == StepStatus.COMPLETED
                    for dep_id in step.dependencies
                )
                if dependencies_met:
                    return step
        return None
    
    def _get_step_status(self, step_id: str) -> StepStatus:
        """Get status of a step by ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step.status
        return StepStatus.PENDING
    
    def is_complete(self) -> bool:
        """Check if plan is complete"""
        return all(
            step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]
            for step in self.steps
        )
    
    def get_progress(self) -> Dict:
        """Get plan progress"""
        total_steps = len(self.steps)
        completed_steps = sum(
            1 for step in self.steps
            if step.status == StepStatus.COMPLETED
        )
        failed_steps = sum(
            1 for step in self.steps
            if step.status == StepStatus.FAILED
        )
        
        return {
            'total_steps': total_steps,
            'completed_steps': completed_steps,
            'failed_steps': failed_steps,
            'progress_percentage': (completed_steps / total_steps * 100) if total_steps > 0 else 0,
            'current_step': self.current_step_index
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'plan_id': self.plan_id,
            'goal': self.goal.to_dict(),
            'steps': [step.to_dict() for step in self.steps],
            'current_step_index': self.current_step_index,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata,
            'progress': self.get_progress()
        }


class ConversationPlanner:
    """
    Advanced conversation planner that creates dynamic plans
    based on user goals, context, and available information
    """
    
    def __init__(self):
        self.clarification_system = SmartClarificationSystem()
        self.constraint_engine = ConstraintEngine()
        self.active_plans: Dict[str, ConversationPlan] = {}
        self.plan_history: List[Dict] = []
    
    def create_plan(self, user_goal: UserGoal, conversation_context: Dict = None) -> ConversationPlan:
        """
        Create a conversation plan based on user goal
        
        Args:
            user_goal: User's goal
            conversation_context: Previous conversation context
            
        Returns:
            ConversationPlan with optimized steps
        """
        try:
            # Create plan
            plan = ConversationPlan(user_goal)
            
            # Build constraint set from goal
            constraint_set = self.constraint_engine.build_constraint_set_from_goal(user_goal)
            
            # Determine plan steps based on goal type and information completeness
            if user_goal.goal == GoalType.FIND_PROPERTY:
                self._create_property_search_plan(plan, user_goal, conversation_context)
            elif user_goal.goal == GoalType.FIND_JOB:
                self._create_job_search_plan(plan, user_goal, conversation_context)
            elif user_goal.goal == GoalType.COMPARISON:
                self._create_comparison_plan(plan, user_goal, conversation_context)
            elif user_goal.goal == GoalType.SAVING:
                self._create_saving_plan(plan, user_goal, conversation_context)
            elif user_goal.goal == GoalType.NAVIGATION:
                self._create_navigation_plan(plan, user_goal, conversation_context)
            else:
                self._create_general_plan(plan, user_goal, conversation_context)
            
            # Optimize plan by removing unnecessary steps
            self._optimize_plan(plan, user_goal)
            
            # Store plan
            self.active_plans[plan.plan_id] = plan
            self.plan_history.append({
                'timestamp': datetime.now().isoformat(),
                'plan_id': plan.plan_id,
                'goal': user_goal.to_dict(),
                'steps_count': len(plan.steps)
            })
            
            logger.info(f"Created plan {plan.plan_id} with {len(plan.steps)} steps")
            return plan
            
        except Exception as e:
            logger.error(f"Error creating conversation plan: {str(e)}")
            return self._create_error_plan(user_goal)
    
    def _create_property_search_plan(self, plan: ConversationPlan, user_goal: UserGoal, context: Dict):
        """Create plan for property search"""
        
        # Step 1: Check if essential information is available
        info_check_step = PlanningStep(
            step_type=StepType.INFORMATION_GATHERING,
            description="Check information completeness",
            required_fields=['governorate', 'property_type', 'price'],
            action_function="check_information_completeness"
        )
        plan.add_step(info_check_step)
        
        # Step 2: Generate clarification questions if needed
        clarification_step = PlanningStep(
            step_type=StepType.CLARIFICATION,
            description="Ask clarification questions",
            dependencies=[info_check_step.step_id],
            action_function="generate_clarification_questions"
        )
        plan.add_step(clarification_step)
        
        # Step 3: Apply constraints
        constraint_step = PlanningStep(
            step_type=StepType.FILTERING,
            description="Apply search constraints",
            dependencies=[clarification_step.step_id],
            action_function="apply_constraints"
        )
        plan.add_step(constraint_step)
        
        # Step 4: Execute search
        search_step = PlanningStep(
            step_type=StepType.SEARCH,
            description="Search for properties",
            dependencies=[constraint_step.step_id],
            action_function="search_properties"
        )
        plan.add_step(search_step)
        
        # Step 5: Rank results
        ranking_step = PlanningStep(
            step_type=StepType.RANKING,
            description="Rank search results",
            dependencies=[search_step.step_id],
            action_function="rank_results"
        )
        plan.add_step(ranking_step)
        
        # Step 6: Select best results
        selection_step = PlanningStep(
            step_type=StepType.SELECTION,
            description="Select top results",
            dependencies=[ranking_step.step_id],
            action_function="select_top_results"
        )
        plan.add_step(selection_step)
        
        # Step 7: Present results
        presentation_step = PlanningStep(
            step_type=StepType.ACTION,
            description="Present results to user",
            dependencies=[selection_step.step_id],
            action_function="present_results"
        )
        plan.add_step(presentation_step)
    
    def _create_job_search_plan(self, plan: ConversationPlan, user_goal: UserGoal, context: Dict):
        """Create plan for job search"""
        
        # Similar structure to property search but for jobs
        info_check_step = PlanningStep(
            step_type=StepType.INFORMATION_GATHERING,
            description="Check job search information",
            required_fields=['governorate', 'job_type'],
            action_function="check_job_information"
        )
        plan.add_step(info_check_step)
        
        clarification_step = PlanningStep(
            step_type=StepType.CLARIFICATION,
            description="Clarify job requirements",
            dependencies=[info_check_step.step_id],
            action_function="clarify_job_requirements"
        )
        plan.add_step(clarification_step)
        
        search_step = PlanningStep(
            step_type=StepType.SEARCH,
            description="Search for jobs",
            dependencies=[clarification_step.step_id],
            action_function="search_jobs"
        )
        plan.add_step(search_step)
        
        presentation_step = PlanningStep(
            step_type=StepType.ACTION,
            description="Present job results",
            dependencies=[search_step.step_id],
            action_function="present_job_results"
        )
        plan.add_step(presentation_step)
    
    def _create_comparison_plan(self, plan: ConversationPlan, user_goal: UserGoal, context: Dict):
        """Create plan for property comparison"""
        
        # Check if items to compare are available
        selection_step = PlanningStep(
            step_type=StepType.SELECTION,
            description="Select items to compare",
            required_fields=['items_to_compare'],
            action_function="select_comparison_items"
        )
        plan.add_step(selection_step)
        
        # Execute comparison
        comparison_step = PlanningStep(
            step_type=StepType.ACTION,
            description="Compare selected items",
            dependencies=[selection_step.step_id],
            action_function="compare_properties"
        )
        plan.add_step(comparison_step)
        
        # Present comparison
        presentation_step = PlanningStep(
            step_type=StepType.ACTION,
            description="Present comparison results",
            dependencies=[comparison_step.step_id],
            action_function="present_comparison"
        )
        plan.add_step(presentation_step)
    
    def _create_saving_plan(self, plan: ConversationPlan, user_goal: UserGoal, context: Dict):
        """Create plan for saving properties"""
        
        # Identify what to save
        identification_step = PlanningStep(
            step_type=StepType.SELECTION,
            description="Identify item to save",
            required_fields=['item_to_save'],
            action_function="identify_save_target"
        )
        plan.add_step(identification_step)
        
        # Execute save
        save_step = PlanningStep(
            step_type=StepType.ACTION,
            description="Save item",
            dependencies=[identification_step.step_id],
            action_function="save_property"
        )
        plan.add_step(save_step)
        
        # Confirm save
        confirmation_step = PlanningStep(
            step_type=StepType.CONFIRMATION,
            description="Confirm save operation",
            dependencies=[save_step.step_id],
            action_function="confirm_save"
        )
        plan.add_step(confirmation_step)
    
    def _create_navigation_plan(self, plan: ConversationPlan, user_goal: UserGoal, context: Dict):
        """Create plan for navigation"""
        
        navigation_step = PlanningStep(
            step_type=StepType.NAVIGATION,
            description="Navigate to requested page",
            required_fields=['destination'],
            action_function="navigate_to_page"
        )
        plan.add_step(navigation_step)
    
    def _create_general_plan(self, plan: ConversationPlan, user_goal: UserGoal, context: Dict):
        """Create general purpose plan"""
        
        # Generate clarification questions
        clarification_step = PlanningStep(
            step_type=StepType.CLARIFICATION,
            description="Clarify user request",
            action_function="clarify_general_request"
        )
        plan.add_step(clarification_step)
        
        # Provide response
        response_step = PlanningStep(
            step_type=StepType.ACTION,
            description="Provide response",
            dependencies=[clarification_step.step_id],
            action_function="provide_general_response"
        )
        plan.add_step(response_step)
    
    def _optimize_plan(self, plan: ConversationPlan, user_goal: UserGoal):
        """Optimize plan by removing unnecessary steps"""
        
        # Check if essential information is already available
        essential_info_available = self._check_essential_information(user_goal)
        
        if essential_info_available:
            # Skip clarification step
            for step in plan.steps:
                if step.step_type == StepType.CLARIFICATION:
                    step.status = StepStatus.SKIPPED
                    step.error = "Essential information already available"
        
        # Check if actions are requested
        if user_goal.actions:
            # Focus on action steps
            for step in plan.steps:
                if step.step_type in [StepType.INFORMATION_GATHERING, StepType.CLARIFICATION]:
                    if step.status == StepStatus.PENDING:
                        step.status = StepStatus.SKIPPED
                        step.error = "Actions requested, skipping information gathering"
    
    def _check_essential_information(self, user_goal: UserGoal) -> bool:
        """Check if essential information is available"""
        if user_goal.goal == GoalType.FIND_PROPERTY:
            return all([
                user_goal.entities.get('governorate'),
                user_goal.entities.get('property_type'),
                user_goal.entities.get('price')
            ])
        elif user_goal.goal == GoalType.FIND_JOB:
            return all([
                user_goal.entities.get('governorate'),
                user_goal.entities.get('job_type')
            ])
        return False
    
    def update_plan(self, plan_id: str, new_information: Dict):
        """Update plan with new information"""
        if plan_id not in self.active_plans:
            logger.warning(f"Plan {plan_id} not found")
            return
        
        plan = self.active_plans[plan_id]
        
        # Update goal with new information
        for key, value in new_information.items():
            if key not in plan.goal.entities:
                plan.goal.entities[key] = value
        
        # Re-optimize plan
        self._optimize_plan(plan, plan.goal)
        
        logger.info(f"Updated plan {plan_id} with new information")
    
    def get_plan(self, plan_id: str) -> Optional[ConversationPlan]:
        """Get plan by ID"""
        return self.active_plans.get(plan_id)
    
    def execute_next_step(self, plan_id: str) -> Tuple[bool, Any]:
        """
        Execute the next executable step in the plan
        
        Returns:
            (success, result)
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return False, "Plan not found"
        
        next_step = plan.get_next_executable_step()
        if not next_step:
            return False, "No executable steps remaining"
        
        # Mark step as in progress
        next_step.status = StepStatus.IN_PROGRESS
        
        try:
            # Execute step (this would call the actual function)
            result = self._execute_step_function(next_step, plan)
            
            # Mark as completed
            plan.mark_step_completed(next_step.step_id, result)
            
            # Advance to next step
            plan.advance_step()
            
            return True, result
            
        except Exception as e:
            error_msg = f"Step execution failed: {str(e)}"
            plan.mark_step_failed(next_step.step_id, error_msg)
            logger.error(error_msg)
            return False, error_msg
    
    def _execute_step_function(self, step: PlanningStep, plan: ConversationPlan) -> Any:
        """Execute the function associated with a step"""
        # This would integrate with the actual tool system
        # For now, return a placeholder result
        
        function_map = {
            "check_information_completeness": self._check_info_completeness,
            "generate_clarification_questions": self._generate_questions,
            "apply_constraints": self._apply_constraints,
            "search_properties": self._search_properties,
            "rank_results": self._rank_results,
            "select_top_results": self._select_top_results,
            "present_results": self._present_results
        }
        
        function = function_map.get(step.action_function)
        if function:
            return function(step, plan)
        
        return f"Executed {step.action_function}"
    
    def _check_info_completeness(self, step: PlanningStep, plan: ConversationPlan) -> Dict:
        """Check information completeness"""
        return {
            'complete': self._check_essential_information(plan.goal),
            'missing': plan.goal.missing_information
        }
    
    def _generate_questions(self, step: PlanningStep, plan: ConversationPlan) -> List[ClarificationQuestion]:
        """Generate clarification questions"""
        context = {'entities': plan.goal.entities}
        return self.clarification_system.generate_clarification_questions(plan.goal, context)
    
    def _apply_constraints(self, step: PlanningStep, plan: ConversationPlan) -> Dict:
        """Apply constraints to search"""
        return self.constraint_engine.apply_constraints_to_query(plan.goal.entities)
    
    def _search_properties(self, step: PlanningStep, plan: ConversationPlan) -> List[Dict]:
        """Search for properties (placeholder)"""
        return []  # Would integrate with actual search
    
    def _rank_results(self, step: PlanningStep, plan: ConversationPlan) -> List[tuple]:
        """Rank search results (placeholder)"""
        return []  # Would integrate with actual ranking
    
    def _select_top_results(self, step: PlanningStep, plan: ConversationPlan) -> List[Dict]:
        """Select top results (placeholder)"""
        return []  # Would integrate with actual selection
    
    def _present_results(self, step: PlanningStep, plan: ConversationPlan) -> str:
        """Present results to user (placeholder)"""
        return "Results presented"
    
    def _create_error_plan(self, user_goal: UserGoal) -> ConversationPlan:
        """Create error plan when planning fails"""
        plan = ConversationPlan(user_goal)
        plan.status = "error"
        
        error_step = PlanningStep(
            step_type=StepType.ACTION,
            description="Handle planning error",
            action_function="handle_error"
        )
        plan.add_step(error_step)
        
        return plan


# Global instance
conversation_planner = ConversationPlanner()