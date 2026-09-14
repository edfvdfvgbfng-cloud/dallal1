"""
Task Queue System
Manages background task execution with priority and retry logic
"""

from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import heapq
import threading
import time

from .ai_task_orchestrator import TaskPriority, AutonomousTask

logger = logging.getLogger(__name__)


class QueueType(Enum):
    """Types of task queues"""
    AI_TASKS = "ai_tasks"
    DOCUMENT_TASKS = "document_tasks"
    EMBEDDING_TASKS = "embedding_tasks"
    IMAGE_TASKS = "image_tasks"
    ANALYTICS_TASKS = "analytics_tasks"
    NOTIFICATION_TASKS = "notification_tasks"


class QueueStatus(Enum):
    """Queue status"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class QueuedTask:
    """Task in queue with priority"""
    task_id: str = None
    queue_type: QueueType = None
    priority: TaskPriority = None
    payload: Dict = None
    created_at: str = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300
    idempotency_key: str = None
    
    def __post_init__(self):
        if not self.idempotency_key:
            self.idempotency_key = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def __lt__(self, other):
        """For priority queue ordering"""
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        return priority_order[self.priority] < priority_order[other.priority]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'task_id': self.task_id,
            'queue_type': self.queue_type.value,
            'priority': self.priority.value,
            'payload': self.payload,
            'created_at': self.created_at,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'timeout_seconds': self.timeout_seconds,
            'idempotency_key': self.idempotency_key
        }


class TaskQueue:
    """Task queue with priority management"""
    
    def __init__(self, queue_type: QueueType):
        self.queue_type = queue_type
        self.queue: List[QueuedTask] = []
        self.status = QueueStatus.ACTIVE
        self.processing: Dict[str, bool] = {}
        self.dead_letter_queue: List[QueuedTask] = []
        self.handlers: Dict[str, Callable] = {}
        self._lock = threading.Lock()
    
    def enqueue(self, task: QueuedTask) -> bool:
        """Add task to queue"""
        with self._lock:
            if self.status != QueueStatus.ACTIVE:
                logger.warning(f"Queue {self.queue_type.value} is not active")
                return False
            
            # Check for idempotency
            for existing_task in self.queue:
                if existing_task.idempotency_key == task.idempotency_key:
                    logger.info(f"Task with idempotency key {task.idempotency_key} already in queue")
                    return False
            
            heapq.heappush(self.queue, task)
            logger.info(f"Enqueued task {task.task_id} to {self.queue_type.value}")
            return True
    
    def dequeue(self) -> Optional[QueuedTask]:
        """Get next task from queue"""
        with self._lock:
            if not self.queue:
                return None
            
            task = heapq.heappop(self.queue)
            self.processing[task.task_id] = True
            return task
    
    def mark_complete(self, task_id: str):
        """Mark task as complete"""
        with self._lock:
            if task_id in self.processing:
                del self.processing[task_id]
    
    def mark_failed(self, task: QueuedTask, error: str):
        """Mark task as failed and handle retry"""
        with self._lock:
            if task.task_id in self.processing:
                del self.processing[task.task_id]
            
            task.retry_count += 1
            
            if task.retry_count < task.max_retries:
                # Re-queue with exponential backoff
                logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count})")
                heapq.heappush(self.queue, task)
            else:
                # Move to dead letter queue
                logger.error(f"Task {task.task_id} failed after {task.max_retries} retries")
                self.dead_letter_queue.append(task)
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        with self._lock:
            return len(self.queue)
    
    def get_processing_count(self) -> int:
        """Get number of tasks being processed"""
        with self._lock:
            return len(self.processing)
    
    def pause(self):
        """Pause queue processing"""
        with self._lock:
            self.status = QueueStatus.PAUSED
            logger.info(f"Paused queue {self.queue_type.value}")
    
    def resume(self):
        """Resume queue processing"""
        with self._lock:
            self.status = QueueStatus.ACTIVE
            logger.info(f"Resumed queue {self.queue_type.value}")
    
    def register_handler(self, handler: Callable):
        """Register handler for queue"""
        self.handlers['default'] = handler
        logger.info(f"Registered handler for queue {self.queue_type.value}")


class TaskQueueManager:
    """
    Manages multiple task queues
    Handles task distribution and worker coordination
    """
    
    def __init__(self):
        self.queues: Dict[QueueType, TaskQueue] = {}
        self._initialize_queues()
        self.workers: Dict[QueueType, List[threading.Thread]] = {}
        self.is_running = False
    
    def _initialize_queues(self):
        """Initialize all queue types"""
        for queue_type in QueueType:
            self.queues[queue_type] = TaskQueue(queue_type)
    
    def enqueue_task(self,
                    queue_type: QueueType,
                    task_id: str,
                    payload: Dict,
                    priority: TaskPriority = TaskPriority.MEDIUM,
                    max_retries: int = 3,
                    timeout_seconds: int = 300,
                    idempotency_key: str = None) -> bool:
        """Enqueue task to specific queue"""
        queue = self.queues.get(queue_type)
        if not queue:
            logger.error(f"Queue {queue_type.value} not found")
            return False
        
        task = QueuedTask(
            task_id=task_id,
            queue_type=queue_type,
            priority=priority,
            payload=payload,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            idempotency_key=idempotency_key
        )
        
        return queue.enqueue(task)
    
    def start_workers(self, queue_type: QueueType, worker_count: int = 2):
        """Start worker threads for a queue"""
        if queue_type in self.workers and self.workers[queue_type]:
            logger.warning(f"Workers already running for {queue_type.value}")
            return
        
        queue = self.queues[queue_type]
        self.workers[queue_type] = []
        
        for i in range(worker_count):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(queue, f"{queue_type.value}_worker_{i}"),
                daemon=True
            )
            worker.start()
            self.workers[queue_type].append(worker)
        
        logger.info(f"Started {worker_count} workers for {queue_type.value}")
    
    def _worker_loop(self, queue: TaskQueue, worker_name: str):
        """Worker thread loop"""
        logger.info(f"Worker {worker_name} started")
        
        while self.is_running or queue.get_queue_size() > 0:
            if queue.status != QueueStatus.ACTIVE:
                time.sleep(1)
                continue
            
            task = queue.dequeue()
            if not task:
                time.sleep(0.1)
                continue
            
            try:
                # Execute task
                handler = queue.handlers.get('default')
                if handler:
                    result = handler(task)
                    queue.mark_complete(task.task_id)
                else:
                    logger.warning(f"No handler for task {task.task_id}")
                    queue.mark_complete(task.task_id)
                    
            except Exception as e:
                logger.error(f"Error executing task {task.task_id}: {str(e)}")
                queue.mark_failed(task, str(e))
        
        logger.info(f"Worker {worker_name} stopped")
    
    def start_all(self):
        """Start all queue workers"""
        self.is_running = True
        
        # Start workers for each queue
        for queue_type in QueueType:
            worker_count = 2 if queue_type in [QueueType.AI_TASKS, QueueType.NOTIFICATION_TASKS] else 1
            self.start_workers(queue_type, worker_count)
        
        logger.info("Started all queue workers")
    
    def stop_all(self):
        """Stop all queue workers"""
        self.is_running = False
        
        # Pause all queues
        for queue in self.queues.values():
            queue.pause()
        
        logger.info("Stopped all queue workers")
    
    def get_queue_statistics(self) -> Dict:
        """Get statistics for all queues"""
        stats = {}
        
        for queue_type, queue in self.queues.items():
            stats[queue_type.value] = {
                'queue_size': queue.get_queue_size(),
                'processing_count': queue.get_processing_count(),
                'status': queue.status.value,
                'dead_letter_count': len(queue.dead_letter_queue)
            }
        
        return stats


# Global instance
task_queue_manager = TaskQueueManager()