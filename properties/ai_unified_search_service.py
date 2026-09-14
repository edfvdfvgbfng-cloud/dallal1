"""
AI Search Service
Unified search service for all content types
Queries actual database and returns matching results
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator

from .models import (
    Property, Hotel, Resort, Job, ServiceProvider, 
    ServiceAdvertisement, Auction, Broker, Country, City
)
from .ai_smart_intent_detection import Intent

logger = logging.getLogger(__name__)


class AISearchService:
    """
    Unified search service for all content types
    Routes to appropriate models based on intent
    """
    
    def __init__(self):
        self.result_limit = 10  # Limit results per search
    
    def search(self, intent: str, filters: Dict, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute search based on intent and filters
        
        Args:
            intent: Detected intent
            filters: Extracted filters
            user_id: User ID (for permission checks)
            
        Returns:
            Dict containing:
            - results: List of matching items
            - total_count: Total matching items
            - metadata: Search metadata
        """
        logger.info(f"Searching with intent: {intent}, filters: {filters}")
        
        try:
            if intent in [Intent.BUY_PROPERTY, Intent.SELL_PROPERTY, Intent.RENT_PROPERTY, Intent.SEARCH_PROPERTY]:
                return self._search_properties(filters, user_id)
            elif intent == Intent.SEARCH_HOTEL:
                return self._search_hotels(filters, user_id)
            elif intent == Intent.SEARCH_RESORT:
                return self._search_resorts(filters, user_id)
            elif intent == Intent.SEARCH_JOB:
                return self._search_jobs(filters, user_id)
            elif intent == Intent.SEARCH_SERVICE:
                return self._search_services(filters, user_id)
            elif intent == Intent.SEARCH_AUCTION:
                return self._search_auctions(filters, user_id)
            elif intent == Intent.SEARCH_BROKER:
                return self._search_brokers(filters, user_id)
            else:
                return {
                    'results': [],
                    'total_count': 0,
                    'metadata': {'error': 'Unsupported intent for search'}
                }
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return {
                'results': [],
                'total_count': 0,
                'metadata': {'error': str(e)}
            }
    
    def _search_properties(self, filters: Dict, user_id: Optional[int]) -> Dict[str, Any]:
        """Search properties in database"""
        queryset = Property.objects.filter(status='published')
        
        # Location type (inside/outside Iraq)
        location_type = filters.get('location_type', 'inside_iraq')
        if location_type == 'outside_iraq':
            queryset = queryset.filter(country__isnull=False)
        else:
            queryset = queryset.filter(country__isnull=True)
        
        # Location (governorate/city)
        location = filters.get('location')
        if location:
            if location_type == 'outside_iraq':
                queryset = queryset.filter(
                    Q(city_outside__name__icontains=location) |
                    Q(country__name__icontains=location)
                )
            else:
                queryset = queryset.filter(
                    Q(governorate__icontains=location) |
                    Q(city__icontains=location)
                )
        
        # Property type
        property_type = filters.get('property_type')
        if property_type:
            queryset = queryset.filter(type__icontains=property_type)
        
        # Purpose (sale/rent/investment)
        purpose = filters.get('purpose')
        if purpose:
            queryset = queryset.filter(purpose=purpose)
        
        # Price
        price = filters.get('price')
        if price and isinstance(price, dict):
            price_value = price.get('value')
            if price_value:
                queryset = queryset.filter(price__lte=price_value)
        
        # Area
        area = filters.get('area')
        if area:
            queryset = queryset.filter(area__gte=area)
        
        # Rooms
        rooms = filters.get('rooms')
        if rooms:
            queryset = queryset.filter(rooms__gte=rooms)
        
        # Count total
        total_count = queryset.count()
        
        # Limit results
        results = list(queryset[:self.result_limit])
        
        # Calculate match scores
        scored_results = []
        for result in results:
            score = self._calculate_property_match_score(result, filters)
            scored_results.append({
                'item': result,
                'score': score,
                'type': 'property',
                'url': f"/property/{result.slug}/" if result.slug else f"/property/id/{result.id}/"
            })
        
        # Sort by score
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'results': scored_results,
            'total_count': total_count,
            'metadata': {
                'intent': 'property_search',
                'filters_applied': filters,
                'limit': self.result_limit
            }
        }
    
    def _search_hotels(self, filters: Dict, user_id: Optional[int]) -> Dict[str, Any]:
        """Search hotels in database"""
        queryset = Hotel.objects.all()
        
        # Location
        location = filters.get('city')
        if location:
            queryset = queryset.filter(
                Q(governorate__icontains=location) |
                Q(city__icontains=location)
            )
        
        # Guests
        guests = filters.get('guests')
        if guests:
            # Filter hotels that can accommodate guests
            queryset = queryset.filter(capacity__gte=guests)
        
        # Star rating
        star_rating = filters.get('star_rating')
        if star_rating:
            queryset = queryset.filter(star_rating=star_rating)
        
        # Price
        price = filters.get('price')
        if price and isinstance(price, dict):
            price_value = price.get('value')
            if price_value:
                queryset = queryset.filter(price_per_night__lte=price_value)
        
        # Count total
        total_count = queryset.count()
        
        # Limit results
        results = list(queryset[:self.result_limit])
        
        # Calculate match scores
        scored_results = []
        for result in results:
            score = self._calculate_hotel_match_score(result, filters)
            scored_results.append({
                'item': result,
                'score': score,
                'type': 'hotel',
                'url': f"/hotels/{result.id}/"
            })
        
        # Sort by score
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'results': scored_results,
            'total_count': total_count,
            'metadata': {
                'intent': 'hotel_search',
                'filters_applied': filters,
                'limit': self.result_limit
            }
        }
    
    def _search_resorts(self, filters: Dict, user_id: Optional[int]) -> Dict[str, Any]:
        """Search resorts in database"""
        # Search both inside and outside Iraq resorts
        from .models import ResortInsideIraq, ResortOutsideIraq
        
        results = []
        total_count = 0
        
        # Search inside Iraq
        queryset_inside = ResortInsideIraq.objects.filter(status='published')
        location = filters.get('city')
        if location:
            queryset_inside = queryset_inside.filter(
                Q(governorate__icontains=location) |
                Q(city__icontains=location)
            )
        
        total_count += queryset_inside.count()
        for result in queryset_inside[:self.result_limit]:
            score = self._calculate_resort_match_score(result, filters)
            results.append({
                'item': result,
                'score': score,
                'type': 'resort_inside',
                'url': f"/resorts-inside-iraq/{result.id}/"
            })
        
        # Search outside Iraq
        queryset_outside = ResortOutsideIraq.objects.filter(status='published')
        if location:
            queryset_outside = queryset_outside.filter(
                Q(country__name__icontains=location) |
                Q(city__name__icontains=location)
            )
        
        total_count += queryset_outside.count()
        for result in queryset_outside[:self.result_limit]:
            score = self._calculate_resort_match_score(result, filters)
            results.append({
                'item': result,
                'score': score,
                'type': 'resort_outside',
                'url': f"/resorts-outside-iraq/{result.id}/"
            })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'results': results[:self.result_limit],
            'total_count': total_count,
            'metadata': {
                'intent': 'resort_search',
                'filters_applied': filters,
                'limit': self.result_limit
            }
        }
    
    def _search_jobs(self, filters: Dict, user_id: Optional[int]) -> Dict[str, Any]:
        """Search jobs in database"""
        queryset = Job.objects.filter(status='active')
        
        # Location
        location = filters.get('location')
        if location:
            queryset = queryset.filter(
                Q(governorate__icontains=location) |
                Q(city__icontains=location)
            )
        
        # Job title
        job_title = filters.get('job_title')
        if job_title:
            queryset = queryset.filter(title__icontains=job_title)
        
        # Salary
        salary = filters.get('salary')
        if salary and isinstance(salary, dict):
            salary_value = salary.get('value')
            if salary_value:
                queryset = queryset.filter(salary_min__lte=salary_value)
        
        # Count total
        total_count = queryset.count()
        
        # Limit results
        results = list(queryset[:self.result_limit])
        
        # Calculate match scores
        scored_results = []
        for result in results:
            score = self._calculate_job_match_score(result, filters)
            scored_results.append({
                'item': result,
                'score': score,
                'type': 'job',
                'url': f"/jobs/{result.slug}/"
            })
        
        # Sort by score
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'results': scored_results,
            'total_count': total_count,
            'metadata': {
                'intent': 'job_search',
                'filters_applied': filters,
                'limit': self.result_limit
            }
        }
    
    def _search_services(self, filters: Dict, user_id: Optional[int]) -> Dict[str, Any]:
        """Search services in database"""
        queryset = ServiceAdvertisement.objects.filter(status='published')
        
        # Location
        location = filters.get('location')
        if location:
            queryset = queryset.filter(
                Q(governorate__icontains=location) |
                Q(city__icontains=location)
            )
        
        # Service type
        service_type = filters.get('service_type')
        if service_type:
            queryset = queryset.filter(service_type__icontains=service_type)
        
        # Price
        price = filters.get('price')
        if price and isinstance(price, dict):
            price_value = price.get('value')
            if price_value:
                queryset = queryset.filter(price__lte=price_value)
        
        # Count total
        total_count = queryset.count()
        
        # Limit results
        results = list(queryset[:self.result_limit])
        
        # Calculate match scores
        scored_results = []
        for result in results:
            score = self._calculate_service_match_score(result, filters)
            scored_results.append({
                'item': result,
                'score': score,
                'type': 'service',
                'url': f"/services/{result.id}/"
            })
        
        # Sort by score
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'results': scored_results,
            'total_count': total_count,
            'metadata': {
                'intent': 'service_search',
                'filters_applied': filters,
                'limit': self.result_limit
            }
        }
    
    def _search_auctions(self, filters: Dict, user_id: Optional[int]) -> Dict[str, Any]:
        """Search auctions in database"""
        queryset = Auction.objects.filter(status='active')
        
        # Location
        location = filters.get('location')
        if location:
            queryset = queryset.filter(
                Q(governorate__icontains=location) |
                Q(city__icontains=location)
            )
        
        # Property type
        property_type = filters.get('property_type')
        if property_type:
            queryset = queryset.filter(property__type__icontains=property_type)
        
        # Max bid
        max_bid = filters.get('max_bid')
        if max_bid and isinstance(max_bid, dict):
            bid_value = max_bid.get('value')
            if bid_value:
                queryset = queryset.filter(starting_price__lte=bid_value)
        
        # Count total
        total_count = queryset.count()
        
        # Limit results
        results = list(queryset[:self.result_limit])
        
        # Calculate match scores
        scored_results = []
        for result in results:
            score = self._calculate_auction_match_score(result, filters)
            scored_results.append({
                'item': result,
                'score': score,
                'type': 'auction',
                'url': f"/auctions/{result.id}/"
            })
        
        # Sort by score
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'results': scored_results,
            'total_count': total_count,
            'metadata': {
                'intent': 'auction_search',
                'filters_applied': filters,
                'limit': self.result_limit
            }
        }
    
    def _search_brokers(self, filters: Dict, user_id: Optional[int]) -> Dict[str, Any]:
        """Search brokers in database"""
        queryset = Broker.objects.filter(is_active=True)
        
        # Location
        location = filters.get('location')
        if location:
            queryset = queryset.filter(
                Q(governorate__icontains=location) |
                Q(city__icontains=location)
            )
        
        # Count total
        total_count = queryset.count()
        
        # Limit results
        results = list(queryset[:self.result_limit])
        
        # Calculate match scores
        scored_results = []
        for result in results:
            score = self._calculate_broker_match_score(result, filters)
            scored_results.append({
                'item': result,
                'score': score,
                'type': 'broker',
                'url': f"/broker/{result.id}/"
            })
        
        # Sort by score
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'results': scored_results,
            'total_count': total_count,
            'metadata': {
                'intent': 'broker_search',
                'filters_applied': filters,
                'limit': self.result_limit
            }
        }
    
    def _calculate_property_match_score(self, property_obj, filters: Dict) -> float:
        """Calculate match score for property"""
        score = 0.0
        
        # Location match (30%)
        location = filters.get('location')
        if location:
            if (property_obj.governorate and location.lower() in property_obj.governorate.lower()) or \
               (property_obj.city and location.lower() in property_obj.city.lower()):
                score += 0.30
        
        # Price match (25%)
        price = filters.get('price')
        if price and isinstance(price, dict) and property_obj.price:
            price_value = price.get('value')
            if price_value:
                # Calculate how close the price is
                price_diff = abs(property_obj.price - price_value) / price_value
                score += max(0, 0.25 - price_diff * 0.25)
        
        # Property type match (15%)
        property_type = filters.get('property_type')
        if property_type and property_obj.type:
            if property_type.lower() in property_obj.type.lower():
                score += 0.15
        
        # Area match (10%)
        area = filters.get('area')
        if area and property_obj.area:
            area_diff = abs(property_obj.area - area) / area
            score += max(0, 0.10 - area_diff * 0.10)
        
        # Rooms match (10%)
        rooms = filters.get('rooms')
        if rooms and property_obj.rooms:
            if property_obj.rooms >= rooms:
                score += 0.10
        
        # Purpose match (10%)
        purpose = filters.get('purpose')
        if purpose and property_obj.purpose:
            if purpose == property_obj.purpose:
                score += 0.10
        
        return min(score, 1.0)
    
    def _calculate_hotel_match_score(self, hotel_obj, filters: Dict) -> float:
        """Calculate match score for hotel"""
        score = 0.0
        
        # Location match (40%)
        location = filters.get('city')
        if location:
            if (hotel_obj.governorate and location.lower() in hotel_obj.governorate.lower()) or \
               (hotel_obj.city and location.lower() in hotel_obj.city.lower()):
                score += 0.40
        
        # Guests match (30%)
        guests = filters.get('guests')
        if guests and hotel_obj.capacity:
            if hotel_obj.capacity >= guests:
                score += 0.30
        
        # Star rating match (20%)
        star_rating = filters.get('star_rating')
        if star_rating and hotel_obj.star_rating:
            if hotel_obj.star_rating >= star_rating:
                score += 0.20
        
        # Price match (10%)
        price = filters.get('price')
        if price and isinstance(price, dict) and hotel_obj.price_per_night:
            price_value = price.get('value')
            if price_value:
                price_diff = abs(hotel_obj.price_per_night - price_value) / price_value
                score += max(0, 0.10 - price_diff * 0.10)
        
        return min(score, 1.0)
    
    def _calculate_resort_match_score(self, resort_obj, filters: Dict) -> float:
        """Calculate match score for resort"""
        score = 0.0
        
        # Location match (40%)
        location = filters.get('city')
        if location:
            if hasattr(resort_obj, 'governorate') and resort_obj.governorate and location.lower() in resort_obj.governorate.lower():
                score += 0.40
            elif hasattr(resort_obj, 'city') and resort_obj.city and location.lower() in resort_obj.city.lower():
                score += 0.40
        
        # Capacity match (30%)
        capacity = filters.get('capacity')
        if capacity and hasattr(resort_obj, 'capacity') and resort_obj.capacity:
            if resort_obj.capacity >= capacity:
                score += 0.30
        
        # Family suitability (20%)
        family_suitable = filters.get('family_suitable')
        if family_suitable and hasattr(resort_obj, 'is_family_friendly') and resort_obj.is_family_friendly:
            score += 0.20
        
        # Price match (10%)
        price = filters.get('price')
        if price and isinstance(price, dict) and hasattr(resort_obj, 'price_per_night'):
            price_value = price.get('value')
            if price_value and resort_obj.price_per_night:
                price_diff = abs(resort_obj.price_per_night - price_value) / price_value
                score += max(0, 0.10 - price_diff * 0.10)
        
        return min(score, 1.0)
    
    def _calculate_job_match_score(self, job_obj, filters: Dict) -> float:
        """Calculate match score for job"""
        score = 0.0
        
        # Location match (40%)
        location = filters.get('location')
        if location:
            if (job_obj.governorate and location.lower() in job_obj.governorate.lower()) or \
               (job_obj.city and location.lower() in job_obj.city.lower()):
                score += 0.40
        
        # Job title match (30%)
        job_title = filters.get('job_title')
        if job_title and job_obj.title:
            if job_title.lower() in job_obj.title.lower():
                score += 0.30
        
        # Salary match (30%)
        salary = filters.get('salary')
        if salary and isinstance(salary, dict) and job_obj.salary_min:
            salary_value = salary.get('value')
            if salary_value:
                salary_diff = abs(job_obj.salary_min - salary_value) / salary_value
                score += max(0, 0.30 - salary_diff * 0.30)
        
        return min(score, 1.0)
    
    def _calculate_service_match_score(self, service_obj, filters: Dict) -> float:
        """Calculate match score for service"""
        score = 0.0
        
        # Location match (50%)
        location = filters.get('location')
        if location:
            if (service_obj.governorate and location.lower() in service_obj.governorate.lower()) or \
               (service_obj.city and location.lower() in service_obj.city.lower()):
                score += 0.50
        
        # Service type match (30%)
        service_type = filters.get('service_type')
        if service_type and service_obj.service_type:
            if service_type.lower() in service_obj.service_type.lower():
                score += 0.30
        
        # Price match (20%)
        price = filters.get('price')
        if price and isinstance(price, dict) and service_obj.price:
            price_value = price.get('value')
            if price_value:
                price_diff = abs(service_obj.price - price_value) / price_value
                score += max(0, 0.20 - price_diff * 0.20)
        
        return min(score, 1.0)
    
    def _calculate_auction_match_score(self, auction_obj, filters: Dict) -> float:
        """Calculate match score for auction"""
        score = 0.0
        
        # Location match (40%)
        location = filters.get('location')
        if location:
            if (auction_obj.governorate and location.lower() in auction_obj.governorate.lower()) or \
               (auction_obj.city and location.lower() in auction_obj.city.lower()):
                score += 0.40
        
        # Property type match (30%)
        property_type = filters.get('property_type')
        if property_type and auction_obj.property and auction_obj.property.type:
            if property_type.lower() in auction_obj.property.type.lower():
                score += 0.30
        
        # Max bid match (30%)
        max_bid = filters.get('max_bid')
        if max_bid and isinstance(max_bid, dict) and auction_obj.starting_price:
            bid_value = max_bid.get('value')
            if bid_value:
                bid_diff = abs(auction_obj.starting_price - bid_value) / bid_value
                score += max(0, 0.30 - bid_diff * 0.30)
        
        return min(score, 1.0)
    
    def _calculate_broker_match_score(self, broker_obj, filters: Dict) -> float:
        """Calculate match score for broker"""
        score = 0.0
        
        # Location match (60%)
        location = filters.get('location')
        if location:
            if (broker_obj.governorate and location.lower() in broker_obj.governorate.lower()) or \
               (broker_obj.city and location.lower() in broker_obj.city.lower()):
                score += 0.60
        
        # Active properties count (20%)
        if hasattr(broker_obj, 'active_properties_count'):
            score += min(broker_obj.active_properties_count() / 10, 0.20)
        
        # Rating (20%)
        if hasattr(broker_obj, 'rating') and broker_obj.rating:
            score += min(broker_obj.rating / 5, 0.20)
        
        return min(score, 1.0)


# Global instance
ai_search_service = AISearchService()
