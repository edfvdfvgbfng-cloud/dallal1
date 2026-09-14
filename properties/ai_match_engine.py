"""
AI Match System - Intelligent Property Matching
Matches user requests with the best properties using advanced algorithms
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass
from collections import defaultdict
import math

from .ai_arabic_normalizer import ArabicNormalizer
from .ai_smart_intent_detection import IntentDetector, Intent
from .ai_smart_request_parser import AIRequestParser

logger = logging.getLogger(__name__)


class MatchCriteria(Enum):
    """Criteria for property matching"""
    LOCATION = "location"
    PRICE = "price"
    SIZE = "size"
    PROPERTY_TYPE = "property_type"
    AMENITIES = "amenities"
    CONDITION = "condition"
    AVAILABILITY = "availability"
    USER_PREFERENCES = "user_preferences"


@dataclass
class MatchScore:
    """Detailed match score with breakdown"""
    overall_score: float
    criteria_scores: Dict[str, float]
    match_reasons: List[str]
    mismatch_reasons: List[str]
    confidence: float

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'overall_score': self.overall_score,
            'criteria_scores': self.criteria_scores,
            'match_reasons': self.match_reasons,
            'mismatch_reasons': self.mismatch_reasons,
            'confidence': self.confidence
        }


@dataclass
class PropertyMatch:
    """Property match result"""
    property_id: int
    property_data: Dict
    match_score: MatchScore
    rank: int
    recommendation_level: str  # excellent, good, fair, poor

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'property_id': self.property_id,
            'property_data': self.property_data,
            'match_score': self.match_score.to_dict(),
            'rank': self.rank,
            'recommendation_level': self.recommendation_level
        }


class AIMatchEngine:
    """
    Advanced AI match engine
    Intelligently matches user requests with properties
    """

    def __init__(self):
        self.normalizer = ArabicNormalizer()
        self.intent_detector = IntentDetector()
        self.request_parser = AIRequestParser()
        self.match_history = defaultdict(list)

        # Criteria weights (can be adjusted)
        self.criteria_weights = {
            MatchCriteria.LOCATION: 0.25,
            MatchCriteria.PRICE: 0.20,
            MatchCriteria.SIZE: 0.15,
            MatchCriteria.PROPERTY_TYPE: 0.15,
            MatchCriteria.AMENITIES: 0.10,
            MatchCriteria.CONDITION: 0.10,
            MatchCriteria.AVAILABILITY: 0.05
        }

    def match_properties(self, user_request: str, available_properties: List[Dict], user_id: Optional[int] = None) -> List[PropertyMatch]:
        """
        Match user request with available properties

        Args:
            user_request: User's natural language request
            available_properties: List of available properties
            user_id: User ID (optional)

        Returns:
            List of matched properties with scores
        """
        # Parse user request
        parsed_request = self.request_parser.parse_request(user_request, user_id)

        # Extract user preferences
        user_preferences = self._extract_user_preferences(parsed_request)

        # Calculate match scores for all properties
        matches = []
        for property_data in available_properties:
            match_score = self._calculate_match_score(user_preferences, property_data)

            if match_score.overall_score > 0.3:  # Only include reasonably matching properties
                property_match = PropertyMatch(
                    property_id=property_data.get('id'),
                    property_data=property_data,
                    match_score=match_score,
                    rank=0,  # Will be set after sorting
                    recommendation_level=self._determine_recommendation_level(match_score.overall_score)
                )
                matches.append(property_match)

        # Sort by match score
        matches.sort(key=lambda x: x.match_score.overall_score, reverse=True)

        # Assign ranks
        for i, match in enumerate(matches):
            match.rank = i + 1

        # Store in history
        if user_id:
            self.match_history[user_id].append({
                'timestamp': logger.info,
                'request': user_request,
                'parsed_request': parsed_request,
                'matches_count': len(matches)
            })

        return matches

    def _extract_user_preferences(self, parsed_request: Dict) -> Dict[str, Any]:
        """Extract user preferences from parsed request"""
        filters = parsed_request.get('filters', {})

        preferences = {
            'location': filters.get('location'),
            'property_type': filters.get('property_type'),
            'price_min': filters.get('price', {}).get('min'),
            'price_max': filters.get('price', {}).get('max'),
            'area_min': filters.get('area', {}).get('min'),
            'area_max': filters.get('area', {}).get('max'),
            'bedrooms': filters.get('bedrooms'),
            'amenities': filters.get('amenities', []),
            'purpose': filters.get('purpose')
        }

        return preferences

    def _calculate_match_score(self, user_preferences: Dict, property_data: Dict) -> MatchScore:
        """
        Calculate detailed match score

        Args:
            user_preferences: User's preferences
            property_data: Property data

        Returns:
            Detailed match score
        """
        criteria_scores = {}
        match_reasons = []
        mismatch_reasons = []

        # Location match
        location_score = self._calculate_location_match(user_preferences, property_data)
        criteria_scores[MatchCriteria.LOCATION.value] = location_score
        if location_score > 0.7:
            match_reasons.append('موقع مثالي')
        elif location_score < 0.3:
            mismatch_reasons.append('موقع غير مناسب')

        # Price match
        price_score = self._calculate_price_match(user_preferences, property_data)
        criteria_scores[MatchCriteria.PRICE.value] = price_score
        if price_score > 0.7:
            match_reasons.append('سعر مناسب')
        elif price_score < 0.3:
            mismatch_reasons.append('سعر غير مناسب')

        # Size match
        size_score = self._calculate_size_match(user_preferences, property_data)
        criteria_scores[MatchCriteria.SIZE.value] = size_score
        if size_score > 0.7:
            match_reasons.append('مساحة مناسبة')
        elif size_score < 0.3:
            mismatch_reasons.append('مساحة غير مناسبة')

        # Property type match
        type_score = self._calculate_property_type_match(user_preferences, property_data)
        criteria_scores[MatchCriteria.PROPERTY_TYPE.value] = type_score
        if type_score > 0.7:
            match_reasons.append('نوع العقار مناسب')
        elif type_score < 0.3:
            mismatch_reasons.append('نوع العقار غير مناسب')

        # Amenities match
        amenities_score = self._calculate_amenities_match(user_preferences, property_data)
        criteria_scores[MatchCriteria.AMENITIES.value] = amenities_score
        if amenities_score > 0.7:
            match_reasons.append('مرافق ممتازة')

        # Condition match
        condition_score = self._calculate_condition_match(property_data)
        criteria_scores[MatchCriteria.CONDITION.value] = condition_score
        if condition_score > 0.7:
            match_reasons.append('حالة جيدة')

        # Availability match
        availability_score = self._calculate_availability_match(property_data)
        criteria_scores[MatchCriteria.AVAILABILITY.value] = availability_score
        if availability_score > 0.7:
            match_reasons.append('متاح فوراً')

        # Calculate overall score using weighted average
        overall_score = 0.0
        for criteria, score in criteria_scores.items():
            weight = self.criteria_weights.get(MatchCriteria(criteria), 0.1)
            overall_score += score * weight

        # Calculate confidence based on number of matched criteria
        matched_criteria = sum(1 for score in criteria_scores.values() if score > 0.5)
        confidence = min(1.0, matched_criteria / len(criteria_scores))

        return MatchScore(
            overall_score=overall_score,
            criteria_scores=criteria_scores,
            match_reasons=match_reasons,
            mismatch_reasons=mismatch_reasons,
            confidence=confidence
        )

    def _calculate_location_match(self, user_preferences: Dict, property_data: Dict) -> float:
        """Calculate location match score"""
        user_location = user_preferences.get('location')
        property_location = property_data.get('location') or property_data.get('district')

        if not user_location:
            return 0.5  # Neutral if no preference

        if not property_location:
            return 0.0

        # Normalize both locations
        user_location_normalized = self.normalizer.normalize_text(user_location)
        property_location_normalized = self.normalizer.normalize_text(property_location)

        # Exact match
        if user_location_normalized == property_location_normalized:
            return 1.0

        # Partial match
        if user_location_normalized in property_location_normalized or property_location_normalized in user_location_normalized:
            return 0.8

        # Governorate match
        user_governorate = self.normalizer.normalize_governorate(user_location_normalized)
        property_governorate = self.normalizer.normalize_governorate(property_location_normalized)

        if user_governorate and property_governorate and user_governorate == property_governorate:
            return 0.6

        return 0.2

    def _calculate_price_match(self, user_preferences: Dict, property_data: Dict) -> float:
        """Calculate price match score"""
        price_min = user_preferences.get('price_min')
        price_max = user_preferences.get('price_max')
        property_price = property_data.get('price')

        if not property_price:
            return 0.5  # Neutral if no price

        if not price_min and not price_max:
            return 0.5  # Neutral if no preference

        # Check if price is within range
        if price_min and property_price < price_min:
            # Below minimum - calculate how far below
            diff = (price_min - property_price) / price_min
            return max(0.0, 1.0 - diff)

        if price_max and property_price > price_max:
            # Above maximum - calculate how far above
            diff = (property_price - price_max) / price_max
            return max(0.0, 1.0 - diff)

        # Within range
        if price_min and price_max:
            # Perfectly in range
            return 1.0

        # Only one boundary specified
        if price_min and property_price >= price_min:
            return 0.9

        if price_max and property_price <= price_max:
            return 0.9

        return 0.5

    def _calculate_size_match(self, user_preferences: Dict, property_data: Dict) -> float:
        """Calculate size/area match score"""
        area_min = user_preferences.get('area_min')
        area_max = user_preferences.get('area_max')
        property_area = property_data.get('area')

        if not property_area:
            return 0.5  # Neutral if no area

        if not area_min and not area_max:
            return 0.5  # Neutral if no preference

        # Check if area is within range
        if area_min and property_area < area_min:
            diff = (area_min - property_area) / area_min
            return max(0.0, 1.0 - diff)

        if area_max and property_area > area_max:
            diff = (property_area - area_max) / area_max
            return max(0.0, 1.0 - diff)

        # Within range
        if area_min and area_max:
            return 1.0

        # Only one boundary specified
        if area_min and property_area >= area_min:
            return 0.9

        if area_max and property_area <= area_max:
            return 0.9

        return 0.5

    def _calculate_property_type_match(self, user_preferences: Dict, property_data: Dict) -> float:
        """Calculate property type match score"""
        user_type = user_preferences.get('property_type')
        property_type = property_data.get('type')

        if not user_type:
            return 0.5  # Neutral if no preference

        if not property_type:
            return 0.0

        # Exact match
        if user_type == property_type:
            return 1.0

        # Partial match (e.g., 'house' vs 'villa')
        type_mappings = {
            'house': ['villa', 'building'],
            'apartment': ['flat', 'studio'],
            'land': ['plot', 'plot']
        }

        if user_type in type_mappings and property_type in type_mappings[user_type]:
            return 0.7

        return 0.2

    def _calculate_amenities_match(self, user_preferences: Dict, property_data: Dict) -> float:
        """Calculate amenities match score"""
        user_amenities = user_preferences.get('amenities', [])
        property_amenities = property_data.get('amenities', [])

        if not user_amenities:
            return 0.5  # Neutral if no preference

        if not property_amenities:
            return 0.0

        # Calculate overlap
        user_amenities_set = set(user_amenities)
        property_amenities_set = set(property_amenities)

        overlap = user_amenities_set & property_amenities_set

        if not overlap:
            return 0.0

        # Calculate score based on percentage of matched amenities
        match_ratio = len(overlap) / len(user_amenities_set)
        return match_ratio

    def _calculate_condition_match(self, property_data: Dict) -> float:
        """Calculate property condition match"""
        condition = property_data.get('condition', 'unknown')

        condition_scores = {
            'excellent': 1.0,
            'good': 0.8,
            'fair': 0.6,
            'needs_repair': 0.4,
            'unknown': 0.5
        }

        return condition_scores.get(condition, 0.5)

    def _calculate_availability_match(self, property_data: Dict) -> float:
        """Calculate availability match"""
        status = property_data.get('status', 'unknown')

        availability_scores = {
            'available': 1.0,
            'pending': 0.7,
            'sold': 0.0,
            'rented': 0.0,
            'unknown': 0.5
        }

        return availability_scores.get(status, 0.5)

    def _determine_recommendation_level(self, score: float) -> str:
        """Determine recommendation level based on score"""
        if score >= 0.8:
            return 'excellent'
        elif score >= 0.6:
            return 'good'
        elif score >= 0.4:
            return 'fair'
        else:
            return 'poor'

    def generate_match_summary(self, matches: List[PropertyMatch]) -> Dict[str, Any]:
        """
        Generate summary of match results

        Args:
            matches: List of property matches

        Returns:
            Match summary
        """
        if not matches:
            return {
                'total_matches': 0,
                'message': 'لم يتم العثور على عقارات مطابقة لطلبك',
                'suggestions': ['حاول توسيع نطاق البحث', 'غيّر بعض الفلاتر', 'اتصل بنا للمساعدة']
            }

        summary = {
            'total_matches': len(matches),
            'excellent_matches': len([m for m in matches if m.recommendation_level == 'excellent']),
            'good_matches': len([m for m in matches if m.recommendation_level == 'good']),
            'fair_matches': len([m for m in matches if m.recommendation_level == 'fair']),
            'top_match': matches[0].to_dict() if matches else None,
            'average_score': sum(m.match_score.overall_score for m in matches) / len(matches),
            'common_match_reasons': self._get_common_reasons(matches)
        }

        return summary

    def _get_common_reasons(self, matches: List[PropertyMatch]) -> List[str]:
        """Get common match reasons across all matches"""
        all_reasons = []
        for match in matches:
            all_reasons.extend(match.match_score.match_reasons)

        # Count frequency
        reason_counts = defaultdict(int)
        for reason in all_reasons:
            reason_counts[reason] += 1

        # Return top 3 most common reasons
        sorted_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)
        return [reason for reason, count in sorted_reasons[:3]]

    def get_match_explanation(self, match: PropertyMatch) -> str:
        """
        Generate natural language explanation for a match

        Args:
            match: Property match

        Returns:
            Natural language explanation
        """
        explanation_parts = []

        property_data = match.property_data
        score = match.match_score

        # Overall assessment
        if match.recommendation_level == 'excellent':
            explanation_parts.append("هذا العقار مطابق تماماً لطلبك! 🌟")
        elif match.recommendation_level == 'good':
            explanation_parts.append("هذا العقار مطابق جيد جداً لطلبك 👍")
        elif match.recommendation_level == 'fair':
            explanation_parts.append("هذا العقار مطابق بشكل معقول لطلبك")
        else:
            explanation_parts.append("هذا العقار قد لا يكون الأنسب لطلبك")

        # Match reasons
        if score.match_reasons:
            explanation_parts.append("الأسباب:")
            for reason in score.match_reasons[:3]:
                explanation_parts.append(f"- {reason}")

        # Mismatch reasons
        if score.mismatch_reasons:
            explanation_parts.append("ملاحظات:")
            for reason in score.mismatch_reasons[:2]:
                explanation_parts.append(f"- {reason}")

        # Score breakdown
        explanation_parts.append(f"درجة المطابقة: {score.overall_score:.1%}")

        return "\n".join(explanation_parts)


# Global instance
ai_match_engine = AIMatchEngine()
