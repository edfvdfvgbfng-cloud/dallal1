"""
Query Rewrite and Normalization
Normalizes and rewrites user queries for better search
"""

from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class NormalizedQuery:
    """Represents a normalized query"""
    original: str
    normalized: str
    structured: Dict
    intent: str
    entities: Dict
    confidence: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'original': self.original,
            'normalized': self.normalized,
            'structured': self.structured,
            'intent': self.intent,
            'entities': self.entities,
            'confidence': self.confidence
        }


class QueryRewriter:
    """
    Normalizes and rewrites user queries
    Handles typos, dialects, and informal language
    """
    
    def __init__(self):
        # Common typos and corrections
        self.typos = {
            'اريد': 'أريد',
            'بلعشار': 'بالعشار',
            'بيت': 'عقار',
            'دار': 'عقار',
            'شغل': 'وظيفة',
            'ادور': 'أبحث',
            'حچي': 'أحكي',
            'شلون': 'كيف',
            'شكد': 'كم',
            'وين': 'أين',
            'ليش': 'لماذا',
            'كلش': 'كل شيء'
        }
        
        # Location mappings
        self.location_mappings = {
            'بصرة': 'البصرة',
            'بغداد': 'بغداد',
            'بابل': 'بابل',
            'كربلاء': 'كربلاء',
            'نجف': 'النجف',
            'دلبي': 'الديوانية',
            'ميسان': 'ميسان',
            'ذي قار': 'ذي قار',
            'القادسية': 'القادسية',
            'واسط': 'واسط'
        }
        
        # Property type mappings
        self.property_type_mappings = {
            'بيت': 'بيت',
            'شقة': 'شقة',
            'فيلا': 'فيلا',
            'محل': 'محل تجاري',
            'ارض': 'أرض',
            'مبنى': 'مبنى'
        }
    
    def normalize(self, query: str) -> NormalizedQuery:
        """
        Normalize a user query
        
        Args:
            query: Original query
            
        Returns:
            Normalized query
        """
        # Step 1: Basic normalization
        normalized = self._basic_normalize(query)
        
        # Step 2: Fix typos
        normalized = self._fix_typos(normalized)
        
        # Step 3: Normalize locations
        normalized = self._normalize_locations(normalized)
        
        # Step 4: Normalize property types
        normalized = self._normalize_property_types(normalized)
        
        # Step 5: Extract entities
        entities = self._extract_entities(normalized)
        
        # Step 6: Determine intent
        intent = self._determine_intent(normalized, entities)
        
        # Step 7: Create structured query
        structured = self._create_structured_query(intent, entities)
        
        return NormalizedQuery(
            original=query,
            normalized=normalized,
            structured=structured,
            intent=intent,
            entities=entities,
            confidence=0.85
        )
    
    def _basic_normalize(self, text: str) -> str:
        """Basic text normalization"""
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing spaces
        text = text.strip()
        
        # Normalize Arabic characters
        text = text.replace('أ', 'ا')
        text = text.replace('إ', 'ا')
        text = text.replace('آ', 'ا')
        
        return text
    
    def _fix_typos(self, text: str) -> str:
        """Fix common typos"""
        for typo, correction in self.typos.items():
            text = text.replace(typo, correction)
        return text
    
    def _normalize_locations(self, text: str) -> str:
        """Normalize location names"""
        for informal, formal in self.location_mappings.items():
            if informal in text:
                text = text.replace(informal, formal)
        return text
    
    def _normalize_property_types(self, text: str) -> str:
        """Normalize property type names"""
        for informal, formal in self.property_type_mappings.items():
            if informal in text:
                text = text.replace(informal, formal)
        return text
    
    def _extract_entities(self, text: str) -> Dict:
        """Extract entities from text"""
        entities = {}
        
        # Extract price
        price_match = re.search(r'(\d+)\s*(مليون|مليار)?', text)
        if price_match:
            amount = int(price_match.group(1))
            unit = price_match.group(2)
            
            if unit == 'مليار':
                amount *= 1000
            elif unit is None:
                # Assume millions if no unit specified for large numbers
                if amount < 1000:
                    amount *= 1000000
            
            entities['price'] = amount
        
        # Extract rooms
        rooms_match = re.search(r'(\d+)\s*(غرفة|غرف)?', text)
        if rooms_match:
            entities['rooms'] = int(rooms_match.group(1))
        
        # Extract area
        area_match = re.search(r'(\d+)\s*(متر|م²)?', text)
        if area_match:
            entities['area'] = int(area_match.group(1))
        
        # Extract governorate
        for location in self.location_mappings.values():
            if location in text:
                entities['governorate'] = location
                break
        
        # Extract property type
        for prop_type in self.property_type_mappings.values():
            if prop_type in text:
                entities['property_type'] = prop_type
                break
        
        return entities
    
    def _determine_intent(self, text: str, entities: Dict) -> str:
        """Determine user intent"""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ['اريد', 'ابحث', 'ادور', 'احتاج']):
            if 'بيع' in text_lower:
                return 'sell_property'
            elif 'شراء' in text_lower or 'إيجار' in text_lower:
                return 'buy_property'
            else:
                return 'search_property'
        
        if 'سعر' in text_lower or 'اسعار' in text_lower:
            return 'price_inquiry'
        
        if 'مقارنة' in text_lower:
            return 'compare_properties'
        
        return 'general_inquiry'
    
    def _create_structured_query(self, intent: str, entities: Dict) -> Dict:
        """Create structured query from intent and entities"""
        structured = {
            'intent': intent,
            'filters': {}
        }
        
        # Map entities to filters
        if 'price' in entities:
            structured['filters']['max_price'] = entities['price']
        
        if 'rooms' in entities:
            structured['filters']['rooms'] = entities['rooms']
        
        if 'area' in entities:
            structured['filters']['min_area'] = entities['area']
        
        if 'governorate' in entities:
            structured['filters']['governorate'] = entities['governorate']
        
        if 'property_type' in entities:
            structured['filters']['property_type'] = entities['property_type']
        
        return structured
    
    def rewrite_conversational(self, current_query: str, previous_query: str, previous_result: Dict) -> str:
        """
        Rewrite a conversational query based on context
        
        Args:
            current_query: Current user query
            previous_query: Previous query
            previous_result: Previous search result
            
        Returns:
            Rewritten query
        """
        # Example conversational patterns
        conversational_patterns = {
            r'خليها ا(ر|و)خ(ص|ر)': 'reduce_max_price',
            r'شيل شرط': 'remove_filter',
            r'اخل(ي|ي) بالبدل': 'replace_location',
            r'اقرب': 'nearby_location'
        }
        
        # Check for conversational patterns
        for pattern, action in conversational_patterns.items():
            if re.search(pattern, current_query):
                return self._apply_conversational_action(action, current_query, previous_query, previous_result)
        
        # If no pattern, return as-is
        return current_query
    
    def _apply_conversational_action(self, action: str, current: str, previous: str, result: Dict) -> str:
        """Apply a conversational action to rewrite query"""
        if action == 'reduce_max_price':
            # Reduce price by 20%
            if 'filters' in result and 'max_price' in result['filters']:
                old_price = result['filters']['max_price']
                new_price = int(old_price * 0.8)
                return previous.replace(str(old_price), str(new_price))
        
        elif action == 'remove_filter':
            # Remove specific filter
            if 'غرف' in current:
                return re.sub(r'\d+\s*غرف', '', previous)
        
        return current


# Global instance
query_rewriter = QueryRewriter()