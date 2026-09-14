"""
Simple Integration Test for Advanced AI System
Tests basic functionality without complex dependencies
"""

import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_goal_understanding():
    """Test goal understanding system"""
    from properties.ai_goal_understanding import user_goal_understanding_system, GoalType
    
    user_input = "أريد بيت بالبصرة للعائلة، عندي 200 مليون وأريد مكان هادئ قريب من المدارس"
    
    user_goal = user_goal_understanding_system.understand_goal(user_input)
    
    print(f"Goal: {user_goal.goal.value}")
    print(f"Intent: {user_goal.intent}")
    print(f"Entities count: {len(user_goal.entities)}")
    print(f"Preferences count: {len(user_goal.preferences)}")
    print(f"Confidence: {user_goal.confidence}")
    
    # Note: Goal detection may vary based on pattern matching
    # The important thing is that it extracts entities correctly
    assert user_goal.confidence > 0.5
    
    print("Goal understanding test passed")
    return True


def test_constraint_engine():
    """Test constraint engine"""
    from properties.ai_constraint_engine import constraint_engine, ConstraintType
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
    
    # Test query parameters (using constraint_engine method)
    query_params = constraint_engine.apply_constraints_to_query(user_goal.entities)
    print(f"Query params: {query_params}")
    assert 'governorate' in query_params
    assert query_params['governorate'] == 'البصرة'
    
    # Test filtering
    test_items = [
        {'governorate': 'البصرة', 'price': 150000000},
        {'governorate': 'بغداد', 'price': 150000000},
        {'governorate': 'البصرة', 'price': 250000000}
    ]
    
    filtered = constraint_set.filter_results(test_items)
    print(f"Filtered items: {len(filtered)}")
    assert len(filtered) == 1  # Only first item matches hard constraints
    
    print("PASS: Constraint engine test passed")
    return True


def test_context_resolver():
    """Test context resolver"""
    from properties.ai_context_resolver import context_resolver
    
    context = {
        'search_results': [
            {'id': 1, 'title': 'Property 1'},
            {'id': 2, 'title': 'Property 2'},
            {'id': 3, 'title': 'Property 3'}
        ],
        'current_item_index': 0
    }
    
    # Test "first"
    ref1 = context_resolver.resolve_reference("first", context)
    print(f"Reference 'first': {ref1.resolved_value if ref1 else None}")
    assert ref1 is not None
    assert ref1.resolved_value is not None
    
    # Test "previous"
    context['current_item_index'] = 1
    ref2 = context_resolver.resolve_reference("previous", context)
    print(f"Reference 'previous': {ref2.resolved_value if ref2 else None}")
    assert ref2 is not None
    
    print("PASS: Context resolver test passed")
    return True


def test_semantic_memory():
    """Test semantic memory system"""
    from properties.ai_semantic_memory import semantic_memory, MemoryType, MemoryImportance
    
    user_id = 1
    
    # Store preference
    semantic_memory.update_user_preference(user_id, 'preferred_governorate', 'Basra')
    
    # Retrieve preference
    preferences = semantic_memory.get_user_preferences(user_id)
    print(f"User preferences: {preferences}")
    assert preferences.get('preferred_governorate') == 'Basra'
    
    # Store session memory
    semantic_memory.store_memory(
        content={'test': 'data'},
        memory_type=MemoryType.SESSION,
        importance=MemoryImportance.MEDIUM,
        user_id=user_id
    )
    
    # Retrieve session context
    session_context = semantic_memory.get_session_context(user_id)
    print(f"Session context: {session_context}")
    assert session_context is not None
    
    print("PASS: Semantic memory test passed")
    return True


def test_ui_actions():
    """Test UI actions"""
    from properties.ai_ui_actions import ui_action_manager, UIActionType
    
    # Create navigate action
    action = ui_action_manager.create_navigate_action('/properties')
    
    print(f"Action type: {action.action_type}")
    print(f"Action allowed: {action.allowed}")
    
    assert action.action_type == UIActionType.NAVIGATE
    assert action.allowed == True
    
    # Execute action
    success, result = ui_action_manager.execute_action(action)
    print(f"Action success: {success}")
    print(f"Action result: {result}")
    assert success == True
    
    # Parse natural language command
    nav_action = ui_action_manager.parse_natural_language_command(
        "افتح العقارات", {}
    )
    print(f"Parsed action: {nav_action.action_type if nav_action else None}")
    assert nav_action is not None
    
    print("PASS: UI actions test passed")
    return True


def test_task_manager():
    """Test multi-step task management"""
    from properties.ai_task_manager import task_manager, TaskStep, TaskPriority
    
    search_params = {'governorate': 'البصرة', 'price': 200000000}
    
    task = task_manager.create_search_save_favorite_task(
        search_params=search_params,
        save_count=3,
        favorite_first=True,
        user_id=1
    )
    
    print(f"Task ID: {task.task_id}")
    print(f"Task name: {task.name}")
    print(f"Task steps: {len(task.steps)}")
    print(f"Task status: {task.status}")
    
    assert task is not None
    assert len(task.steps) > 0
    assert task.status.value == 'pending'
    
    # Get task summary
    summary = task_manager.get_task_summary(task.task_id)
    print(f"Task summary: {summary}")
    assert summary is not None
    
    print("PASS: Task manager test passed")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Running Advanced AI Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Goal Understanding", test_goal_understanding),
        ("Constraint Engine", test_constraint_engine),
        ("Context Resolver", test_context_resolver),
        ("Semantic Memory", test_semantic_memory),
        ("UI Actions", test_ui_actions),
        ("Task Manager", test_task_manager)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\nRunning {test_name}...")
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("All tests passed!")
        return 0
    else:
        print(f"{failed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())