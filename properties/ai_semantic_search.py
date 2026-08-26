"""
Semantic Search and Hybrid Search System
Implements intelligent search combining structured filters, semantic search, and ranking
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from django.db.models import Q
from django.core.cache import cache
from decimal import Decimal

from .models import Property, Broker, HotelPage, ServiceProviderPage
from .ai_arabic_normalizer import arabic_normalizer

logger = logging.getLogger('properties')


class SemanticSearchEngine:
    """
    Semantic search engine for intelligent property matching
    Uses similarity scoring and ranking algorithms
    """
    
    def __init__(self):
        self.arabic_normalizer = arabic_normalizer
        self.search_weights = {
            'price_match': 0.3,
            'location_match': 0.25,
            'type_match': 0.2,
            'area_match': 0.15,
            'semantic_match': 0.1
        }
    
    def search_properties(self, entities: Dict[str, Any], preferences: List[str] = None) -> List[Dict]:
        """
        Intelligent property search with ranking
        
        Args:
            entities: Extracted entities from user request
            preferences: User preferences (optional)
            
        Returns:
            Ranked list of properties
        """
        # Start with structured query
        query = Property.objects.filter(status='published')
        
        # Apply structured filters
        query = self._apply_structured_filters(query, entities)
        
        # Get initial results
        properties = query.all()[:50]  # Get up to 50 candidates
        
        # Apply semantic scoring and ranking
        ranked_properties = self._rank_properties(properties, entities, preferences)
        
        # Return top results
        return ranked_properties[:10]
    
    def _apply_structured_filters(self, query, entities: Dict[str, Any]):
        """Apply structured database filters"""
        
        # Property type filter
        if 'property_type' in entities and entities['property_type']:
            query = query.filter(type=entities['property_type'])
        
        # Governorate filter
        if 'governorate' in entities and entities['governorate']:
            query = query.filter(governorate=entities['governorate'])
        
        # District filter
        if 'district' in entities and entities['district']:
            query = query.filter(district__icontains=entities['district'])
        
        # Budget filter
        if 'budget' in entities and entities['budget']:
            query = query.filter(price__lte=entities['budget'])
        
        # Area filter
        if 'area' in entities and entities['area']:
            query = query.filter(area__gte=entities['area'])
        
        # Rooms filter
        if 'rooms' in entities and entities['rooms']:
            query = query.filter(rooms__gte=entities['rooms'])
        
        return query
    
    def _rank_properties(self, properties: List[Property], entities: Dict[str, Any], preferences: List[str] = None) -> List[Dict]:
        """
        Rank properties based on multiple factors
        
        Args:
            properties: Query results
            entities: User entities
            preferences: User preferences
            
        Returns:
            Ranked list of property dictionaries
        """
        scored_properties = []
        
        for prop in properties:
            score = self._calculate_property_score(prop, entities, preferences)
            
            scored_properties.append({
                'id': prop.id,
                'title': prop.title,
                'price': prop.price,
                'governorate': prop.governorate,
                'district': prop.district,
                'area': prop.area,
                'type': prop.type,
                'rooms': prop.rooms,
                'image': prop.image.url if prop.image else None,
                'url': f'/property/{prop.id}/',
                'score': score,
                'match_reasons': self._get_match_reasons(prop, entities, preferences)
            })
        
        # Sort by score descending
        scored_properties.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_properties
    
    def _calculate_property_score(self, property: Property, entities: Dict[str, Any], preferences: List[str] = None) -> float:
        """Calculate relevance score for a property"""
        score = 0.0
        
        # Price match score
        if 'budget' in entities and entities['budget']:
            price_score = self._calculate_price_score(property.price, entities['budget'])
            score += price_score * self.search_weights['price_match']
        
        # Location match score
        if 'governorate' in entities and entities['governorate']:
            location_score = self._calculate_location_score(property.governorate, entities['governorate'])
            score += location_score * self.search_weights['location_match']
        
        # Type match score
        if 'property_type' in entities and entities['property_type']:
            type_score = self._calculate_type_score(property.type, entities['property_type'])
            score += type_score * self.search_weights['type_match']
        
        # Area match score
        if 'area' in entities and entities['area']:
            area_score = self._calculate_area_score(property.area, entities['area'])
            score += area_score * self.search_weights['area_match']
        
        # Semantic preference score
        if preferences:
            semantic_score = self._calculate_semantic_score(property, preferences)
            score += semantic_score * self.search_weights['semantic_match']
        
        return min(1.0, score)  # Cap at 1.0
    
    def _calculate_price_score(self, property_price: int, user_budget: int) -> float:
        """Calculate price match score"""
        if not property_price or not user_budget:
            return 0.5  # Neutral score if missing
        
        # Price within budget gets higher score
        if property_price <= user_budget:
            # Closer to budget gets higher score
            ratio = property_price / user_budget
            return 0.8 + (1.0 - ratio) * 0.2
        else:
            # Over budget but close gets some score
            over_budget_ratio = property_price / user_budget
            if over_budget_ratio < 1.1:
                return 0.6
            elif over_budget_ratio < 1.2:
                return 0.4
            else:
                return 0.1
    
    def _calculate_location_score(self, property_gov: str, user_gov: str) -> float:
        """Calculate location match score"""
        if not property_gov or not user_gov:
            return 0.5
        
        if property_gov == user_gov:
            return 1.0
        else:
            return 0.0  # Different governorate gets no score
    
    def _calculate_type_score(self, property_type: str, user_type: str) -> float:
        """Calculate property type match score"""
        if not property_type or not user_type:
            return 0.5
        
        if property_type == user_type:
            return 1.0
        else:
            return 0.0
    
    def _calculate_area_score(self, property_area: int, user_area: int) -> float:
        """Calculate area match score"""
        if not property_area or not user_area:
            return 0.5
        
        # Area close to requested gets higher score
        ratio = property_area / user_area if user_area > 0 else 0
        
        if 0.8 <= ratio <= 1.2:
            return 1.0
        elif 0.6 <= ratio <= 1.4:
            return 0.8
        elif 0.4 <= ratio <= 1.6:
            return 0.6
        else:
            return 0.3
    
    def _calculate_semantic_score(self, property: Property, preferences: List[str]) -> float:
        """Calculate semantic preference score"""
        if not preferences:
            return 0.5
        
        score = 0.0
        property_text = f"{property.title} {property.description or ''}".lower()
        
        for pref in preferences:
            if pref.lower() in property_text:
                score += 0.3
        
        return min(1.0, score)
    
    def _get_match_reasons(self, property: Property, entities: Dict[str, Any], preferences: List[str] = None) -> List[str]:
        """Get reasons why this property matches"""
        reasons = []
        
        if 'budget' in entities and entities['budget']:
            if property.price <= entities['budget']:
                reasons.append("السعر ضمن ميزانيتك")
        
        if 'governorate' in entities and entities['governorate']:
            if property.governorate == entities['governorate']:
                reasons.append(f"موجود في {entities['governorate']}")
        
        if 'property_type' in entities and entities['property_type']:
            if property.type == entities['property_type']:
                reasons.append(f"نوع العقار: {entities['property_type']}")
        
        if preferences:
            property_text = f"{property.title} {property.description or ''}".lower()
            for pref in preferences:
                if pref.lower() in property_text:
                    reasons.append(f"يحقق: {pref}")
        
        return reasons if reasons else ["عقار مطابق لطلبك"]


class HybridSearchEngine:
    """
    Hybrid search combining structured filters, semantic search, and ranking
    Ensures database accuracy while using AI for intelligent ranking
    """
    
    def __init__(self):
        self.semantic_engine = SemanticSearchEngine()
        self.arabic_normalizer = arabic_normalizer
    
    def search(self, entities: Dict[str, Any], preferences: List[str] = None, search_type: str = 'property') -> List[Dict]:
        """
        Perform hybrid search
        
        Args:
            entities: Extracted entities
            preferences: User preferences
            search_type: Type of search (property, hotel, job, etc.)
            
        Returns:
            Ranked search results
        """
        if search_type == 'property':
            return self.semantic_engine.search_properties(entities, preferences)
        elif search_type == 'hotel':
            return self._search_hotels(entities, preferences)
        elif search_type == 'service':
            return self._search_services(entities, preferences)
        else:
            return self._search_general(entities, preferences)
    
    def _search_hotels(self, entities: Dict[str, Any], preferences: List[str] = None) -> List[Dict]:
        """Search hotels with hybrid approach"""
        query = HotelPage.objects.filter(is_active=True)
        
        # Apply structured filters
        if 'location' in entities and entities['location']:
            query = query.filter(governorate=entities['location'])
        
        if 'stars' in entities and entities['stars']:
            query = query.filter(stars__gte=entities['stars'])
        
        hotels = query.all()[:20]
        
        # Rank hotels
        scored_hotels = []
        for hotel in hotels:
            score = self._calculate_hotel_score(hotel, entities, preferences)
            scored_hotels.append({
                'id': hotel.id,
                'name': hotel.name,
                'governorate': hotel.governorate,
                'stars': hotel.stars,
                'image': hotel.image.url if hotel.image else None,
                'url': f'/hotel/{hotel.id}/',
                'score': score
            })
        
        scored_hotels.sort(key=lambda x: x['score'], reverse=True)
        return scored_hotels[:10]
    
    def _calculate_hotel_score(self, hotel: HotelPage, entities: Dict[str, Any], preferences: List[str] = None) -> float:
        """Calculate hotel relevance score"""
        score = 0.5  # Base score
        
        if 'location' in entities and entities['location']:
            if hotel.governorate == entities['location']:
                score += 0.3
        
        if 'stars' in entities and entities['stars']:
            if hotel.stars >= entities['stars']:
                score += 0.2
        
        return min(1.0, score)
    
    def _search_services(self, entities: Dict[str, Any], preferences: List[str] = None) -> List[Dict]:
        """Search services with hybrid approach"""
        query = ServiceProviderPage.objects.filter(is_active=True)
        
        if 'location' in entities and entities['location']:
            query = query.filter(governorate=entities['location'])
        
        if 'service_type' in entities and entities['service_type']:
            query = query.filter(service_type=entities['service_type'])
        
        services = query.all()[:20]
        
        scored_services = []
        for service in services:
            score = self._calculate_service_score(service, entities, preferences)
            scored_services.append({
                'id': service.id,
                'name': service.name,
                'service_type': service.service_type,
                'governorate': service.governorate,
                'url': f'/service/{service.id}/',
                'score': score
            })
        
        scored_services.sort(key=lambda x: x['score'], reverse=True)
        return scored_services[:10]
    
    def _calculate_service_score(self, service: ServiceProviderPage, entities: Dict[str, Any], preferences: List[str] = None) -> float:
        """Calculate service relevance score"""
        score = 0.5
        
        if 'location' in entities and entities['location']:
            if service.governorate == entities['location']:
                score += 0.3
        
        if 'service_type' in entities and entities['service_type']:
            if service.service_type == entities['service_type']:
                score += 0.2
        
        return min(1.0, score)
    
    def _search_general(self, entities: Dict[str, Any], preferences: List[str] = None) -> List[Dict]:
        """General search fallback"""
        return [{
            'action': 'info',
            'message': 'يرجى تحديد نوع البحث المطلوب'
        }]


class ConversationLearner:
    """
    Learning from user conversations to improve accuracy
    Collects corrections and feedback for model improvement
    """
    
    def __init__(self):
        self.corrections = []
        self.feedback_data = []
        self.conversation_logs = []
    
    def record_correction(self, original_intent: str, corrected_intent: str, original_entities: Dict, corrected_entities: Dict, user_message: str):
        """
        Record user correction for learning
        
        Args:
            original_intent: Originally predicted intent
            corrected_intent: Correct intent specified by user
            original_entities: Originally extracted entities
            corrected_entities: Correct entities specified by user
            user_message: Original user message
        """
        correction = {
            'original_intent': original_intent,
            'corrected_intent': corrected_intent,
            'original_entities': original_entities,
            'corrected_entities': corrected_entities,
            'user_message': user_message,
            'timestamp': self._get_timestamp()
        }
        
        self.corrections.append(correction)
        logger.info(f"Recorded correction: {original_intent} -> {corrected_intent}")
    
    def record_feedback(self, conversation_id: str, feedback_type: str, message: str, response: str):
        """
        Record user feedback on response quality
        
        Args:
            conversation_id: Conversation identifier
            feedback_type: 'positive' or 'negative'
            message: User message
            response: AI response
        """
        feedback = {
            'conversation_id': conversation_id,
            'feedback_type': feedback_type,
            'message': message,
            'response': response,
            'timestamp': self._get_timestamp()
        }
        
        self.feedback_data.append(feedback)
        logger.info(f"Recorded feedback: {feedback_type}")
    
    def record_conversation(self, conversation_id: str, messages: List[Dict]):
        """
        Record complete conversation for analysis
        
        Args:
            conversation_id: Conversation identifier
            messages: List of message dictionaries
        """
        conversation_log = {
            'conversation_id': conversation_id,
            'messages': messages,
            'timestamp': self._get_timestamp()
        }
        
        self.conversation_logs.append(conversation_log)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            'total_corrections': len(self.corrections),
            'total_feedback': len(self.feedback_data),
            'total_conversations': len(self.conversation_logs),
            'intent_accuracy': self._calculate_intent_accuracy(),
            'entity_accuracy': self._calculate_entity_accuracy(),
            'positive_feedback_rate': self._calculate_positive_feedback_rate()
        }
    
    def _calculate_intent_accuracy(self) -> float:
        """Calculate intent accuracy from corrections"""
        if not self.corrections:
            return 0.0
        
        correct_predictions = sum(1 for c in self.corrections if c['original_intent'] == c['corrected_intent'])
        return correct_predictions / len(self.corrections)
    
    def _calculate_entity_accuracy(self) -> float:
        """Calculate entity extraction accuracy"""
        if not self.corrections:
            return 0.0
        
        total_entity_comparisons = 0
        correct_entity_comparisons = 0
        
        for correction in self.corrections:
            orig_entities = correction['original_entities']
            corr_entities = correction['corrected_entities']
            
            for key in set(orig_entities.keys()) | set(corr_entities.keys()):
                total_entity_comparisons += 1
                if orig_entities.get(key) == corr_entities.get(key):
                    correct_entity_comparisons += 1
        
        if total_entity_comparisons == 0:
            return 0.0
        
        return correct_entity_comparisons / total_entity_comparisons
    
    def _calculate_positive_feedback_rate(self) -> float:
        """Calculate positive feedback rate"""
        if not self.feedback_data:
            return 0.0
        
        positive_count = sum(1 for f in self.feedback_data if f['feedback_type'] == 'positive')
        return positive_count / len(self.feedback_data)
    
    def export_training_data(self) -> List[Dict]:
        """
        Export data suitable for training ML models
        This is for future use when implementing real ML training
        """
        training_data = []
        
        for correction in self.corrections:
            training_data.append({
                'text': correction['user_message'],
                'intent': correction['corrected_intent'],
                'entities': correction['corrected_entities'],
                'source': 'user_correction'
            })
        
        for conversation in self.conversation_logs:
            for message in conversation['messages']:
                if message.get('intent'):
                    training_data.append({
                        'text': message.get('text', ''),
                        'intent': message.get('intent'),
                        'entities': message.get('entities', {}),
                        'source': 'conversation_log'
                    })
        
        return training_data


# Global instances
semantic_search_engine = SemanticSearchEngine()
hybrid_search_engine = HybridSearchEngine()
conversation_learner = ConversationLearner()