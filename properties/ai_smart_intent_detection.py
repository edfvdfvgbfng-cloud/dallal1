"""
AI Intent Detection System
Detects user intent from natural language input
Supports Iraqi Arabic dialect and standard Arabic
"""

from typing import Dict, List, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class Intent:
    """Intent types for AI assistant"""
    
    # Property-related intents
    BUY_PROPERTY = "buy_property"
    SELL_PROPERTY = "sell_property"
    RENT_PROPERTY = "rent_property"
    SEARCH_PROPERTY = "search_property"
    
    # Hotel-related intents
    SEARCH_HOTEL = "search_hotel"
    
    # Resort-related intents
    SEARCH_RESORT = "search_resort"
    
    # Job-related intents
    SEARCH_JOB = "search_job"
    POST_JOB = "post_job"
    
    # Service-related intents
    SEARCH_SERVICE = "search_service"
    POST_SERVICE = "post_service"
    
    # Auction-related intents
    SEARCH_AUCTION = "search_auction"
    
    # Broker-related intents
    CONTACT_BROKER = "contact_broker"
    SEARCH_BROKER = "search_broker"
    
    # General intents
    GENERAL_QUESTION = "general_question"
    GREETING = "greeting"
    CLEAR_CONVERSATION = "clear_conversation"
    HELP = "help"


class IntentDetector:
    """
    Detects user intent from natural language input
    Supports multiple patterns and Iraqi Arabic dialect
    """
    
    def __init__(self):
        # Keyword patterns for each intent
        self.patterns = {
            Intent.BUY_PROPERTY: [
                r'أريد.*اشتري',
                r'أريد.*أشتري',
                r'أريد.*شراء',
                r'أدور.*على.*بيت',
                r'أبحث.*عن.*عقار',
                r'وين.*أكو.*بيت',
                r'وين.*أكو.*دار',
                r'وين.*أكو.*عقار',
                r'محتاج.*بيت',
                r'محتاج.*دار',
                r'بدي.*اشتري',
                r'بدي.*أشتري',
                r'اريد.*بيت',
                r'اريد.*دار',
                r'search.*house',
                r'buy.*property',
                r'looking.*for.*property',
                r'want.*buy',
            ],
            Intent.SELL_PROPERTY: [
                r'أريد.*بيع',
                r'أريد.*أبيع',
                r'أريد.*بيع.*عقاري',
                r'أريد.*بيع.*داري',
                r'عندي.*عقار.*للبيع',
                r'عندي.*دار.*للبيع',
                r'بدي.*بيع',
                r'بدي.*أبيع',
                r'اريد.*بيع',
                r'اريد.*أبيع',
                r'sell.*property',
                r'sell.*house',
                r'want.*sell',
            ],
            Intent.RENT_PROPERTY: [
                r'أريد.*إيجار',
                r'أريد.*أكري',
                r'أريد.*أستأجر',
                r'محتاج.*إيجار',
                r'محتاج.*أكري',
                r'بدي.*أكري',
                r'بدي.*إيجار',
                r'rent.*property',
                r'looking.*for.*rent',
            ],
            Intent.SEARCH_HOTEL: [
                r'أريد.*فندق',
                r'أريد.*فنادق',
                r'محتاج.*فندق',
                r'محتاج.*فنادق',
                r'بدي.*فندق',
                r'بدي.*فنادق',
                r'hotel',
                r'فندق.*بغداد',
                r'فندق.*بصرة',
                r'فندق.*أربيل',
            ],
            Intent.SEARCH_RESORT: [
                r'أريد.*منتجع',
                r'أريد.*منتجعات',
                r'محتاج.*منتجع',
                r'محتاج.*منتجعات',
                r'بدي.*منتجع',
                r'بدي.*منتجعات',
                r'resort',
                r'منتجع.*عائلي',
                r'منتجع.*أربيل',
                r'منتجع.*دهوك',
            ],
            Intent.SEARCH_JOB: [
                r'أبحث.*عن.*وظيفة',
                r'أريد.*وظيفة',
                r'محتاج.*شغل',
                r'محتاج.*وظيفة',
                r'بدي.*شغل',
                r'بدي.*وظيفة',
                r'أبحث.*عن.*عمل',
                r'job',
                r'work',
                r'function',
                r'محاسب',
                r'مهندس',
                r'دكتور',
            ],
            Intent.POST_JOB: [
                r'أريد.*نشر.*وظيفة',
                r'أريد.*إعلان.*وظيفة',
                r'عندي.*وظيفة',
                r'بدي.*نشر.*وظيفة',
                r'post.*job',
                r'announce.*job',
            ],
            Intent.SEARCH_SERVICE: [
                r'أريد.*خدمة',
                r'أريد.*كهربائي',
                r'أريد.*سباك',
                r'أريد.*نجار',
                r'أريد.*بناء',
                r'محتاج.*كهربائي',
                r'محتاج.*سباك',
                r'بدي.*كهربائي',
                r'بدي.*سباك',
                r'service',
                r'electrician',
                r'plumber',
            ],
            Intent.POST_SERVICE: [
                r'أريد.*نشر.*خدمة',
                r'أريد.*إعلان.*خدمة',
                r'عندي.*خدمة',
                r'بدي.*نشر.*خدمة',
                r'post.*service',
            ],
            Intent.SEARCH_AUCTION: [
                r'أريد.*مزاد',
                r'أريد.*مزادات',
                r'محتاج.*مزاد',
                r'بدي.*مزاد',
                r'auction',
                r'مزاد.*عقاري',
            ],
            Intent.CONTACT_BROKER: [
                r'أريد.*كلام.*دلال',
                r'أريد.*تواصل.*مع.*دلال',
                r'مراسلة.*الدلال',
                r'contact.*broker',
                r'talk.*broker',
            ],
            Intent.SEARCH_BROKER: [
                r'أبحث.*عن.*دلال',
                r'أريد.*دلال',
                r'محتاج.*دلال',
                r'بدي.*دلال',
                r'search.*broker',
                r'find.*broker',
            ],
            Intent.GREETING: [
                r'مرحبا',
                r'السلام.*عليكم',
                r'صباح.*الخير',
                r'مساء.*الخير',
                r'هلا',
                r'هاي',
                r'hello',
                r'hi',
                r'hey',
            ],
            Intent.CLEAR_CONVERSATION: [
                r'ابدأ.*من.*جديد',
                r'محادثة.*جديدة',
                r'بدء.*جديد',
                r'clear',
                r'reset',
                r'new.*conversation',
            ],
            Intent.HELP: [
                r'مساعدة',
                r'كيف.*أستخدم',
                r'كيف.*أشتري',
                r'كيف.*أبيع',
                r'help',
                r'assist',
            ],
        }
        
        # Property type mapping (Arabic to English)
        self.property_type_mapping = {
            'بيت': 'house',
            'دار': 'house',
            'شقة': 'apartment',
            'فيلا': 'villa',
            'أرض': 'land',
            'محل': 'shop',
            'مبنى': 'building',
            'مجمع': 'complex',
            'مكتب': 'office',
            'home': 'house',
            'house': 'house',
            'apartment': 'apartment',
            'villa': 'villa',
            'land': 'land',
        }
        
        # Location mapping (Iraqi dialect to standard)
        self.location_mapping = {
            'بغداد': 'Baghdad',
            'البصرة': 'Basra',
            'أربيل': 'Erbil',
            'دهوك': 'Duhok',
            'السليمانية': 'Sulaymaniyah',
            'الناصرية': 'Nasiriyah',
            'كربلاء': 'Karbala',
            'النجف': 'Najaf',
            'كirkuk': 'Kirkuk',
            'صلاح الدين': 'Salahaddin',
            'ديالى': 'Diyala',
            'المثنى': 'Muthanna',
            'القادسية': 'Qadisiyyah',
            'واسط': 'Wasit',
            'ميسان': 'Maysan',
            'ذي قار': 'Dhi Qar',
            'بابل': 'Babylon',
        }
        
        # Currency patterns
        self.currency_patterns = {
            r'(\d+)\s*(مليون)': 'million_iqd',
            r'(\d+)\s*(ألف)': 'thousand_iqd',
            r'(\d+)\s*(دولار)': 'usd',
            r'(\d+)\s*(\$)': 'usd',
            r'(\d+)\s*(د\.ع)': 'iqd',
        }
    
    def detect_intent(self, text: str) -> Tuple[str, float]:
        """
        Detect the primary intent from user input
        
        Args:
            text: User input text
            
        Returns:
            Tuple of (intent, confidence_score)
        """
        text = text.lower().strip()
        
        if not text:
            return Intent.GENERAL_QUESTION, 0.0
        
        # Check each intent pattern
        best_intent = Intent.GENERAL_QUESTION
        best_score = 0.0
        
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Calculate confidence based on match strength
                    score = self._calculate_confidence(text, pattern)
                    if score > best_score:
                        best_score = score
                        best_intent = intent
        
        logger.info(f"Detected intent: {best_intent} with confidence: {best_score}")
        return best_intent, best_score
    
    def _calculate_confidence(self, text: str, pattern: str) -> float:
        """
        Calculate confidence score for a pattern match
        Higher score for more specific/longer matches
        """
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return 0.0
        
        # Base score
        score = 0.5
        
        # Increase score for longer matches
        match_length = len(match.group())
        score += min(match_length / len(text), 0.3)
        
        # Increase score for exact matches
        if match.group().lower() == text.lower():
            score += 0.2
        
        return min(score, 1.0)
    
    def extract_property_type(self, text: str) -> Optional[str]:
        """Extract property type from text"""
        text = text.lower()
        for arabic, english in self.property_type_mapping.items():
            if arabic in text:
                return english
        return None
    
    def extract_location(self, text: str) -> Optional[str]:
        """Extract location from text"""
        text = text.lower()
        for arabic, english in self.location_mapping.items():
            if arabic in text:
                return english
        return None
    
    def extract_price(self, text: str) -> Optional[Dict]:
        """
        Extract price information from text
        Returns dict with value and currency
        """
        price_info = None
        
        # Try to match price patterns
        for pattern, currency in self.currency_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                if currency == 'million_iqd':
                    value *= 1_000_000
                elif currency == 'thousand_iqd':
                    value *= 1_000
                
                price_info = {
                    'value': value,
                    'currency': currency if currency != 'million_iqd' and currency != 'thousand_iqd' else 'iqd'
                }
                break
        
        return price_info
    
    def extract_area(self, text: str) -> Optional[int]:
        """Extract area (square meters) from text"""
        # Match patterns like "200 متر", "200م", "200 m²"
        patterns = [
            r'(\d+)\s*(?:متر|م|m²|m2)',
            r'(\d+)\s*(?:square.*meter)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def extract_rooms(self, text: str) -> Optional[int]:
        """Extract number of rooms from text"""
        patterns = [
            r'(\d+)\s*(?:غرفة|غرف|room)',
            r'(\d+)\s*(?:bedroom)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None


# Global instance
intent_detector = IntentDetector()
