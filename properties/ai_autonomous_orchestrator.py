"""
Autonomous Agent Orchestrator
Integrates all autonomous agent components for complete task management
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from .ai_task_orchestrator import (
    TaskOrchestrator, AutonomousTask, TaskStep, TaskStatus, TaskPriority
)
from .ai_task_queue import TaskQueueManager, QueueType
from .ai_agent_profiles import (
    AgentHandoffSystem, AgentType, AgentContext
)
from .ai_safety_gateway import SafetyGateway, ActionRequest, ActionType, SafetyCheck
from .ai_business_rules import BusinessRulesEngine
from .ai_contradiction_detector import ContradictionDetector

logger = logging.getLogger(__name__)


class AutonomousAgentOrchestrator:
    """
    Orchestrates autonomous agent execution
    Integrates task management, safety, business rules, and agent handoff
    """
    
    def __init__(self):
        # Core components
        self.task_orchestrator = TaskOrchestrator()
        self.queue_manager = TaskQueueManager()
        self.agent_handoff = AgentHandoffSystem()
        self.safety_gateway = SafetyGateway()
        self.business_rules = BusinessRulesEngine()
        self.contradiction_detector = ContradictionDetector()
        
        # Execution state
        self.is_running = False
        self.active_contexts: Dict[str, AgentContext] = {}
    
    def start(self):
        """Start the autonomous agent system"""
        self.is_running = True
        self.queue_manager.start_all()
        logger.info("Autonomous Agent Orchestrator started")
    
    def stop(self):
        """Stop the autonomous agent system"""
        self.is_running = False
        self.queue_manager.stop_all()
        logger.info("Autonomous Agent Orchestrator stopped")
    
    def process_user_request(self,
                            user_id: int,
                            conversation_id: str,
                            user_input: str,
                            context: Dict = None) -> Dict:
        """
        Process a user request through autonomous agent
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID
            user_input: User's input
            context: Additional context
            
        Returns:
            Response with task information
        """
        try:
            # Determine best agent
            agent_type = self.agent_handoff.determine_best_agent(user_input, context)
            
            # Create or update context
            if context and context.get('context_id'):
                agent_context = self.agent_handoff.get_context(context['context_id'])
                if agent_context:
                    # Update context
                    self.agent_handoff.update_context(
                        agent_context.context_id,
                        {'intent': user_input}
                    )
                else:
                    # Create new context
                    agent_context = self.agent_handoff.create_context(
                        user_id=user_id,
                        conversation_id=conversation_id,
                        intent=user_input,
                        entities=context.get('entities', {}),
                        goal=context.get('goal', user_input)
                    )
            else:
                # Create new context
                agent_context = self.agent_handoff.create_context(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    intent=user_input,
                    entities=context.get('entities', {}),
                    goal=context.get('goal', user_input)
                )
            
            # Create task
            task = self.task_orchestrator.create_task(
                user_id=user_id,
                conversation_id=conversation_id,
                goal=user_input,
                agent_type=agent_type.value,
                priority=TaskPriority.MEDIUM,
                metadata={'context_id': agent_context.context_id}
            )
            
            # Add default steps for basic task
            self._add_default_steps(task, agent_type)
            
            # Start task
            self.task_orchestrator.start_task(task.task_id)
            
            # Enqueue for background processing
            self.queue_manager.enqueue_task(
                queue_type=QueueType.AI_TASKS,
                task_id=task.task_id,
                payload={
                    'task_id': task.task_id,
                    'user_id': user_id,
                    'conversation_id': conversation_id,
                    'user_input': user_input,
                    'agent_type': agent_type.value,
                    'context_id': agent_context.context_id
                },
                priority=TaskPriority.MEDIUM
            )
            
            # Get initial progress message
            progress_message = self.task_orchestrator.get_progress_message(task.task_id)
            
            return {
                'task_id': task.task_id,
                'agent_type': agent_type.value,
                'context_id': agent_context.context_id,
                'status': 'started',
                'progress_message': progress_message,
                'task': task.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error processing user request: {str(e)}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def _add_default_steps(self, task: AutonomousTask, agent_type: AgentType):
        """Add default steps based on agent type"""
        if agent_type == AgentType.PROPERTY:
            task.steps = [
                TaskStep(name="understand_request", description="فهم طلبك"),
                TaskStep(name="search_properties", description="البحث عن العقارات"),
                TaskStep(name="filter_results", description="تصفية النتائج"),
                TaskStep(name="rank_results", description="ترتيب النتائج"),
                TaskStep(name="prepare_response", description="إعداد الرد")
            ]
        elif agent_type == AgentType.SELLER:
            task.steps = [
                TaskStep(name="collect_data", description="جمع البيانات"),
                TaskStep(name="validate_data", description="التحقق من البيانات"),
                TaskStep(name="match_agent", description="مطابقة الدلال"),
                TaskStep(name="prepare_listing", description="إعداد الإعلان")
            ]
        elif agent_type == AgentType.BUYER:
            task.steps = [
                TaskStep(name="understand_preferences", description="فهم التفضيلات"),
                TaskStep(name="search_properties", description="البحث عن العقارات"),
                TaskStep(name="compare_options", description="مقارنة الخيارات"),
                TaskStep(name="recommend", description="التوصية")
            ]
        else:
            task.steps = [
                TaskStep(name="understand_request", description="فهم طلبك"),
                TaskStep(name="process", description="المعالجة"),
                TaskStep(name="respond", description="الرد")
            ]
    
    def execute_task_step(self, task_id: str) -> Dict:
        """
        Execute a single step of a task with safety checks
        
        Args:
            task_id: Task ID
            
        Returns:
            Step execution result
        """
        task = self.task_orchestrator.get_task(task_id)
        if not task:
            return {'error': 'Task not found', 'status': 'failed'}
        
        # Safety check before execution
        action_request = ActionRequest(
            action_id=f"{task_id}_step_{task.current_step_index}",
            action_type=ActionType.EXECUTE,
            user_id=task.user_id,
            agent_type=task.agent_type,
            tool_name="task_step",
            parameters={'step_index': task.current_step_index}
        )
        
        safety_check = self.safety_gateway.check_action(action_request)
        
        if not safety_check.passed:
            return {
                'error': 'Safety check failed',
                'safety_check': safety_check.to_dict(),
                'status': 'blocked'
            }
        
        # Execute step
        step = self.task_orchestrator.execute_step(task_id)
        
        if not step:
            # Task completed
            self.task_orchestrator.complete_task(task_id)
            return {
                'status': 'completed',
                'task_id': task_id,
                'result': task.result
            }
        
        if step.status == TaskStatus.FAILED:
            # Check if we should retry
            if step.retry_count < 3:
                self.task_orchestrator.retry_task(task_id)
                return {
                    'status': 'retrying',
                    'task_id': task_id,
                    'retry_count': task.retry_count
                }
            else:
                self.task_orchestrator.fail_task(task_id, f"Step {step.name} failed after retries")
                return {
                    'status': 'failed',
                    'error': step.error
                }
        
        # Return step result
        return {
            'status': 'success',
            'step': step.to_dict(),
            'task_progress': task.progress
        }
    
    def execute_tool_action(self,
                           user_id: int,
                           agent_type: str,
                           tool_name: str,
                           parameters: Dict) -> Dict:
        """
        Execute a tool action with safety and business rules validation
        
        Args:
            user_id: User ID
            agent_type: Agent type
            tool_name: Tool to execute
            parameters: Tool parameters
            
        Returns:
            Execution result
        """
        # Determine action type
        action_type = self._determine_action_type(tool_name)
        
        # Create action request
        action_request = ActionRequest(
            action_id=f"{tool_name}_{datetime.now().timestamp()}",
            action_type=action_type,
            user_id=user_id,
            agent_type=agent_type,
            tool_name=tool_name,
            parameters=parameters
        )
        
        # Safety check
        safety_check = self.safety_gateway.check_action(action_request)
        
        if not safety_check.passed:
            return {
                'success': False,
                'blocked': True,
                'safety_check': safety_check.to_dict()
            }
        
        # Business rules validation
        entity = self._determine_entity(tool_name)
        business_validation = self.business_rules.validate_action(
            action=tool_name,
            entity=entity,
            data=parameters
        )
        
        if not business_validation['valid']:
            return {
                'success': False,
                'blocked': True,
                'business_validation': business_validation
            }
        
        # Check for user confirmation if required
        if safety_check.requires_confirmation:
            return {
                'success': False,
                'requires_confirmation': True,
                'action': tool_name,
                'parameters': parameters,
                'safety_check': safety_check.to_dict()
            }
        
        # Execute action (placeholder - would call actual tool)
        result = self._execute_tool(tool_name, parameters)
        
        return {
            'success': True,
            'result': result,
            'safety_check': safety_check.to_dict(),
            'business_validation': business_validation
        }
    
    def _determine_action_type(self, tool_name: str) -> ActionType:
        """Determine action type from tool name"""
        if 'delete' in tool_name.lower():
            return ActionType.DELETE
        elif 'publish' in tool_name.lower():
            return ActionType.PUBLISH
        elif 'send' in tool_name.lower() or 'contact' in tool_name.lower():
            return ActionType.SEND
        elif 'modify' in tool_name.lower() or 'update' in tool_name.lower():
            return ActionType.MODIFY
        elif 'upload' in tool_name.lower():
            return ActionType.UPLOAD
        else:
            return ActionType.READ
    
    def _determine_entity(self, tool_name: str) -> str:
        """Determine entity type from tool name"""
        if 'property' in tool_name.lower():
            return 'property'
        elif 'user' in tool_name.lower():
            return 'user'
        elif 'listing' in tool_name.lower():
            return 'listing'
        elif 'job' in tool_name.lower():
            return 'job'
        else:
            return 'general'
    
    def _execute_tool(self, tool_name: str, parameters: Dict) -> Any:
        """Execute tool (placeholder)"""
        # This would call the actual tool implementation
        logger.info(f"Executing tool {tool_name} with parameters {parameters}")
        return {'executed': True, 'tool': tool_name}
    
    def handoff_agent(self,
                     context_id: str,
                     from_agent: AgentType,
                     to_agent: AgentType) -> Dict:
        """
        Handoff context from one agent to another
        
        Args:
            context_id: Context ID
            from_agent: Source agent
            to_agent: Destination agent
            
        Returns:
            Handoff result
        """
        context = self.agent_handoff.get_context(context_id)
        if not context:
            return {'error': 'Context not found', 'status': 'failed'}
        
        updated_context = self.agent_handoff.handoff(from_agent, to_agent, context)
        
        return {
            'status': 'success',
            'context': updated_context.to_dict(),
            'from_agent': from_agent.value,
            'to_agent': to_agent.value
        }
    
    def get_task_status(self, task_id: str) -> Dict:
        """Get current status of a task"""
        task = self.task_orchestrator.get_task(task_id)
        if not task:
            return {'error': 'Task not found'}
        
        return {
            'task': task.to_dict(),
            'progress_message': self.task_orchestrator.get_progress_message(task_id)
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        return self.task_orchestrator.cancel_task(task_id)
    
    def get_system_status(self) -> Dict:
        """Get overall system status"""
        return {
            'is_running': self.is_running,
            'task_orchestrator': self.task_orchestrator.get_orchestrator_statistics(),
            'queue_manager': self.queue_manager.get_queue_statistics(),
            'safety_gateway': self.safety_gateway.get_safety_statistics(),
            'business_rules': self.business_rules.get_evaluation_statistics(),
            'agent_handoff': self.agent_handoff.get_handoff_statistics(),
            'contradiction_detector': self.contradiction_detector.get_conflict_statistics()
        }


# Global instance
autonomous_agent_orchestrator = AutonomousAgentOrchestrator()