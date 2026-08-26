"""
Task Orchestrator
Manages long-running autonomous tasks with progress tracking and retry logic
"""

from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
import json

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task lifecycle statuses"""
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING_USER = "waiting_user"
    WAITING_CONFIRMATION = "waiting_confirmation"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TaskStep:
    """Represents a single step in a task"""
    step_id: str = None
    name: str = None
    description: str = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = None
    started_at: str = None
    completed_at: str = None
    retry_count: int = 0
    
    def __post_init__(self):
        if not self.step_id:
            self.step_id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'step_id': self.step_id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'retry_count': self.retry_count
        }


@dataclass
class AutonomousTask:
    """Represents an autonomous task"""
    task_id: str = None
    user_id: int = None
    conversation_id: str = None
    goal: str = None
    agent_type: str = None
    priority: TaskPriority = None
    status: TaskStatus = TaskStatus.PENDING
    steps: List[TaskStep] = field(default_factory=list)
    current_step_index: int = 0
    progress: float = 0.0
    result: Any = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    created_at: str = None
    updated_at: str = None
    started_at: str = None
    completed_at: str = None
    retry_count: int = 0
    max_retries: int = 3
    idempotency_key: str = None
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.idempotency_key:
            self.idempotency_key = str(uuid.uuid4())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'task_id': self.task_id,
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'goal': self.goal,
            'agent_type': self.agent_type,
            'priority': self.priority.value,
            'status': self.status.value,
            'steps': [step.to_dict() for step in self.steps],
            'current_step_index': self.current_step_index,
            'progress': self.progress,
            'result': self.result,
            'errors': self.errors,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'idempotency_key': self.idempotency_key
        }


class TaskOrchestrator:
    """
    Orchestrates autonomous tasks with progress tracking
    Manages task lifecycle, retry logic, and error handling
    """
    
    def __init__(self):
        self.tasks: Dict[str, AutonomousTask] = {}
        self.task_history: List[Dict] = []
        self.step_handlers: Dict[str, Callable] = {}
        self.active_tasks: Dict[str, AutonomousTask] = {}
        self._register_default_handlers()
    
    def create_task(self,
                   user_id: int,
                   conversation_id: str,
                   goal: str,
                   agent_type: str = "general",
                   priority: TaskPriority = TaskPriority.MEDIUM,
                   steps: List[TaskStep] = None,
                   metadata: Dict = None) -> AutonomousTask:
        """
        Create a new autonomous task
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID
            goal: Task goal description
            agent_type: Type of agent to execute
            priority: Task priority
            steps: Predefined steps (optional)
            metadata: Additional metadata
            
        Returns:
            Created task
        """
        task = AutonomousTask(
            user_id=user_id,
            conversation_id=conversation_id,
            goal=goal,
            agent_type=agent_type,
            priority=priority,
            steps=steps or [],
            metadata=metadata or {}
        )
        
        self.tasks[task.task_id] = task
        logger.info(f"Created task {task.task_id}: {goal}")
        return task
    
    def add_step(self, task_id: str, step: TaskStep):
        """Add a step to a task"""
        if task_id in self.tasks:
            self.tasks[task_id].steps.append(step)
            self.tasks[task_id].updated_at = datetime.now().isoformat()
    
    def start_task(self, task_id: str) -> bool:
        """Start executing a task"""
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} not found")
            return False
        
        task = self.tasks[task_id]
        
        if task.status in [TaskStatus.RUNNING, TaskStatus.COMPLETED]:
            logger.warning(f"Task {task_id} already {task.status.value}")
            return False
        
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()
        task.updated_at = datetime.now().isoformat()
        
        self.active_tasks[task_id] = task
        
        logger.info(f"Started task {task_id}")
        return True
    
    def execute_step(self, task_id: str, step_handler: Callable = None) -> TaskStep:
        """
        Execute the current step of a task
        
        Args:
            task_id: Task ID
            step_handler: Optional handler function for the step
            
        Returns:
            Executed step
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        
        if task.status != TaskStatus.RUNNING:
            raise ValueError(f"Task {task_id} is not running")
        
        if task.current_step_index >= len(task.steps):
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now().isoformat()
            task.progress = 1.0
            del self.active_tasks[task_id]
            logger.info(f"Task {task_id} completed")
            return None
        
        step = task.steps[task.current_step_index]
        step.status = TaskStatus.RUNNING
        step.started_at = datetime.now().isoformat()
        
        try:
            # Execute step handler if provided
            if step_handler:
                result = step_handler(task, step)
                step.result = result
            else:
                # Check for registered handler
                handler = self.step_handlers.get(step.name)
                if handler:
                    result = handler(task, step)
                    step.result = result
                else:
                    # Use default handler
                    default_handler = self.step_handlers.get('default')
                    if default_handler:
                        result = default_handler(task, step)
                        step.result = result
                    else:
                        logger.warning(f"No handler for step {step.name}")
            
            step.status = TaskStatus.COMPLETED
            step.completed_at = datetime.now().isoformat()
            
            # Update task progress
            task.current_step_index += 1
            task.progress = task.current_step_index / len(task.steps)
            task.updated_at = datetime.now().isoformat()
            
            logger.info(f"Completed step {step.step_id} for task {task_id}")
            
        except Exception as e:
            step.status = TaskStatus.FAILED
            step.error = str(e)
            task.errors.append(f"Step {step.name} failed: {str(e)}")
            task.updated_at = datetime.now().isoformat()
            
            logger.error(f"Step {step.step_id} failed for task {task_id}: {str(e)}")
        
        return step
    
    def complete_task(self, task_id: str, result: Any = None):
        """Mark task as completed"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now().isoformat()
        task.progress = 1.0
        task.result = result
        task.updated_at = datetime.now().isoformat()
        
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        
        # Log to history
        self.task_history.append({
            'timestamp': datetime.now().isoformat(),
            'task_id': task_id,
            'user_id': task.user_id,
            'goal': task.goal,
            'status': 'completed',
            'duration_seconds': self._calculate_duration(task)
        })
        
        logger.info(f"Task {task_id} completed")
    
    def fail_task(self, task_id: str, error: str):
        """Mark task as failed"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.status = TaskStatus.FAILED
        task.errors.append(error)
        task.updated_at = datetime.now().isoformat()
        
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        
        # Log to history
        self.task_history.append({
            'timestamp': datetime.now().isoformat(),
            'task_id': task_id,
            'user_id': task.user_id,
            'goal': task.goal,
            'status': 'failed',
            'error': error
        })
        
        logger.error(f"Task {task_id} failed: {error}")
    
    def cancel_task(self, task_id: str):
        """Cancel a task"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.status = TaskStatus.CANCELLED
        task.updated_at = datetime.now().isoformat()
        
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        
        logger.info(f"Task {task_id} cancelled")
    
    def retry_task(self, task_id: str) -> bool:
        """Retry a failed task"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        if task.status != TaskStatus.FAILED:
            logger.warning(f"Task {task_id} is not failed, cannot retry")
            return False
        
        if task.retry_count >= task.max_retries:
            logger.warning(f"Task {task_id} exceeded max retries")
            return False
        
        # Reset task for retry
        task.status = TaskStatus.RETRYING
        task.retry_count += 1
        task.current_step_index = 0
        task.progress = 0.0
        task.errors = []
        
        # Reset steps
        for step in task.steps:
            step.status = TaskStatus.PENDING
            step.result = None
            step.error = None
            step.started_at = None
            step.completed_at = None
        
        task.updated_at = datetime.now().isoformat()
        
        logger.info(f"Retrying task {task_id} (attempt {task.retry_count})")
        return True
    
    def request_user_input(self, task_id: str, question: str) -> TaskStatus:
        """Request user input during task execution"""
        if task_id not in self.tasks:
            return TaskStatus.FAILED
        
        task = self.tasks[task_id]
        task.status = TaskStatus.WAITING_USER
        task.metadata['pending_question'] = question
        task.updated_at = datetime.now().isoformat()
        
        logger.info(f"Task {task_id} waiting for user input")
        return task.status
    
    def request_confirmation(self, task_id: str, action: str) -> TaskStatus:
        """Request user confirmation for an action"""
        if task_id not in self.tasks:
            return TaskStatus.FAILED
        
        task = self.tasks[task_id]
        task.status = TaskStatus.WAITING_CONFIRMATION
        task.metadata['pending_confirmation'] = action
        task.updated_at = datetime.now().isoformat()
        
        logger.info(f"Task {task_id} waiting for confirmation")
        return task.status
    
    def resume_task(self, task_id: str):
        """Resume a task that was waiting for user input/confirmation"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        
        if task.status not in [TaskStatus.WAITING_USER, TaskStatus.WAITING_CONFIRMATION]:
            logger.warning(f"Task {task_id} is not waiting, cannot resume")
            return
        
        task.status = TaskStatus.RUNNING
        self.active_tasks[task_id] = task
        task.updated_at = datetime.now().isoformat()
        
        logger.info(f"Resumed task {task_id}")
    
    def escalate_to_human(self, task_id: str, reason: str):
        """Escalate task to human review"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.status = TaskStatus.NEEDS_HUMAN_REVIEW
        task.metadata['escalation_reason'] = reason
        task.updated_at = datetime.now().isoformat()
        
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        
        logger.info(f"Task {task_id} escalated to human review: {reason}")
    
    def register_step_handler(self, step_name: str, handler: Callable):
        """Register a handler function for a step type"""
        self.step_handlers[step_name] = handler
        logger.info(f"Registered handler for step: {step_name}")
    
    def get_task(self, task_id: str) -> Optional[AutonomousTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def get_user_tasks(self, user_id: int) -> List[AutonomousTask]:
        """Get all tasks for a user"""
        return [task for task in self.tasks.values() if task.user_id == user_id]
    
    def get_active_tasks(self) -> List[AutonomousTask]:
        """Get all currently running tasks"""
        return list(self.active_tasks.values())
    
    def get_progress_message(self, task_id: str) -> str:
        """Get human-readable progress message"""
        task = self.tasks.get(task_id)
        if not task:
            return "المهمة غير موجودة"
        
        if task.status == TaskStatus.PENDING:
            return "⏳ جاري التحضير..."
        elif task.status == TaskStatus.PLANNING:
            return "📋 جاري التخطيط..."
        elif task.status == TaskStatus.RUNNING:
            current_step = task.steps[task.current_step_index] if task.current_step_index < len(task.steps) else None
            if current_step:
                return f"🔄 {current_step.description}"
            return "⏳ جاري التنفيذ..."
        elif task.status == TaskStatus.WAITING_USER:
            return "❓ في انتظار إدخالك..."
        elif task.status == TaskStatus.WAITING_CONFIRMATION:
            return "⚠️ في انتظار تأكيدك..."
        elif task.status == TaskStatus.RETRYING:
            return f"🔄 إعادة المحاولة ({task.retry_count}/{task.max_retries})..."
        elif task.status == TaskStatus.COMPLETED:
            return "✅ تمت المهمة بنجاح"
        elif task.status == TaskStatus.FAILED:
            return "❌ فشلت المهمة"
        elif task.status == TaskStatus.CANCELLED:
            return "🚫 تم إلغاء المهمة"
        elif task.status == TaskStatus.NEEDS_HUMAN_REVIEW:
            return "👤 تحتاج مراجعة بشرية"
        
        return "⏳ جاري المعالجة..."
    
    def _calculate_duration(self, task: AutonomousTask) -> float:
        """Calculate task duration in seconds"""
        if not task.started_at or not task.completed_at:
            return 0.0
        
        start = datetime.fromisoformat(task.started_at)
        end = datetime.fromisoformat(task.completed_at)
        return (end - start).total_seconds()
    
    def cleanup_old_tasks(self, days: int = 7):
        """Remove completed tasks older than specified days"""
        cutoff_date = datetime.now() - datetime.timedelta(days=days)
        
        to_delete = []
        for task_id, task in self.tasks.items():
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                if task.completed_at:
                    completed_date = datetime.fromisoformat(task.completed_at)
                    if completed_date < cutoff_date:
                        to_delete.append(task_id)
        
        for task_id in to_delete:
            del self.tasks[task_id]
        
        logger.info(f"Cleaned up {len(to_delete)} old tasks")
    
    def get_orchestrator_statistics(self) -> Dict:
        """Get orchestrator statistics"""
        status_counts = {}
        for task in self.tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_tasks': len(self.tasks),
            'active_tasks': len(self.active_tasks),
            'status_distribution': status_counts,
            'history_count': len(self.task_history),
            'registered_handlers': len(self.step_handlers)
        }
    
    def _register_default_handlers(self):
        """Register default step handlers"""
        def default_handler(task, step):
            return f"Completed {step.name}"
        
        self.step_handlers['default'] = default_handler


# Global instance
task_orchestrator = TaskOrchestrator()