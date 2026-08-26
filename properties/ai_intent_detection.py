"""
Intent Detection Module
Machine Learning-based intent detection with confidence scoring
"""

import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import re
from django.core.cache import cache

logger = logging.getLogger('properties')


class IntentDetector:
    """
    Intent Detection with confidence scoring and threshold handling
    Supports rule-based and ML-based detection
    """
    
    def __init__(self, confidence_threshold: float = 0.70):
        self.confidence_threshold = confidence_threshold
        self.intent_patterns = self._load_intent_patterns()
        self.intent_statistics = defaultdict(int)
        self.intent_corrections = defaultdict(list)
        
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load intent patterns for rule-based detection"""
        return {
            'buy_property': [
                r'أريد\s+(شراء|أشتري)\s+(بيت|دار|منزل|شقة|أرض|عقار)',
                r'أبحث\s+عن\s+(بيت|دار|منزل|شقة|أرض|عقار)',
                r'أدور\s+على\s+(بيت|دار|منزل|شقة|أرض|عقار)',
                r'لي\s+(بيت|دار|منزل|شقة|أرض|عقار)',
                r'أحتاج\s+(بيت|دار|منزل|شقة|أرض|عقار)',
                r'شراء\s+(عقار|بيت|دار|منزل|شقة|أرض)',
                r'أريد\s+(بيت|دار|منزل|شقة|أرض|عقار)\s+بال',
                r'شوي\s+(بيت|دار|منزل|شقة|أرض|عقار)',
                r'شكو\s+(بيت|دار|منزل|شقة|أرض|عقار)'
            ],
            'sell_property': [
                r'أريد\s+(بيع|أبيع)\s+(بيت|دار|منزل|شقة|أرض|عقار)',
                r'عندي\s+(بيت|دار|منزل|شقة|أرض|عقار)\s+أريد\s+أبيع',
                r'أملك\s+(بيت|دار|منزل|شقة|أرض|عقار)',
                r'بيع\s+(عقار|بيت|دار|منزل|شقة|أرض)',
                r'أبيعه\s+(بيت|دار|منزل|شقة|أرض|عقار)',
                r'عقاري\s+(بيت|دار|منزل|شقة|أرض|عقار)'
            ],
            'join_agent': [
                r'أريد\s+(دلال|أصير\s+دلال|أكون\s+دلال)',
                r'انضمام\s+دلال',
                r'تسجيل\s+دلال',
                r'أنا\s+دلال',
                r'وسيط\s+عقاري',
                r'مكتب\s+عقاري',
                r'أعمل\s+دلال'
            ],
            'find_job': [
                r'أبحث\s+عن\s+(وظيفة|عمل|شغل)',
                r'أريد\s+(وظيفة|عمل|شغل)',
                r'أدور\s+(وظيفة|عمل|شغل)',
                r'فري\s+لانس|فريلانس',
                r'شغل\s+لدي'
            ],
            'travel': [
                r'أريد\s+(سفر|رحلة|أسافر)',
                r'شركة\s+سفر',
                r'وكالة\s+سفر',
                r'سياحة',
                r'رحلة\s+إلى'
            ],
            'find_hotel': [
                r'أبحث\s+عن\s+(فندق|سكن|مكان\s+إقامة|غرفة)',
                r'أريد\s+(فندق|سكن|مكان\s+إقامة|غرفة)',
                r'مبيت',
                r'مكان\s+للسكن'
            ],
            'find_service': [
                r'أحتاج\s+(خدمة|خدمات)',
                r'أبحث\s+عن\s+(خدمة|خدمات)',
                r'(سباك|كهربائي|نجار|بناء|صيانة)',
                r'خدمة\s+(سباكة|كهرباء|نجارة|بناء)'
            ],
            'construction': [
                r'أريد\s+(بناء|تعمير|أبني)',
                r'مقاول',
                r'شركة\s+بناء',
                r'مقاولات',
                r'إنشاء\s+(بيت|دار|منزل)'
            ],
            'auction': [
                r'أريد\s+(مزاد|مزادات)',
                r'أبحث\s+عن\s+(مزاد|مزادات)',
                r'بيع\s+بالمزاد',
                r'مناقصة'
            ],
            'find_resort': [
                r'أبحث\s+عن\s+(منتجع|مصيف|استراحة|قصر|فيلا)',
                r'أريد\s+(منتجع|مصيف|استراحة|قصر|فيلا)',
                r'قضاء\s+عطلة'
            ],
            'find_product': [
                r'أبحث\s+عن\s+(منتج|سلعة|بضاعة)',
                r'أريد\s+(منتج|سلعة|بضاعة)',
                r'شراء\s+(منتج|سلعة|بضاعة)'
            ]
        }
    
    def detect_intent(self, text: str, context: Optional[Dict] = None) -> Dict:
        """
        Detect intent with confidence scoring
        
        Args:
            text: User input text
            context: Conversation context
            
        Returns:
            Dict with intent and confidence
        """
        normalized_text = text.lower().strip()
        
        # Use pattern matching for initial detection
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, normalized_text):
                    score += 1
            if score > 0:
                intent_scores[intent] = score
        
        # Calculate confidence
        if not intent_scores:
            return {
                "intent": "unknown",
                "confidence": 0.3,
                "requires_clarification": True,
                "method": "pattern_matching"
            }
        
        best_intent = max(intent_scores, key=intent_scores.get)
        max_score = intent_scores[best_intent]
        
        # Calculate confidence based on pattern matches
        total_patterns = len(self.intent_patterns[best_intent])
        confidence = min(0.95, 0.5 + (max_score / total_patterns) * 0.45)
        
        # Track intent statistics
        self.intent_statistics[best_intent] += 1
        
        # Check if confidence is below threshold
        requires_clarification = confidence < self.confidence_threshold
        
        return {
            "intent": best_intent,
            "confidence": confidence,
            "requires_clarification": requires_clarification,
            "threshold": self.confidence_threshold,
            "method": "pattern_matching",
            "all_scores": intent_scores
        }
    
    def record_correction(self, predicted_intent: str, correct_intent: str, text: str):
        """
        Record intent correction for learning
        
        Args:
            predicted_intent: The originally predicted intent
            correct_intent: The correct intent as specified by user
            text: The original user text
        """
        self.intent_corrections[predicted_intent].append({
            "correct_intent": correct_intent,
            "text": text,
            "timestamp": None  # Would add timestamp
        })
        
        logger.info(f"Recorded intent correction: {predicted_intent} -> {correct_intent}")
    
    def get_intent_statistics(self) -> Dict:
        """Get intent detection statistics"""
        return {
            "total_intents": sum(self.intent_statistics.values()),
            "intent_distribution": dict(self.intent_statistics),
            "total_corrections": sum(len(corrections) for corrections in self.intent_corrections.values()),
            "correction_distribution": {
                intent: len(corrections) 
                for intent, corrections in self.intent_corrections.items()
            }
        }
    
    def set_confidence_threshold(self, threshold: float):
        """Set confidence threshold for intent detection"""
        if 0.0 <= threshold <= 1.0:
            self.confidence_threshold = threshold
            logger.info(f"Updated confidence threshold to {threshold}")
        else:
            logger.warning(f"Invalid threshold: {threshold}. Must be between 0.0 and 1.0")
    
    def get_suggested_clarification(self, detected_intent: str, confidence: float) -> str:
        """
        Get suggested clarification question based on detected intent and confidence
        
        Args:
            detected_intent: The detected intent
            confidence: The confidence score
            
        Returns:
            Clarification question string
        """
        if detected_intent == "buy_property":
            return "حتى أساعدك بشكل أدق، تقصد تريد شراء عقار لو بيع عقار؟"
        elif detected_intent == "sell_property":
            return "حتى أساعدك بشكل أدق، تقصد تريد بيع عقار لو شراء عقار؟"
        elif detected_intent == "find_job":
            return "حتى أساعدك بشكل أدق، تقصد تبحث عن وظيفة لو تريد توظيف أشخاص؟"
        else:
            return "حتى أساعدك بشكل أدق، هل يمكنك توضيح طلبك أكثر؟"


class IntentFeatureExtractor:
    """
    Feature extraction for ML-based intent detection
    Prepares text data for machine learning models
    """
    
    def __init__(self):
        self.arabic_stopwords = self._load_arabic_stopwords()
        self.feature_weights = {
            'verbs': 2.0,
            'nouns': 1.5,
            'numbers': 1.0,
            'locations': 2.5
        }
    
    def _load_arabic_stopwords(self) -> set:
        """Load Arabic stopwords"""
        return {
            'في', 'من', 'على', 'إلى', 'عن', 'مع', 'هذا', 'هذه', 'ذلك',
            'تلك', 'هو', 'هي', 'هم', 'هن', 'أنا', 'أنت', 'أنتما', 'أنتم',
            'أنتن', 'نحن', 'كان', 'كانت', 'كانوا', 'كنت', 'كن', 'سيكون',
            'ليس', 'ليست', 'ليسوا', 'ما', 'لا', 'نعم', 'كلا', 'قد', 'ربما',
            'كيف', 'كم', 'أين', 'متى', 'لماذا', 'لما', 'ماذا', 'شكد', 'شنو'
        }
    
    def extract_features(self, text: str) -> Dict:
        """
        Extract features from text for ML models
        
        Args:
            text: Input text
            
        Returns:
            Feature dictionary
        """
        features = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'has_number': bool(re.search(r'\d', text)),
            'has_location': self._has_location(text),
            'verb_count': self._count_verbs(text),
            'noun_count': self._count_nouns(text),
            'normalized_text': self._normalize_text(text)
        }
        
        return features
    
    def _has_location(self, text: str) -> bool:
        """Check if text contains location indicators"""
        location_indicators = ['في', 'بـ', 'في', 'إلى', 'محافظة', 'منطقة', 'حي']
        return any(indicator in text for indicator in location_indicators)
    
    def _count_verbs(self, text: str) -> int:
        """Count verbs in text (simplified for Arabic)"""
        verb_indicators = ['أريد', 'أبحث', 'أدور', 'لي', 'عندي', 'أملك', 'أحتاج', 'أبيع', 'أشتري']
        return sum(1 for indicator in verb_indicators if indicator in text)
    
    def _count_nouns(self, text: str) -> int:
        """Count nouns in text (simplified for Arabic)"""
        noun_indicators = ['بيت', 'دار', 'منزل', 'شقة', 'أرض', 'عقار', 'وظيفة', 'عمل', 'فندق', 'خدمة']
        return sum(1 for indicator in noun_indicators if indicator in text)
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for feature extraction"""
        normalized = text.lower()
        # Remove stopwords
        words = normalized.split()
        filtered_words = [word for word in words if word not in self.arabic_stopwords]
        return ' '.join(filtered_words)
    
    def prepare_training_data(self, texts: List[str], labels: List[str]) -> Tuple[List[Dict], List[str]]:
        """
        Prepare training data for ML models
        
        Args:
            texts: List of training texts
            labels: List of corresponding intent labels
            
        Returns:
            Tuple of (features, labels)
        """
        features = [self.extract_features(text) for text in texts]
        return features, labels


# Global intent detector instance
intent_detector = IntentDetector(confidence_threshold=0.70)
feature_extractor = IntentFeatureExtractor()