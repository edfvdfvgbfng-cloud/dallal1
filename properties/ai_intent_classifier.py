"""
Intent Classification System
Classifies user intent for better matching and recommendations
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime

from .ai_market_intelligence import BuyerIntentType, SellerIntentType

logger = logging.getLogger(__name__)


class IntentCategory(Enum):
    """High-level intent categories"""
    BUY = "buy"
    SELL = "sell"
    RENT = "rent"
    SEARCH = "search"
    COMPARE = "compare"
    ANALYZE = "analyze"
    INQUIRE = "inquire"
    HELP = "help"


@dataclass
class IntentClassification:
    """Result of intent classification"""
    category: IntentCategory
    buyer_intent: Optional[BuyerIntentType] = None
    seller_intent: Optional[SellerIntentType] = None
    confidence: float = 0.0
    extracted_params: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'category': self.category.value,
            'buyer_intent': self.buyer_intent.value if self.buyer_intent else None,
            'seller_intent': self.seller_intent.value if self.seller_intent else None,
            'confidence': self.confidence,
            'extracted_params': self.extracted_params,
            'metadata': self.metadata
        }


class IntentClassifier:
    """
    Classifies user intent from natural language
    Extracts buyer/seller intent and parameters
    """
    
    def __init__(self):
        self.classification_history: List[Dict] = []
    
    def classify_intent(self, user_input: str, context: Dict = None) -> IntentClassification:
        """
        Classify user intent from input
        
        Args:
            user_input: User's natural language input
            context: Conversation context
            
        Returns:
            IntentClassification result
        """
        try:
            user_input_lower = user_input.lower()
            
            # Determine category
            category = self._classify_category(user_input_lower)
            
            # Determine specific intent
            buyer_intent = None
            seller_intent = None
            
            if category == IntentCategory.BUY:
                buyer_intent = self._classify_buyer_intent(user_input_lower)
            elif category == IntentCategory.SELL:
                seller_intent = self._classify_seller_intent(user_input_lower)
            
            # Extract parameters
            extracted_params = self._extract_parameters(user_input_lower)
            
            # Calculate confidence
            confidence = self._calculate_confidence(category, buyer_intent, seller_intent, extracted_params)
            
            classification = IntentClassification(
                category=category,
                buyer_intent=buyer_intent,
                seller_intent=seller_intent,
                confidence=confidence,
                extracted_params=extracted_params,
                metadata={'context': context}
            )
            
            # Log classification
            self.classification_history.append({
                'timestamp': datetime.now().isoformat(),
                'input': user_input,
                'category': category.value,
                'buyer_intent': buyer_intent.value if buyer_intent else None,
                'seller_intent': seller_intent.value if seller_intent else None,
                'confidence': confidence
            })
            
            logger.info(f"Classified intent: {category.value} (confidence: {confidence})")
            return classification
            
        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            return IntentClassification(
                category=IntentCategory.HELP,
                confidence=0.0
            )
    
    def _classify_category(self, user_input: str) -> IntentCategory:
        """Classify high-level intent category"""
        # Buy keywords
        buy_keywords = ['أريد', 'أبحث عن', 'شراء', 'شتري', 'أبي', 'منزل', 'بيت', 'شقة', 'أرض']
        if any(kw in user_input for kw in buy_keywords):
            return IntentCategory.BUY
        
        # Sell keywords
        sell_keywords = ['بيع', 'أبيع', 'نشر', 'أريد أبيع', 'عندي عقار', 'عندي منزل']
        if any(kw in user_input for kw in sell_keywords):
            return IntentCategory.SELL
        
        # Rent keywords
        rent_keywords = ['إيجار', 'أجار', 'استأجر', 'كرائي']
        if any(kw in user_input for kw in rent_keywords):
            return IntentCategory.RENT
        
        # Compare keywords
        compare_keywords = ['قارن', 'مقارنة', 'الفرق بين', 'أحسن']
        if any(kw in user_input for kw in compare_keywords):
            return IntentCategory.COMPARE
        
        # Analyze keywords
        analyze_keywords = ['سعر', 'متوسط', 'أسعار', 'إحصاء', 'معلومات السوق', 'وين أرخص', 'أغلى']
        if any(kw in user_input for kw in analyze_keywords):
            return IntentCategory.ANALYZE
        
        # Search keywords
        search_keywords = ['دورلي', 'ابحث', 'أطلع', 'عرض']
        if any(kw in user_input for kw in search_keywords):
            return IntentCategory.SEARCH
        
        # Default to help
        return IntentCategory.HELP
    
    def _classify_buyer_intent(self, user_input: str) -> Optional[BuyerIntentType]:
        """Classify buyer intent type"""
        # First home
        if any(kw in user_input for kw in ['أول منزل', 'أول بيت', 'بداية', 'زواج']):
            return BuyerIntentType.FIRST_HOME
        
        # Family home
        if any(kw in user_input for kw in ['عائلة', 'عائلي', 'أولاد', 'أطفال']):
            return BuyerIntentType.FAMILY_HOME
        
        # Investment
        if any(kw in user_input for kw in ['استثمار', 'استثماري', 'تجارة', 'ربح']):
            return BuyerIntentType.INVESTMENT
        
        # Commercial
        if any(kw in user_input for kw in ['تجاري', 'محل', 'مكتب', 'شركة']):
            return BuyerIntentType.COMMERCIAL
        
        # Land
        if any(kw in user_input for kw in ['أرض', 'قطعة', 'بناء']):
            return BuyerIntentType.LAND_FOR_BUILDING
        
        # Vacation
        if any(kw in user_input for kw in ['استجمام', 'قضاء', 'عطلة']):
            return BuyerIntentType.VACATION
        
        # Default to family home
        return BuyerIntentType.FAMILY_HOME
    
    def _classify_seller_intent(self, user_input: str) -> Optional[SellerIntentType]:
        """Classify seller intent type"""
        # Quick sale
        if any(kw in user_input for kw in ['بسرعة', 'عاجل', 'سريع', 'أبي أبيعه']):
            return SellerIntentType.QUICK_SALE
        
        # Best price
        if any(kw in user_input for kw in ['أفضل سعر', 'أعلى سعر', 'أكبر سعر']):
            return SellerIntentType.BEST_PRICE
        
        # Agent assistance
        if any(kw in user_input for kw in ['دلال', 'وكيل', 'حابة دلال']):
            return SellerIntentType.AGENT_ASSISTANCE
        
        # Direct sale
        if any(kw in user_input for kw in ['مباشر', 'بدون دلال', 'أنا أبيع']):
            return SellerIntentType.DIRECT_SALE
        
        # Rental
        if any(kw in user_input for kw in ['أجار', 'كرائي', 'للإيجار']):
            return SellerIntentType.RENTAL
        
        # Default to best price
        return SellerIntentType.BEST_PRICE
    
    def _extract_parameters(self, user_input: str) -> Dict:
        """Extract parameters from user input"""
        params = {}
        
        # Price extraction (placeholder)
        import re
        price_match = re.search(r'(\d+(?:,\d+)*)\s*(مليون|م)?', user_input)
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            price = float(price_str)
            if 'مليون' in price_match.group(2) or 'م' in price_match.group(2):
                price *= 1_000_000
            params['price'] = price
        
        # Location extraction (placeholder)
        governorates = ['البصرة', 'بغداد', 'بابل', 'نجف', 'كربلاء', 'المثنى', 'الديوانية', 'ذي قار', 'ميسان', 'واسط']
        for gov in governorates:
            if gov in user_input:
                params['governorate'] = gov
                break
        
        # Property type extraction
        property_types = ['بيت', 'منزل', 'شقة', 'أرض', 'محل', 'مكتب', 'فيلا']
        for prop_type in property_types:
            if prop_type in user_input:
                params['property_type'] = prop_type
                break
        
        return params
    
    def _calculate_confidence(self,
                            category: IntentCategory,
                            buyer_intent: Optional[BuyerIntentType],
                            seller_intent: Optional[SellerIntentType],
                            params: Dict) -> float:
        """Calculate confidence in classification"""
        confidence = 0.5
        
        # Boost confidence if specific intent is identified
        if buyer_intent or seller_intent:
            confidence += 0.3
        
        # Boost confidence if parameters are extracted
        if params:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def get_classification_statistics(self) -> Dict:
        """Get statistics of classifications"""
        category_counts = {}
        
        for cls in self.classification_history:
            cat = cls['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        return {
            'total_classifications': len(self.classification_history),
            'category_counts': category_counts,
            'average_confidence': sum(c['confidence'] for c in self.classification_history) / len(self.classification_history) if self.classification_history else 0
        }


# Global instance
intent_classifier = IntentClassifier()