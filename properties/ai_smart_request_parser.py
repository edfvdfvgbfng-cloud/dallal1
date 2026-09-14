"""
AI Request Parser
Parses user input into structured search filters
Validates and normalizes extracted data
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

from .ai_smart_intent_detection import intent_detector, Intent

logger = logging.getLogger(__name__)


class AIRequestParser:
    """
    Parses user input into structured search filters
    Extracts and validates filters based on detected intent
    """
    
    def __init__(self):
        self.detector = intent_detector
    
    def parse_request(self, text: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Parse user request into structured data
        
        Args:
            text: User input text
            user_id: User ID (optional)
            
        Returns:
            Dict containing:
            - intent: Detected intent
            - filters: Extracted filters
            - missing_fields: List of required fields still missing
            - confidence: Confidence score
        """
        # Detect intent
        intent, confidence = self.detector.detect_intent(text)
        
        # Extract filters based on intent
        filters = self._extract_filters(text, intent)
        
        # Identify missing fields
        missing_fields = self._identify_missing_fields(intent, filters)
        
        result = {
            'intent': intent,
            'filters': filters,
            'missing_fields': missing_fields,
            'confidence': confidence,
            'original_text': text,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Parsed request: {result}")
        return result
    
    def _extract_filters(self, text: str, intent: str) -> Dict[str, Any]:
        """Extract filters based on intent"""
        filters = {}
        
        # Common filters that apply to multiple intents
        if intent in [Intent.BUY_PROPERTY, Intent.SELL_PROPERTY, Intent.RENT_PROPERTY, Intent.SEARCH_PROPERTY]:
            filters.update(self._extract_property_filters(text))
        elif intent == Intent.SEARCH_HOTEL:
            filters.update(self._extract_hotel_filters(text))
        elif intent == Intent.SEARCH_RESORT:
            filters.update(self._extract_resort_filters(text))
        elif intent == Intent.SEARCH_JOB:
            filters.update(self._extract_job_filters(text))
        elif intent == Intent.SEARCH_SERVICE:
            filters.update(self._extract_service_filters(text))
        elif intent == Intent.SEARCH_AUCTION:
            filters.update(self._extract_auction_filters(text))
        
        return filters
    
    def _extract_property_filters(self, text: str) -> Dict[str, Any]:
        """Extract property-specific filters"""
        filters = {}
        
        # Property type
        property_type = self.detector.extract_property_type(text)
        if property_type:
            filters['property_type'] = property_type
        
        # Location
        location = self.detector.extract_location(text)
        if location:
            filters['location'] = location
        
        # Price
        price_info = self.detector.extract_price(text)
        if price_info:
            filters['price'] = price_info
        
        # Area
        area = self.detector.extract_area(text)
        if area:
            filters['area'] = area
        
        # Rooms
        rooms = self.detector.extract_rooms(text)
        if rooms:
            filters['rooms'] = rooms
        
        # Purpose (buy/rent/investment)
        if 'شراء' in text or 'اشتري' in text or 'buy' in text.lower():
            filters['purpose'] = 'sale'
        elif 'إيجار' in text or 'أكري' in text or 'rent' in text.lower():
            filters['purpose'] = 'rent'
        elif 'استثمار' in text or 'investment' in text.lower():
            filters['purpose'] = 'investment'
        
        # Inside/Outside Iraq
        if 'خارج' in text or 'خارج.*العراق' in text or 'outside' in text.lower():
            filters['location_type'] = 'outside_iraq'
        else:
            filters['location_type'] = 'inside_iraq'
        
        return filters
    
    def _extract_hotel_filters(self, text: str) -> Dict[str, Any]:
        """Extract hotel-specific filters"""
        filters = {}
        
        # Location
        location = self.detector.extract_location(text)
        if location:
            filters['city'] = location
        
        # Guests (look for numbers with context)
        import re
        guest_match = re.search(r'(\d+)\s*(?:شخص|أفراد|guest|people)', text, re.IGNORECASE)
        if guest_match:
            filters['guests'] = int(guest_match.group(1))
        
        # Star rating
        star_match = re.search(r'(\d+)\s*(?:نجمة|نجوم|star)', text, re.IGNORECASE)
        if star_match:
            filters['star_rating'] = int(star_match.group(1))
        
        # Price range
        price_info = self.detector.extract_price(text)
        if price_info:
            filters['price'] = price_info
        
        return filters
    
    def _extract_resort_filters(self, text: str) -> Dict[str, Any]:
        """Extract resort-specific filters"""
        filters = {}
        
        # Location
        location = self.detector.extract_location(text)
        if location:
            filters['city'] = location
        
        # Capacity
        import re
        capacity_match = re.search(r'(\d+)\s*(?:شخص|أفراد|guest|people)', text, re.IGNORECASE)
        if capacity_match:
            filters['capacity'] = int(capacity_match.group(1))
        
        # Family suitability
        if 'عائلي' in text or 'family' in text.lower():
            filters['family_suitable'] = True
        
        # Price
        price_info = self.detector.extract_price(text)
        if price_info:
            filters['price'] = price_info
        
        return filters
    
    def _extract_job_filters(self, text: str) -> Dict[str, Any]:
        """Extract job-specific filters"""
        filters = {}
        
        # Location
        location = self.detector.extract_location(text)
        if location:
            filters['location'] = location
        
        # Job title/category
        import re
        # Common job titles
        job_titles = ['محاسب', 'مهندس', 'دكتور', 'معلم', 'مبرمج', 'accountant', 'engineer', 'doctor', 'teacher', 'programmer']
        for title in job_titles:
            if title in text:
                filters['job_title'] = title
                break
        
        # Salary
        price_info = self.detector.extract_price(text)
        if price_info:
            filters['salary'] = price_info
        
        return filters
    
    def _extract_service_filters(self, text: str) -> Dict[str, Any]:
        """Extract service-specific filters"""
        filters = {}
        
        # Location
        location = self.detector.extract_location(text)
        if location:
            filters['location'] = location
        
        # Service type
        service_types = ['كهربائي', 'سباك', 'نجار', 'بناء', 'electrician', 'plumber', 'carpenter', 'builder']
        for service in service_types:
            if service in text:
                filters['service_type'] = service
                break
        
        # Price
        price_info = self.detector.extract_price(text)
        if price_info:
            filters['price'] = price_info
        
        return filters
    
    def _extract_auction_filters(self, text: str) -> Dict[str, Any]:
        """Extract auction-specific filters"""
        filters = {}
        
        # Location
        location = self.detector.extract_location(text)
        if location:
            filters['location'] = location
        
        # Property type
        property_type = self.detector.extract_property_type(text)
        if property_type:
            filters['property_type'] = property_type
        
        # Price
        price_info = self.detector.extract_price(text)
        if price_info:
            filters['max_bid'] = price_info
        
        return filters
    
    def _identify_missing_fields(self, intent: str, filters: Dict) -> List[str]:
        """
        Identify required fields that are still missing
        Returns list of field names that need to be collected
        """
        required_fields = {
            Intent.BUY_PROPERTY: ['location', 'price'],
            Intent.SELL_PROPERTY: ['property_type', 'location'],
            Intent.RENT_PROPERTY: ['location'],
            Intent.SEARCH_HOTEL: ['location'],
            Intent.SEARCH_RESORT: ['location'],
            Intent.SEARCH_JOB: ['location'],
            Intent.SEARCH_SERVICE: ['service_type', 'location'],
            Intent.SEARCH_AUCTION: ['location'],
        }
        
        if intent not in required_fields:
            return []
        
        missing = []
        for field in required_fields[intent]:
            if field not in filters or not filters[field]:
                missing.append(field)
        
        return missing
    
    def validate_filters(self, intent: str, filters: Dict) -> Tuple[bool, List[str]]:
        """
        Validate extracted filters
        Returns (is_valid, error_messages)
        """
        errors = []
        
        # Validate price
        if 'price' in filters:
            price = filters['price']
            if not isinstance(price, dict) or 'value' not in price:
                errors.append('Invalid price format')
            elif price['value'] <= 0:
                errors.append('Price must be positive')
        
        # Validate area
        if 'area' in filters:
            area = filters['area']
            if not isinstance(area, (int, float)) or area <= 0:
                errors.append('Area must be a positive number')
        
        # Validate rooms
        if 'rooms' in filters:
            rooms = filters['rooms']
            if not isinstance(rooms, int) or rooms <= 0:
                errors.append('Number of rooms must be a positive integer')
        
        return len(errors) == 0, errors


# Global instance
ai_request_parser = AIRequestParser()
