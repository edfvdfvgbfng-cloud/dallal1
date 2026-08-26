"""
Search Suggestions System
Provides intelligent search suggestions based on context and history
"""

from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchSuggestion:
    """Represents a search suggestion"""
    text: str
    type: str  # location, property_type, completion
    relevance: float
    source: str  # history, popular, context
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'text': self.text,
            'type': self.type,
            'relevance': self.relevance,
            'source': self.source
        }


class SearchSuggestionsSystem:
    """
    Provides intelligent search suggestions
    Based on user history, popular searches, and context
    """
    
    def __init__(self):
        self.popular_locations = [
            'البصرة', 'بغداد', 'بابل', 'كربلاء', 'النجف',
            'الديوانية', 'ميسان', 'ذي قار', 'القادسية', 'واسط'
        ]
        
        self.popular_property_types = [
            'بيت', 'شقة', 'فيلا', 'محل تجاري', 'أرض'
        ]
        
        self.user_search_history: Dict[int, List[Dict]] = {}
    
    def get_suggestions(self,
                       user_id: int,
                       partial_query: str,
                       context: Dict = None) -> List[SearchSuggestion]:
        """
        Get search suggestions for a partial query
        
        Args:
            user_id: User ID
            partial_query: Partial user query
            context: Additional context
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Get location suggestions
        location_suggestions = self._get_location_suggestions(partial_query)
        suggestions.extend(location_suggestions)
        
        # Get property type suggestions
        type_suggestions = self._get_property_type_suggestions(partial_query)
        suggestions.extend(type_suggestions)
        
        # Get user history suggestions
        history_suggestions = self._get_history_suggestions(user_id, partial_query)
        suggestions.extend(history_suggestions)
        
        # Sort by relevance
        suggestions.sort(key=lambda x: x.relevance, reverse=True)
        
        # Return top 5
        return suggestions[:5]
    
    def _get_location_suggestions(self, partial_query: str) -> List[SearchSuggestion]:
        """Get location-based suggestions"""
        suggestions = []
        
        for location in self.popular_locations:
            if location.startswith(partial_query) or partial_query in location:
                suggestions.append(SearchSuggestion(
                    text=location,
                    type='location',
                    relevance=0.8,
                    source='popular'
                ))
        
        return suggestions
    
    def _get_property_type_suggestions(self, partial_query: str) -> List[SearchSuggestion]:
        """Get property type suggestions"""
        suggestions = []
        
        for prop_type in self.popular_property_types:
            if prop_type.startswith(partial_query) or partial_query in prop_type:
                suggestions.append(SearchSuggestion(
                    text=prop_type,
                    type='property_type',
                    relevance=0.7,
                    source='popular'
                ))
        
        return suggestions
    
    def _get_history_suggestions(self, user_id: int, partial_query: str) -> List[SearchSuggestion]:
        """Get suggestions from user search history"""
        suggestions = []
        
        if user_id not in self.user_search_history:
            return suggestions
        
        history = self.user_search_history[user_id]
        
        for search in history:
            query = search.get('query', '')
            if partial_query in query:
                suggestions.append(SearchSuggestion(
                    text=query,
                    type='history',
                    relevance=0.9,
                    source='history'
                ))
        
        return suggestions
    
    def record_search(self, user_id: int, query: str, filters: Dict):
        """
        Record a search in user history
        
        Args:
            user_id: User ID
            query: Search query
            filters: Search filters
        """
        if user_id not in self.user_search_history:
            self.user_search_history[user_id] = []
        
        self.user_search_history[user_id].append({
            'query': query,
            'filters': filters,
            'timestamp': None  # Would be datetime
        })
        
        # Keep only last 20 searches
        if len(self.user_search_history[user_id]) > 20:
            self.user_search_history[user_id] = self.user_search_history[user_id][-20:]
        
        logger.info(f"Recorded search for user {user_id}: {query}")
    
    def get_recent_searches(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get recent searches for a user"""
        if user_id not in self.user_search_history:
            return []
        
        return self.user_search_history[user_id][-limit:]


# Global instance
search_suggestions_system = SearchSuggestionsSystem()