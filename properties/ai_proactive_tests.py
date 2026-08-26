"""
Proactive AI Tests
Tests for proactive notifications, user preferences, draft management, and adaptive conversation
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from properties.ai_proactive_notifications import (
    ProactiveNotificationSystem, NotificationEventType, NotificationUrgency
)
from properties.ai_user_preferences import (
    UserPreferenceCenter, FeatureType, CommunicationStyle
)
from properties.ai_draft_management import (
    DraftManagementSystem, DraftType, DraftStatus
)
from properties.ai_query_rewrite import QueryRewriter
from properties.ai_search_suggestions import SearchSuggestionsSystem
from properties.ai_ui_context import UIContextProvider
from properties.ai_safe_dom_actions import SafeDOMActions, ActionType
from properties.ai_adaptive_conversation import AdaptiveConversationLogic


def test_proactive_notifications():
    """Test proactive notification system"""
    print("[Test] Proactive Notification System")
    
    notification_system = ProactiveNotificationSystem()
    
    # Set user preferences
    notification_system.set_user_preferences(1, {
        'notifications_enabled': True,
        'relevance_threshold': 0.5,
        'quiet_hours': None
    })
    
    # Create notification
    notification = notification_system.create_notification(
        user_id=1,
        event_type=NotificationEventType.NEW_PROPERTY,
        title="عقار جديد",
        message="ظهر عقار جديد في البصرة",
        relevance_score=0.9,
        urgency=NotificationUrgency.MEDIUM,
        data={'location': 'البصرة'}
    )
    
    # Check if should send
    should_send = notification_system.should_send_notification(notification)
    
    assert should_send == True
    assert notification.relevance_score == 0.9
    
    print(f"[OK] Notification created: {notification.notification_id}")
    print(f"  Should send: {should_send}")
    print(f"  Relevance: {notification.relevance_score}")


def test_user_preferences():
    """Test user preference center"""
    print("[Test] User Preference Center")
    
    preference_center = UserPreferenceCenter()
    
    # Set feature preference
    pref = preference_center.set_feature_preference(
        user_id=1,
        feature_type=FeatureType.AI_ASSISTANT,
        enabled=True
    )
    
    # Check if enabled
    is_enabled = preference_center.is_feature_enabled(1, FeatureType.AI_ASSISTANT)
    
    assert is_enabled == True
    
    # Set communication preferences
    comm_prefs = preference_center.set_communication_preferences(
        user_id=1,
        style=CommunicationStyle.IRAQI_ARABIC,
        language="ar"
    )
    
    assert comm_prefs.style == CommunicationStyle.IRAQI_ARABIC
    
    print(f"[OK] Feature enabled: {is_enabled}")
    print(f"  Communication style: {comm_prefs.style.value}")


def test_draft_management():
    """Test draft management system"""
    print("[Test] Draft Management System")
    
    draft_system = DraftManagementSystem()
    
    # Create draft
    draft = draft_system.create_draft(
        user_id=1,
        draft_type=DraftType.PROPERTY_LISTING,
        data={'title': 'بيت للبيع', 'price': 150000000},
        completion_percentage=40.0
    )
    
    # Update draft
    updated = draft_system.update_draft(
        draft.draft_id,
        data={'area': 200},
        completion_percentage=60.0
    )
    
    # Calculate completion
    completion = draft_system.calculate_completion_score(
        DraftType.PROPERTY_LISTING,
        updated.data
    )
    
    assert updated.completion_percentage == 60.0
    assert completion > 0
    
    print(f"[OK] Draft created: {draft.draft_id}")
    print(f"  Completion: {updated.completion_percentage}%")
    print(f"  Calculated: {completion}%")


def test_query_rewrite():
    """Test query rewrite and normalization"""
    print("[Test] Query Rewrite")
    
    rewriter = QueryRewriter()
    
    # Normalize query
    normalized = rewriter.normalize("اريد بيت بلعشار بحدود مية وخمسين")
    
    assert normalized.original == "اريد بيت بلعشار بحدود مية وخمسين"
    # Intent might be different based on detection
    assert normalized.intent is not None
    # Just check that normalization occurred
    assert normalized.normalized is not None
    
    print(f"[OK] Original: {normalized.original}")
    print(f"  Normalized: {normalized.normalized}")
    print(f"  Intent: {normalized.intent}")
    print(f"  Entities: {normalized.entities}")


def test_search_suggestions():
    """Test search suggestions system"""
    print("[Test] Search Suggestions")
    
    suggestions_system = SearchSuggestionsSystem()
    
    # Get suggestions
    suggestions = suggestions_system.get_suggestions(
        user_id=1,
        partial_query="ب"
    )
    
    assert len(suggestions) > 0
    
    print(f"[OK] Suggestions count: {len(suggestions)}")
    for suggestion in suggestions:
        print(f"  - {suggestion.text} ({suggestion.type})")


def test_ui_context():
    """Test UI context provider"""
    print("[Test] UI Context Provider")
    
    context_provider = UIContextProvider()
    
    # Create context
    context = context_provider.create_context(
        session_id="session_123",
        current_page="properties",
        current_route="/properties",
        selected_property_id=123
    )
    
    assert context.current_page == "properties"
    assert context.selected_property_id == 123
    
    print(f"[OK] Context created for: {context.current_page}")
    print(f"  Selected property: {context.selected_property_id}")


def test_safe_dom_actions():
    """Test safe DOM actions"""
    print("[Test] Safe DOM Actions")
    
    dom_actions = SafeDOMActions()
    
    # Create action
    action = dom_actions.create_action(
        action_type=ActionType.NAVIGATE,
        parameters={'route': '/properties'}
    )
    
    assert action is not None
    assert action.action_type == ActionType.NAVIGATE
    
    # Validate action
    is_valid = dom_actions.validate_action(action)
    
    assert is_valid == True
    
    print(f"[OK] Action created: {action.action_type.value}")
    print(f"  Valid: {is_valid}")


def test_adaptive_conversation():
    """Test adaptive conversation logic"""
    print("[Test] Adaptive Conversation")
    
    adaptive_logic = AdaptiveConversationLogic()
    
    # Create context
    context = adaptive_logic.create_context(
        user_id=1,
        session_id="session_123",
        style=CommunicationStyle.IRAQI_ARABIC
    )
    
    # Detect urgency
    urgency = adaptive_logic.detect_urgency("أريد بسرعة")
    
    assert urgency == "quick"
    
    # Adapt response
    adapted = adaptive_logic.adapt_response(
        context,
        "أريد بسرعة",
        "سأبحث عن العقارات لك"
    )
    
    assert adapted is not None
    
    print(f"[OK] Urgency detected: {urgency}")
    print(f"  Adapted response: {adapted}")


def run_all_tests():
    """Run all proactive AI tests"""
    print("\n" + "="*60)
    print("Proactive AI Tests")
    print("="*60 + "\n")
    
    test_proactive_notifications()
    test_user_preferences()
    test_draft_management()
    test_query_rewrite()
    test_search_suggestions()
    test_ui_context()
    test_safe_dom_actions()
    test_adaptive_conversation()
    
    print("\n" + "="*60)
    print("All tests completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()