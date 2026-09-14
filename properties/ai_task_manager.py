"""
Multi-Step Task Management System
Handles complex tasks that require multiple operations with state management
"""

from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json

from .ai_conversation_planner import ConversationPlan, PlanningStep, StepStatus

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of multi-step tasks"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_USER_APPROVAL = "waiting_user_approval"


class TaskPriority(Enum):
    """Priority levels for tasks"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class TaskStep:
    """Individual step within a task"""
    name: str
    description: str
    action_function: str
    step_id: str = None
    parameters: Dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = None
    started_at: str = None
    completed_at: str = None
    requires_approval: bool = False
    approval_granted: bool = False
    
    def __post_init__(self):
        if not self.step_id:
            self.step_id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'step_id': self.step_id,
            'name': self.name,
            'description': self.description,
            'action_function': self.action_function,
            'parameters': self.parameters,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'requires_approval': self.requires_approval,
            'approval_granted': self.approval_granted
        }


class MultiStepTask:
    """Multi-step task with state management and execution"""
    
    def __init__(self, 
                 task_id: str = None,
                 name: str = None,
                 description: str = None,
                 priority: TaskPriority = TaskPriority.MEDIUM):
        self.task_id = task_id or str(uuid.uuid4())
        self.name = name or "Unnamed Task"
        self.description = description or "No description"
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.steps: List[TaskStep] = []
        self.current_step_index = 0
        self.created_at = datetime.now().isoformat()
        self.started_at: str = None
        self.completed_at: str = None
        self.result: Any = None
        self.error: str = None
        self.metadata: Dict = {}
        self.context: Dict = {}
        self.user_id: int = None
        self.approval_required: bool = False
    
    def add_step(self, step: TaskStep):
        """Add a step to the task"""
        self.steps.append(step)
    
    def start(self):
        """Start task execution"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now().isoformat()
        logger.info(f"Task {self.task_id} started")
    
    def pause(self):
        """Pause task execution"""
        self.status = TaskStatus.PAUSED
        logger.info(f"Task {self.task_id} paused")
    
    def resume(self):
        """Resume task execution"""
        if self.status == TaskStatus.PAUSED:
            self.status = TaskStatus.RUNNING
            logger.info(f"Task {self.task_id} resumed")
    
    def cancel(self):
        """Cancel task execution"""
        self.status = TaskStatus.CANCELLED
        logger.info(f"Task {self.task_id} cancelled")
    
    def complete(self, result: Any = None):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        self.result = result
        logger.info(f"Task {self.task_id} completed")
    
    def fail(self, error: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.error = error
        logger.error(f"Task {self.task_id} failed: {error}")
    
    def get_current_step(self) -> Optional[TaskStep]:
        """Get current step"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def advance_step(self):
        """Advance to next step"""
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            return True
        return False
    
    def mark_step_started(self, step_id: str):
        """Mark a step as started"""
        for step in self.steps:
            if step.step_id == step_id:
                step.status = TaskStatus.RUNNING
                step.started_at = datetime.now().isoformat()
                break
    
    def mark_step_completed(self, step_id: str, result: Any = None):
        """Mark a step as completed"""
        for step in self.steps:
            if step.step_id == step_id:
                step.status = TaskStatus.COMPLETED
                step.result = result
                step.completed_at = datetime.now().isoformat()
                break
    
    def mark_step_failed(self, step_id: str, error: str):
        """Mark a step as failed"""
        for step in self.steps:
            if step.step_id == step_id:
                step.status = TaskStatus.FAILED
                step.error = error
                step.completed_at = datetime.now().isoformat()
                break
    
    def get_progress(self) -> Dict:
        """Get task progress"""
        total_steps = len(self.steps)
        completed_steps = sum(
            1 for step in self.steps
            if step.status == TaskStatus.COMPLETED
        )
        failed_steps = sum(
            1 for step in self.steps
            if step.status == TaskStatus.FAILED
        )
        
        return {
            'total_steps': total_steps,
            'completed_steps': completed_steps,
            'failed_steps': failed_steps,
            'current_step': self.current_step_index,
            'progress_percentage': (completed_steps / total_steps * 100) if total_steps > 0 else 0
        }
    
    def requires_user_approval(self) -> bool:
        """Check if task requires user approval"""
        return any(step.requires_approval and not step.approval_granted for step in self.steps)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'steps': [step.to_dict() for step in self.steps],
            'current_step_index': self.current_step_index,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'result': self.result,
            'error': self.error,
            'metadata': self.metadata,
            'context': self.context,
            'user_id': self.user_id,
            'approval_required': self.approval_required,
            'progress': self.get_progress()
        }
    
    def to_json(self) -> str:
        """Convert to JSON for storage"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MultiStepTask':
        """Create task from JSON"""
        data = json.loads(json_str)
        task = cls(
            task_id=data.get('task_id'),
            name=data.get('name'),
            description=data.get('description'),
            priority=TaskPriority(data.get('priority', 'medium'))
        )
        
        # Restore state
        task.status = TaskStatus(data.get('status', 'pending'))
        task.current_step_index = data.get('current_step_index', 0)
        task.created_at = data.get('created_at')
        task.started_at = data.get('started_at')
        task.completed_at = data.get('completed_at')
        task.result = data.get('result')
        task.error = data.get('error')
        task.metadata = data.get('metadata', {})
        task.context = data.get('context', {})
        task.user_id = data.get('user_id')
        task.approval_required = data.get('approval_required', False)
        
        # Restore steps
        for step_data in data.get('steps', []):
            step = TaskStep(
                step_id=step_data.get('step_id'),
                name=step_data.get('name'),
                description=step_data.get('description'),
                action_function=step_data.get('action_function'),
                parameters=step_data.get('parameters', {}),
                requires_approval=step_data.get('requires_approval', False),
                approval_granted=step_data.get('approval_granted', False)
            )
            step.status = TaskStatus(step_data.get('status', 'pending'))
            step.result = step_data.get('result')
            step.error = step_data.get('error')
            step.started_at = step_data.get('started_at')
            step.completed_at = step_data.get('completed_at')
            task.add_step(step)
        
        return task


class TaskManager:
    """
    Manages multi-step tasks with state persistence and execution
    """
    
    def __init__(self):
        self.active_tasks: Dict[str, MultiStepTask] = {}
        self.task_history: List[Dict] = []
        self.action_registry: Dict[str, Callable] = {}
        self._register_default_actions()
    
    def create_task(self, 
                   name: str,
                   description: str,
                   steps: List[TaskStep],
                   priority: TaskPriority = TaskPriority.MEDIUM,
                   user_id: int = None,
                   context: Dict = None) -> MultiStepTask:
        """
        Create a new multi-step task
        
        Args:
            name: Task name
            description: Task description
            steps: List of task steps
            priority: Task priority
            user_id: User ID
            context: Task context
            
        Returns:
            Created MultiStepTask
        """
        task = MultiStepTask(
            name=name,
            description=description,
            priority=priority
        )
        
        # Add steps
        for step in steps:
            task.add_step(step)
        
        # Set metadata
        task.user_id = user_id
        task.context = context or {}
        task.approval_required = any(step.requires_approval for step in steps)
        
        # Store task
        self.active_tasks[task.task_id] = task
        
        logger.info(f"Created task {task.task_id}: {name} with {len(steps)} steps")
        return task
    
    def execute_task(self, task_id: str) -> Tuple[bool, Any]:
        """
        Execute a task step by step
        
        Args:
            task_id: Task ID to execute
            
        Returns:
            (success, result)
        """
        task = self.active_tasks.get(task_id)
        if not task:
            return False, "Task not found"
        
        # Start task if not started
        if task.status == TaskStatus.PENDING:
            task.start()
        
        # Check if task requires approval
        if task.requires_user_approval():
            task.status = TaskStatus.WAITING_USER_APPROVAL
            return False, "Task requires user approval"
        
        # Execute steps
        while True:
            current_step = task.get_current_step()
            if not current_step:
                # No more steps, task complete
                task.complete(task.result)
                break
            
            # Check if step requires approval
            if current_step.requires_approval and not current_step.approval_granted:
                task.status = TaskStatus.WAITING_USER_APPROVAL
                return False, f"Step {current_step.name} requires approval"
            
            # Mark step as started
            task.mark_step_started(current_step.step_id)
            
            try:
                # Execute step action
                result = self._execute_step_action(current_step, task)
                
                # Mark step as completed
                task.mark_step_completed(current_step.step_id, result)
                
                # Store result in task context
                task.context[f"step_{current_step.step_id}_result"] = result
                
                # Advance to next step
                if not task.advance_step():
                    # No more steps
                    task.complete(result)
                    break
                
            except Exception as e:
                error_msg = f"Step execution failed: {str(e)}"
                task.mark_step_failed(current_step.step_id, error_msg)
                task.fail(error_msg)
                return False, error_msg
        
        # Add to history
        self.task_history.append({
            'timestamp': datetime.now().isoformat(),
            'task_id': task.task_id,
            'name': task.name,
            'status': task.status.value,
            'result': task.result
        })
        
        # Remove from active tasks
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            del self.active_tasks[task_id]
        
        return True, task.result
    
    def approve_step(self, task_id: str, step_id: str):
        """Approve a step that requires user approval"""
        task = self.active_tasks.get(task_id)
        if not task:
            return False
        
        for step in task.steps:
            if step.step_id == step_id:
                step.approval_granted = True
                logger.info(f"Step {step_id} approved in task {task_id}")
                return True
        
        return False
    
    def approve_task(self, task_id: str):
        """Approve all steps in a task"""
        task = self.active_tasks.get(task_id)
        if not task:
            return False
        
        for step in task.steps:
            if step.requires_approval:
                step.approval_granted = True
        
        logger.info(f"All steps approved in task {task_id}")
        return True
    
    def pause_task(self, task_id: str):
        """Pause a running task"""
        task = self.active_tasks.get(task_id)
        if task:
            task.pause()
            return True
        return False
    
    def resume_task(self, task_id: str):
        """Resume a paused task"""
        task = self.active_tasks.get(task_id)
        if task:
            task.resume()
            return True
        return False
    
    def cancel_task(self, task_id: str):
        """Cancel a task"""
        task = self.active_tasks.get(task_id)
        if task:
            task.cancel()
            # Remove from active tasks
            del self.active_tasks[task_id]
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[MultiStepTask]:
        """Get task by ID"""
        return self.active_tasks.get(task_id)
    
    def get_user_tasks(self, user_id: int) -> List[MultiStepTask]:
        """Get all tasks for a user"""
        return [
            task for task in self.active_tasks.values()
            if task.user_id == user_id
        ]
    
    def save_task_state(self, task_id: str) -> bool:
        """Save task state to persistent storage"""
        task = self.active_tasks.get(task_id)
        if not task:
            return False
        
        try:
            # This would integrate with database or cache
            # For now, we'll just log it
            logger.info(f"Saving task state for {task_id}: {task.to_json()[:100]}...")
            return True
        except Exception as e:
            logger.error(f"Error saving task state: {str(e)}")
            return False
    
    def load_task_state(self, task_data: Dict) -> Optional[MultiStepTask]:
        """Load task state from persistent storage"""
        try:
            task = MultiStepTask.from_json(json.dumps(task_data))
            self.active_tasks[task.task_id] = task
            logger.info(f"Loaded task state for {task.task_id}")
            return task
        except Exception as e:
            logger.error(f"Error loading task state: {str(e)}")
            return None
    
    def _execute_step_action(self, step: TaskStep, task: MultiStepTask) -> Any:
        """Execute the action for a step"""
        action_function = self.action_registry.get(step.action_function)
        if not action_function:
            raise ValueError(f"Action function {step.action_function} not registered")
        
        # Execute action with step parameters and task context
        return action_function(step.parameters, task.context)
    
    def _register_default_actions(self):
        """Register default action functions"""
        self.action_registry = {
            'search_properties': self._default_search_properties,
            'save_property': self._default_save_property,
            'favorite_property': self._default_favorite_property,
            'compare_properties': self._default_compare_properties,
            'sort_results': self._default_sort_results,
            'filter_results': self._default_filter_results
        }
    
    def register_action(self, action_name: str, action_function: Callable):
        """Register a custom action function"""
        self.action_registry[action_name] = action_function
        logger.info(f"Registered action: {action_name}")
    
    def _default_search_properties(self, parameters: Dict, context: Dict) -> List[Dict]:
        """Default search properties action"""
        # This would integrate with actual search
        logger.info(f"Searching properties with parameters: {parameters}")
        return []  # Placeholder
    
    def _default_save_property(self, parameters: Dict, context: Dict) -> bool:
        """Default save property action"""
        # This would integrate with actual save functionality
        logger.info(f"Saving property with parameters: {parameters}")
        return True  # Placeholder
    
    def _default_favorite_property(self, parameters: Dict, context: Dict) -> bool:
        """Default favorite property action"""
        # This would integrate with actual favorite functionality
        logger.info(f"Favoriting property with parameters: {parameters}")
        return True  # Placeholder
    
    def _default_compare_properties(self, parameters: Dict, context: Dict) -> Dict:
        """Default compare properties action"""
        # This would integrate with actual comparison
        logger.info(f"Comparing properties with parameters: {parameters}")
        return {}  # Placeholder
    
    def _default_sort_results(self, parameters: Dict, context: Dict) -> List[Dict]:
        """Default sort results action"""
        # This would integrate with actual sorting
        logger.info(f"Sorting results with parameters: {parameters}")
        return []  # Placeholder
    
    def _default_filter_results(self, parameters: Dict, context: Dict) -> List[Dict]:
        """Default filter results action"""
        # This would integrate with actual filtering
        logger.info(f"Filtering results with parameters: {parameters}")
        return []  # Placeholder
    
    def create_search_save_favorite_task(self, 
                                       search_params: Dict,
                                       save_count: int = 3,
                                       favorite_first: bool = True,
                                       user_id: int = None) -> MultiStepTask:
        """
        Create a common task: search, save top N, favorite first
        
        Args:
            search_params: Search parameters
            save_count: Number of properties to save
            favorite_first: Whether to favorite the first result
            user_id: User ID
            
        Returns:
            Created MultiStepTask
        """
        steps = [
            TaskStep(
                name="Search Properties",
                description="Search for properties based on criteria",
                action_function="search_properties",
                parameters=search_params
            ),
            TaskStep(
                name="Select Top Results",
                description="Select top results from search",
                action_function="sort_results",
                parameters={"sort_by": "relevance", "limit": save_count}
            ),
            TaskStep(
                name="Save Properties",
                description=f"Save top {save_count} properties",
                action_function="save_property",
                parameters={"count": save_count},
                requires_approval=True
            )
        ]
        
        if favorite_first:
            steps.append(
                TaskStep(
                    name="Favorite First Property",
                    description="Add first property to favorites",
                    action_function="favorite_property",
                    parameters={"index": 0},
                    requires_approval=True
                )
            )
        
        return self.create_task(
            name="Search, Save, and Favorite Properties",
            description=f"Search properties, save top {save_count}, and favorite first",
            steps=steps,
            priority=TaskPriority.HIGH,
            user_id=user_id,
            context={"search_params": search_params}
        )
    
    def get_task_summary(self, task_id: str) -> Optional[Dict]:
        """Get summary of task status and progress"""
        task = self.get_task(task_id)
        if not task:
            return None
        
        return {
            'task_id': task.task_id,
            'name': task.name,
            'status': task.status.value,
            'progress': task.get_progress(),
            'current_step': task.get_current_step().to_dict() if task.get_current_step() else None,
            'requires_approval': task.requires_user_approval(),
            'estimated_completion': self._estimate_completion(task)
        }
    
    def _estimate_completion(self, task: MultiStepTask) -> str:
        """Estimate task completion time"""
        progress = task.get_progress()
        if progress['progress_percentage'] == 100:
            return "Completed"
        elif progress['progress_percentage'] > 50:
            return "Near completion"
        elif progress['progress_percentage'] > 25:
            return "In progress"
        else:
            return "Just started"


# Global instance
task_manager = TaskManager()