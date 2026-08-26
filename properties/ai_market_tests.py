"""
Market Intelligence Tests
Tests for buyer-seller matching, analytics, and market intelligence
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from properties.ai_market_intelligence import (
    MarketIntelligenceSystem, BuyerProfile, MatchScore,
    BuyerIntentType, PropertyStatus
)
from properties.ai_agent_matching import (
    AgentMatchingSystem, AgentProfile, AgentMatchScore,
    AgentSpecialization, AgentVerificationStatus
)
from properties.ai_safe_analytics import (
    SafeAnalyticsQueryLayer, AnalyticsQuery, QueryType, MetricType
)
from properties.ai_property_lifecycle import (
    PropertyLifecycleManager, PropertyStatus
)
from properties.ai_intent_classifier import (
    IntentClassifier, IntentCategory
)
from properties.ai_progressive_profiling import (
    ProgressiveProfilingSystem, ProfilingStage
)


def test_buyer_property_match():
    """Test buyer-property matching"""
    market_system = MarketIntelligenceSystem()
    
    # Create buyer profile
    buyer_profile = BuyerProfile(
        buyer_id=1,
        intent_type=BuyerIntentType.FAMILY_HOME,
        budget_max=200_000_000,
        preferred_governorate="البصرة",
        property_type_preference="بيت",
        min_rooms=4
    )
    
    # Create property data
    property_data = {
        'id': 1,
        'governorate': 'البصرة',
        'property_type': 'بيت',
        'price': 190_000_000,
        'rooms': 4,
        'area': 200,
        'status': 'active'
    }
    
    # Calculate match
    match_score = market_system.calculate_buyer_property_match(buyer_profile, property_data)
    
    assert match_score.overall_score > 0.5
    assert len(match_score.reasons) > 0
    assert match_score.overall_score <= 1.0
    
    print(f"[OK] Buyer-Property Match Test: Score = {match_score.overall_score}")
    print(f"  Reasons: {match_score.reasons}")


def test_budget_over_property():
    """Test property over budget"""
    market_system = MarketIntelligenceSystem()
    
    buyer_profile = BuyerProfile(
        buyer_id=1,
        budget_max=150_000_000,
        preferred_governorate="البصرة"
    )
    
    property_data = {
        'id': 1,
        'governorate': 'البصرة',
        'price': 200_000_000,
        'status': 'active'
    }
    
    match_score = market_system.calculate_buyer_property_match(buyer_profile, property_data)
    
    assert match_score.overall_score < 0.8  # Should be lower due to budget
    assert len(match_score.warnings) > 0  # Should have warning
    
    print(f"[OK] Budget Over Test: Score = {match_score.overall_score}")
    print(f"  Warnings: {match_score.warnings}")


def test_agent_matching():
    """Test agent matching for seller"""
    agent_system = AgentMatchingSystem()
    
    # Register agent
    agent_profile = AgentProfile(
        agent_id=1,
        name="أحمد الدلال",
        verification_status=AgentVerificationStatus.VERIFIED,
        specializations=[AgentSpecialization.RESIDENTIAL],
        governorate="البصرة",
        districts=["العشار", "الجزائر"],
        active_listings_count=35,
        total_sales=120,
        average_sale_time_days=45,
        response_rate=0.9,
        rating=4.5
    )
    
    agent_system.register_agent(agent_profile)
    
    # Match for seller
    seller_requirements = {
        'governorate': 'البصرة',
        'property_type': 'بيت',
        'intent': 'best_price'
    }
    
    matches = agent_system.match_agent_for_seller(seller_requirements)
    
    assert len(matches) > 0
    assert matches[0].overall_score > 0.5
    assert len(matches[0].reasons) > 0
    
    print(f"[OK] Agent Matching Test: Found {len(matches)} matches")
    print(f"  Top agent: {matches[0].agent.name} (Score: {matches[0].overall_score})")
    print(f"  Reasons: {matches[0].reasons}")


def test_safe_analytics_query():
    """Test safe analytics query layer"""
    analytics_layer = SafeAnalyticsQueryLayer()
    
    # Create query
    query = analytics_layer.create_query(
        entity='property',
        metric=MetricType.PRICE,
        query_type=QueryType.MEDIAN,
        filters={'governorate': 'البصرة', 'property_type': 'بيت'},
        user_id=1
    )
    
    assert query.entity == 'property'
    assert query.metric == MetricType.PRICE
    assert query.query_type == QueryType.MEDIAN
    
    # Execute query (without database function, will return placeholder)
    result = analytics_layer.execute_query(query)
    
    assert result is not None
    assert result.query_id == query.query_id
    
    print(f"[OK] Safe Analytics Query Test: {result.success}")
    print(f"  Explanation: {analytics_layer.explain_query(query)}")


def test_property_lifecycle():
    """Test property lifecycle management"""
    lifecycle_manager = PropertyLifecycleManager()
    
    # Set property status through proper transition
    success1 = lifecycle_manager.set_property_status(
        property_id=1,
        new_status=PropertyStatus.PENDING_REVIEW,
        user_id=1
    )
    
    success2 = lifecycle_manager.set_property_status(
        property_id=1,
        new_status=PropertyStatus.PUBLISHED,
        user_id=1
    )
    
    success3 = lifecycle_manager.set_property_status(
        property_id=1,
        new_status=PropertyStatus.ACTIVE,
        user_id=1
    )
    
    # At least one transition should succeed
    assert success1 == True or success2 == True or success3 == True
    
    # Get status
    status = lifecycle_manager.get_property_status(1)
    
    # Get available properties
    available = lifecycle_manager.get_available_properties()
    
    print(f"[OK] Property Lifecycle Test: Status = {status.value if status else 'None'}")
    print(f"  Available properties: {len(available)}")


def test_intent_classification():
    """Test intent classification"""
    intent_classifier = IntentClassifier()
    
    # Test buy intent
    classification = intent_classifier.classify_intent("أريد بيت بالبصرة بـ150 مليون")
    
    assert classification.category == IntentCategory.BUY
    assert classification.buyer_intent is not None
    assert classification.confidence > 0.5
    
    print(f"[OK] Intent Classification Test: {classification.category.value}")
    print(f"  Buyer Intent: {classification.buyer_intent.value if classification.buyer_intent else None}")
    print(f"  Extracted Params: {classification.extracted_params}")


def test_progressive_profiling():
    """Test progressive profiling"""
    profiling_system = ProgressiveProfilingSystem()
    
    # Get user profile
    profile = profiling_system.get_user_profile(1)
    
    assert profile.stage == ProfilingStage.INITIAL
    
    # Update profile
    profiling_system.update_profile(1, 'governorate', 'البصرة')
    profiling_system.update_profile(1, 'budget', 200_000_000)
    
    # Get next question
    next_question = profiling_system.get_next_question(1)
    
    assert next_question is not None
    assert next_question.stage == ProfilingStage.INITIAL
    
    print(f"[OK] Progressive Profiling Test: Stage = {profile.stage.value}")
    print(f"  Next question: {next_question.question_text}")


def test_market_area_comparison():
    """Test market area comparison"""
    market_system = MarketIntelligenceSystem()
    
    # Compare areas (without database, will return placeholder)
    comparison = market_system.compare_market_areas('العشار', 'الجزائر', 'بيت')
    
    assert comparison['area1'] == 'العشار'
    assert comparison['area2'] == 'الجزائر'
    
    print(f"[OK] Market Area Comparison Test: {comparison}")


def test_price_per_m2():
    """Test price per square meter calculation"""
    market_system = MarketIntelligenceSystem()
    
    property_data = {
        'price': 200_000_000,
        'area': 200
    }
    
    price_per_m2 = market_system.calculate_price_per_m2(property_data)
    
    assert price_per_m2 == 1_000_000  # 200M / 200 = 1M per m2
    
    print(f"[OK] Price per m2 Test: {price_per_m2:,.0f} دينار/م²")


def run_all_tests():
    """Run all market intelligence tests"""
    print("\n" + "="*60)
    print("Market Intelligence Tests")
    print("="*60 + "\n")
    
    test_buyer_property_match()
    test_budget_over_property()
    test_agent_matching()
    test_safe_analytics_query()
    test_property_lifecycle()
    test_intent_classification()
    test_progressive_profiling()
    test_market_area_comparison()
    test_price_per_m2()
    
    print("\n" + "="*60)
    print("All tests completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()