"""
NLP Layer - Abstract Interface for NLP Models
Provides a pluggable architecture for different NLP models
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger('properties')


class NLPModel(ABC):
    """Abstract base class for NLP models"""
    
    @abstractmethod
    def detect_intent(self, text: str, context: Optional[Dict] = None) -> Dict:
        """
        Detect user intent from text
        
        Args:
            text: User input text
            context: Conversation context
            
        Returns:
            Dict with intent and confidence score
            {
                "intent": "buy_property",
                "confidence": 0.97,
                "raw_text": text
            }
        """
        pass
    
    @abstractmethod
    def extract_entities(self, text: str, intent: Optional[str] = None) -> Dict:
        """
        Extract entities from text
        
        Args:
            text: User input text
            intent: Detected intent (optional, can help guide extraction)
            
        Returns:
            Dict with extracted entities
            {
                "property_type": "house",
                "governorate": "البصرة",
                "district": "العشار",
                "area": 200,
                "budget": 180000000
            }
        """
        pass
    
    @abstractmethod
    def generate_response(self, context: Dict, action: str, results: Optional[List] = None) -> str:
        """
        Generate natural language response
        
        Args:
            context: Conversation context
            action: Determined action
            results: Search results (optional)
            
        Returns:
            Natural language response string
        """
        pass
    
    @abstractmethod
    def normalize_text(self, text: str) -> str:
        """
        Normalize text (handle spelling, dialect, variations)
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict:
        """
        Get model information
        
        Returns:
            Dict with model details
            {
                "name": "ModelName",
                "version": "1.0",
                "language": "ar",
                "capabilities": ["intent_detection", "entity_extraction"]
            }
        """
        pass


class RuleBasedNLP(NLPModel):
    """
    Rule-based NLP implementation as fallback/initial model
    Can be replaced with ML models later
    """
    
    def __init__(self):
        self.name = "RuleBasedNLP"
        self.version = "1.0"
        self.language = "ar"
        
        # Iraqi dialect normalization mapping
        self.dialect_mapping = {
            'شكد': 'كم',
            'شنو': 'ماذا',
            'أدور': 'أبحث',
            'لكيت': 'وجدت',
            'دار': 'بيت',
            'دلال': 'وسيط عقاري',
            'بلبصرة': 'بالبصرة',
            'بالبصره': 'بالبصرة',
            'بصرة': 'البصرة',
            'مليون': '1000000',
            'مليار': '1000000000',
            'راح': 'ذهب',
            'اتروح': 'أذهب',
            'اكو': 'يوجد',
            'ماكو': 'لا يوجد',
            'زين': 'جيد',
            'عشر': 'نصف',
            'ربع': 'ربع',
            'ثمن': 'ثمن'
        }
        
        # Property type variations
        self.property_type_mapping = {
            'بيت': 'house',
            'دار': 'house',
            'منزل': 'house',
            'شقة': 'apartment',
            'قسيمة': 'plot',
            'أرض': 'land',
            'محل': 'commercial',
            'مخبز': 'bakery',
            'عمارة': 'building'
        }
        
        # Governorate normalization
        self.governorate_mapping = {
            'بغداد': 'بغداد',
            'بالبغداد': 'بغداد',
            'البصرة': 'البصرة',
            'بلبصرة': 'بالبصرة',
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
            'البابل': 'بابل',
            'واسط': 'واسط',
            'بابل': 'بابل',
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
            'ذي قار': 'ذي قار',
            'البصرة': 'البصرة',
            'القادسية': 'القادسية',
            'كركوك': 'كركوك',
            'سليمانية': 'سليمانية',
            'حلبجة': 'سليمانية',
            'ميسان': 'ميسان',
            'العمارة': 'ميسان',
            'المثنى': 'المثنى',
            'السماوة': 'المثنى',
            'ديالى': 'ديالى',
            'بغداد': 'بغداد',
            'بابل': 'بابل',
            'كربلاء': 'كربلاء',
            'النجف': 'النجف',
            'القادسية': 'القادسية',
            'الديوانية': 'الديوانية',
            'واسط': 'واسط',
            'الانبار': 'الانبار',
            'صلاح الدين': 'صلاح الدين',
            'نينوى': 'نينوى',
            'دهوك': 'دهوك',
            'أربيل': 'أربيل',
            'سليمانية': 'سليمانية',
            'كركوك': 'كركوك',
            'ميسان': 'ميسان',
            'المثنى': 'المثنى',
            'ذي قار': 'ذي قار',
            'بابل': 'بابل'
        }
        
        # Intent keywords mapping
        self.intent_keywords = {
            'buy_property': [
                'أريد', 'اشتري', 'شراء', 'أبحث عن', 'أدور على', 'ألقا', 'لي', 'عندي',
                'بيت', 'دار', 'منزل', 'شقة', 'أرض', 'محل', 'عقار'
            ],
            'sell_property': [
                'أبيع', 'بيع', 'عندي', 'أريد أبيع', 'أريد بيع', 'أملك',
                'بيت', 'دار', 'منزل', 'شقة', 'أرض', 'محل', 'عقار'
            ],
            'join_agent': [
                'أريد دلال', 'أصير دلال', 'انضمام دلال', 'تسجيل دلال',
                'أنا دلال', 'وسيط عقاري', 'مكتب عقاري'
            ],
            'find_job': [
                'وظيفة', 'عمل', 'شغل', 'أبحث عن عمل', 'أريد وظيفة',
                'أدور شغل', 'فري لانس', 'فريلانس'
            ],
            'travel': [
                'سفر', 'رحلة', 'أريد أسافر', 'أريد رحلة', 'شركة سفر',
                'وكالة سفر', 'سياحة'
            ],
            'find_hotel': [
                'فندق', 'سكن', 'مكان إقامة', 'غرفة', 'أريد فندق',
                'أبحث عن فندق', 'مبيت'
            ],
            'find_service': [
                'خدمة', 'خدمات', 'أحتاج خدمة', 'أبحث عن خدمة',
                'سباك', 'كهربائي', 'نجار', 'بناء', 'صيانة'
            ],
            'construction': [
                'بناء', 'تعمير', 'أريد أبني', 'أريد بناء', 'مقاول',
                'شركة بناء', 'مقاولات', 'إنشاء'
            ],
            'auction': [
                'مزاد', 'مزادات', 'أريد مزاد', 'أبحث عن مزاد',
                'بيع بالمزاد', 'مناقصة'
            ],
            'find_resort': [
                'منتجع', 'مصيف', 'استراحة', 'قصر', 'فيلا',
                'أريد منتجع', 'أبحث عن منتجع'
            ],
            'find_product': [
                'منتج', 'سلعة', 'أريد منتج', 'أبحث عن منتج',
                'شراء منتج', 'بضاعة'
            ]
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize text using dialect and spelling mappings"""
        normalized = text.lower()
        
        # Apply dialect mapping
        for dialect_word, standard_word in self.dialect_mapping.items():
            normalized = normalized.replace(dialect_word, standard_word)
        
        return normalized
    
    def detect_intent(self, text: str, context: Optional[Dict] = None) -> Dict:
        """Detect intent using keyword matching (rule-based)"""
        normalized_text = self.normalize_text(text)
        
        intent_scores = {}
        
        for intent, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in normalized_text:
                    score += 1
            if score > 0:
                intent_scores[intent] = score
        
        if not intent_scores:
            return {
                "intent": "unknown",
                "confidence": 0.5,
                "raw_text": text
            }
        
        # Get intent with highest score
        best_intent = max(intent_scores, key=intent_scores.get)
        max_score = intent_scores[best_intent]
        
        # Calculate confidence based on keyword matches
        confidence = min(0.95, 0.6 + (max_score * 0.1))
        
        return {
            "intent": best_intent,
            "confidence": confidence,
            "raw_text": text,
            "method": "rule_based"
        }
    
    def extract_entities(self, text: str, intent: Optional[str] = None) -> Dict:
        """Extract entities using pattern matching"""
        normalized_text = self.normalize_text(text)
        entities = {}
        
        # Extract property type
        for arabic_type, english_type in self.property_type_mapping.items():
            if arabic_type in normalized_text:
                entities['property_type'] = english_type
                break
        
        # Extract governorate
        for arabic_gov, standard_gov in self.governorate_mapping.items():
            if arabic_gov in normalized_text:
                entities['governorate'] = standard_gov
                break
        
        # Extract numbers (area, budget)
        import re
        numbers = re.findall(r'\d+', normalized_text)
        if numbers:
            # Try to identify if numbers represent area or budget
            for num in numbers:
                num_int = int(num)
                if num_int < 1000:  # Likely area in square meters
                    if 'area' not in entities:
                        entities['area'] = num_int
                elif num_int > 10000:  # Likely budget
                    if 'budget' not in entities:
                        entities['budget'] = num_int * 1000000  # Convert to full amount
        
        # Handle "مليون" and "مليار"
        if 'مليون' in normalized_text:
            numbers = re.findall(r'\d+', normalized_text)
            if numbers:
                entities['budget'] = int(numbers[0]) * 1000000
        
        if 'مليار' in normalized_text:
            numbers = re.findall(r'\d+', normalized_text)
            if numbers:
                entities['budget'] = int(numbers[0]) * 1000000000
        
        return entities
    
    def generate_response(self, context: Dict, action: str, results: Optional[List] = None) -> str:
        """Generate response based on context and action"""
        intent = context.get('intent', 'unknown')
        entities = context.get('entities', {})
        
        if action == 'ask_missing_info':
            missing_fields = context.get('missing_fields', [])
            if missing_fields:
                field_names = {
                    'governorate': 'المحافظة',
                    'property_type': 'نوع العقار',
                    'budget': 'الميزانية',
                    'area': 'المساحة'
                }
                if missing_fields:
                    return f"حتى أساعدك بشكل أدق، من فضلك أخبرني بـ {field_names.get(missing_fields[0], missing_fields[0])}"
        
        elif action == 'show_results':
            if results and len(results) > 0:
                return f"وجدت {len(results)} نتيجة مطابقة لطلبك. يمكنك مراجعة النتائج أدناه."
            else:
                return "لم أجد نتائج مطابقة لطلبك حالياً. هل تريد توسيع نطاق البحث أو تغيير بعض المعايير؟"
        
        elif action == 'clarify_intent':
            return "حتى أساعدك بشكل أدق، تقصد تريد شراء عقار لو بيع عقار؟"
        
        return "شكراً لك، كيف يمكنني مساعدتك اليوم؟"
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            "name": self.name,
            "version": self.version,
            "language": self.language,
            "capabilities": ["intent_detection", "entity_extraction", "text_normalization"],
            "type": "rule_based",
            "description": "Rule-based NLP model as initial implementation"
        }


class NLPModelManager:
    """Manager for NLP models - allows switching between different models"""
    
    def __init__(self):
        self.current_model = RuleBasedNLP()
        self.models = {
            "rule_based": RuleBasedNLP()
        }
    
    def set_model(self, model_name: str):
        """Switch to a different NLP model"""
        if model_name in self.models:
            self.current_model = self.models[model_name]
            logger.info(f"Switched to NLP model: {model_name}")
        else:
            logger.warning(f"Model {model_name} not found, keeping current model")
    
    def register_model(self, name: str, model: NLPModel):
        """Register a new NLP model"""
        self.models[name] = model
        logger.info(f"Registered new NLP model: {name}")
    
    def get_current_model(self) -> NLPModel:
        """Get the current NLP model"""
        return self.current_model
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return list(self.models.keys())


# Global NLP manager instance
nlp_manager = NLPModelManager()