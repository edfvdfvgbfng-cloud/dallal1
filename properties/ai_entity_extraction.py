"""
Entity Extraction Module
Advanced entity extraction with context awareness and dialect support
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from decimal import Decimal

logger = logging.getLogger('properties')


class EntityExtractor:
    """
    Advanced entity extraction for Arabic text with Iraqi dialect support
    Extracts structured information from unstructured text
    """
    
    def __init__(self):
        self.entity_patterns = self._load_entity_patterns()
        self.governorate_list = self._load_governorates()
        self.property_types = self._load_property_types()
        self.number_conversions = self._load_number_conversions()
        self.entity_statistics = defaultdict(int)
        self.extraction_corrections = defaultdict(list)
    
    def _load_entity_patterns(self) -> Dict[str, List[str]]:
        """Load regex patterns for entity extraction"""
        return {
            'property_type': [
                r'(بيت|دار|منزل|شقة|قسيمة|أرض|محل|مخبز|عمارة|فيلا|دبلكس)',
                r'(عقار|مبنى|بناية)'
            ],
            'governorate': [
                r'(بغداد|البصرة|أربيل|دهوك|نينوى|كربلاء|النجف|الديوانية|القادسية|بابل|واسط|الانبار|صلاح الدين|ذي قار|ميسان|المثنى|ديالى|كركوك|سليمانية)',
                r'(بلبصرة|بالبصره|هولير|الموصل|العمارة|السماوة|الرمادي|تكريت|الناصرية)'
            ],
            'district': [
                r'(الكاظمية|الاعظمية|المنصور|الكرادة|السيدية|الشعب|الرصافة|المأمون|الجوخ)',
                r'(العشار|الجزيرة|المناطق|الشمالية|الشرقية|الغربية|الوسط)'
            ],
            'area': [
                r'(\d+)\s*(متر|م²|م|متر\s+مربع)',
                r'مساحته\s+(\d+)',
                r'مساحة\s+(\d+)'
            ],
            'budget': [
                r'(\d+)\s*(مليون|مليار)',
                r'ميزانيتي\s+(\d+)',
                'بحدود\s+(\d+)',
                r'سعر\s+(\d+)'
            ],
            'rooms': [
                r'(\d+)\s*(غرفة|غرف)',
                r'(\d+)\s*(طابق|طوابق)'
            ],
            'phone': [
                r'(?:\+?964)?\s*0?\d{10,15}',
                r'07\d{9}'
            ]
        }
    
    def _load_governorates(self) -> Dict[str, str]:
        """Load Iraqi governorates with normalizations"""
        return {
            'بغداد': 'بغداد',
            'البصرة': 'البصرة',
            'بلبصرة': 'البصرة',
            'بالبصره': 'البصرة',
            'بصرة': 'البصرة',
            'أربيل': 'أربيل',
            'هولير': 'أربيل',
            'دهوك': 'دهوك',
            'نينوى': 'نينوى',
            'الموصل': 'نينوى',
            'كربلاء': 'كربلاء',
            'النجف': 'النجف',
            'الديوانية': 'الديوانية',
            'القادسية': 'القادسية',
            'بابل': 'بابل',
            'واسط': 'واسط',
            'الانبار': 'الانبار',
            'الرمادي': 'الانبار',
            'صلاح الدين': 'صلاح الدين',
            'تكريت': 'صلاح الدين',
            'ذي قار': 'ذي قار',
            'الناصرية': 'ذي قار',
            'ميسان': 'ميسان',
            'العمارة': 'ميسان',
            'المثنى': 'المثنى',
            'السماوة': 'المثنى',
            'ديالى': 'ديالى',
            'كركوك': 'كركوك',
            'سليمانية': 'سليمانية',
            'حلبجة': 'سليمانية'
        }
    
    def _load_property_types(self) -> Dict[str, str]:
        """Load property type mappings"""
        return {
            'بيت': 'house',
            'دار': 'house',
            'منزل': 'house',
            'شقة': 'apartment',
            'قسيمة': 'plot',
            'أرض': 'land',
            'محل': 'commercial',
            'مخبز': 'bakery',
            'عمارة': 'building',
            'فيلا': 'villa',
            'دبلكس': 'duplex'
        }
    
    def _load_number_conversions(self) -> Dict[str, int]:
        """Load number conversion mappings for Iraqi dialect"""
        return {
            'مليون': 1000000,
            'مليار': 1000000000,
            'ألف': 1000,
            'مئة': 100,
            'مائة': 100,
            'نصف': 0.5,
            'ربع': 0.25,
            'ثمن': 0.125
        }
    
    def extract_entities(self, text: str, intent: Optional[str] = None, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract entities from text with context awareness
        
        Args:
            text: User input text
            intent: Detected intent (optional, guides extraction)
            context: Conversation context (optional)
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        normalized_text = text.lower()
        
        # Extract based on intent to prioritize relevant entities
        if intent in ['buy_property', 'sell_property']:
            entities.update(self._extract_property_entities(normalized_text))
        elif intent == 'find_job':
            entities.update(self._extract_job_entities(normalized_text))
        elif intent == 'find_hotel':
            entities.update(self._extract_hotel_entities(normalized_text))
        elif intent == 'travel':
            entities.update(self._extract_travel_entities(normalized_text))
        else:
            # General extraction
            entities.update(self._extract_general_entities(normalized_text))
        
        # Track extraction statistics
        for entity_type in entities.keys():
            self.entity_statistics[entity_type] += 1
        
        # Apply context-based corrections
        if context:
            entities = self._apply_context_corrections(entities, context)
        
        return entities
    
    def _extract_property_entities(self, text: str) -> Dict[str, Any]:
        """Extract property-related entities"""
        entities = {}
        
        # Property type
        for arabic_type, english_type in self.property_types.items():
            if arabic_type in text:
                entities['property_type'] = english_type
                break
        
        # Governorate
        for arabic_gov, standard_gov in self.governorate_list.items():
            if arabic_gov in text:
                entities['governorate'] = standard_gov
                break
        
        # Area
        area_match = re.search(r'(\d+)\s*(متر|م²|م|متر\s+مربع)', text)
        if area_match:
            entities['area'] = int(area_match.group(1))
        else:
            area_match = re.search(r'مساحته\s+(\d+)', text)
            if area_match:
                entities['area'] = int(area_match.group(1))
        
        # Budget
        budget_match = re.search(r'(\d+)\s*(مليون|مليار)', text)
        if budget_match:
            number = int(budget_match.group(1))
            unit = budget_match.group(2)
            multiplier = self.number_conversions.get(unit, 1)
            entities['budget'] = number * multiplier
        else:
            budget_match = re.search(r'بحدود\s+(\d+)', text)
            if budget_match:
                # Assume millions if number is small
                number = int(budget_match.group(1))
                if number < 1000:
                    entities['budget'] = number * 1000000
                else:
                    entities['budget'] = number
        
        # Rooms
        rooms_match = re.search(r'(\d+)\s*(غرفة|غرف)', text)
        if rooms_match:
            entities['rooms'] = int(rooms_match.group(1))
        
        # District
        district_match = re.search(r'(الكاظمية|الاعظمية|المنصور|الكرادة|السيدية|الشعب|الرصافة|المأمون|الجوخ|العشار|الجزيرة)', text)
        if district_match:
            entities['district'] = district_match.group(1)
        
        return entities
    
    def _extract_job_entities(self, text: str) -> Dict[str, Any]:
        """Extract job-related entities"""
        entities = {}
        
        # Job type
        job_keywords = ['برمجة', 'تصميم', 'كتابة', 'ترجمة', 'تسويق', 'مبيعات', 'محاسبة', 'إدارة']
        for keyword in job_keywords:
            if keyword in text:
                entities['job_type'] = keyword
                break
        
        # Location
        for arabic_gov, standard_gov in self.governorate_list.items():
            if arabic_gov in text:
                entities['location'] = standard_gov
                break
        
        # Salary
        salary_match = re.search(r'(\d+)\s*(مليون|مليار|ألف)', text)
        if salary_match:
            number = int(salary_match.group(1))
            unit = salary_match.group(2)
            multiplier = self.number_conversions.get(unit, 1)
            entities['salary'] = number * multiplier
        
        return entities
    
    def _extract_hotel_entities(self, text: str) -> Dict[str, Any]:
        """Extract hotel-related entities"""
        entities = {}
        
        # Location
        for arabic_gov, standard_gov in self.governorate_list.items():
            if arabic_gov in text:
                entities['location'] = standard_gov
                break
        
        # Room type
        room_types = ['غرفة مفردة', 'غرفة مزدوجة', 'جناح', 'شقة فندقية']
        for room_type in room_types:
            if room_type in text:
                entities['room_type'] = room_type
                break
        
        # Duration
        duration_match = re.search(r'(\d+)\s*(ليلة|يوم|أسبوع)', text)
        if duration_match:
            entities['duration'] = {
                'value': int(duration_match.group(1)),
                'unit': duration_match.group(2)
            }
        
        return entities
    
    def _extract_travel_entities(self, text: str) -> Dict[str, Any]:
        """Extract travel-related entities"""
        entities = {}
        
        # Destination
        for arabic_gov, standard_gov in self.governorate_list.items():
            if arabic_gov in text:
                entities['destination'] = standard_gov
                break
        
        # Date indicators
        date_keywords = ['غداً', 'بعد غد', 'الأسبوع القادم', 'الشهر القادم']
        for keyword in date_keywords:
            if keyword in text:
                entities['time_preference'] = keyword
                break
        
        return entities
    
    def _extract_general_entities(self, text: str) -> Dict[str, Any]:
        """Extract general entities without specific intent"""
        entities = {}
        
        # Extract any location
        for arabic_gov, standard_gov in self.governorate_list.items():
            if arabic_gov in text:
                entities['location'] = standard_gov
                break
        
        # Extract any numbers
        numbers = re.findall(r'\d+', text)
        if numbers:
            entities['numbers'] = [int(num) for num in numbers]
        
        return entities
    
    def _apply_context_corrections(self, entities: Dict[str, Any], context: Dict) -> Dict[str, Any]:
        """Apply context-based corrections to extracted entities"""
        corrected_entities = entities.copy()
        
        # If context has previous entities, prioritize them
        if 'previous_entities' in context:
            previous = context['previous_entities']
            
            # Don't overwrite existing entities with lower confidence
            for key, value in corrected_entities.items():
                if key in previous and self._is_higher_confidence(value, previous[key]):
                    corrected_entities[key] = value
                elif key in previous:
                    corrected_entities[key] = previous[key]
        
        return corrected_entities
    
    def _is_higher_confidence(self, new_value: Any, old_value: Any) -> bool:
        """Compare confidence of entity values (simplified)"""
        # For now, just prefer new values unless they're empty
        return new_value is not None and new_value != ''
    
    def record_correction(self, predicted_entities: Dict, correct_entities: Dict, text: str):
        """
        Record entity extraction correction for learning
        
        Args:
            predicted_entities: The originally extracted entities
            correct_entities: The correct entities as specified by user
            text: The original user text
        """
        for entity_type, predicted_value in predicted_entities.items():
            if entity_type in correct_entities:
                if predicted_value != correct_entities[entity_type]:
                    self.extraction_corrections[entity_type].append({
                        "predicted": predicted_value,
                        "correct": correct_entities[entity_type],
                        "text": text,
                        "timestamp": None
                    })
        
        logger.info(f"Recorded entity extraction correction")
    
    def get_extraction_statistics(self) -> Dict:
        """Get entity extraction statistics"""
        return {
            "total_extractions": sum(self.entity_statistics.values()),
            "entity_distribution": dict(self.entity_statistics),
            "total_corrections": sum(len(corrections) for corrections in self.extraction_corrections.values()),
            "correction_distribution": {
                entity_type: len(corrections) 
                for entity_type, corrections in self.extraction_corrections.items()
            }
        }
    
    def validate_entities(self, entities: Dict, intent: str) -> Tuple[bool, List[str]]:
        """
        Validate extracted entities based on intent
        
        Args:
            entities: Extracted entities
            intent: Detected intent
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if intent == 'buy_property':
            if 'property_type' in entities and entities['property_type'] not in self.property_types.values():
                errors.append(f"Invalid property type: {entities['property_type']}")
            
            if 'budget' in entities and (entities['budget'] < 0 or entities['budget'] > 10000000000):
                errors.append("Budget seems unrealistic")
            
            if 'area' in entities and (entities['area'] < 10 or entities['area'] > 10000):
                errors.append("Area seems unrealistic")
        
        return len(errors) == 0, errors


class EntityNormalizer:
    """
    Normalizes extracted entities to standard formats
    Handles various data formats and units
    """
    
    def __init__(self):
        self.governorate_normalizer = self._load_governorate_normalizer()
        self.property_type_normalizer = self._load_property_type_normalizer()
    
    def _load_governorate_normalizer(self) -> Dict[str, str]:
        """Load governorate normalization mappings"""
        return {
            'بغداد': 'بغداد',
            'البصرة': 'البصرة',
            'أربيل': 'أربيل',
            'دهوك': 'دهوك',
            'نينوى': 'نينوى',
            'كربلاء': 'كربلاء',
            'النجف': 'النجف',
            'الديوانية': 'الديوانية',
            'القادسية': 'القادسية',
            'بابل': 'بابل',
            'واسط': 'واسط',
            'الانبار': 'الانبار',
            'صلاح الدين': 'صلاح الدين',
            'ذي قار': 'ذي قار',
            'ميسان': 'ميسان',
            'المثنى': 'المثنى',
            'ديالى': 'ديالى',
            'كركوك': 'كركوك',
            'سليمانية': 'سليمانية'
        }
    
    def _load_property_type_normalizer(self) -> Dict[str, str]:
        """Load property type normalization mappings"""
        return {
            'house': 'house',
            'apartment': 'apartment',
            'plot': 'plot',
            'land': 'land',
            'commercial': 'commercial',
            'villa': 'villa',
            'duplex': 'duplex',
            'building': 'building'
        }
    
    def normalize(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize extracted entities to standard formats
        
        Args:
            entities: Raw extracted entities
            
        Returns:
            Normalized entities
        """
        normalized = {}
        
        for entity_type, value in entities.items():
            if entity_type == 'governorate' or entity_type == 'location':
                normalized[entity_type] = self._normalize_governorate(value)
            elif entity_type == 'property_type':
                normalized[entity_type] = self._normalize_property_type(value)
            elif entity_type == 'budget':
                normalized[entity_type] = self._normalize_budget(value)
            elif entity_type == 'area':
                normalized[entity_type] = self._normalize_area(value)
            else:
                normalized[entity_type] = value
        
        return normalized
    
    def _normalize_governorate(self, value: str) -> str:
        """Normalize governorate name"""
        if isinstance(value, str):
            for variant, standard in self.governorate_normalizer.items():
                if variant in value or value in variant:
                    return standard
        return value
    
    def _normalize_property_type(self, value: str) -> str:
        """Normalize property type"""
        if isinstance(value, str):
            for variant, standard in self.property_type_normalizer.items():
                if variant in value or value in variant:
                    return standard
        return value
    
    def _normalize_budget(self, value: Any) -> int:
        """Normalize budget to integer"""
        if isinstance(value, (int, float)):
            return int(value)
        elif isinstance(value, str):
            # Try to extract number from string
            match = re.search(r'\d+', value)
            if match:
                return int(match.group(1))
        return 0
    
    def _normalize_area(self, value: Any) -> int:
        """Normalize area to integer"""
        if isinstance(value, (int, float)):
            return int(value)
        elif isinstance(value, str):
            # Try to extract number from string
            match = re.search(r'\d+', value)
            if match:
                return int(match.group(1))
        return 0


# Global entity extractor instance
entity_extractor = EntityExtractor()
entity_normalizer = EntityNormalizer()