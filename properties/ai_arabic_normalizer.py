"""
Arabic Text Normalizer - Advanced Arabic and Iraqi Dialect Processing
Handles spelling errors, dialect variations, and number conversions
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict

logger = logging.getLogger('properties')


class ArabicNormalizer:
    """
    Advanced Arabic text normalization for Iraqi dialect and Modern Standard Arabic
    Handles spelling variations, dialect patterns, and number conversions
    """
    
    def __init__(self):
        # Iraqi dialect normalization
        self.dialect_mapping = {
            # Common dialect words
            'شكد': 'كم',
            'شنو': 'ماذا',
            'أدور': 'أبحث',
            'لكيت': 'وجدت',
            'دار': 'بيت',
            'دلال': 'وسيط عقاري',
            'بلبصرة': 'بالبصرة',
            'بالبصره': 'بالبصرة',
            'بصرة': 'البصرة',
            'مليون': 'مليون',
            'مليار': 'مليار',
            'راح': 'ذهب',
            'اتروح': 'أذهب',
            'اكو': 'يوجد',
            'ماكو': 'لا يوجد',
            'زين': 'جيد',
            'عشر': 'نصف',
            'ربع': 'ربع',
            'ثمن': 'ثمن',
            'گت': 'قد',
            'چن': 'كم',
            'وين': 'أين',
            'لحد': 'إلى حد',
            'حدود': 'حول',
            'تقريباً': 'تقريباً',
            'ميه': 'مائة',
            'تي': 'التي',
            'هي': 'هي',
            'هاي': 'هذه',
            'هاذا': 'هذا',
            'شكو': 'كيف',
            'شو': 'ماذا',
            'شسم': 'ما اسم',
            'شلون': 'كيف',
            'شوخ': 'متى',
            'متى': 'متى',
            'لأن': 'لأن',
            'بسبب': 'بسبب',
            'لك': 'لكن',
            'يعني': 'يعني',
            'يمن': 'يمكن',
            'نبي': 'نريد',
            'نبغ': 'نحتاج',
            'أريده': 'أريده',
            'اريد': 'أريد',
            'أبي': 'أبي',
            'الخاصة': 'الخاص',
            'بغت': 'بقيت',
            'بغيه': 'بقيته',
            'خلي': 'اجعل',
            'خل': 'اجعل',
            'خله': 'اجعله',
            'سوت': 'صف',
            'سوي': 'اصنع',
            'تيب': 'تعيب',
            'تبو': 'تعيب',
            'حلو': 'جيد',
            'حليو': 'جيد',
            'عيب': 'سيء',
            'ميب': 'سيء',
            'رايح': 'استراحة',
            'راحة': 'استراحة',
            'تمام': 'ممتاز',
            'تمامي': 'ممتاز',
            'كول': 'كل',
            'هلي': 'هذا',
            'هليش': 'هذا لا',
            'حسبا': 'حسباً',
            'حسب': 'حسباً',
            'بشكل': 'بشكل',
            'بسال': 'بسرعة',
            'بسرعة': 'بسرعة',
            'سال': 'سريع',
            'صعب': 'صعب',
            'سهل': 'سهل',
            'سهول': 'سهل',
            'يصير': 'يصبح',
            'تخيل': 'تخيل',
            'تخول': 'تخيل',
            'مو': 'أين',
            'موين': 'أين',
            'مين': 'أين',
            'منين': 'من أين',
            'إيش': 'ماذا',
            'إيش': 'أي شيء',
            'أيش': 'أي شيء',
            'ليش': 'لماذا',
            'لايش': 'لماذا',
            'علاش': 'لماذا',
            'عليش': 'لماذا',
            'شلون': 'كيف',
            'شلون': 'كيف',
            'شسم': 'ما اسم',
            'شو': 'ماذا',
            'شنو': 'ماذا',
            'شلو': 'ماذا',
            'كو': 'هناك',
            'مكو': 'ليس هناك',
            'مكان': 'مكان',
            'مكانش': 'ليس هناك'
        }
        
        # Spelling corrections
        self.spelling_corrections = {
            'العراق': 'العراق',
            'العراقي': 'العراق',
            'البصره': 'البصرة',
            'بغداد': 'بغداد',
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
            'سليمانية': 'سليمانية',
            'اربيل': 'أربيل',
            'دهوك': 'دهوك',
            'نينوى': 'نينوى',
            'الموصل': 'نينوى',
            'بصرة': 'البصرة',
            'العمارة': 'ميسان',
            'السماوة': 'المثنى',
            'الرمادي': 'الانبار',
            'تكريت': 'صلاح الدين',
            'الناصرية': 'ذي قار',
            'العشار': 'العشار',
            'الجزيرة': 'الجزيرة',
            'المتن': 'المتن',
            'الشورجة': 'الشورجة',
            'الكاظمية': 'الكاظمية',
            'الاعظمية': 'الاعظمية',
            'المنصور': 'المنصور',
            'الكرادة': 'الكرادة',
            'السيدية': 'السيدية',
            'الشعب': 'الشعب',
            'الرصافة': 'الرصافة',
            'المأمون': 'المأمون',
            'الجوخ': 'الجوخ'
        }
        
        # Number patterns for Iraqi dialect
        self.number_patterns = {
            # Fraction expressions
            'نصف': 0.5,
            'نص': 0.5,
            'ربع': 0.25,
            'ثمن': 0.125,
            'ثلث': 0.333,
            'ثلثين': 0.666,
            'عشر': 0.1,
            'عشرين': 0.2,
            'خمس': 0.2,
            'خمسين': 0.5,
            'سبع': 0.142,
            'سبعين': 0.7,
            'تسع': 0.111,
            'تسعين': 0.9
        }
        
        # Unit patterns
        self.unit_multipliers = {
            'مليون': 1000000,
            'مليار': 1000000000,
            'ألف': 1000,
            'مئة': 100,
            'مائة': 100,
            'بليون': 1000000000,
            'تيلي': 1000000000,
            'كليو': 1000,
            'طن': 1000,
            'فدان': 2500,
            'دونم': 1000
        }
        
        # Governorate variations
        self.governorate_variations = {
            'بغداد': ['بغداد', 'بغداد'],
            'البصرة': ['البصرة', 'بلبصرة', 'بالبصره', 'بصرة'],
            'أربيل': ['أربيل', 'هولير', 'أربيل'],
            'دهوك': ['دهوك', 'دهوك'],
            'نينوى': ['نينوى', 'الموصل', 'نينوى'],
            'كربلاء': ['كربلاء', 'كربلاء'],
            'النجف': ['النجف', 'النجف'],
            'الديوانية': ['الديوانية', 'الديوانية'],
            'القادسية': ['القادسية', 'القادسية'],
            'بابل': ['بابل', 'بابل'],
            'واسط': ['واسط', 'واسط'],
            'الانبار': ['الانبار', 'الرمادي', 'الانبار'],
            'صلاح الدين': ['صلاح الدين', 'تكريت', 'صلاح الدين'],
            'ذي قار': ['ذي قار', 'الناصرية', 'ذي قار'],
            'ميسان': ['ميسان', 'العمارة', 'ميسان'],
            'المثنى': ['المثنى', 'السماوة', 'المثنى'],
            'ديالى': ['ديالى', 'ديالى'],
            'كركوك': ['كركوك', 'كركوك'],
            'سليمانية': ['سليمانية', 'حلبجة', 'سليمانية']
        }
        
        # Property type variations
        self.property_type_variations = {
            'house': ['بيت', 'دار', 'منزل', 'سكن', 'منزل'],
            'apartment': ['شقة', 'شقة سكنية', 'شقة'],
            'land': ['أرض', 'قسيمة', 'أرض', 'قطعة أرض'],
            'commercial': ['محل', 'مستودع', 'مطعم', 'مقهى', 'سوق تجاري'],
            'villa': ['فيلا', 'قصر', 'منتجع', 'فيلا'],
            'building': ['عمارة', 'بناية', 'برج', 'طابق', 'عمارة']
        }
        
        # Statistics
        self.normalization_stats = defaultdict(int)
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize Arabic text including dialect and spelling corrections
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not text:
            return text
        
        normalized = text
        
        # Apply dialect mapping
        for dialect_word, standard_word in self.dialect_mapping.items():
            if dialect_word in normalized:
                normalized = normalized.replace(dialect_word, standard_word)
                self.normalization_stats['dialect_corrections'] += 1
        
        # Apply spelling corrections
        for misspelled, correct in self.spelling_corrections.items():
            if misspelled in normalized:
                normalized = normalized.replace(misspelled, correct)
                self.normalization_stats['spelling_corrections'] += 1
        
        # Normalize Arabic characters (optional)
        normalized = self._normalize_arabic_chars(normalized)
        
        return normalized
    
    def _normalize_arabic_chars(self, text: str) -> str:
        """Normalize Arabic characters (alef, teh, etc.)"""
        # Normalize alef variants
        text = re.sub('[أإآ]', 'ا', text)
        # Normalize teh variants
        text = re.sub('[ة]', 'ة', text)
        # Normalize yeh variants
        text = re.sub('[يى]', 'ي', text)
        
        return text
    
    def extract_numbers(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract numbers with their units and context
        
        Args:
            text: Input text
            
        Returns:
            List of extracted numbers with context
        """
        numbers = []
        
        # Extract explicit numbers with units
        for unit, multiplier in self.unit_multipliers.items():
            # Pattern: number + unit (e.g., "100 مليون")
            pattern = rf'(\d+(?:\.\d+)?)\s*{unit}'
            matches = re.finditer(pattern, text)
            for match in matches:
                number_value = float(match.group(1))
                converted_value = number_value * multiplier
                numbers.append({
                    'original': match.group(0),
                    'value': number_value,
                    'unit': unit,
                    'converted': converted_value,
                    'position': match.start()
                })
        
        # Extract fractional expressions
        for fraction, value in self.number_patterns.items():
            if fraction in text:
                numbers.append({
                    'original': fraction,
                    'value': value,
                    'unit': 'fraction',
                    'converted': value,
                    'position': text.find(fraction)
                })
        
        # Extract standalone numbers
        standalone_numbers = re.findall(r'\d+(?:\.\d+)?', text)
        for num_str in standalone_numbers:
            number_value = float(num_str)
            numbers.append({
                'original': num_str,
                'value': number_value,
                'unit': None,
                'converted': number_value,
                'position': text.find(num_str)
            })
        
        # Sort by position
        numbers.sort(key=lambda x: x['position'])
        
        return numbers
    
    def interpret_budget(self, text: str) -> Optional[int]:
        """
        Interpret budget from text with Iraqi dialect support
        
        Args:
            text: Input text
            
        Returns:
            Budget as integer or None
        """
        numbers = self.extract_numbers(text)
        
        if not numbers:
            return None
        
        # Find the most likely budget (largest number usually indicates budget)
        budget_candidates = []
        
        for num in numbers:
            # Check if this looks like a budget
            if num['unit'] in ['مليون', 'مليار', 'بليون', 'تيلي']:
                budget_candidates.append(num['converted'])
            elif num['unit'] is None and num['value'] > 1000:
                # Large standalone number - assume it's in millions
                budget_candidates.append(num['value'] * 1000000)
        
        if budget_candidates:
            return max(budget_candidates)
        
        return None
    
    def interpret_area(self, text: str) -> Optional[int]:
        """
        Interpret area from text
        
        Args:
            text: Input text
            
        Returns:
            Area as integer or None
        """
        numbers = self.extract_numbers(text)
        
        for num in numbers:
            # Look for area indicators
            text_context = text[max(0, num['position'] - 20):num['position'] + 20]
            
            if any(indicator in text_context for indicator in ['متر', 'م²', 'م', 'مساحة', 'حجم']):
                return int(num['value'])
            
            # Numbers less than 1000 usually indicate area
            if num['unit'] is None and num['value'] < 1000:
                return int(num['value'])
        
        return None
    
    def normalize_governorate(self, text: str) -> Optional[str]:
        """
        Normalize governorate name from text
        
        Args:
            text: Input text
            
        Returns:
            Standardized governorate name or None
        """
        for standard, variations in self.governorate_variations.items():
            for variation in variations:
                if variation in text:
                    return standard
        
        return None
    
    def normalize_property_type(self, text: str) -> Optional[str]:
        """
        Normalize property type from text
        
        Args:
            text: Input text
            
        Returns:
            Standardized property type or None
        """
        for standard, variations in self.property_type_variations.items():
            for variation in variations:
                if variation in text:
                    return standard
        
        return None
    
    def parse_compound_request(self, text: str) -> Dict[str, Any]:
        """
        Parse compound request with multiple entities
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with extracted entities
        """
        normalized_text = self.normalize_text(text)
        
        result = {
            'normalized_text': normalized_text,
            'entities': {},
            'confidence': 0.0
        }
        
        # Extract governorate
        governorate = self.normalize_governorate(normalized_text)
        if governorate:
            result['entities']['governorate'] = governorate
        
        # Extract property type
        property_type = self.normalize_property_type(normalized_text)
        if property_type:
            result['entities']['property_type'] = property_type
        
        # Extract budget
        budget = self.interpret_budget(normalized_text)
        if budget:
            result['entities']['budget'] = budget
        
        # Extract area
        area = self.interpret_area(normalized_text)
        if area:
            result['entities']['area'] = area
        
        # Extract preferences (qualitative terms)
        preferences = self._extract_preferences(normalized_text)
        if preferences:
            result['entities']['preferences'] = preferences
        
        # Calculate confidence based on extraction success
        confidence = min(0.95, 0.5 + (len(result['entities']) * 0.1))
        result['confidence'] = confidence
        
        return result
    
    def _extract_preferences(self, text: str) -> List[str]:
        """Extract qualitative preferences from text"""
        preference_keywords = [
            'هادئ', 'منطقة هادئة', 'سكن', 'عائلي', 'للعوائل',
            'قريب من المدارس', 'قريب من الخدمات', 'قريب من السوق',
            'جديد', 'قديم', 'كامل', 'مفروش', 'غير مفروش',
            'في وضع جيد', 'مع حديقة', 'مع موقف', 'دورين',
            'ثلاثة طوابق', 'طابق واحد', 'طابقين',
            'الطابق الأول', 'الطابق الأخير', 'وسط المدينة',
            'الحوش', 'الصينية', 'الرصافة', 'المنصور'
        ]
        
        found_preferences = []
        for pref in preference_keywords:
            if pref in text:
                found_preferences.append(pref)
        
        return found_preferences
    
    def get_normalization_statistics(self) -> Dict[str, Any]:
        """Get normalization statistics"""
        return {
            'total_normalizations': sum(self.normalization_stats.values()),
            'dialect_corrections': self.normalization_stats['dialect_corrections'],
            'spelling_corrections': self.normalization_stats['spelling_corrections'],
            'most_common_corrections': dict(self.normalization_stats)
        }


class NumberParser:
    """
    Advanced number parsing for Iraqi dialect expressions
    Handles complex number expressions and conversions
    """
    
    def __init__(self):
        self.arabic_numbers = {
            'صفر': 0,
            'واحد': 1,
            'اثنان': 2,
            'اثنين': 2,
            'ثلاثة': 3,
            'ثلاث': 3,
            'أربعة': 4,
            'أربع': 4,
            'خمسة': 5,
            'خمس': 5,
            'ستة': 6,
            'ست': 6,
            'سبعة': 7,
            'سبع': 7,
            'ثمانية': 8,
            'ثمان': 8,
            'تسعة': 9,
            'تسع': 9,
            'عشرة': 10,
            'عشر': 10,
            'عشرون': 20,
            'ثلاثون': 30,
            'أربعون': 40,
            'خمسون': 50,
            'ستون': 60,
            'سبعون': 70,
            'ثمانون': 80,
            'تسعون': 90,
            'مائة': 100,
            'مئة': 100,
            'مئتان': 200,
            'مئتان': 200,
            'ثلاثمائة': 300,
            'أربعمائة': 400,
            'خمسمائة': 500,
            'ستمائة': 600,
            'سبعمائة': 700,
            'ثمانمائة': 800,
            'تسعمائة': 900,
            'ألف': 1000,
            'ألفان': 2000,
            'ألفين': 2000,
            'مليون': 1000000,
            'مليار': 1000000000
        }
        
        self.fractional_expressions = {
            'نصف': 0.5,
            'نص': 0.5,
            'ثلث': 1/3,
            'ربع': 0.25,
            'خمس': 0.2,
            'سدس': 0.166,
            'سبع': 0.142,
            'ثمن': 0.125,
            'تسع': 0.111,
            'عشر': 0.1
        }
    
    def parse_arabic_number(self, text: str) -> Optional[float]:
        """
        Parse Arabic number text to numeric value
        
        Args:
            text: Arabic number text
            
        Returns:
            Numeric value or None
        """
        # Direct lookup
        if text in self.arabic_numbers:
            return self.arabic_numbers[text]
        
        # Check for compound expressions
        if 'مليون ونص' in text or 'مليون ونصف' in text:
            base = self._extract_base_number(text)
            return base * 1000000 * 1.5
        
        if 'مليار ونص' in text or 'مليار ونصف' in text:
            base = self._extract_base_number(text)
            return base * 1000000000 * 1.5
        
        return None
    
    def _extract_base_number(self, text: str) -> int:
        """Extract base number from compound expression"""
        # Extract first number found
        match = re.search(r'\d+', text)
        if match:
            return int(match.group(0))
        return 1
    
    def parse_complex_expression(self, text: str) -> Optional[float]:
        """
        Parse complex number expressions like "مئة وخمسون مليون"
        
        Args:
            text: Input text
            
        Returns:
            Numeric value or None
        """
        total = 0
        
        # Check for unit
        if 'مليون' in text:
            multiplier = 1000000
        elif 'مليار' in text:
            multiplier = 1000000000
        elif 'ألف' in text:
            multiplier = 1000
        else:
            multiplier = 1
        
        # Extract numbers
        numbers = re.findall(r'\d+', text)
        if numbers:
            total = sum(int(num) for num in numbers)
            return total * multiplier
        
        # Try Arabic numbers
        for arabic_num, value in self.arabic_numbers.items():
            if arabic_num in text:
                total += value
        
        if total > 0:
            return total * multiplier
        
        return None


# Global instances
arabic_normalizer = ArabicNormalizer()
number_parser = NumberParser()