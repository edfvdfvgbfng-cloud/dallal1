"""
Market Intelligence Orchestrator
Integrates all market intelligence components with existing AI Agent
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from .ai_market_intelligence import (
    MarketIntelligenceSystem, BuyerProfile, MatchScore, MarketStatistics,
    BuyerIntentType, PropertyStatus
)
from .ai_agent_matching import (
    AgentMatchingSystem, AgentProfile, AgentMatchScore, AgentSpecialization
)
from .ai_safe_analytics import (
    SafeAnalyticsQueryLayer, AnalyticsQuery, AnalyticsResult, QueryType, MetricType
)
from .ai_smart_notifications import (
    SmartNotificationsSystem, Notification, SavedSearch, NotificationType
)
from .ai_duplicate_anomaly import (
    DuplicateAnomalyDetector, DuplicateDetection, AnomalyDetection
)
from .ai_property_lifecycle import (
    PropertyLifecycleManager, LifecycleEvent, PropertyStatus
)
from .ai_intent_classifier import (
    IntentClassifier, IntentClassification, IntentCategory
)
from .ai_progressive_profiling import (
    ProgressiveProfilingSystem, UserProfile, ProfilingStage
)

logger = logging.getLogger(__name__)


class MarketIntelligenceOrchestrator:
    """
    Orchestrates all market intelligence components
    Integrates with existing AI Agent for unified experience
    """
    
    def __init__(self):
        # Market intelligence components
        self.market_system = MarketIntelligenceSystem()
        self.agent_system = AgentMatchingSystem()
        self.analytics_layer = SafeAnalyticsQueryLayer()
        self.notifications_system = SmartNotificationsSystem()
        self.duplicate_detector = DuplicateAnomalyDetector()
        self.lifecycle_manager = PropertyLifecycleManager()
        self.intent_classifier = IntentClassifier()
        self.profiling_system = ProgressiveProfilingSystem()
    
    def process_market_query(self,
                            user_input: str,
                            user_id: int,
                            context: Dict = None) -> Dict:
        """
        Process market-related query
        
        Args:
            user_input: User's natural language input
            user_id: User ID
            context: Conversation context
            
        Returns:
            Comprehensive response
        """
        try:
            # Classify intent
            intent = self.intent_classifier.classify_intent(user_input, context)
            
            # Route based on intent
            if intent.category == IntentCategory.ANALYZE:
                return self._handle_analytics_query(user_input, intent, user_id)
            
            elif intent.category == IntentCategory.BUY:
                return self._handle_buy_query(user_input, intent, user_id, context)
            
            elif intent.category == IntentCategory.SELL:
                return self._handle_sell_query(user_input, intent, user_id)
            
            elif intent.category == IntentCategory.COMPARE:
                return self._handle_compare_query(user_input, intent, user_id)
            
            else:
                return self._handle_general_query(user_input, intent, user_id)
                
        except Exception as e:
            logger.error(f"Error processing market query: {str(e)}")
            return {
                'error': str(e),
                'response': 'حدث خطأ أثناء معالجة طلبك.'
            }
    
    def _handle_analytics_query(self,
                               user_input: str,
                               intent: IntentClassification,
                               user_id: int) -> Dict:
        """Handle analytics/statistics queries"""
        # Extract parameters
        params = intent.extracted_params
        
        # Create safe analytics query
        governorate = params.get('governorate')
        property_type = params.get('property_type')
        
        filters = {}
        if governorate:
            filters['governorate'] = governorate
        if property_type:
            filters['property_type'] = property_type
        
        query = self.analytics_layer.create_query(
            entity='property',
            metric=MetricType.PRICE,
            query_type=QueryType.MEDIAN,
            filters=filters,
            user_id=user_id
        )
        
        # Execute query
        result = self.analytics_layer.execute_query(query)
        
        if result.success:
            median_price = result.result.get('median')
            if median_price:
                response = f"حسب البيانات المسجلة في المنصة، متوسط أسعار العقارات"
                if governorate:
                    response += f" في {governorate}"
                if property_type:
                    response += f" ({property_type})"
                response += f" هو {median_price:,.0f} دينار."
                
                return {
                    'response': response,
                    'confidence': result.confidence,
                    'data': result.result,
                    'data_source': result.data_source
                }
            else:
                return {
                    'response': 'لا توجد بيانات كافية لحساب المتوسط.',
                    'confidence': 'low'
                }
        else:
            return {
                'response': 'حدث خطأ أثناء جلب البيانات.',
                'error': result.error
            }
    
    def _handle_buy_query(self,
                         user_input: str,
                         intent: IntentClassification,
                         user_id: int,
                         context: Dict) -> Dict:
        """Handle buy property queries"""
        # Update user profile
        params = intent.extracted_params
        for field, value in params.items():
            self.profiling_system.update_profile(user_id, field, value)
        
        # Check if more profiling needed
        if self.profiling_system.should_ask_question(user_id, context):
            next_question = self.profiling_system.get_next_question(user_id, context)
            if next_question:
                return {
                    'response': next_question.question_text,
                    'requires_input': True,
                    'question_id': next_question.question_id
                }
        
        # Get buyer profile
        buyer_profile = self.market_system.get_buyer_profile(user_id)
        if not buyer_profile:
            # Create from params
            buyer_profile = self.market_system.create_buyer_profile(user_id, params)
        
        # Create saved search
        saved_search = self.notifications_system.create_saved_search(
            user_id=user_id,
            filters=params
        )
        
        return {
            'response': 'جاري البحث عن العقارات المطابقة...',
            'buyer_profile': buyer_profile.to_dict(),
            'saved_search_id': saved_search.search_id
        }
    
    def _handle_sell_query(self,
                          user_input: str,
                          intent: IntentClassification,
                          user_id: int) -> Dict:
        """Handle sell property queries"""
        # Get seller requirements
        params = intent.extracted_params
        
        seller_requirements = {
            'governorate': params.get('governorate'),
            'property_type': params.get('property_type'),
            'intent': intent.seller_intent.value if intent.seller_intent else 'best_price'
        }
        
        # Match agents
        agent_matches = self.agent_system.match_agent_for_seller(seller_requirements)
        
        if agent_matches:
            top_agent = agent_matches[0]
            response = f"الأفضل لك: {top_agent.agent.name}. "
            response += ". ".join(top_agent.reasons)
            
            if top_agent.warnings:
                response += " " + ". ".join(top_agent.warnings)
            
            return {
                'response': response,
                'matched_agents': [m.to_dict() for m in agent_matches[:3]],
                'match_count': len(agent_matches)
            }
        else:
            return {
                'response': 'لم أجد دلالين مناسبين حاليًا في منطقتك.',
                'match_count': 0
            }
    
    def _handle_compare_query(self,
                            user_input: str,
                            intent: IntentClassification,
                            user_id: int) -> Dict:
        """Handle comparison queries"""
        # This would need property IDs from context
        # For now, return placeholder
        return {
            'response': 'يمكنني مساعدتك في مقارنة العقارات. حدد العقارات التي تريد مقارنتها.',
            'requires_input': True
        }
    
    def _handle_general_query(self,
                             user_input: str,
                             intent: IntentClassification,
                             user_id: int) -> Dict:
        """Handle general queries"""
        return {
            'response': 'كيف أستطيع مساعدتك في البحث عن العقارات؟',
            'intent': intent.to_dict()
        }
    
    def calculate_property_match(self,
                                 user_id: int,
                                 property_data: Dict) -> MatchScore:
        """Calculate match score for property"""
        buyer_profile = self.market_system.get_buyer_profile(user_id)
        
        if not buyer_profile:
            # Create profile from available data
            buyer_profile = self.market_system.create_buyer_profile(user_id, {})
        
        return self.market_system.calculate_buyer_property_match(buyer_profile, property_data)
    
    def process_new_property(self, property_data: Dict) -> Dict:
        """
        Process new property listing
        Checks for duplicates, anomalies, and notifies matched users
        """
        results = {
            'duplicate_check': None,
            'anomaly_check': None,
            'notifications_sent': 0
        }
        
        # Check for duplicates
        duplicate = self.duplicate_detector.detect_duplicate_listing(property_data)
        if duplicate:
            results['duplicate_check'] = duplicate.to_dict()
        
        # Check for anomalies
        anomaly = self.duplicate_detector.detect_data_inconsistency(property_data)
        if anomaly:
            results['anomaly_check'] = anomaly.to_dict()
        
        # Check against saved searches
        # This would require actual property database
        # Placeholder implementation
        # self.notifications_system.check_and_notify_new_properties([property_data])
        
        return results
    
    def get_market_summary(self) -> Dict:
        """Get overall market intelligence summary"""
        return {
            'market_intelligence': self.market_system.get_market_summary(),
            'agent_matching': {
                'total_agents': len(self.agent_system.agent_profiles),
                'matching_history': len(self.agent_system.matching_history)
            },
            'analytics': self.analytics_layer.get_query_statistics(),
            'notifications': self.notifications_system.get_notification_statistics(),
            'duplicate_detection': self.duplicate_detector.get_detection_summary(),
            'lifecycle': self.lifecycle_manager.get_status_statistics(),
            'intent_classification': self.intent_classifier.get_classification_statistics(),
            'profiling': self.profiling_system.get_profiling_statistics()
        }


# Global instance
market_intelligence_orchestrator = MarketIntelligenceOrchestrator()