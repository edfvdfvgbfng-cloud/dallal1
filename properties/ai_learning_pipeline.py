"""
AI Learning Pipeline - Data Collection, Processing, and Training Preparation
Handles the complete pipeline from user conversations to training data
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re
import json
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q, Count
from django.utils import timezone

from .ai_training_models import (
    TrainingExample, UserFeedback, UnknownQuery, 
    ModelVersion, ModelEvaluation, SearchAnalytics,
    ConversationLog, KnowledgeBaseEntry, ToolUsageLog
)
from .ai_arabic_normalizer import arabic_normalizer
from .ai_intent_detection import intent_detector
from .ai_entity_extraction import entity_extractor
from .ai_context_engine import context_manager
from .ai_agent_tools import tool_registry
from .ai_voice_provider import voice_analytics

logger = logging.getLogger('properties')


class MoneyParser:
    """Parse Arabic money expressions into standardized format"""
    
    # Arabic number words
    ARABIC_NUMBERS = {
        'صفر': 0, 'واحد': 1, 'اثنان': 2, 'ثلاثة': 3, 'أربعة': 4,
        'خمسة': 5, 'ستة': 6, 'سبعة': 7, 'ثمانية': 8, 'تسعة': 9,
        'عشرة': 10, 'عشر': 10, 'أحد عشر': 11, 'أحد عشر': 11,
        'اثنا عشر': 12, 'اثنا عشر': 12, 'ثلاثة عشر': 13,
        'أربعة عشر': 14, 'خمسة عشر': 15, 'ستة عشر': 16,
        'سبعة عشر': 17, 'ثمانية عشر': 18, 'تسعة عشر': 19,
        'عشرون': 20, 'ثلاثون': 30, 'أربعون': 40, 'خمسون': 50,
        'ستون': 60, 'سبعون': 70, 'ثمانون': 80, 'تسعون': 90,
        'مئة': 100, 'مائة': 100, 'مئتان': 200, 'مئتين': 200,
        'ثلاثمئة': 300, 'ثلاثمائة': 300, 'أربعمئة': 400,
        'أربعمائة': 400, 'خمسمئة': 500, 'خمسمائة': 500,
        'ستمئة': 600, 'ستمائة': 600, 'سبعمئة': 700,
        'سبعمائة': 700, 'ثمانمئة': 800, 'ثمانمائة': 800,
        'تسعمئة': 900, 'تسعمائة': 900, 'ألف': 1000,
        'ألفين': 2000, 'مليون': 1000000, 'مليونين': 2000000,
        'مليار': 1000000000, 'مليارين': 2000000000
    }
    
    # Iraqi dialect variations
    IRAQI_VARIATIONS = {
        'مية': 100, 'ميتين': 200, 'ثلاثمية': 300, 'اربعمية': 400,
        'خمسمية': 500, 'ستمية': 600, 'سبعمية': 700, 'ثمانمية': 800,
        'تسعمية': 900, 'نص': 0.5, 'ونص': 0.5, 'ونصه': 0.5
    }
    
    def __init__(self):
        self.currency_map = {
            'د.ع': 'IQD', 'دينار': 'IQD', 'دولار': 'USD', '$': 'USD',
            'يورو': 'EUR', 'جنيه': 'EGP', 'ريال': 'SAR'
        }
    
    def parse_money_expression(self, text: str) -> Dict[str, Any]:
        """
        Parse Arabic money expression
        
        Args:
            text: Money expression like "150 مليون", "حدود 150 مليون"
            
        Returns:
            Parsed money data with min, max, currency
        """
        try:
            result = {
                'min': None,
                'max': None,
                'currency': 'IQD',
                'original': text
            }
            
            # Detect currency
            currency = 'IQD'  # Default
            for arabic, iso in self.currency_map.items():
                if arabic in text:
                    currency = iso
                    break
            result['currency'] = currency
            
            # Extract numbers
            text_clean = text.replace(',', '').replace(' ', '')
            
            # Check for range indicators
            is_less_than = any(word in text for word in ['أقل من', 'اقل من', 'حتى', 'لغاية'])
            is_more_than = any(word in text for word in ['أكثر من', 'اكثر من', 'فوق'])
            is_approximate = any(word in text for word in ['حدود', 'تقريبا', 'حول', 'حوالي'])
            
            # Parse the number
            number = self._parse_arabic_number(text)
            
            if number is None:
                # Try to extract digits directly
                digits = re.findall(r'\d+', text)
                if digits:
                    number = int(digits[0])
            
            if number is not None:
                if is_less_than:
                    result['max'] = number
                elif is_more_than:
                    result['min'] = number
                else:
                    # For approximate, give a range
                    if is_approximate:
                        margin = number * 0.1  # 10% margin
                        result['min'] = number - margin
                        result['max'] = number + margin
                    else:
                        result['max'] = number
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing money expression: {str(e)}")
            return {'min': None, 'max': None, 'currency': 'IQD', 'original': text}
    
    def _parse_arabic_number(self, text: str) -> Optional[float]:
        """Parse Arabic number words to digits"""
        try:
            # First check for direct digits
            digits = re.findall(r'\d+', text)
            if digits:
                return float(digits[0])
            
            # Then try Arabic number words
            number = 0
            remaining_text = text
            
            # Check for large units first
            if 'مليار' in text:
                billion_match = re.search(r'(\d+)?\s*مليار', text)
                if billion_match:
                    billions = float(billion_match.group(1)) if billion_match.group(1) else 1
                    number += billions * 1000000000
                    remaining_text = remaining_text.replace(billion_match.group(0), '')
            
            if 'مليون' in remaining_text:
                million_match = re.search(r'(\d+)?\s*مليون', remaining_text)
                if million_match:
                    millions = float(million_match.group(1)) if million_match.group(1) else 1
                    number += millions * 1000000
                    remaining_text = remaining_text.replace(million_match.group(0), '')
            
            if 'ألف' in remaining_text:
                thousand_match = re.search(r'(\d+)?\s*ألف', remaining_text)
                if thousand_match:
                    thousands = float(thousand_match.group(1)) if thousand_match.group(1) else 1
                    number += thousands * 1000
                    remaining_text = remaining_text.replace(thousand_match.group(0), '')
            
            # Handle number words
            for word, value in {**self.ARABIC_NUMBERS, **self.IRAQI_VARIATIONS}.items():
                if word in remaining_text:
                    number += value
                    remaining_text = remaining_text.replace(word, '')
            
            return number if number > 0 else None
            
        except Exception as e:
            logger.error(f"Error parsing Arabic number: {str(e)}")
            return None


class TimeDateParser:
    """Parse Arabic time and date expressions"""
    
    # Arabic time expressions
    TIME_EXPRESSIONS = {
        'باچر': 1, 'بكرا': 1, 'غدا': 1, 'الغد': 1,
        'بعد باچر': 2, 'بعد بكرا': 2, 'بعد غدا': 2,
        'الأسبوع الجاي': 7, 'الاسبوع الجاي': 7, 'أسبوع جاي': 7,
        'هذا الشهر': 30, 'هذا الشهر': 30,
        'بداية الشهر الجاي': 30, 'بداية الشهر القادم': 30,
        'بعد أسبوع': 7, 'بعد شهر': 30,
        'الشهر الجاي': 30, 'الشهر القادم': 30,
        'السنة الجاية': 365, 'السنة القادمة': 365
    }
    
    def __init__(self):
        self.timezone = timezone.now().tzinfo
    
    def parse_time_expression(self, text: str) -> Dict[str, Any]:
        """
        Parse Arabic time expression
        
        Args:
            text: Time expression like "باچر", "بعد أسبوع"
            
        Returns:
            Parsed time data with start_date, end_date
        """
        try:
            result = {
                'start_date': None,
                'end_date': None,
                'days_offset': None,
                'original': text
            }
            
            now = timezone.now()
            
            # Check for time expressions
            for expression, days in self.TIME_EXPRESSIONS.items():
                if expression in text:
                    result['days_offset'] = days
                    result['start_date'] = now + timedelta(days=days)
                    result['end_date'] = result['start_date'] + timedelta(days=1)
                    return result
            
            # Check for specific dates
            date_pattern = r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})'
            date_match = re.search(date_pattern, text)
            if date_match:
                day, month, year = date_match.groups()
                try:
                    if len(year) == 2:
                        year = f"20{year}"
                    result['start_date'] = datetime(int(year), int(month), int(day))
                    result['end_date'] = result['start_date'] + timedelta(days=1)
                except ValueError:
                    pass
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing time expression: {str(e)}")
            return {'start_date': None, 'end_date': None, 'days_offset': None, 'original': text}


class EntityNormalizer:
    """Normalize entity values to standard format"""
    
    # Governorate normalization
    GOVERNORATE_MAP = {
        'بغداد': 'Baghdad', 'بغداذ': 'Baghdad', 'بغدادَ': 'Baghdad',
        'البصرة': 'Basra', 'البصره': 'Basra', 'بصرة': 'Basra',
        'الناصرية': 'Nasiriyah', 'ناصرية': 'Nasiriyah', 'الناصره': 'Nasiriyah',
        'ذي قار': 'Dhi Qar', 'ذي قار': 'Dhi Qar',
        'كربلاء': 'Karbala', 'كربلاء': 'Karbala',
        'النجف': 'Najaf', 'نجف': 'Najaf', 'النجف الأشرف': 'Najaf',
        'أربيل': 'Erbil', 'اربيل': 'Erbil', 'هولير': 'Erbil',
        'الموصل': 'Mosul', 'موصل': 'Mosul',
        'الأنبار': 'Anbar', 'انبار': 'Anbar', 'الرمادي': 'Anbar',
        'ديالى': 'Diyala', 'ديالى': 'Diyala', 'بعقوبة': 'Diyala',
        'واسط': 'Wasit', 'واسط': 'Wasit', 'الكوت': 'Wasit',
        'ميسان': 'Maysan', 'ميسان': 'Maysan', 'العمارة': 'Maysan',
        'القادسية': 'Qadisiyyah', 'قادسية': 'Qadisiyyah', 'الديوانية': 'Qadisiyyah',
        'بابل': 'Babil', 'بابل': 'Babil', 'الحلة': 'Babil',
        'صلاح الدين': 'Salahaddin', 'صلاح الدين': 'Salahaddin', 'تكريت': 'Salahaddin',
        'الضليعة': 'Dhi Qar', 'النجف': 'Najaf', 'كربلاء': 'Karbala'
    }
    
    # Property type normalization
    PROPERTY_TYPE_MAP = {
        'بيت': 'house', 'دار': 'house', 'منزل': 'house', 'سكن': 'house',
        'شقة': 'apartment', 'شقة': 'apartment', 'فيلا': 'villa',
        'فيلا': 'villa', 'أرض': 'land', 'ارض': 'land',
        'محل': 'commercial', 'مبنى': 'building', 'عمارة': 'building',
        'دور': 'floor', 'طابق': 'floor'
    }
    
    # Job type normalization
    JOB_TYPE_MAP = {
        'وظيفة': 'job', 'عمل': 'job', 'شغل': 'job',
        'دوام': 'full_time', 'دوام كامل': 'full_time',
        'نص دوام': 'part_time', 'دوام جزئي': 'part_time',
        'عن بعد': 'remote', 'عن بعد': 'remote', 'حر': 'freelance'
    }
    
    def normalize_governorate(self, text: str) -> Optional[str]:
        """Normalize governorate name"""
        for arabic, english in self.GOVERNORATE_MAP.items():
            if arabic in text or text == arabic:
                return english
        return None
    
    def normalize_property_type(self, text: str) -> Optional[str]:
        """Normalize property type"""
        for arabic, english in self.PROPERTY_TYPE_MAP.items():
            if arabic in text or text == arabic:
                return english
        return None
    
    def normalize_job_type(self, text: str) -> Optional[str]:
        """Normalize job type"""
        for arabic, english in self.JOB_TYPE_MAP.items():
            if arabic in text or text == arabic:
                return english
        return None
    
    def normalize_entity(self, entity_type: str, value: str) -> Optional[str]:
        """Normalize entity based on type"""
        normalizers = {
            'governorate': self.normalize_governorate,
            'property_type': self.normalize_property_type,
            'job_type': self.normalize_job_type
        }
        
        normalizer = normalizers.get(entity_type)
        if normalizer:
            return normalizer(value)
        return value


class DataAugmenter:
    """Generate variations of training examples for better model training"""
    
    # Arabic variations for common phrases
    PHRASE_VARIATIONS = {
        'أريد': ['أبغى', 'أبي', 'أكدر', 'أريد أن', 'محتاج', 'بدي'],
        'بيت': ['دار', 'منزل', 'سكن', 'مكان سكن'],
        'أبحث عن': ['أدور على', 'ألتمس', 'أشوف', 'وين ألاقي'],
        'بغداد': ['بغداذ', 'العاصمة', 'بغدادَ'],
        'البصرة': ['البصره', 'البصرة'],
        'شمال': ['شمال', 'جهة الشمال', 'الجهة الشمالية'],
        'جنوب': ['جنوب', 'جهة الجنوب', 'الجهة الجنوبية'],
        'شراء': ['أشتري', 'شراء', 'اقتناء'],
        'بيع': ['أبيع', 'بيع', 'تسويق'],
        'أرخص': ['السعر الأقل', 'اقل سعر', 'الأقل سعراً'],
        'أغلى': ['السعر الأعلى', 'اعلى سعر', 'الأعلى سعراً']
    }
    
    def __init__(self):
        self.arabic_normalizer = arabic_normalizer
    
    def generate_variations(self, text: str, intent: str, entities: Dict, 
                           num_variations: int = 3) -> List[Dict[str, Any]]:
        """
        Generate variations of a training example
        
        Args:
            text: Original text
            intent: Original intent
            entities: Original entities
            num_variations: Number of variations to generate
            
        Returns:
            List of varied training examples
        """
        variations = []
        
        for i in range(num_variations):
            varied_text = self._apply_random_variation(text)
            
            # Ensure the variation is different enough
            if varied_text != text:
                variations.append({
                    'text': varied_text,
                    'normalized_text': self.arabic_normalizer.normalize_text(varied_text),
                    'intent': intent,
                    'entities': entities,
                    'confidence': 0.8,  # Lower confidence for augmented data
                    'source': 'augmented',
                    'dataset_type': 'augmented'
                })
        
        return variations
    
    def _apply_random_variation(self, text: str) -> str:
        """Apply a random variation to text"""
        import random
        
        varied_text = text
        
        # Randomly select a phrase to vary
        for original, variations in self.PHRASE_VARIATIONS.items():
            if original in text and variations:
                # Select a random variation
                selected_variation = random.choice(variations)
                varied_text = varied_text.replace(original, selected_variation, 1)
                break  # Only one variation per call
        
        return varied_text
    
    def generate_iraqi_dialect_variations(self, text: str) -> List[str]:
        """Generate Iraqi dialect variations"""
        iraqi_variations = {
            'أريد': ['أبي', 'أبغى', 'أكدر'],
            'عندي': ['عندي', 'لدي', 'مهم'],
            'شكد': ['شكد', 'كم', 'قدش'],
            'وين': ['وين', 'أين', 'في أي مكان'],
            'ماكو': ['ماكو', 'لا يوجد', 'مافي'],
            'اكو': ['اكو', 'يوجد', 'موجود'],
            'خلي': ['خلي', 'دعني', 'اسمحلي'],
            'حلو': ['حلو', 'جيد', 'ممتاز'],
            'كوم': ['كوم', 'تعال', 'تفضل'],
            'شوف': ['شوف', 'انظر', 'تابع']
        }
        
        variations = [text]
        
        for standard, iraqi_list in iraqi_variations.items():
            if standard in text:
                for iraqi in iraqi_list:
                    varied = text.replace(standard, iraqi, 1)
                    if varied != text:
                        variations.append(varied)
        
        return variations





class DataCollector:
    """
    Collects and processes data from user interactions for learning
    Separates sensitive data from training data
    """
    
    def __init__(self):
        self.arabic_normalizer = arabic_normalizer
        self.intent_detector = intent_detector
        self.entity_extractor = entity_extractor
        self.context_manager = context_manager
        self.money_parser = MoneyParser()
        self.time_parser = TimeDateParser()
        self.entity_normalizer = EntityNormalizer()
        self.data_augmenter = DataAugmenter()
    
    def collect_user_correction(self, conversation_id: str, original_intent: str, 
                              corrected_intent: str, original_entities: Dict, 
                              corrected_entities: Dict, user_message: str,
                              user: Optional[User] = None) -> Dict[str, Any]:
        """
        Collect user corrections for learning
        
        Args:
            conversation_id: Conversation identifier
            original_intent: Originally detected intent
            corrected_intent: User-corrected intent
            original_entities: Originally extracted entities
            corrected_entities: User-corrected entities
            user_message: User's message
            user: Current user (optional)
            
        Returns:
            Correction collection result
        """
        try:
            # Create training example with corrected data
            corrected_example = TrainingExample.objects.create(
                text=user_message,
                normalized_text=self.arabic_normalizer.normalize_text(user_message),
                intent=corrected_intent,
                confidence=1.0,  # High confidence for user corrections
                entities=corrected_entities,
                source='user_correction',
                dataset_type='expert_curated',
                status='approved',
                metadata={
                    'original_intent': original_intent,
                    'original_entities': original_entities,
                    'correction_type': 'intent' if original_intent != corrected_intent else 'entity'
                }
            )
            
            return {
                'success': True,
                'correction_id': corrected_example.id,
                'original_intent': original_intent,
                'corrected_intent': corrected_intent
            }
            
        except Exception as e:
            logger.error(f"Error collecting user correction: {str(e)}")
            return {'success': False, 'error': str(e)}
        self.money_parser = MoneyParser()
        self.time_parser = TimeDateParser()
        self.entity_normalizer = EntityNormalizer()
        self.data_augmenter = DataAugmenter()
    
    def collect_conversation_data(self, conversation_id: str, user: Optional[User] = None) -> Dict[str, Any]:
        """
        Collect complete conversation data for learning
        
        Args:
            conversation_id: Conversation identifier
            user: Current user (optional)
            
        Returns:
            Collected conversation data
        """
        try:
            context = self.context_manager.get_context(conversation_id)
            conversation_state = context.get_complete_context()
            
            # Create conversation log
            conversation_log = ConversationLog.objects.create(
                conversation_id=conversation_id,
                user=user,
                messages=conversation_state.get('messages', []),
                final_intent=conversation_state.get('intent'),
                resolved=conversation_state.get('intent') is not None,
                session_data=conversation_state
            )
            
            return {
                'success': True,
                'conversation_log_id': conversation_log.id,
                'conversation_state': conversation_state
            }
            
        except Exception as e:
            logger.error(f"Error collecting conversation data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def collect_training_example(self, message: str, intent: str, entities: Dict, 
                                 confidence: float, source: str = 'conversation') -> Dict[str, Any]:
        """
        Collect training example from user interaction
        
        Args:
            message: User message
            intent: Detected intent
            entities: Extracted entities
            confidence: Detection confidence
            source: Source of the example
            
        Returns:
            Training example creation result
        """
        try:
            # Normalize text
            normalized_text = self.arabic_normalizer.normalize_text(message)
            
            # Create training example
            example = TrainingExample.objects.create(
                text=message,
                normalized_text=normalized_text,
                intent=intent,
                confidence=confidence,
                entities=entities,
                source=source,
                dataset_type='user_generated'
            )
            
            return {
                'success': True,
                'example_id': example.id,
                'intent': intent,
                'entities': entities
            }
            
        except Exception as e:
            logger.error(f"Error collecting training example: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def collect_user_feedback(self, conversation_id: str, user_message: str, 
                           ai_response: str, feedback_type: str, 
                           detected_intent: str, entities: Dict, 
                           confidence: float, user: Optional[User] = None) -> Dict[str, Any]:
        """
        Collect user feedback for learning
        
        Args:
            conversation_id: Conversation identifier
            user_message: User's message
            ai_response: AI's response
            feedback_type: Type of feedback (positive/negative/neutral)
            detected_intent: Detected intent
            entities: Extracted entities
            confidence: Detection confidence
            user: Current user (optional)
            
        Returns:
            Feedback collection result
        """
        try:
            feedback = UserFeedback.objects.create(
                conversation_id=conversation_id,
                user_message=user_message,
                ai_response=ai_response,
                feedback_type=feedback_type,
                detected_intent=detected_intent,
                detected_entities=entities,
                confidence=confidence,
                user=user
            )
            
            return {
                'success': True,
                'feedback_id': feedback.id,
                'feedback_type': feedback_type
            }
            
        except Exception as e:
            logger.error(f"Error collecting user feedback: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def collect_unknown_query(self, message: str, conversation_id: str, 
                             attempted_intent: str, entities: Dict, 
                             confidence: float) -> Dict[str, Any]:
        """
        Collect unknown/failed queries for learning
        
        Args:
            message: User message
            conversation_id: Conversation identifier
            attempted_intent: Intent that was attempted
            entities: Entities that were extracted
            confidence: Detection confidence
            
        Returns:
            Unknown query collection result
        """
        try:
            # Check if this query already exists
            existing = UnknownQuery.objects.filter(
                text=message,
                resolved=False
            ).first()
            
            if existing:
                # Increment occurrence count
                existing.occurrence_count += 1
                existing.last_seen = timezone.now()
                existing.save()
                return {
                    'success': True,
                    'query_id': existing.id,
                    'updated': True
                }
            
            # Create new unknown query
            unknown_query = UnknownQuery.objects.create(
                text=message,
                conversation_id=conversation_id,
                attempted_intent=attempted_intent,
                attempted_entities=entities,
                confidence=confidence,
                priority=1  # Default priority
            )
            
            return {
                'success': True,
                'query_id': unknown_query.id,
                'updated': False
            }
            
        except Exception as e:
            logger.error(f"Error collecting unknown query: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def collect_search_analytics(self, conversation_id: str, query: str, 
                                detected_intent: str, entities: Dict, 
                                confidence: float, search_params: Dict, 
                                results: List, execution_time: float,
                                user: Optional[User] = None) -> Dict[str, Any]:
        """
        Collect search analytics for learning user preferences
        
        Args:
            conversation_id: Conversation identifier
            query: Search query
            detected_intent: Detected intent
            entities: Extracted entities
            confidence: Detection confidence
            search_params: Search parameters used
            results: Search results
            execution_time: Search execution time
            user: Current user (optional)
            
        Returns:
            Search analytics collection result
        """
        try:
            # Normalize query
            normalized_query = self.arabic_normalizer.normalize_text(query)
            
            analytics = SearchAnalytics.objects.create(
                conversation_id=conversation_id,
                query=query,
                normalized_query=normalized_query,
                detected_intent=detected_intent,
                detected_entities=entities,
                confidence=confidence,
                search_params=search_params,
                results_count=len(results),
                results_shown=results[:10],  # Store first 10 results
                search_duration_ms=execution_time,
                user=user
            )
            
            return {
                'success': True,
                'analytics_id': analytics.id,
                'results_count': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error collecting search analytics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def record_user_correction(self, conversation_id: str, original_intent: str, 
                             corrected_intent: str, original_entities: Dict, 
                             corrected_entities: Dict, message: str) -> Dict[str, Any]:
        """
        Record user correction for learning
        
        Args:
            conversation_id: Conversation identifier
            original_intent: Originally predicted intent
            corrected_intent: Correct intent specified by user
            original_entities: Originally extracted entities
            corrected_entities: Correct entities specified by user
            message: Original user message
            
        Returns:
            Correction recording result
        """
        try:
            # Create training example with source as correction
            example = TrainingExample.objects.create(
                text=message,
                normalized_text=self.arabic_normalizer.normalize_text(message),
                intent=corrected_intent,
                confidence=1.0,  # User correction is high confidence
                entities=corrected_entities,
                source='user_correction',
                dataset_type='expert_curated',  # User corrections are like expert labels
                status='approved',  # Auto-approve user corrections
                original_message=message
            )
            
            return {
                'success': True,
                'example_id': example.id,
                'original_intent': original_intent,
                'corrected_intent': corrected_intent
            }
            
        except Exception as e:
            logger.error(f"Error recording user correction: {str(e)}")
            return {'success': False, 'error': str(e)}


class DataAugmentor:
    """
    Data augmentation for generating variations of training examples
    Creates synthetic examples to improve model robustness
    """
    
    def __init__(self):
        self.arabic_normalizer = arabic_normalizer
        self.augmentation_methods = {
            'dialect_variation': self._dialect_variation,
            'word_reordering': self._word_reordering,
            'synonym_replacement': self._synonym_replacement,
            'noise_addition': self._noise_addition
        }
    
    def augment_text(self, text: str, intent: str, entities: Dict, 
                   method: str = 'dialect_variation') -> List[Dict[str, Any]]:
        """
        Augment training text with specified method
        
        Args:
            text: Original text
            intent: Original intent
            entities: Original entities
            method: Augmentation method
            
        Returns:
            List of augmented examples
        """
        if method not in self.augmentation_methods:
            logger.warning(f"Unknown augmentation method: {method}")
            return []
        
        augmenter = self.augmentation_methods[method]
        augmented_texts = augmenter(text, intent, entities)
        
        return augmented_texts
    
    def _dialect_variation(self, text: str, intent: str, entities: Dict) -> List[Dict[str, Any]]:
        """Generate dialect variations of text"""
        variations = []
        
        # Iraqi dialect variations
        dialect_replacements = {
            'أريد': ['أبغى', 'نيب'],
            'أبحث عن': ['أدور على', 'لكيت'],
            'في': ['بـ', 'بال'],
            'بيت': ['دار', 'منزل'],
            'شقة': ['شقة سكنية'],
            'كم': ['شكد', 'شوخ']
        }
        
        for original, replacements in dialect_replacements.items():
            if original in text:
                for replacement in replacements:
                    if replacement not in text:
                        augmented = text.replace(original, replacement)
                        if augmented != text:
                            variations.append({
                                'text': augmented,
                                'intent': intent,
                                'entities': entities,
                                'is_augmented': True,
                                'augmentation_method': 'dialect_variation',
                                'parent_text': text
                            })
        
        return variations
    
    def _word_reordering(self, text: str, intent: str, entities: Dict) -> List[Dict[str, Any]]:
        """Generate word order variations"""
        variations = []
        
        words = text.split()
        if len(words) < 3:
            return variations  # Too short for meaningful reordering
        
        # Simple reordering - swap adjacent words
        for i in range(len(words) - 1):
            reordered = words.copy()
            reordered[i], reordered[i+1] = reordered[i+1], reordered[i]
            reordered_text = ' '.join(reordered)
            
            if reordered_text != text:
                variations.append({
                    'text': reordered_text,
                    'intent': intent,
                    'entities': entities,
                    'is_augmented': True,
                    'augmentation_method': 'word_reordering',
                    'parent_text': text
                })
        
        return variations
    
    def _synonym_replacement(self, text: str, intent: str, entities: Dict) -> List[Dict[str, Any]]:
        """Generate synonym variations"""
        variations = []
        
        # Synonyms for common words
        synonyms = {
            'بيت': ['دار', 'منزل', 'سكن'],
            'أريد': ['أبحث عن', 'أحتاج', 'نيب'],
            'البصرة': ['بصرة', 'البصره'],
            'بغداد': ['بغداد', 'بغداد'],
            'مليون': ['مليون', 'مئة ألف']
        }
        
        for original, replacement_list in synonyms.items():
            if original in text:
                for replacement in replacement_list:
                    if replacement not in text:
                        augmented = text.replace(original, replacement)
                        if augmented != text:
                            variations.append({
                                'text': augmented,
                                'intent': intent,
                                'entities': entities,
                                'is_augmented': True,
                                'augmentation_method': 'synonym_replacement',
                                'parent_text': text
                            })
        
        return variations
    
    def _noise_addition(self, text: str, intent: str, entities: Dict) -> List[Dict[str, Any]]:
        """Add minimal noise to text (e.g., extra spacing)"""
        variations = []
        
        # Add extra spaces in random places
        words = text.split()
        if len(words) > 2:
            for i in range(1, len(words)):
                noisy_words = words.copy()
                noisy_words.insert(i, ' ')  # Add extra space
                noisy_text = ' '.join(noisy_words)
                
                if noisy_text != text:
                    variations.append({
                        'text': noisy_text,
                        'intent': intent,
                        'entities': entities,
                        'is_augmented': True,
                        'augmentation_method': 'noise_addition',
                        'parent_text': text
                    })
        
        return variations


class DataAnonymizer:
    """
    Anonymizes sensitive data before using for training
    Removes or masks personal identifiers
    """
    
    def __init__(self):
        self.sensitive_patterns = {
            'phone': r'\b\d{7,15}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'address': r'\b\d+\s+\w+\s+\w+',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{16}\b',
            'personal_id': r'\b\d{10,20}\b'
        }
    
    def anonymize_text(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Anonymize sensitive information from text
        
        Args:
            text: Text to anonymize
            
        Returns:
            Tuple of (anonymized_text, redacted_info)
        """
        anonymized = text
        redacted_info = {}
        
        for data_type, pattern in self.sensitive_patterns.items():
            matches = re.finditer(pattern, anonymized)
            for i, match in enumerate(matches):
                placeholder = f"[{data_type.upper()}_{i}]"
                anonymized = anonymized.replace(match.group(), placeholder)
                redacted_info[placeholder] = match.group()
        
        return anonymized, redacted_info
    
    def anonymize_entities(self, entities: Dict) -> Dict[str, Any]:
        """
        Anonymize sensitive entity values
        
        Args:
            entities: Dictionary of entities
            
        Returns:
            Anonymized entities
        """
        anonymized = {}
        
        for key, value in entities.items():
            if isinstance(value, str):
                # Check if it looks like sensitive data
                if self._is_sensitive_data(value):
                    anonymized[key] = "[REDACTED]"
                else:
                    anonymized[key] = value
            else:
                anonymized[key] = value
        
        return anonymized
    
    def _is_sensitive_data(self, text: str) -> bool:
        """Check if text contains sensitive information"""
        for pattern in self.sensitive_patterns.values():
            if re.search(pattern, text):
                return True
        return False


class DatasetManager:
    """
    Manages training datasets, quality control, and export
    """
    
    def __init__(self):
        self.anonymizer = DataAnonymizer()
        self.augmentor = DataAugmentor()
    
    def create_training_dataset(self, filters: Dict = None, split_ratio: float = 0.8) -> Dict[str, Any]:
        """
        Create training and test datasets from approved examples
        
        Args:
            filters: Filters for selecting examples
            split_ratio: Ratio for train/test split
            
        Returns:
            Dataset statistics
        """
        try:
            query = TrainingExample.objects.filter(status='approved')
            
            # Apply filters if provided
            if filters:
                if 'intent' in filters:
                    query = query.filter(intent=filters['intent'])
                if 'dataset_type' in filters:
                    query = query.filter(dataset_type=filters['dataset_type'])
                if 'min_quality' in filters:
                    query = query.filter(quality_score__gte=filters['min_quality'])
            
            total_count = query.count()
            train_count = int(total_count * split_ratio)
            
            # Mark examples for test set
            test_examples = query.filter(is_test=False)[train_count:]
            test_examples.update(is_test=True)
            
            return {
                'success': True,
                'total_examples': total_count,
                'train_examples': total_count - test_examples.count(),
                'test_examples': test_examples.count(),
                'split_ratio': split_ratio
            }
            
        except Exception as e:
            logger.error(f"Error creating training dataset: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def export_training_data(self, output_format: str = 'json', include_test: bool = False) -> Dict[str, Any]:
        """
        Export training data for external model training
        
        Args:
            output_format: Format for export (json, csv)
            include_test: Whether to include test set
            
        Returns:
            Export result with file path
        """
        try:
            query = TrainingExample.objects.filter(status='approved')
            if not include_test:
                query = query.filter(is_test=False)
            
            examples = query.all()
            
            # Prepare data for export
            export_data = []
            for example in examples:
                # Anonymize sensitive data
                anonymized_text, redacted_info = self.anonymizer.anonymize_text(example.text)
                anonymized_entities = self.anonymizer.anonymize_entities(example.entities)
                
                export_data.append({
                    'text': anonymized_text,
                    'normalized_text': example.normalized_text,
                    'intent': example.intent,
                    'confidence': example.confidence,
                    'entities': anonymized_entities,
                    'dataset_type': example.dataset_type,
                    'source': example.source,
                    'is_test': example.is_test,
                    'quality_score': example.quality_score
                })
            
            # In real implementation, would write to file
            # For now, return data in memory
            
            return {
                'success': True,
                'exported_count': len(export_data),
                'data': export_data,
                'format': output_format
            }
            
        except Exception as e:
            logger.error(f"Error exporting training data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_dataset_statistics(self) -> Dict[str, Any]:
        """Get comprehensive dataset statistics"""
        try:
            total_examples = TrainingExample.objects.count()
            approved_examples = TrainingExample.objects.filter(status='approved').count()
            pending_examples = TrainingExample.objects.filter(status='pending').count()
            test_examples = TrainingExample.objects.filter(is_test=True).count()
            
            # Intent distribution
            intent_dist = TrainingExample.objects.filter(status='approved').values('intent').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Dataset type distribution
            dataset_dist = TrainingExample.objects.values('dataset_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            return {
                'total_examples': total_examples,
                'approved_examples': approved_examples,
                'pending_examples': pending_examples,
                'test_examples': test_examples,
                'train_examples': approved_examples - test_examples,
                'intent_distribution': list(intent_dist),
                'dataset_type_distribution': list(dataset_dist)
            }
            
        except Exception as e:
            logger.error(f"Error getting dataset statistics: {str(e)}")
            return {'error': str(e)}


class ModelTrainer:
    """
    Placeholder for model training functionality
    Designed to be extensible for real ML training
    """
    
    def __init__(self):
        self.training_status = 'idle'
        self.current_model_version = 'model-v1'
    
    def train_intent_classifier(self, training_data: List[Dict], config: Dict = None) -> Dict[str, Any]:
        """
        Train intent classifier (placeholder for future ML implementation)
        
        Args:
            training_data: Training data
            config: Training configuration
            
        Returns:
            Training result
        """
        # This is a placeholder - would contain actual ML training code
        logger.info(f"Intent classifier training requested with {len(training_data)} examples")
        
        return {
            'success': True,
            'message': 'Intent classifier training not yet implemented - using rule-based system',
            'training_data_count': len(training_data),
            'status': 'placeholder'
        }
    
    def train_entity_extractor(self, training_data: List[Dict], config: Dict = None) -> Dict[str, Any]:
        """
        Train entity extractor (placeholder for future ML implementation)
        
        Args:
            training_data: Training data
            config: Training configuration
            
        Returns:
            Training result
        """
        # This is a placeholder - would contain actual ML training code
        logger.info(f"Entity extractor training requested with {len(training_data)} examples")
        
        return {
            'success': True,
            'message': 'Entity extractor training not yet implemented - using rule-based system',
            'training_data_count': len(training_data),
            'status': 'placeholder'
        }
    
    def create_model_version(self, model_type: str, training_config: Dict, 
                          evaluation_results: Dict = None) -> Dict[str, Any]:
        """
        Create a new model version record
        
        Args:
            model_type: Type of model (intent_classifier, entity_extractor, etc.)
            training_config: Training configuration
            evaluation_results: Evaluation results
            
        Returns:
            Model version creation result
        """
        try:
            # Generate version number
            last_version = ModelVersion.objects.filter(model_type=model_type).order_by('-training_date').first()
            if last_version:
                version_num = int(last_version.version.split('-')[-1]) + 1
            else:
                version_num = 1
            
            version = f"{model_type}-v{version_num}"
            
            # Create model version
            model_version = ModelVersion.objects.create(
                version=version,
                model_type=model_type,
                description=f"Training run for {model_type}",
                training_dataset_version='dataset-v1',
                training_date=timezone.now(),
                training_config=training_config,
                status='training'
            )
            
            if evaluation_results:
                model_version.accuracy = evaluation_results.get('accuracy')
                model_version.precision = evaluation_results.get('precision')
                model_version.recall = evaluation_results.get('recall')
                model_version.f1_score = evaluation_results.get('f1_score')
                model_version.evaluation_date = timezone.now()
                model_version.status = 'staging'
            
            return {
                'success': True,
                'model_version': version,
                'model_id': model_version.id
            }
            
        except Exception as e:
            logger.error(f"Error creating model version: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def deploy_model(self, model_version: str, user: User) -> Dict[str, Any]:
        """
        Deploy a model version to production
        
        Args:
            model_version: Version to deploy
            user: User deploying the model
            
        Returns:
            Deployment result
        """
        try:
            model = ModelVersion.objects.get(version=model_version)
            
            # Archive current production model
            current_production = ModelVersion.objects.filter(
                model_type=model.model_type,
                status='production'
            ).first()
            
            if current_production:
                current_production.status = 'archived'
                current_production.save()
            
            # Deploy new model
            model.status = 'production'
            model.deployed_at = timezone.now()
            model.deployed_by = user
            model.save()
            
            return {
                'success': True,
                'deployed_version': model_version,
                'previous_version': current_production.version if current_production else None
            }
            
        except ModelVersion.DoesNotExist:
            return {'success': False, 'error': f'Model version {model_version} not found'}
        except Exception as e:
            logger.error(f"Error deploying model: {str(e)}")
            return {'success': False, 'error': str(e)}


class Evaluator:
    """
    Evaluates model performance and creates comparison reports
    """
    
    def __init__(self):
        self.current_model_version = 'model-v1'
    
    def evaluate_intent_accuracy(self, test_data: List[Dict]) -> Dict[str, Any]:
        """
        Evaluate intent detection accuracy
        
        Args:
            test_data: Test data with known intents
            
        Returns:
            Evaluation results
        """
        correct = 0
        total = len(test_data)
        
        predictions = []
        
        for example in test_data:
            # Use current intent detector
            result = intent_detector.detect_intent(example['text'])
            predicted_intent = result['intent']
            
            predictions.append({
                'text': example['text'],
                'true_intent': example['intent'],
                'predicted_intent': predicted_intent,
                'correct': predicted_intent == example['intent']
            })
            
            if predicted_intent == example['intent']:
                correct += 1
        
        accuracy = correct / total if total > 0 else 0
        
        return {
            'total_tests': total,
            'correct_predictions': correct,
            'accuracy': accuracy,
            'predictions': predictions
        }
    
    def evaluate_entity_accuracy(self, test_data: List[Dict]) -> Dict[str, Any]:
        """
        Evaluate entity extraction accuracy
        
        Args:
            test_data: Test data with known entities
            
        Returns:
            Evaluation results
        """
        correct_entities = 0
        total_entities = 0
        
        for example in test_data:
            # Use current entity extractor
            extracted = entity_extractor.extract_entities(
                example['text'], 
                example.get('intent')
            )
            
            # Compare entities
            true_entities = example.get('entities', {})
            for key, true_value in true_entities.items():
                total_entities += 1
                if extracted.get(key) == true_value:
                    correct_entities += 1
        
        accuracy = correct_entities / total_entities if total_entities > 0 else 0
        
        return {
            'total_entities': total_entities,
            'correct_entities': correct_entities,
            'accuracy': accuracy
        }
    
    def compare_model_versions(self, old_version: str, new_version: str, 
                            test_data: List[Dict]) -> Dict[str, Any]:
        """
        Compare performance between two model versions
        
        Args:
            old_version: Old model version
            new_version: New model version
            test_data: Test data
            
        Returns:
            Comparison results
        """
        # This is a placeholder - would run both models and compare
        logger.info(f"Model comparison requested: {old_version} vs {new_version}")
        
        return {
            'success': True,
            'message': 'Model comparison not yet implemented - using single model',
            'old_version': old_version,
            'new_version': new_version
        }


class DebugMode:
    """Debug mode for developers to see internal AI processing"""
    
    def __init__(self):
        self.enabled = False
        self.debug_data = {}
    
    def enable_debug_mode(self, user: User) -> bool:
        """Enable debug mode for authorized users"""
        if user.is_staff or user.is_superuser:
            self.enabled = True
            return True
        return False
    
    def disable_debug_mode(self):
        """Disable debug mode"""
        self.enabled = False
        self.debug_data = {}
    
    def log_debug_data(self, key: str, data: Any):
        """Log debug data during processing"""
        if self.enabled:
            self.debug_data[key] = data
    
    def get_debug_data(self) -> Dict[str, Any]:
        """Get all debug data"""
        if self.enabled:
            return self.debug_data
        return {}
    
    def format_debug_response(self, user_message: str, ai_response: str, 
                            processing_data: Dict) -> Dict[str, Any]:
        """Format debug response for developer"""
        if not self.enabled:
            return ai_response
        
        return {
            'user_message': user_message,
            'normalized_message': processing_data.get('normalized_message'),
            'intent': processing_data.get('intent'),
            'confidence': processing_data.get('confidence'),
            'entities': processing_data.get('entities'),
            'conversation_state': processing_data.get('conversation_state'),
            'tool_calls': processing_data.get('tool_calls'),
            'api_response': processing_data.get('api_response'),
            'ranking_score': processing_data.get('ranking_score'),
            'final_response': ai_response,
            'latency_ms': processing_data.get('latency_ms'),
            'timestamp': timezone.now().isoformat()
        }


class AIHealthChecker:
    """Monitor AI system health and performance"""
    
    def __init__(self):
        self.last_check = None
        self.health_status = 'unknown'
    
    def check_system_health(self) -> Dict[str, Any]:
        """
        Check overall AI system health
        
        Returns:
            Health status report
        """
        try:
            health_report = {
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'components': {}
            }
            
            # Check database connection
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                health_report['components']['database'] = {
                    'status': 'connected',
                    'latency_ms': self._measure_db_latency()
                }
            except Exception as e:
                health_report['components']['database'] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_report['status'] = 'degraded'
            
            # Check intent detector
            try:
                test_result = intent_detector.detect_intent("اختبار")
                health_report['components']['intent_detector'] = {
                    'status': 'operational',
                    'test_intent': test_result.get('intent'),
                    'confidence': test_result.get('confidence')
                }
            except Exception as e:
                health_report['components']['intent_detector'] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_report['status'] = 'degraded'
            
            # Check entity extractor
            try:
                test_result = entity_extractor.extract_entities("بيت في بغداد")
                health_report['components']['entity_extractor'] = {
                    'status': 'operational',
                    'entities_extracted': len(test_result.get('entities', {}))
                }
            except Exception as e:
                health_report['components']['entity_extractor'] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_report['status'] = 'degraded'
            
            # Check context manager
            try:
                test_context = context_manager.get_context("test_health_check")
                health_report['components']['context_manager'] = {
                    'status': 'operational',
                    'context_available': test_context is not None
                }
            except Exception as e:
                health_report['components']['context_manager'] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_report['status'] = 'degraded'
            
            # Check tool registry
            try:
                from .ai_agent_tools import tool_registry
                tool_count = len(tool_registry.get_all_tools())
                health_report['components']['tool_registry'] = {
                    'status': 'operational',
                    'available_tools': tool_count
                }
            except Exception as e:
                health_report['components']['tool_registry'] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_report['status'] = 'degraded'
            
            # Check learning pipeline
            try:
                health_report['components']['learning_pipeline'] = {
                    'status': 'operational',
                    'training_examples': TrainingExample.objects.count(),
                    'user_feedback': UserFeedback.objects.count()
                }
            except Exception as e:
                health_report['components']['learning_pipeline'] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_report['status'] = 'degraded'
            
            # Check voice system
            try:
                from .ai_voice_provider import voice_analytics
                health_report['components']['voice_system'] = {
                    'status': 'operational',
                    'voice_analytics': voice_analytics.get_statistics()
                }
            except Exception as e:
                health_report['components']['voice_system'] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_report['status'] = 'degraded'
            
            self.last_check = timezone.now()
            self.health_status = health_report['status']
            
            return health_report
            
        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def _measure_db_latency(self) -> float:
        """Measure database query latency"""
        import time
        from django.db import connection
        
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        end_time = time.time()
        
        return (end_time - start_time) * 1000  # Convert to milliseconds
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get AI system performance metrics"""
        try:
            # Get recent performance data
            recent_conversations = ConversationLog.objects.filter(
                started_at__gte=timezone.now() - timedelta(hours=24)
            )
            
            # Calculate metrics
            total_conversations = recent_conversations.count()
            resolved_conversations = recent_conversations.filter(resolved=True).count()
            resolution_rate = (resolved_conversations / total_conversations * 100) if total_conversations > 0 else 0
            
            # Average response time (if logged)
            avg_response_time = 0  # Would need to add timing tracking
            
            # Tool success rate
            recent_tools = ToolUsageLog.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            )
            total_tools = recent_tools.count()
            successful_tools = recent_tools.filter(success=True).count()
            tool_success_rate = (successful_tools / total_tools * 100) if total_tools > 0 else 0
            
            return {
                'resolution_rate': resolution_rate,
                'avg_response_time_ms': avg_response_time,
                'tool_success_rate': tool_success_rate,
                'total_conversations_24h': total_conversations,
                'resolved_conversations_24h': resolved_conversations,
                'total_tool_calls_24h': total_tools,
                'successful_tool_calls_24h': successful_tools
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return {}


# Global instances
data_collector = DataCollector()
data_augmentor = DataAugmentor()
data_anonymizer = DataAnonymizer()
dataset_manager = DatasetManager()
model_trainer = ModelTrainer()
evaluator = Evaluator()
debug_mode = DebugMode()
health_checker = AIHealthChecker()