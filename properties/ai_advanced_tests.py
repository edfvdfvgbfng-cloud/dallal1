"""
Advanced AI Phase 8 - Complex Scenario Tests
Tests for advanced reasoning, context management, and multi-step tasks
"""

import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from properties.ai_goal_understanding import user_goal_understanding_system, GoalType
from properties.ai_constraint_engine import constraint_engine, ConstraintType
from properties.ai_smart_clarification import smart_clarification_system
from properties.ai_conversation_planner import conversation_planner
from properties.ai_task_manager import task_manager, TaskStep, TaskPriority
from properties.ai_context_resolver import context_resolver
from properties.ai_semantic_memory import semantic_memory, MemoryType, MemoryImportance
from properties.ai_smart_recommendations import smart_recommendation_engine
from properties.ai_query_relaxation import query_relaxation_engine
from properties.ai_evidence_response import evidence_based_response_system
from properties.ai_ui_actions import ui_action_manager, UIActionType
from properties.ai_advanced_orchestrator import advanced_ai_orchestrator

logger = logging.getLogger(__name__)


class TestScenario1:
    """Scenario 1: Progressive property search with context preservation"""
    
    def test_scenario_1_full_flow(self):
        """
        Test: "أريد بيت بالبصرة أقل من 200 مليون للعائلة."
        Then: "قريب من المدارس."
        Then: "أريد 4 غرف."
        Then: "خليها العشار."
        Then: "وريني الأرخص."
        Then: "قارن الأول والثالث."
        Then: "احفظ الأول."
        """
        conversation_id = "test_scenario_1"
        user_id = 1
        
        # Step 1: Initial request
        response1 = advanced_ai_orchestrator.process_advanced_query(
            "أريد بيت بالبصرة أقل من 200 مليون للعائلة",
            conversation_id,
            user_id
        )
        
        assert response1['confidence'] > 0.7
        assert 'goal' in response1.get('metadata', {})
        
        # Step 2: Add preference
        response2 = advanced_ai_orchestrator.process_advanced_query(
            "قريب من المدارس",
            conversation_id,
            user_id
        )
        
        # Context should be preserved
        context = advanced_ai_orchestrator.get_conversation_state(conversation_id)
        assert context is not None
        assert 'user_goal' in context
        
        # Step 3: Add room requirement
        response3 = advanced_ai_orchestrator.process_advanced_query(
            "أريد 4 غرف",
            conversation_id,
            user_id
        )
        
        # Step 4: Specify district
        response4 = advanced_ai_orchestrator.process_advanced_query(
            "خليها العشار",
            conversation_id,
            user_id
        )
        
        # Step 5: Sort by price
        response5 = advanced_ai_orchestrator.process_advanced_query(
            "وريني الأرخص",
            conversation_id,
            user_id
        )
        
        # Step 6: Compare first and third
        response6 = advanced_ai_orchestrator.process_advanced_query(
            "قارن الأول والثالث",
            conversation_id,
            user_id
        )
        
        assert response6['type'] == 'comparison' or 'comparison' in response6
        
        # Step 7: Save first
        response7 = advanced_ai_orchestrator.process_advanced_query(
            "احفظ الأول",
            conversation_id,
            user_id
        )
        
        # All context should be preserved throughout
        final_context = advanced_ai_orchestrator.get_conversation_state(conversation_id)
        assert final_context is not None
        assert len(final_context.get('messages', [])) >= 7
        
        logger.info("Scenario 1 test passed: Context preserved across 7 turns")


class TestScenario2:
    """Scenario 2: Task change without data mixing"""
    
    def test_scenario_2_task_change(self):
        """
        Test: "أريد بيت بالبصرة."
        Then: "لا، خلها شقة."
        Then: "لا خلاص، أريد وظيفة."
        """
        conversation_id = "test_scenario_2"
        user_id = 2
        
        # Step 1: Property search
        response1 = advanced_ai_orchestrator.process_advanced_query(
            "أريد بيت بالبصرة",
            conversation_id,
            user_id
        )
        
        assert response1.get('type') != 'error'
        
        # Step 2: Change to apartment
        response2 = advanced_ai_orchestrator.process_advanced_query(
            "لا، خلها شقة",
            conversation_id,
            user_id
        )
        
        # Step 3: Change to job search
        response3 = advanced_ai_orchestrator.process_advanced_query(
            "لا خلاص، أريد وظيفة",
            conversation_id,
            user_id
        )
        
        # Check that context switched correctly
        context = advanced_ai_orchestrator.get_conversation_state(conversation_id)
        assert context is not None
        
        # Final goal should be job search
        user_goal = context.get('user_goal', {})
        assert user_goal.get('goal') == 'find_job' or user_goal.get('intent') == 'find_job'
        
        # Property context should not interfere with job context
        assert 'property_type' not in context.get('entities', {}) or \
               context['entities'].get('property_type') is None or \
               'job_type' in context.get('entities', {})
        
        logger.info("Scenario 2 test passed: Task change without data mixing")


class TestScenario3:
    """Scenario 3: Ambiguous request requires clarification"""
    
    def test_scenario_3_ambiguous_request(self):
        """
        Test: "أريد أفضل عقار."
        Should require clarification before responding.
        """
        conversation_id = "test_scenario_3"
        user_id = 3
        
        response = advanced_ai_orchestrator.process_advanced_query(
            "أريد أفضل عقار",
            conversation_id,
            user_id
        )
        
        # Should either ask for clarification or have low confidence
        assert response.get('type') == 'clarification' or response.get('confidence') < 0.7
        
        if response.get('type') == 'clarification':
            assert 'questions' in response
            assert len(response['questions']) > 0
        
        logger.info("Scenario 3 test passed: Ambiguous request handled correctly")


class TestScenario4:
    """Scenario 4: Unspecified service requires clarification"""
    
    def test_scenario_4_unspecified_service(self):
        """
        Test: "أريد شيء بـ150 مليون."
        Should clarify what service is requested.
        """
        conversation_id = "test_scenario_4"
        user_id = 4
        
        response = advanced_ai_orchestrator.process_advanced_query(
            "أريد شيء بـ150 مليون",
            conversation_id,
            user_id
        )
        
        # Should ask for clarification about what is requested
        assert response.get('type') == 'clarification' or response.get('confidence') < 0.6
        
        logger.info("Scenario 4 test passed: Unspecified service requires clarification")


class TestScenario5:
    """Scenario 5: Fallback preference handling"""
    
    def test_scenario_5_fallback_preference(self):
        """
        Test: "أريد بيت بالبصرة، بس إذا ماكو خلي شقة."
        Should understand primary preference and fallback.
        """
        conversation_id = "test_scenario_5"
        user_id = 5
        
        response = advanced_ai_orchestrator.process_advanced_query(
            "أريد بيت بالبصرة، بس إذا ماكو خلي شقة",
            conversation_id,
            user_id
        )
        
        assert response.get('type') != 'error'
        
        # Check that both house and apartment are understood
        context = advanced_ai_orchestrator.get_conversation_state(conversation_id)
        user_goal = context.get('user_goal', {})
        
        entities = user_goal.get('entities', {})
        # Should have primary and fallback
        assert 'property_type' in entities or 'alternative_types' in entities
        
        logger.info("Scenario 5 test passed: Fallback preference handled correctly")


class TestGoalUnderstanding:
    """Test goal understanding system"""
    
    def test_comprehensive_goal_extraction(self):
        """Test extraction of comprehensive goal information"""
        user_input = "أريد بيت بالبصرة للعائلة، عندي 200 مليون وأريد مكان هادئ قريب من المدارس"
        
        user_goal = user_goal_understanding_system.understand_goal(user_input)
        
        assert user_goal.goal == GoalType.FIND_PROPERTY
        assert user_goal.entities.get('governorate') == 'البصرة'
        assert user_goal.purpose == 'family'
        assert 'quiet' in user_goal.preferences or 'near_schools' in user_goal.preferences
        assert user_goal.confidence > 0.5
        
        logger.info("Goal understanding test passed")


class TestConstraintEngine:
    """Test constraint engine"""
    
    def test_hard_vs_soft_constraints(self):
        """Test hard vs soft constraint application"""
        from properties.ai_goal_understanding import UserGoal, GoalType
        
        user_goal = UserGoal()
        user_goal.goal = GoalType.FIND_PROPERTY
        user_goal.entities = {
            'governorate': 'البصرة',
            'price': {'max': 200000000}
        }
        user_goal.constraints = {
            ConstraintType.MUST_HAVE: [
                {'type': 'location', 'value': 'البصرة'},
                {'type': 'budget', 'value': {'max': 200000000}}
            ],
            ConstraintType.PREFERRED: [
                {'type': 'district', 'value': 'العشار'}
            ],
            ConstraintType.OPTIONAL: [
                {'type': 'amenity', 'value': 'حديقة'}
            ]
        }
        
        constraint_set = constraint_engine.build_constraint_set_from_goal(user_goal)
        
        # Test query parameters
        query_params = constraint_set.apply_constraints_to_query({})
        assert 'governorate' in query_params
        assert query_params['governorate'] == 'البصرة'
        
        # Test filtering
        test_items = [
            {'governorate': 'البصرة', 'price': 150000000},
            {'governorate': 'بغداد', 'price': 150000000},
            {'governorate': 'البصرة', 'price': 250000000}
        ]
        
        filtered = constraint_set.filter_results(test_items)
        assert len(filtered) == 1  # Only first item matches hard constraints
        
        logger.info("Constraint engine test passed")


class TestContextResolver:
    """Test context resolver"""
    
    def test_reference_resolution(self):
        """Test reference resolution"""
        context = {
            'search_results': [
                {'id': 1, 'title': 'عقار 1'},
                {'id': 2, 'title': 'عقار 2'},
                {'id': 3, 'title': 'عقار 3'}
            ],
            'current_item_index': 0
        }
        
        # Test "الأول"
        ref1 = context_resolver.resolve_reference("الأول", context)
        assert ref1 is not None
        assert ref1.resolved_value is not None
        
        # Test "السابق"
        context['current_item_index'] = 1
        ref2 = context_resolver.resolve_reference("السابق", context)
        assert ref2 is not None
        
        logger.info("Context resolver test passed")


class TestSemanticMemory:
    """Test semantic memory system"""
    
    def test_memory_storage_and_retrieval(self):
        """Test memory storage and retrieval"""
        user_id = 1
        
        # Store preference
        semantic_memory.update_user_preference(user_id, 'preferred_governorate', 'البصرة')
        
        # Retrieve preference
        preferences = semantic_memory.get_user_preferences(user_id)
        assert preferences.get('preferred_governorate') == 'البصرة'
        
        # Store session memory
        semantic_memory.store_memory(
            content={'test': 'data'},
            memory_type=MemoryType.SESSION,
            importance=MemoryImportance.MEDIUM,
            user_id=user_id
        )
        
        # Retrieve session context
        session_context = semantic_memory.get_session_context(user_id)
        assert session_context is not None
        
        logger.info("Semantic memory test passed")


class TestSmartRecommendations:
    """Test smart recommendations"""
    
    def test_diversified_recommendations(self):
        """Test diversified recommendations"""
        from properties.ai_goal_understanding import UserGoal, GoalType
        
        user_goal = UserGoal()
        user_goal.goal = GoalType.FIND_PROPERTY
        user_goal.entities = {'governorate': 'البصرة', 'price': 200000000}
        
        available_items = [
            {'id': 1, 'price': 150000000, 'area': 200, 'governorate': 'البصرة'},
            {'id': 2, 'price': 180000000, 'area': 250, 'governorate': 'البصرة'},
            {'id': 3, 'price': 120000000, 'area': 180, 'governorate': 'البصرة'},
            {'id': 4, 'price': 190000000, 'area': 300, 'governorate': 'البصرة'},
            {'id': 5, 'price': 140000000, 'area': 220, 'governorate': 'البصرة'}
        ]
        
        recommendations = smart_recommendation_engine.generate_recommendations(
            user_goal, available_items, user_id=1, count=5
        )
        
        assert len(recommendations) > 0
        assert len(recommendations) <= 5
        
        # Check for diversity
        categories = set(r.category for r in recommendations)
        assert len(categories) > 1  # Should have different categories
        
        logger.info("Smart recommendations test passed")


class TestQueryRelaxation:
    """Test query relaxation engine"""
    
    def test_empty_results_relaxation(self):
        """Test relaxation suggestions for empty results"""
        from properties.ai_goal_understanding import UserGoal, GoalType
        
        user_goal = UserGoal()
        user_goal.goal = GoalType.FIND_PROPERTY
        user_goal.entities = {'price': {'max': 100000000}, 'governorate': 'البصرة'}
        
        suggestions = query_relaxation_engine.analyze_empty_results(
            user_goal, user_goal.entities, estimated_total_count=0
        )
        
        assert len(suggestions) > 0
        
        # Test applying relaxation
        if suggestions:
            relaxed_goal = query_relaxation_engine.apply_relaxation(
                user_goal, suggestions[0], user_approved=True
            )
            assert relaxed_goal is not None
        
        logger.info("Query relaxation test passed")


class TestUIActions:
    """Test UI actions"""
    
    def test_safe_ui_actions(self):
        """Test safe UI action execution"""
        # Create navigate action
        action = ui_action_manager.create_navigate_action('/properties')
        
        assert action.action_type == UIActionType.NAVIGATE
        assert action.allowed == True
        
        # Execute action
        success, result = ui_action_manager.execute_action(action)
        assert success == True
        
        # Parse natural language command
        nav_action = ui_action_manager.parse_natural_language_command(
            "افتح العقارات", {}
        )
        assert nav_action is not None
        
        logger.info("UI actions test passed")


class TestEvidenceBasedResponse:
    """Test evidence-based response system"""
    
    def test_response_verification(self):
        """Test response verification"""
        ai_response = "هذا العقار سعره 150 مليون دينار ومساحته 200 متر"
        tool_results = {
            'search_properties': {
                'results': [
                    {'price': 150000000, 'area': 200}
                ]
            }
        }
        
        verified = evidence_based_response_system.verify_response(
            ai_response, tool_results, {}
        )
        
        assert verified is not None
        assert verified.overall_confidence > 0.5
        assert verified.confidence_level is not None
        
        logger.info("Evidence-based response test passed")


class TestMultiStepTasks:
    """Test multi-step task management"""
    
    def test_task_creation_and_execution(self):
        """Test creating and executing multi-step tasks"""
        search_params = {'governorate': 'البصرة', 'price': 200000000}
        
        task = task_manager.create_search_save_favorite_task(
            search_params=search_params,
            save_count=3,
            favorite_first=True,
            user_id=1
        )
        
        assert task is not None
        assert len(task.steps) > 0
        assert task.status.value == 'pending'
        
        # Get task summary
        summary = task_manager.get_task_summary(task.task_id)
        assert summary is not None
        
        logger.info("Multi-step task test passed")


class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_full_integration(self):
        """Test full integration of all components"""
        conversation_id = "test_integration"
        user_id = 999
        
        # Process a complex query
        response = advanced_ai_orchestrator.process_advanced_query(
            "أريد بيت بالبصرة أقل من 200 مليون للعائلة قريب من المدارس",
            conversation_id,
            user_id
        )
        
        assert response is not None
        assert 'text' in response
        assert 'confidence' in response
        
        # Check context
        context = advanced_ai_orchestrator.get_conversation_state(conversation_id)
        assert context is not None
        
        # Check user context summary
        user_summary = advanced_ai_orchestrator.get_user_context_summary(user_id)
        assert user_summary is not None
        assert 'preferences' in user_summary
        
        logger.info("Full integration test passed")


# Run tests
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Running Advanced AI Phase 8 Tests...")
    print("=" * 60)
    
    # Run all test classes
    test_classes = [
        TestScenario1,
        TestScenario2,
        TestScenario3,
        TestScenario4,
        TestScenario5,
        TestGoalUnderstanding,
        TestConstraintEngine,
        TestContextResolver,
        TestSemanticMemory,
        TestSmartRecommendations,
        TestQueryRelaxation,
        TestUIActions,
        TestEvidenceBasedResponse,
        TestMultiStepTasks,
        TestIntegration
    ]
    
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]
        
        for method_name in test_methods:
            try:
                print(f"Running {test_class.__name__}.{method_name}...")
                getattr(test_instance, method_name)()
                passed += 1
                print(f"  ✓ PASSED")
            except Exception as e:
                failed += 1
                print(f"  ✗ FAILED: {str(e)}")
    
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("All tests passed! ✓")
    else:
        print(f"{failed} test(s) failed. ✗")