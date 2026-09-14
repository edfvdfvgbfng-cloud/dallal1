"""
AI Agent Loop System
Implements the complete agent workflow: Understand -> Plan -> Execute -> Verify -> Respond
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import uuid
from django.contrib.auth.models import User

from .ai_agent_tools import tool_registry, ToolResult, ToolPermission
from .ai_arabic_normalizer import arabic_normalizer
from .ai_intent_classifier import intent_classifier
from .ai_entity_extraction import entity_extractor
from .ai_context_engine import context_manager
from .ai_semantic_search import hybrid_search_engine
from .ai_learning_pipeline import data_collector

logger = logging.getLogger('properties')


class AgentState(Enum):
    """Agent workflow states"""
    UNDERSTANDING = "understanding"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    RESPONDING = "responding"
    WAITING_CONFIRMATION = "waiting_confirmation"
    ERROR = "error"


@dataclass
class AgentStep:
    """Single step in agent execution"""
    step_id: str
    step_type: str
    tool_name: Optional[str]
    input_data: Optional[Dict]
    result: Optional[ToolResult]
    timestamp: datetime
    duration_ms: float


@dataclass
class AgentPlan:
    """Execution plan for agent"""
    plan_id: str
    goal: str
    steps: List[Dict]
    estimated_duration: float
    requires_confirmation: bool


class AIAgent:
    """
    Main AI Agent that orchestrates the complete workflow
    Implements: Understand -> Analyze -> Plan -> Execute -> Verify -> Respond
    """
    
    def __init__(self):
        self.tool_registry = tool_registry
        self.arabic_normalizer = arabic_normalizer
        self.intent_classifier = intent_classifier
        self.entity_extractor = entity_extractor
        self.context_manager = context_manager
        self.semantic_search = hybrid_search_engine
        self.data_collector = data_collector
        
        # Agent memory
        self.short_term_memory: Dict[str, Any] = {}
        self.session_memory: Dict[str, Any] = {}
        self.long_term_memory: Dict[str, Any] = {}
        
        # Execution tracking
        self.current_state = AgentState.UNDERSTANDING
        self.execution_history: List[AgentStep] = []
        self.current_plan: Optional[AgentPlan] = None
        
        # Configuration
        self.max_execution_steps = 10
        self.default_timeout = 30  # seconds
        self.retry_attempts = 3
    
    def process_message(self, message: str, conversation_id: str, user: Optional[User] = None) -> Dict[str, Any]:
        """
        Process user message through complete agent loop
        
        Args:
            message: User input message
            conversation_id: Conversation identifier
            user: Current user (optional)
            
        Returns:
            Complete agent response
        """
        try:
            # Step 1: Understand
            self.current_state = AgentState.UNDERSTANDING
            understanding = self._understand(message, conversation_id)
            
            if not understanding['success']:
                return self._create_error_response(understanding['error'])
            
            # Step 2: Analyze Context
            context = self._analyze_context(understanding, conversation_id, user)
            
            # Step 3: Determine Goal
            goal = self._determine_goal(understanding, context)
            
            # Step 4: Plan
            self.current_state = AgentState.PLANNING
            plan = self._create_plan(goal, context, user)
            self.current_plan = plan
            
            # Step 5: Check if confirmation needed
            if plan.requires_confirmation:
                return self._create_confirmation_response(plan, context)
            
            # Step 6: Execute
            self.current_state = AgentState.EXECUTING
            execution_result = self._execute_plan(plan, user)
            
            if not execution_result['success']:
                return self._create_error_response(execution_result['error'])
            
            # Step 7: Verify
            self.current_state = AgentState.VERIFYING
            verification = self._verify_results(execution_result, goal)
            
            # Step 8: Respond
            self.current_state = AgentState.RESPONDING
            response = self._create_response(understanding, execution_result, verification, context)
            
            # Update memories
            self._update_memories(understanding, execution_result, conversation_id)
            
            return response
            
        except Exception as e:
            logger.error(f"Agent processing error: {str(e)}")
            self.current_state = AgentState.ERROR
            return self._create_error_response(str(e))
    
    def _understand(self, message: str, conversation_id: str) -> Dict[str, Any]:
        """Step 1: Understand user message"""
        try:
            # Normalize text
            normalized_message = self.arabic_normalizer.normalize_text(message)
            
            # Detect intent
            intent_result = self.intent_classifier.classify_intent(normalized_message)
            intent = intent_result['intent']
            confidence = intent_result.get('confidence', 0.5)

            # Extract entities
            entities = self.entity_extractor.extract_entities(
                normalized_message,
                intent
            )

            # Parse compound request
            compound_request = self.arabic_normalizer.parse_compound_request(normalized_message)
            entities.update(compound_request['entities'])

            # Extract preferences
            if 'preferences' in compound_request['entities']:
                entities['preferences'] = compound_request['entities']['preferences']

            # Collect unknown query if confidence is very low
            if confidence < 0.5:
                self.data_collector.collect_unknown_query(
                    message, conversation_id, intent, entities, confidence
                )
            
            return {
                'success': True,
                'original_message': message,
                'normalized_message': normalized_message,
                'intent': intent,
                'confidence': confidence,
                'entities': entities,
                'requires_clarification': intent_result.get('requires_clarification', False)
            }
            
        except Exception as e:
            logger.error(f"Understanding error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _analyze_context(self, understanding: Dict, conversation_id: str, user: Optional[User]) -> Dict[str, Any]:
        """Step 2: Analyze conversation context"""
        try:
            # Get conversation context
            context = self.context_manager.get_context(conversation_id)
            conversation_state = context.get_complete_context()
            
            # Analyze user context if available
            user_context = {}
            if user and user.is_authenticated:
                user_context = {
                    'user_id': user.id,
                    'is_authenticated': True,
                    'preferred_governorate': getattr(user, 'preferred_governorate', None),
                    'saved_properties': [],  # Would fetch from user model
                    'previous_searches': []  # Would fetch from user model
                }
            
            # Analyze for intent switching
            previous_intent = conversation_state.get('intent')
            current_intent = understanding['intent']
            intent_switched = previous_intent and previous_intent != current_intent
            
            # Analyze for multi-intent
            multi_intent = self._detect_multi_intent(understanding['normalized_message'])
            
            return {
                'conversation_state': conversation_state,
                'user_context': user_context,
                'intent_switched': intent_switched,
                'multi_intent': multi_intent,
                'previous_entities': conversation_state.get('entities', {}),
                'missing_entities': self._identify_missing_entities(understanding['entities'], current_intent)
            }
            
        except Exception as e:
            logger.error(f"Context analysis error: {str(e)}")
            return {'error': str(e)}
    
    def _determine_goal(self, understanding: Dict, context: Dict) -> str:
        """Step 3: Determine user goal"""
        intent = understanding['intent']
        entities = understanding['entities']
        
        # Define goals based on intent and entities
        if intent == 'buy_property':
            if 'governorate' in entities and 'budget' in entities:
                return 'search_and_display_properties'
            elif 'governorate' in entities:
                return 'collect_budget_and_search'
            else:
                return 'collect_location_and_budget'
        
        elif intent == 'sell_property':
            return 'guide_to_property_selling'
        
        elif intent == 'find_job':
            if 'location' in entities:
                return 'search_jobs'
            else:
                return 'collect_job_location'
        
        elif intent == 'find_hotel':
            if 'location' in entities:
                return 'search_hotels'
            else:
                return 'collect_hotel_location'
        
        elif intent == 'join_agent':
            return 'guide_to_agent_registration'
        
        else:
            return 'provide_general_assistance'
    
    def _create_plan(self, goal: str, context: Dict, user: Optional[User] = None) -> AgentPlan:
        """Step 4: Create execution plan"""
        plan_id = str(uuid.uuid4())
        steps = []
        requires_confirmation = False
        
        # Define steps based on goal
        if goal == 'search_and_display_properties':
            steps = [
                {
                    'step_type': 'tool_call',
                    'tool_name': 'search_properties',
                    'input_data': self._prepare_search_input(context),
                    'description': 'Search for properties matching criteria'
                }
            ]
        
        elif goal == 'collect_budget_and_search':
            steps = [
                {
                    'step_type': 'question',
                    'question': 'وشكد ميزانيتك تقريباً؟',
                    'description': 'Ask for budget information'
                }
            ]
        
        elif goal == 'collect_location_and_budget':
            steps = [
                {
                    'step_type': 'question',
                    'question': 'بأي محافظة تبحث؟',
                    'description': 'Ask for location information'
                }
            ]
        
        elif goal == 'guide_to_property_selling':
            steps = [
                {
                    'step_type': 'action',
                    'action': 'redirect',
                    'url': '/add-property/',
                    'description': 'Redirect to property listing page'
                }
            ]
        
        elif goal == 'search_jobs':
            steps = [
                {
                    'step_type': 'tool_call',
                    'tool_name': 'search_jobs',
                    'input_data': self._prepare_job_search_input(context),
                    'description': 'Search for jobs'
                }
            ]
        
        elif goal == 'guide_to_agent_registration':
            steps = [
                {
                    'step_type': 'action',
                    'action': 'redirect',
                    'url': '/broker-register/',
                    'description': 'Redirect to agent registration'
                }
            ]
        
        # Check if any step requires confirmation
        for step in steps:
            if step.get('step_type') == 'tool_call':
                tool_name = step.get('tool_name')
                tool = self.tool_registry.get_tool(tool_name)
                if tool and tool.permission != ToolPermission.READ:
                    requires_confirmation = True
        
        return AgentPlan(
            plan_id=plan_id,
            goal=goal,
            steps=steps,
            estimated_duration=len(steps) * 2.0,  # Estimate 2 seconds per step
            requires_confirmation=requires_confirmation
        )
    
    def _execute_plan(self, plan: AgentPlan, user: Optional[User] = None) -> Dict[str, Any]:
        """Step 6: Execute the plan"""
        results = []
        errors = []
        
        for i, step in enumerate(plan.steps):
            if i >= self.max_execution_steps:
                errors.append("Maximum execution steps reached")
                break
            
            step_start = datetime.now()
            step_id = str(uuid.uuid4())
            
            try:
                if step['step_type'] == 'tool_call':
                    result = self._execute_tool_step(step, user)
                    results.append(result)
                    
                    if not result['success']:
                        errors.append(f"Tool {step['tool_name']} failed: {result.get('error')}")
                        break
                
                elif step['step_type'] == 'question':
                    # Question steps don't execute, they return questions
                    results.append({
                        'step_type': 'question',
                        'question': step['question'],
                        'success': True
                    })
                
                elif step['step_type'] == 'action':
                    # Action steps return redirect information
                    results.append({
                        'step_type': 'action',
                        'action': step['action'],
                        'url': step.get('url'),
                        'success': True
                    })
                
                step_duration = (datetime.now() - step_start).total_seconds() * 1000
                
                # Record execution step
                agent_step = AgentStep(
                    step_id=step_id,
                    step_type=step['step_type'],
                    tool_name=step.get('tool_name'),
                    input_data=step.get('input_data'),
                    result=result if step['step_type'] == 'tool_call' else None,
                    timestamp=step_start,
                    duration_ms=step_duration
                )
                self.execution_history.append(agent_step)
                
            except Exception as e:
                logger.error(f"Step execution error: {str(e)}")
                errors.append(str(e))
                break
        
        return {
            'success': len(errors) == 0,
            'results': results,
            'errors': errors,
            'steps_executed': len(results)
        }
    
    def _execute_tool_step(self, step: Dict, user: Optional[User] = None) -> Dict[str, Any]:
        """Execute a single tool step"""
        tool_name = step['tool_name']
        input_data = step['input_data']
        
        # Check permission
        if not self.tool_registry.check_permission(tool_name, user):
            return {
                'success': False,
                'error': f'Permission denied for tool: {tool_name}'
            }
        
        # Get tool
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return {
                'success': False,
                'error': f'Tool not found: {tool_name}'
            }
        
        # Execute tool with retry
        for attempt in range(self.retry_attempts):
            try:
                result = tool.execute(input_data, user)
                
                if result.success:
                    return {
                        'success': True,
                        'tool_name': tool_name,
                        'data': result.data,
                        'requires_confirmation': result.requires_confirmation,
                        'confirmation_data': result.confirmation_data
                    }
                else:
                    if attempt == self.retry_attempts - 1:
                        return {
                            'success': False,
                            'tool_name': tool_name,
                            'error': result.error
                        }
            
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    return {
                        'success': False,
                        'tool_name': tool_name,
                        'error': str(e)
    }
    
    def _verify_results(self, execution_result: Dict, goal: str) -> Dict[str, Any]:
        """Step 7: Verify execution results"""
        verification = {
            'success': True,
            'checks': [],
            'warnings': []
        }
        
        if not execution_result['success']:
            verification['success'] = False
            verification['checks'].append('Execution failed')
            return verification
        
        for result in execution_result['results']:
            if result.get('step_type') == 'tool_call':
                data = result.get('data', {})
                
                # Verify data quality
                if 'results' in data:
                    result_count = len(data['results'])
                    if result_count == 0:
                        verification['warnings'].append('No results found')
                    elif result_count > 50:
                        verification['warnings'].append('Large result set, may need refinement')
                    else:
                        verification['checks'].append(f'Found {result_count} results')
                
                # Verify data structure
                if 'property' in data:
                    verification['checks'].append('Property data retrieved successfully')
        
        return verification
    
    def _create_response(self, understanding: Dict, execution_result: Dict, 
                        verification: Dict, context: Dict) -> Dict[str, Any]:
        """Step 8: Create natural language response"""
        intent = understanding['intent']
        confidence = understanding['confidence']
        
        # Handle clarification needed
        if understanding.get('requires_clarification'):
            return {
                'success': True,
                'response': self._generate_clarification_response(intent, confidence),
                'action': 'clarify_intent',
                'requires_clarification': True
            }
        
        # Handle question steps
        for result in execution_result['results']:
            if result.get('step_type') == 'question':
                return {
                    'success': True,
                    'response': result['question'],
                    'action': 'ask_question',
                    'intent': intent
                }
        
        # Handle action steps
        for result in execution_result['results']:
            if result.get('step_type') == 'action':
                return {
                    'success': True,
                    'response': self._generate_action_response(result),
                    'action': result['action'],
                    'url': result.get('url'),
                    'intent': intent
                }
        
        # Handle tool results
        for result in execution_result['results']:
            if result.get('step_type') == 'tool_call':
                if result.get('requires_confirmation'):
                    return self._create_confirmation_response_from_result(result, context)
                
                if result['success']:
                    return self._generate_tool_response(result, intent, verification)
                else:
                    return self._create_error_response(result.get('error', 'Unknown error'))
        
        # Default response
        return {
            'success': True,
            'response': 'كيف يمكنني مساعدتك اليوم؟',
            'action': 'general_response'
        }
    
    def _generate_clarification_response(self, intent: str, confidence: float) -> str:
        """Generate clarification response for low confidence"""
        if intent == 'buy_property':
            return "حتى أساعدك بشكل أدق، تقصد تريد شراء عقار لو بيع عقار؟"
        elif intent == 'find_job':
            return "حتى أساعدك بشكل أدق، تقصد تبحث عن وظيفة لو تريد توظيف أشخاص؟"
        else:
            return "حتى أساعدك بشكل أدق، هل يمكنك توضيح طلبك أكثر؟"
    
    def _generate_action_response(self, result: Dict) -> str:
        """Generate response for action steps"""
        action = result.get('action')
        if action == 'redirect':
            return "جاري تحويلك إلى الصفحة المناسبة..."
        return "جاري تنفيذ طلبك..."
    
    def _generate_tool_response(self, result: Dict, intent: str, verification: Dict) -> Dict[str, Any]:
        """Generate response for tool results"""
        data = result.get('data', {})
        
        if 'results' in data:
            results = data['results']
            count = len(results)
            
            if count == 0:
                return {
                    'success': True,
                    'response': self._generate_no_results_response(intent),
                    'action': 'no_results',
                    'suggestions': self._generate_suggestions(intent)
                }
            
            # Generate natural response
            response = self._generate_results_response(count, intent, verification)
            
            return {
                'success': True,
                'response': response,
                'action': 'display_results',
                'results': results,
                'verification': verification
            }
        
        elif 'property' in data:
            return {
                'success': True,
                'response': 'تفاصيل العقار:',
                'action': 'display_property',
                'property': data['property']
            }
        
        return {
            'success': True,
            'response': 'تم تنفيذ العملية بنجاح',
            'action': 'success'
        }
    
    def _generate_results_response(self, count: int, intent: str, verification: Dict) -> str:
        """Generate natural response for results"""
        responses = {
            'buy_property': [
                f"حلو، لكيت {count} عقار مطابق لطلبك 👍",
                f"تمام، عندك {count} نتيجة من العقارات",
                f"حلو، وجدت {count} عقار تناسب طلبك"
            ],
            'find_job': [
                f"حلو، لكيت {count} وظيفة مطابقة لطلبك",
                f"تمام، عندك {count} فرصة عمل"
            ],
            'find_hotel': [
                f"حلو، لكيت {count} فندق مطابق لطلبك",
                f"تمام، عندك {count} فندق للاختيار"
            ]
        }
        
        import random
        base_response = random.choice(responses.get(intent, responses['buy_property']))
        
        # Add warnings if any
        if verification.get('warnings'):
            warnings = verification['warnings']
            if 'Large result set' in str(warnings):
                base_response += ". عدد النتائج كبير، تريد أضيق البحث؟"
        
        return base_response + ". شو رايك تنك تشوف النتائج؟"
    
    def _generate_no_results_response(self, intent: str) -> str:
        """Generate response when no results found"""
        responses = {
            'buy_property': "ما زين، ما لقيت نتائج مطابقة لطلبك حالياً",
            'find_job': "ما زين، ما لقيت وظائف مطابقة لطلبك حالياً",
            'find_hotel': "ما زين، ما لقيت فنادق مطابقة لطلبك حالياً"
        }
        
        base = responses.get(intent, "ما زين، ما لقيت نتائج")
        
        return f"{base}. تريد أوسع نطاق البحث أو تغير بعض المعايير؟"
    
    def _generate_suggestions(self, intent: str) -> List[str]:
        """Generate suggestions for no results case"""
        if intent == 'buy_property':
            return [
                "رفع الميزانية",
                "توسيع المنطقة",
                "تغيير نوع العقار",
                "بحث من جديد"
            ]
        return []
    
    def _create_confirmation_response(self, plan: AgentPlan, context: Dict) -> Dict[str, Any]:
        """Create confirmation response for operations requiring confirmation"""
        confirmation_data = {
            'action': plan.goal,
            'plan_id': plan.plan_id,
            'steps': plan.steps
        }
        
        message = self._generate_confirmation_message(plan)
        
        return {
            'success': True,
            'response': message,
            'action': 'request_confirmation',
            'requires_confirmation': True,
            'confirmation_data': confirmation_data
        }
    
    def _create_confirmation_response_from_result(self, result: Dict, context: Dict) -> Dict[str, Any]:
        """Create confirmation response from tool result"""
        confirmation_data = result.get('confirmation_data', {})
        
        message = self._generate_confirmation_message_from_data(confirmation_data)
        
        return {
            'success': True,
            'response': message,
            'action': 'request_confirmation',
            'requires_confirmation': True,
            'confirmation_data': confirmation_data
        }
    
    def _generate_confirmation_message(self, plan: AgentPlan) -> str:
        """Generate confirmation message"""
        goal = plan.goal
        
        if goal == 'create_property_listing':
            return "أنا جاهز لنشر العقار بالبيانات الليدك. تريد أن أكمل النشر؟"
        
        elif goal == 'contact_agent':
            return "أنا جاهز لإرسال رسالتك للدلال. تريد الإرسال؟"
        
        return "تريد تأكيد هذه العملية؟"
    
    def _generate_confirmation_message_from_data(self, data: Dict) -> str:
        """Generate confirmation message from confirmation data"""
        action = data.get('action')
        
        if action == 'save_property':
            return f"تريد حفظ العقار '{data.get('property_title')}' في المفضلة؟"
        
        elif action == 'contact_agent':
            return f"تريد إرسال رسالة للدلال '{data.get('agent_name')}'؟"
        
        elif action == 'create_property':
            details = []
            for key in ['title', 'property_type', 'governorate', 'district', 'area', 'price']:
                if key in data:
                    details.append(f"{key}: {data[key]}")
            
            return f"تفاصيل العقار:\n" + "\n".join(details) + "\n\nتريد نشر هذه البيانات؟"
        
        return "تريد تأكيد هذه العملية؟"
    
    def _create_error_response(self, error: str) -> Dict[str, Any]:
        """Create error response"""
        logger.error(f"Agent error: {error}")
        
        return {
            'success': False,
            'response': 'صار عندي خلل مؤقت 😕 حاول مرة ثانية.',
            'action': 'error',
            'error': error  # For debugging, not shown to user
        }
    
    def _prepare_search_input(self, context: Dict) -> Dict[str, Any]:
        """Prepare input data for property search"""
        conversation_state = context.get('conversation_state', {})
        entities = conversation_state.get('entities', {})
        
        input_data = {}
        
        if 'property_type' in entities:
            input_data['property_type'] = entities['property_type']
        if 'governorate' in entities:
            input_data['governorate'] = entities['governorate']
        if 'district' in entities:
            input_data['district'] = entities['district']
        if 'budget' in entities:
            input_data['max_price'] = entities['budget']
        if 'area' in entities:
            input_data['min_area'] = entities['area']
        if 'rooms' in entities:
            input_data['min_rooms'] = entities['rooms']
        
        input_data['limit'] = 10
        
        return input_data
    
    def _prepare_job_search_input(self, context: Dict) -> Dict[str, Any]:
        """Prepare input data for job search"""
        conversation_state = context.get('conversation_state', {})
        entities = conversation_state.get('entities', {})
        
        input_data = {}
        
        if 'location' in entities:
            input_data['location'] = entities['location']
        if 'job_type' in entities:
            input_data['job_type'] = entities['job_type']
        if 'salary' in entities:
            input_data['min_salary'] = entities['salary']
        
        input_data['limit'] = 10
        
        return input_data
    
    def _detect_multi_intent(self, message: str) -> bool:
        """Detect if message contains multiple intents"""
        multi_intent_indicators = [
            'وأيضاً',
            'بالإضافة إلى',
            'كذلك',
            'و',
            'وماذا عن'
        ]
        
        return any(indicator in message for indicator in multi_intent_indicators)
    
    def _identify_missing_entities(self, entities: Dict, intent: str) -> List[str]:
        """Identify missing required entities for intent"""
        required_entities = {
            'buy_property': ['property_type', 'governorate', 'budget'],
            'find_job': ['job_type', 'location'],
            'find_hotel': ['location']
        }
        
        required = required_entities.get(intent, [])
        missing = [entity for entity in required if entity not in entities or not entities[entity]]
        
        return missing
    
    def _update_memories(self, understanding: Dict, execution_result: Dict, conversation_id: str):
        """Update agent memories"""
        # Update short-term memory
        self.short_term_memory.update({
            'last_intent': understanding['intent'],
            'last_entities': understanding['entities'],
            'last_success': execution_result['success']
        })
        
        # Update session memory
        self.session_memory[conversation_id] = {
            'intent_history': self.session_memory.get(conversation_id, {}).get('intent_history', []) + [understanding['intent']],
            'entities': understanding['entities'],
            'last_activity': datetime.now().isoformat()
        }
    
    def handle_confirmation(self, conversation_id: str, confirmed: bool, user: Optional[User] = None) -> Dict[str, Any]:
        """Handle user confirmation response"""
        if confirmed and self.current_plan:
            # Execute the plan
            execution_result = self._execute_plan(self.current_plan, user)
            
            if execution_result['success']:
                verification = self._verify_results(execution_result, self.current_plan.goal)
                return self._create_response(
                    {'intent': self.current_plan.goal, 'confidence': 1.0},
                    execution_result,
                    verification,
                    {}
                )
            else:
                return self._create_error_response(execution_result.get('error', 'Confirmation execution failed'))
        else:
            return {
                'success': True,
                'response': 'تم إلغاء العملية.',
                'action': 'cancelled'
            }
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get agent execution statistics"""
        total_steps = len(self.execution_history)
        successful_steps = sum(1 for step in self.execution_history if step.result and step.result.success)
        
        return {
            'total_executions': total_steps,
            'successful_executions': successful_steps,
            'success_rate': successful_steps / total_steps if total_steps > 0 else 0,
            'current_state': self.current_state.value,
            'tools_used': self._get_tool_usage_stats()
        }
    
    def _get_tool_usage_stats(self) -> Dict[str, int]:
        """Get tool usage statistics"""
        tool_stats = {}
        
        for step in self.execution_history:
            if step.tool_name:
                tool_stats[step.tool_name] = tool_stats.get(step.tool_name, 0) + 1
        
        return tool_stats


# Global AI Agent instance
ai_agent = AIAgent()