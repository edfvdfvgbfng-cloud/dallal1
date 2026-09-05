"""
Hotel and Travel Assistant - Specialized AI Assistant
Plans trips based on budget and preferences
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict

from .ai_arabic_normalizer import ArabicNormalizer, NumberParser
from .ai_smart_intent_detection import IntentDetector, Intent
from .ai_smart_request_parser import AIRequestParser

logger = logging.getLogger(__name__)


class TravelPreference(Enum):
    """Travel preferences"""
    BUDGET = "budget"
    MID_RANGE = "mid_range"
    LUXURY = "luxury"
    FAMILY = "family"
    BUSINESS = "business"
    ROMANTIC = "romantic"
    ADVENTURE = "adventure"
    CULTURAL = "cultural"


class AccommodationType(Enum):
    """Types of accommodation"""
    HOTEL = "hotel"
    RESORT = "resort"
    APARTMENT = "apartment"
    GUESTHOUSE = "guesthouse"
    HOSTEL = "hostel"
    VILLA = "villa"


@dataclass
class TravelRequest:
    """User's travel request"""
    destination: str
    check_in: Optional[datetime]
    check_out: Optional[datetime]
    guests: int
    budget: Optional[int]
    preferences: List[TravelPreference]
    accommodation_type: Optional[AccommodationType]
    special_requirements: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'destination': self.destination,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'guests': self.guests,
            'budget': self.budget,
            'preferences': [p.value for p in self.preferences],
            'accommodation_type': self.accommodation_type.value if self.accommodation_type else None,
            'special_requirements': self.special_requirements
        }


@dataclass
class HotelRecommendation:
    """Hotel recommendation with scoring"""
    hotel_id: int
    hotel_name: str
    location: str
    price_per_night: float
    total_price: float
    rating: float
    amenities: List[str]
    match_score: float
    match_reasons: List[str]
    booking_url: str

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'hotel_id': self.hotel_id,
            'hotel_name': self.hotel_name,
            'location': self.location,
            'price_per_night': self.price_per_night,
            'total_price': self.total_price,
            'rating': self.rating,
            'amenities': self.amenities,
            'match_score': self.match_score,
            'match_reasons': self.match_reasons,
            'booking_url': self.booking_url
        }


@dataclass
class TravelPlan:
    """Complete travel plan"""
    request: TravelRequest
    recommendations: List[HotelRecommendation]
    total_estimated_cost: float
    itinerary: List[Dict]
    tips: List[str]
    alternatives: List[Dict]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'request': self.request.to_dict(),
            'recommendations': [r.to_dict() for r in self.recommendations],
            'total_estimated_cost': self.total_estimated_cost,
            'itinerary': self.itinerary,
            'tips': self.tips,
            'alternatives': self.alternatives
        }


class HotelTravelAssistant:
    """
    Specialized AI assistant for hotels and travel planning
    Plans trips based on budget and preferences
    """

    def __init__(self):
        self.normalizer = ArabicNormalizer()
        self.number_parser = NumberParser()
        self.intent_detector = IntentDetector()
        self.request_parser = AIRequestParser()
        self.travel_history = defaultdict(list)

    def parse_travel_request(self, text: str, user_id: Optional[int] = None) -> TravelRequest:
        """
        Parse travel request from natural language

        Args:
            text: User input text
            user_id: User ID (optional)

        Returns:
            Structured travel request
        """
        # Normalize text
        normalized_text = self.normalizer.normalize_text(text)

        # Extract entities
        destination = self._extract_destination(normalized_text)
        dates = self._extract_dates(normalized_text)
        guests = self._extract_guests(normalized_text)
        budget = self._extract_budget(normalized_text)
        preferences = self._extract_preferences(normalized_text)
        accommodation_type = self._extract_accommodation_type(normalized_text)
        special_requirements = self._extract_special_requirements(normalized_text)

        request = TravelRequest(
            destination=destination,
            check_in=dates.get('check_in'),
            check_out=dates.get('check_out'),
            guests=guests,
            budget=budget,
            preferences=preferences,
            accommodation_type=accommodation_type,
            special_requirements=special_requirements
        )

        # Store in history
        if user_id:
            self.travel_history[user_id].append({
                'timestamp': datetime.now(),
                'request': request,
                'original_text': text
            })

        return request

    def _extract_destination(self, text: str) -> str:
        """Extract destination from text"""
        # Check for governorate
        governorate = self.normalizer.normalize_governorate(text)
        if governorate:
            return governorate

        # Check for common destinations
        destinations = ['بغداد', 'البصرة', 'أربيل', 'دهوك', 'النجف', 'كربلاء',
                       'دبي', 'اسطنبول', 'أنقرة', 'لندن', 'باريس']

        for dest in destinations:
            if dest in text:
                return dest

        return ""

    def _extract_dates(self, text: str) -> Dict[str, Optional[datetime]]:
        """Extract check-in and check-out dates"""
        dates = {'check_in': None, 'check_out': None}

        # This is a simplified version - in production, use NLP date parsing
        # For now, we'll look for common patterns

        # Check for "اليوم" (today)
        if 'اليوم' in text:
            dates['check_in'] = datetime.now()

        # Check for "غداً" (tomorrow)
        if 'غدا' in text or 'بكرة' in text:
            dates['check_in'] = datetime.now() + timedelta(days=1)

        # Check for "بعد أسبوع" (after a week)
        if 'أسبوع' in text:
            dates['check_in'] = datetime.now() + timedelta(weeks=1)

        # If check-in is found, assume check-out is after 3 days
        if dates['check_in'] and not dates['check_out']:
            dates['check_out'] = dates['check_in'] + timedelta(days=3)

        return dates

    def _extract_guests(self, text: str) -> int:
        """Extract number of guests"""
        # Look for number patterns
        numbers = self.normalizer.extract_numbers(text)

        for num in numbers:
            # Check if this number is related to guests
            context = text[max(0, num['position'] - 20):num['position'] + 20]
            if any(indicator in context for indicator in ['شخص', 'ناس', 'ضيف', 'أفراد']):
                return int(num['value'])

        # Default to 1 if not specified
        return 1

    def _extract_budget(self, text: str) -> Optional[int]:
        """Extract budget from text"""
        return self.normalizer.interpret_budget(text)

    def _extract_preferences(self, text: str) -> List[TravelPreference]:
        """Extract travel preferences"""
        preferences = []

        preference_keywords = {
            TravelPreference.BUDGET: ['اقتصادي', 'رخص', 'بسعر مناسب', 'ميزانية محدودة'],
            TravelPreference.MID_RANGE: ['متوسط', 'معقول', 'جيد'],
            TravelPreference.LUXURY: ['فاخر', 'فخم', 'عالي الجودة', 'مميز'],
            TravelPreference.FAMILY: ['عائلي', 'للعوائل', 'أطفال'],
            TravelPreference.BUSINESS: ['عمل', 'رجال أعمال', 'اجتماعات'],
            TravelPreference.ROMANTIC: ['رومانسي', 'زوجين', 'شهر عسل'],
            TravelPreference.ADVENTURE: ['مغامرة', 'رياضة', 'استكشاف'],
            TravelPreference.CULTURAL: ['ثقافي', 'تاريخي', 'آثار']
        }

        for preference, keywords in preference_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    preferences.append(preference)
                    break

        return preferences

    def _extract_accommodation_type(self, text: str) -> Optional[AccommodationType]:
        """Extract accommodation type"""
        type_keywords = {
            AccommodationType.HOTEL: ['فندق', 'هوتيل'],
            AccommodationType.RESORT: ['منتجع', 'منتجعات'],
            AccommodationType.APARTMENT: ['شقة', 'شقق', 'أpartment'],
            AccommodationType.GUESTHOUSE: ['بيت ضيافة', 'guesthouse'],
            AccommodationType.HOSTEL: ['hostel', 'نزل'],
            AccommodationType.VILLA: ['فيلا', 'قصر', 'villa']
        }

        for acc_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return acc_type

        return None

    def _extract_special_requirements(self, text: str) -> List[str]:
        """Extract special requirements"""
        requirements = []

        requirement_keywords = [
            'إفطار', 'واي فاي', 'مسبح', 'موقف سيارات', 'غرفة لغير المدخنين',
            'غرفة عائلية', 'مصعد', 'خدمة الغرف', 'صالة رياضة',
            'سبا', 'مطعم', 'قريب من المطار', 'نقل من المطار'
        ]

        for keyword in requirement_keywords:
            if keyword in text:
                requirements.append(keyword)

        return requirements

    def generate_travel_plan(self, request: TravelRequest, available_hotels: List[Dict]) -> TravelPlan:
        """
        Generate comprehensive travel plan

        Args:
            request: Travel request
            available_hotels: Available hotels data

        Returns:
            Complete travel plan
        """
        # Filter and score hotels
        recommendations = self._recommend_hotels(request, available_hotels)

        # Calculate total cost
        total_cost = self._calculate_total_cost(request, recommendations)

        # Generate itinerary
        itinerary = self._generate_itinerary(request, recommendations)

        # Generate tips
        tips = self._generate_travel_tips(request, recommendations)

        # Generate alternatives
        alternatives = self._generate_alternatives(request, available_hotels)

        plan = TravelPlan(
            request=request,
            recommendations=recommendations,
            total_estimated_cost=total_cost,
            itinerary=itinerary,
            tips=tips,
            alternatives=alternatives
        )

        return plan

    def _recommend_hotels(self, request: TravelRequest, hotels: List[Dict]) -> List[HotelRecommendation]:
        """Recommend hotels based on request"""
        recommendations = []

        for hotel in hotels:
            score = 0.0
            reasons = []

            # Budget match
            if request.budget:
                hotel_price = hotel.get('price_start', 0)
                if hotel_price <= request.budget:
                    score += 0.3
                    reasons.append('ضمن الميزانية')
                else:
                    score -= 0.2

            # Location match
            if request.destination and request.destination in hotel.get('location', ''):
                score += 0.2
                reasons.append('موقع مثالي')

            # Rating match
            rating = hotel.get('rating', 0)
            if rating >= 4.0:
                score += 0.2
                reasons.append('تقييم عالي')

            # Preference match
            if TravelPreference.LUXURY in request.preferences and hotel.get('stars', 0) >= 4:
                score += 0.15
                reasons.append('فاخر')

            if TravelPreference.BUDGET in request.preferences and hotel.get('price_start', 0) < 100000:
                score += 0.15
                reasons.append('اقتصادي')

            # Calculate total price
            nights = 3  # Default 3 nights
            if request.check_in and request.check_out:
                nights = (request.check_out - request.check_in).days

            total_price = hotel.get('price_start', 0) * nights

            # Create recommendation
            if score > 0.3:  # Only include reasonably matching hotels
                recommendation = HotelRecommendation(
                    hotel_id=hotel.get('id'),
                    hotel_name=hotel.get('title', ''),
                    location=hotel.get('location', ''),
                    price_per_night=hotel.get('price_start', 0),
                    total_price=total_price,
                    rating=rating,
                    amenities=hotel.get('amenities', []),
                    match_score=min(score, 1.0),
                    match_reasons=reasons,
                    booking_url=f"/hotels/{hotel.get('slug', '')}/"
                )
                recommendations.append(recommendation)

        # Sort by match score
        recommendations.sort(key=lambda x: x.match_score, reverse=True)

        return recommendations[:5]  # Return top 5

    def _calculate_total_cost(self, request: TravelRequest, recommendations: List[HotelRecommendation]) -> float:
        """Calculate total estimated cost"""
        if not recommendations:
            return 0.0

        # Use the top recommendation for cost calculation
        top_hotel = recommendations[0]
        return top_hotel.total_price

    def _generate_itinerary(self, request: TravelRequest, recommendations: List[HotelRecommendation]) -> List[Dict]:
        """Generate travel itinerary"""
        itinerary = []

        if not request.check_in or not request.check_out:
            return itinerary

        current_date = request.check_in
        end_date = request.check_out

        day_count = 1
        while current_date < end_date:
            day_plan = {
                'day': day_count,
                'date': current_date.strftime('%Y-%m-%d'),
                'activities': self._suggest_activities_for_day(request, day_count)
            }
            itinerary.append(day_plan)

            current_date += timedelta(days=1)
            day_count += 1

        return itinerary

    def _suggest_activities_for_day(self, request: TravelRequest, day: int) -> List[str]:
        """Suggest activities for a specific day"""
        activities = []

        if request.destination == 'بغداد':
            activities = [
                'زيارة المنطقة الخضراء',
                'جولة في ساحة التحرير',
                'زيارة المتحف العراقي',
                'تسوق في شارع الرشيد'
            ]
        elif request.destination == 'البصرة':
            activities = [
                'جولة في كورنيش البصرة',
                'زيارة سوق الهاشمي',
                'استكشاف المركز الثقافي'
            ]
        else:
            activities = [
                'استكشاف المدينة',
                'زيارة المعالم السياحية',
                'التسوق المحلي',
                'تجربة المطاعم المحلية'
            ]

        return activities[:3]  # Return top 3 activities

    def _generate_travel_tips(self, request: TravelRequest, recommendations: List[HotelRecommendation]) -> List[str]:
        """Generate travel tips"""
        tips = []

        if request.destination:
            tips.append(f'يفضل الحجز المبكر للسفر إلى {request.destination}')

        if TravelPreference.BUDGET in request.preferences:
            tips.append('ابحث عن العروض الخاصة والتخفيضات')
            tips.append('اعتبر الإقامة في شقق مفروشة لتوفير التكاليف')

        if TravelPreference.FAMILY in request.preferences:
            tips.append('تأكد من توفر غرف عائلية')
            tips.append('تحقق من المرافق المناسبة للأطفال')

        if TravelPreference.BUSINESS in request.preferences:
            tips.append('اختر فندق قريب من مراكز الأعمال')
            tips.append('تأكد من توفر خدمة الإنترنت السريع')

        tips.append('احمل جواز سفر ساري المفعول')
        tips.append('تحقق من متطلبات التأشيرة للسفر')

        return tips

    def _generate_alternatives(self, request: TravelRequest, hotels: List[Dict]) -> List[Dict]:
        """Generate alternative options"""
        alternatives = []

        # Alternative dates
        if request.check_in:
            alt_check_in = request.check_in + timedelta(days=7)
            alternatives.append({
                'type': 'alternative_dates',
                'title': 'تواريخ بديلة',
                'description': f'حاول التواريخ: {alt_check_in.strftime("%Y-%m-%d")}'
            })

        # Alternative destinations
        nearby_destinations = {
            'بغداد': ['المنصور', 'الكرادة', 'السيدية'],
            'البصرة': ['العمارة', 'البصرة القديمة'],
            'أربيل': ['دهوك', 'سليمانية']
        }

        if request.destination in nearby_destinations:
            alternatives.append({
                'type': 'alternative_destinations',
                'title': 'وجهات بديلة',
                'description': f'جرب: {", ".join(nearby_destinations[request.destination])}'
            })

        return alternatives

    def generate_response(self, request: TravelRequest, plan: TravelPlan) -> str:
        """
        Generate natural language response

        Args:
            request: Travel request
            plan: Generated travel plan

        Returns:
            Natural language response
        """
        response_parts = []

        # Greeting
        response_parts.append(f"بناءً على طلبك للسفر إلى {request.destination}، وجدت لك خيارات رائعة! 🌟")

        # Top recommendation
        if plan.recommendations:
            top_hotel = plan.recommendations[0]
            response_parts.append(f"أفضل خيار: {top_hotel.hotel_name}")
            response_parts.append(f"- الموقع: {top_hotel.location}")
            response_parts.append(f"- السعر: {top_hotel.price_per_night:,} د.ع لليلة")
            response_parts.append(f"- التقييم: ⭐ {top_hotel.rating}/5")
            response_parts.append(f"- أسباب الاختيار: {', '.join(top_hotel.match_reasons)}")

        # Total cost
        if plan.total_estimated_cost > 0:
            response_parts.append(f"التكلفة التقديرية: {plan.total_estimated_cost:,} د.ع")

        # Tips
        if plan.tips:
            response_parts.append("\nنصائح مفيدة:")
            for tip in plan.tips[:3]:
                response_parts.append(f"- {tip}")

        # Call to action
        response_parts.append("\nهل تريد أن أحجز لك هذا الفندق أو تفضل خيارات أخرى؟")

        return "\n".join(response_parts)


# Global instance
hotel_travel_assistant = HotelTravelAssistant()
