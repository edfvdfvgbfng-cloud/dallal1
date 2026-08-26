"""
Advanced AI Orchestrator - Integrates all advanced reasoning components
Connects goal understanding, planning, task management, context resolution, memory, and UI actions
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

from .ai_goal_understanding import user_goal_understanding_system, UserGoal, GoalType
from .ai_constraint_engine import constraint_engine
from .ai_smart_clarification import smart_clarification_system
from .ai_conversation_planner import conversation_planner, ConversationPlan
from .ai_task_manager import task_manager, MultiStepTask, TaskStatus, TaskPriority
from .ai_context_resolver import context_resolver
from .ai_semantic_memory import semantic_memory, MemoryType, MemoryImportance
from .ai_smart_recommendations import smart_recommendation_engine
from .ai_query_relaxation import query_relaxation_engine
from .ai_evidence_response import evidence_based_response_system
from .ai_ui_actions import ui_action_manager, UIAction
from .ai_agent_loop import ai_agent
from .ai_agent_tools import tool_registry

logger = logging.getLogger(__name__)


class AdvancedAIOrchestrator:
    """
    Advanced AI Orchestrator that integrates all advanced reasoning components
    Provides comprehensive understanding, planning, and execution capabilities
    """
    
    def __init__(self):
        # Component systems
        self.goal_system = user_goal_understanding_system
        self.constraint_engine = constraint_engine
        self.clarification_system = smart_clarification_system
        self.planner = conversation_planner
        self.task_manager = task_manager
        self.context_resolver = context_resolver
        self.memory_system = semantic_memory
        self.recommendation_engine = smart_recommendation_engine
        self.relaxation_engine = query_relaxation_engine
        self.evidence_system = evidence_based_response_system
        self.ui_actions = ui_action_manager
        
        # State management
        self.active_conversation: str = None
        self.active_task: str = None
        self.conversation_contexts: Dict[str, Dict] = {}
        self.orchestration_history: List[Dict] = []
    
    def process_advanced_query(self, 
                              user_input: str,
                              conversation_id: str,
                              user_id: int = None,
                              is_voice: bool = False) -> Dict:
        """
        Process user query with advanced reasoning capabilities
        
        Args:
            user_input: User's text or voice input
            conversation_id: Conversation identifier
            user_id: User ID
            is_voice: Whether input is voice
            
        Returns:
            Comprehensive response with advanced reasoning
        """
        try:
            # Get or create conversation context
            context = self._get_or_create_context(conversation_id, user_id)
            
            # Update context with current input
            context['current_input'] = user_input
            context['is_voice'] = is_voice
            context['timestamp'] = datetime.now().isoformat()
            
            # Store in semantic memory
            self.memory_system.store_memory(
                content={'user_input': user_input, 'timestamp': datetime.now().isoformat()},
                memory_type=MemoryType.EPHEMERAL,
                importance=MemoryImportance.MEDIUM,
                user_id=user_id,
                tags=['conversation', 'input']
            )
            
            # Step 1: Understand user goal
            user_goal = self.goal_system.understand_goal(user_input, context)
            
            # Update context with goal
            context['user_goal'] = user_goal.to_dict()
            
            # Step 2: Resolve references in input
            resolved_references = self._resolve_references(user_input, context)
            context['resolved_references'] = [r.to_dict() for r in resolved_references]
            
            # Step 3: Check for task changes
            task_change = self._detect_task_change(user_goal, context)
            if task_change:
                context['task_change'] = task_change
            
            # Step 4: Handle different goal types
            if user_goal.goal == GoalType.NAVIGATION:
                return self._handle_navigation_goal(user_goal, context)
            
            elif user_goal.goal == GoalType.COMPARISON:
                return self._handle_comparison_goal(user_goal, context)
            
            elif user_goal.actions:
                return self._handle_action_goal(user_goal, context)
            
            # Step 5: Create conversation plan
            plan = self.planner.create_plan(user_goal, context)
            context['plan'] = plan.to_dict()
            
            # Step 6: Execute plan steps
            execution_result = self._execute_plan_steps(plan, context)
            
            # Step 7: Generate response
            response = self._generate_advanced_response(
                user_goal, plan, execution_result, context
            )
            
            # Step 8: Verify response with evidence
            verified_response = self.evidence_system.verify_response(
                response['text'], execution_result.get('tool_results', {}), context
            )
            
            # Step 9: Add recommendations if applicable
            if user_goal.goal == GoalType.FIND_PROPERTY and execution_result.get('results'):
                recommendations = self.recommendation_engine.generate_recommendations(
                    user_goal, execution_result['results'], user_id
                )
                response['recommendations'] = [r.to_dict() for r in recommendations]
            
            # Step 10: Store successful interaction in memory
            if user_id:
                self._store_interaction_in_memory(user_id, user_goal, context)
            
            # Update context
            self.conversation_contexts[conversation_id] = context
            
            # Log orchestration
            self.orchestration_history.append({
                'timestamp': datetime.now().isoformat(),
                'conversation_id': conversation_id,
                'user_id': user_id,
                'goal': user_goal.to_dict(),
                'plan_id': plan.plan_id,
                'execution_success': execution_result.get('success', False)
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error in advanced orchestration: {str(e)}")
            return self._create_error_response(str(e), context)
    
    def _get_or_create_context(self, conversation_id: str, user_id: int) -> Dict:
        """Get or create conversation context"""
        if conversation_id not in self.conversation_contexts:
            self.conversation_contexts[conversation_id] = {
                'conversation_id': conversation_id,
                'user_id': user_id,
                'messages': [],
                'entities': {},
                'recent_items': [],
                'active_entity': None,
                'task_history': [],
                'timestamp': datetime.now().isoformat()
            }
        
        return self.conversation_contexts[conversation_id]
    
    def _resolve_references(self, user_input: str, context: Dict) -> List:
        """Resolve references in user input"""
        references = []
        
        # Find potential references in input
        reference_keywords = ['هذا', 'هاذا', 'الأول', 'الثاني', 'السابق', 'الأفضل', 'الأرخص']
        
        for keyword in reference_keywords:
            if keyword in user_input:
                resolved = self.context_resolver.resolve_reference(keyword, context)
                if resolved:
                    references.append(resolved)
        
        return references
    
    def _detect_task_change(self, user_goal: UserGoal, context: Dict) -> Optional[Dict]:
        """Detect if user changed their goal/task"""
        previous_goals = context.get('task_history', [])
        
        if previous_goals:
            last_goal = previous_goals[-1]
            if last_goal.get('goal') != user_goal.goal.value:
                return {
                    'previous_goal': last_goal,
                    'new_goal': user_goal.goal.value,
                    'requires_confirmation': True
                }
        
        return None
    
    def _handle_navigation_goal(self, user_goal: UserGoal, context: Dict) -> Dict:
        """Handle navigation goal"""
        # Parse navigation intent
        ui_action = self.ui_actions.parse_natural_language_command(
            user_goal.metadata.get('original_input'), context
        )
        
        if ui_action:
            # Execute UI action
            success, result = self.ui_actions.execute_action(ui_action)
            
            return {
                'success': success,
                'action': ui_action.to_dict(),
                'result': result,
                'text': f"سأنتقل {self.ui_actions.get_action_summary(ui_action)}",
                'requires_confirmation': ui_action.requires_confirmation,
                'confidence': 0.9
            }
        
        return {
            'success': False,
            'text': "لم أفهم المكان الذي تريد الذهاب إليه. هل يمكنك التوضيح؟",
            'confidence': 0.3
        }
    
    def _handle_comparison_goal(self, user_goal: UserGoal, context: Dict) -> Dict:
        """Handle comparison goal"""
        # Resolve items to compare
        items_to_compare = []
        
        # Resolve references
        resolved_references = context.get('resolved_references', [])
        for ref in resolved_references:
            if ref.get('resolved_value'):
                items_to_compare.append(ref['resolved_value'])
        
        # If not enough items resolved, ask for clarification
        if len(items_to_compare) < 2:
            return {
                'success': False,
                'text': "أحتاج إلى معرفة العقارات التي تريد مقارنتها. حدد العقارين مثلاً: قارن الأول والثالث.",
                'confidence': 0.5
            }
        
        # Perform comparison
        comparison_result = self._perform_comparison(items_to_compare, context)
        
        return {
            'success': True,
            'comparison': comparison_result,
            'text': f"قارنت بين {len(items_to_compare)} عقارات",
            'confidence': 0.85
        }
    
    def _handle_action_goal(self, user_goal: UserGoal, context: Dict) -> Dict:
        """Handle action-oriented goal"""
        # Create multi-step task for actions
        if 'save' in user_goal.actions and 'search' in user_goal.actions:
            # Create save task
            search_params = self._extract_search_params(user_goal, context)
            task = self.task_manager.create_search_save_favorite_task(
                search_params=search_params,
                user_id=context.get('user_id')
            )
            
            # Execute task
            success, result = self.task_manager.execute_task(task.task_id)
            
            return {
                'success': success,
                'task': task.to_dict(),
                'result': result,
                'text': "سأبحث عن العقارات، أحفظ أفضل 3، وأضع الأول بالمفضلة",
                'confidence': 0.8
            }
        
        return {
            'success': False,
            'text': "لم أفهم الإجراء المطلوب بالتحديد",
            'confidence': 0.4
        }
    
    def _execute_plan_steps(self, plan: ConversationPlan, context: Dict) -> Dict:
        """Execute conversation plan steps"""
        execution_result = {
            'success': True,
            'steps_executed': 0,
            'tool_results': {},
            'results': [],
            'errors': []
        }
        
        # Execute steps until clarification needed or plan complete
        for step in plan.steps:
            if step.status.value in ['completed', 'skipped']:
                continue
            
            try:
                # Execute step function
                if step.action_function:
                    result = self._execute_step_function(step, context)
                    execution_result['tool_results'][step.step_id] = result
                    execution_result['steps_executed'] += 1
                
                # Mark step as completed
                plan.mark_step_completed(step.step_id, result)
                
                # Check if clarification is needed
                if step.step_type.value == 'clarification':
                    clarification_questions = self.clarification_system.generate_clarification_questions(
                        UserGoal(**context.get('user_goal', {})), context
                    )
                    
                    if clarification_questions:
                        execution_result['needs_clarification'] = True
                        execution_result['clarification_questions'] = [
                            q.question_text for q in clarification_questions
                        ]
                        break  # Stop for clarification
                
            except Exception as e:
                execution_result['errors'].append(str(e))
                plan.mark_step_failed(step.step_id, str(e))
        
        execution_result['success'] = len(execution_result['errors']) == 0
        return execution_result
    
    def _execute_step_function(self, step, context: Dict) -> Any:
        """Execute individual step function"""
        function_map = {
            'search_properties': self._search_properties_step,
            'apply_constraints': self._apply_constraints_step,
            'generate_clarification_questions': self._generate_clarification_step,
            'rank_results': self._rank_results_step,
            'select_top_results': self._select_top_results_step
        }
        
        function = function_map.get(step.action_function)
        if function:
            return function(step.parameters, context)
        
        return None
    
    def _search_properties_step(self, parameters: Dict, context: Dict) -> List[Dict]:
        """Execute property search step"""
        # Use AI agent to search
        search_params = parameters or context.get('entities', {})
        
        # Get search tool
        search_tool = tool_registry.get_tool('search_properties')
        if search_tool:
            results = search_tool(search_params)
            return results.get('results', [])
        
        return []
    
    def _apply_constraints_step(self, parameters: Dict, context: Dict) -> Dict:
        """Apply constraints to search"""
        user_goal = UserGoal(**context.get('user_goal', {}))
        constraint_set = self.constraint_engine.build_constraint_set_from_goal(user_goal)
        
        return constraint_set.apply_constraints_to_query(user_goal.entities)
    
    def _generate_clarification_step(self, parameters: Dict, context: Dict) -> List[str]:
        """Generate clarification questions"""
        user_goal = UserGoal(**context.get('user_goal', {}))
        questions = self.clarification_system.generate_clarification_questions(user_goal, context)
        
        return [q.question_text for q in questions]
    
    def _rank_results_step(self, parameters: Dict, context: Dict) -> List[tuple]:
        """Rank search results"""
        results = context.get('search_results', [])
        user_goal = UserGoal(**context.get('user_goal', {}))
        
        constraint_set = self.constraint_engine.build_constraint_set_from_goal(user_goal)
        ranked = constraint_set.rank_results(results)
        
        return ranked
    
    def _select_top_results_step(self, parameters: Dict, context: Dict) -> List[Dict]:
        """Select top results"""
        ranked_results = context.get('ranked_results', [])
        limit = parameters.get('limit', 5)
        
        return [item for item, score in ranked_results[:limit]]
    
    def _generate_advanced_response(self, 
                                 user_goal: UserGoal,
                                 plan: ConversationPlan,
                                 execution_result: Dict,
                                 context: Dict) -> Dict:
        """Generate advanced response with full context"""
        base_response = ""
        
        # Check if clarification needed
        if execution_result.get('needs_clarification'):
            questions = execution_result.get('clarification_questions', [])
            if questions:
                base_response = questions[0]  # Ask first question
                return {
                    'text': base_response,
                    'type': 'clarification',
                    'questions': questions,
                    'confidence': 0.6
                }
        
        # Check for empty results
        if execution_result.get('results') == []:
            # Generate relaxation suggestions
            suggestions = self.relaxation_engine.analyze_empty_results(
                user_goal, context.get('entities', {}), 0
            )
            
            if suggestions:
                suggestion = suggestions[0]
                message = self.relaxation_engine.generate_counterfactual_message(
                    suggestion, 0
                )
                
                return {
                    'text': message,
                    'type': 'relaxation_suggestion',
                    'suggestions': [s.to_dict() for s in suggestions],
                    'confidence': 0.7
                }
            
            return {
                'text': "لم أجد نتائج تطابق معايبك. هل تريد محاولة معايير مختلفة؟",
                'type': 'no_results',
                'confidence': 0.5
            }
        
        # Generate normal response
        results = execution_result.get('results', [])
        if results:
            base_response = f"وجدت {len(results)} نتيجة تطابق معايبك. راغب أحداً من هذه الخيارات أو أخبرني بمزيد من التفضيلات."
            
            # Add plan progress
            progress = plan.get_progress()
            if progress:
                base_response += f" (استكملت {progress['progress_percentage']:.0%} من البحث)"
        
        return {
            'text': base_response,
            'type': 'normal',
            'results': results,
            'confidence': 0.8,
            'metadata': {
                'plan_id': plan.plan_id,
                'progress': progress
            }
        }
    
    def _perform_comparison(self, items: List, context: Dict) -> Dict:
        """Perform property comparison"""
        comparison = {
            'items': items,
            'differences': [],
            'recommendation': None
        }
        
        # Simple comparison logic
        if len(items) >= 2:
            item1, item2 = items[0], items[1]
            
            # Compare prices
            if item1.get('price') and item2.get('price'):
                if item1['price'] < item2['price']:
                    comparison['differences'].append(f"العقار الأول أرخص بـ{item2['price'] - item1['price']:,} دينار")
                else:
                    comparison['differences'].append(f"العقار الثاني أرخص بـ{item1['price'] - item2['price']:,} دينار")
            
            # Compare areas
            if item1.get('area') and item2.get('area'):
                if item1['area'] > item2['area']:
                    comparison['differences'].append(f"العقار الأول أكبر بـ{item1['area'] - item2['area']} متر")
                else:
                    comparison['differences'].append(f"العقار الثاني أكبر بـ{item2['area'] - item1['area']} متر")
            
            # Generate recommendation
            comparison['recommendation'] = self._generate_comparison_recommendation(items, context)
        
        return comparison
    
    def _generate_comparison_recommendation(self, items: List, context: Dict) -> str:
        """Generate recommendation based on comparison"""
        # Simple recommendation based on context preferences
        user_preferences = context.get('user_preferences', {})
        
        if user_preferences.get('priority') == 'price':
            cheapest = min(items, key=lambda x: x.get('price', float('inf')))
            return f"بناءً على تفضيلك للسعر، العقار {cheapest.get('title', 'الأرخص')} قد يكون الأنسب."
        
        return "كلا العقاران لديهما مزايا مختلفة. يعتم الاختيار حسب أهميتك الشخصية."
    
    def _extract_search_params(self, user_goal: UserGoal, context: Dict) -> Dict:
        """Extract search parameters from user goal"""
        params = {}
        
        # Extract from entities
        if user_goal.entities.get('governorate'):
            params['governorate'] = user_goal.entities['governorate']
        
        if user_goal.entities.get('property_type'):
            params['property_type'] = user_goal.entities['property_type']
        
        if user_goal.entities.get('price'):
            params['price'] = user_goal.entities['price']
        
        return params
    
    def _store_interaction_in_memory(self, user_id: int, user_goal: UserGoal, context: Dict):
        """Store interaction in semantic memory"""
        # Store user preferences if detected
        if user_goal.entities.get('governorate'):
            self.memory_system.update_user_preference(
                user_id, 'preferred_governorate', user_goal.entities['governorate']
            )
        
        if user_goal.entities.get('property_type'):
            self.memory_system.update_user_preference(
                user_id, 'preferred_property_type', user_goal.entities['property_type']
            )
        
        # Store as session memory
        self.memory_system.store_memory(
            content={
                'interaction_type': user_goal.goal.value,
                'entities': user_goal.entities,
                'preferences': user_goal.preferences
            },
            memory_type=MemoryType.SESSION,
            importance=MemoryImportance.HIGH,
            user_id=user_id,
            tags=['interaction', user_goal.goal.value]
        )
    
    def _create_error_response(self, error: str, context: Dict) -> Dict:
        """Create error response"""
        return {
            'text': f"حدث خطأ: {error}",
            'type': 'error',
            'confidence': 0.1,
            'error': error
        }
    
    def get_conversation_state(self, conversation_id: str) -> Optional[Dict]:
        """Get current conversation state"""
        return self.conversation_contexts.get(conversation_id)
    
    def resume_interrupted_task(self, task_id: str) -> Dict:
        """Resume an interrupted task"""
        task = self.task_manager.get_task(task_id)
        if not task:
            return {
                'success': False,
                'message': 'Task not found'
            }
        
        if task.status == TaskStatus.PAUSED:
            success, result = self.task_manager.resume_task(task_id)
            return {
                'success': success,
                'message': 'Task resumed' if success else 'Failed to resume task',
                'task': task.to_dict()
            }
        
        return {
            'success': False,
            'message': f'Task status is {task.status.value}, cannot resume'
        }
    
    def get_user_context_summary(self, user_id: int) -> Dict:
        """Get summary of user's context and preferences"""
        preferences = self.memory_system.get_user_preferences(user_id)
        user_tasks = self.task_manager.get_user_tasks(user_id)
        
        return {
            'user_id': user_id,
            'preferences': preferences,
            'active_tasks': [task.to_dict() for task in user_tasks],
            'memory_stats': self.memory_system.get_memory_statistics()
        }


# Global instance
advanced_ai_orchestrator = AdvancedAIOrchestrator()