"""
Market Intelligence System
Advanced market analysis and buyer-seller-agent matching
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class MatchDimension(Enum):
    """Dimensions for matching scores"""
    LOCATION = "location"
    BUDGET = "budget"
    PROPERTY_TYPE = "property_type"
    AREA = "area"
    ROOMS = "rooms"
    FEATURES = "features"
    PURPOSE = "purpose"
    AVAILABILITY = "availability"
    PRICE_PER_M2 = "price_per_m2"


class BuyerIntentType(Enum):
    """Types of buyer intents"""
    FIRST_HOME = "first_home"
    FAMILY_HOME = "family_home"
    INVESTMENT = "investment"
    RENTAL = "rental"
    COMMERCIAL = "commercial"
    LAND_FOR_BUILDING = "land_for_building"
    VACATION = "vacation"
    RETIREMENT = "retirement"


class SellerIntentType(Enum):
    """Types of seller intents"""
    QUICK_SALE = "quick_sale"
    BEST_PRICE = "best_price"
    AGENT_ASSISTANCE = "agent_assistance"
    DIRECT_SALE = "direct_sale"
    AUCTION = "auction"
    RENTAL = "rental"


class PropertyStatus(Enum):
    """Property lifecycle statuses"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    ACTIVE = "active"
    RESERVED = "reserved"
    SOLD = "sold"
    RENTED = "rented"
    EXPIRED = "expired"
    HIDDEN = "hidden"
    REJECTED = "rejected"


class AgentVerificationStatus(Enum):
    """Agent verification statuses"""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    PENDING_REVIEW = "pending_review"
    SUSPENDED = "suspended"


@dataclass
class MatchScore:
    """Detailed match score with breakdown"""
    overall_score: float
    dimension_scores: Dict[MatchDimension, float]
    reasons: List[str]
    warnings: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'overall_score': self.overall_score,
            'dimension_scores': {
                dim.value: score for dim, score in self.dimension_scores.items()
            },
            'reasons': self.reasons,
            'warnings': self.warnings,
            'metadata': self.metadata
        }


@dataclass
class BuyerProfile:
    """Comprehensive buyer profile"""
    buyer_id: int
    name: str = None
    intent_type: BuyerIntentType = BuyerIntentType.FAMILY_HOME
    budget_min: float = None
    budget_max: float = None
    preferred_governorate: str = None
    preferred_district: str = None
    property_type_preference: str = None
    min_area: float = None
    max_area: float = None
    min_rooms: int = None
    max_rooms: int = None
    preferences: List[str] = field(default_factory=list)
    saved_searches: List[Dict] = field(default_factory=list)
    interaction_history: List[Dict] = field(default_factory=list)
    created_at: str = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'buyer_id': self.buyer_id,
            'name': self.name,
            'intent_type': self.intent_type.value,
            'budget_min': self.budget_min,
            'budget_max': self.budget_max,
            'preferred_governorate': self.preferred_governorate,
            'preferred_district': self.preferred_district,
            'property_type_preference': self.property_type_preference,
            'min_area': self.min_area,
            'max_area': self.max_area,
            'min_rooms': self.min_rooms,
            'max_rooms': self.max_rooms,
            'preferences': self.preferences,
            'saved_searches_count': len(self.saved_searches),
            'interaction_count': len(self.interaction_history),
            'created_at': self.created_at
        }


@dataclass
class MarketStatistics:
    """Market statistics from platform data"""
    entity_type: str
    filters: Dict[str, Any]
    count: int
    min_price: float = None
    max_price: float = None
    median_price: float = None
    average_price: float = None
    price_distribution: Dict = field(default_factory=dict)
    data_confidence: str = "high"  # high, medium, low
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'entity_type': self.entity_type,
            'filters': self.filters,
            'count': self.count,
            'min_price': self.min_price,
            'max_price': self.max_price,
            'median_price': self.median_price,
            'average_price': self.average_price,
            'price_distribution': self.price_distribution,
            'data_confidence': self.data_confidence,
            'timestamp': self.timestamp
        }


class MarketIntelligenceSystem:
    """
    Advanced market intelligence system
    Provides market analysis, buyer-seller matching, and recommendations
    """
    
    def __init__(self):
        self.match_weights = self._initialize_match_weights()
        self.market_cache: Dict[str, MarketStatistics] = {}
        self.buyer_profiles: Dict[int, BuyerProfile] = {}
        self.query_history: List[Dict] = []
    
    def calculate_buyer_property_match(self,
                                      buyer_profile: BuyerProfile,
                                      property_data: Dict) -> MatchScore:
        """
        Calculate match score between buyer and property
        
        Args:
            buyer_profile: Buyer's profile
            property_data: Property data
            
        Returns:
            Detailed match score with breakdown
        """
        try:
            dimension_scores = {}
            reasons = []
            warnings = []
            
            # Location match
            location_score = self._calculate_location_match(buyer_profile, property_data)
            dimension_scores[MatchDimension.LOCATION] = location_score
            if location_score > 0.8:
                reasons.append("ضمن الموقع المطلوب")
            elif location_score > 0.5:
                reasons.append("الموقع قريب من المنطقة المفضلة")
            
            # Budget match
            budget_score, budget_status = self._calculate_budget_match(buyer_profile, property_data)
            dimension_scores[MatchDimension.BUDGET] = budget_score
            if budget_status == "exact":
                reasons.append("ضمن الميزانية")
            elif budget_status == "near":
                reasons.append("قريب من الميزانية")
            elif budget_status == "over":
                warnings.append(f"أعلى من ميزانيتك")
            
            # Property type match
            type_score = self._calculate_type_match(buyer_profile, property_data)
            dimension_scores[MatchDimension.PROPERTY_TYPE] = type_score
            if type_score > 0.8:
                reasons.append("نوع العقار مطابق")
            
            # Area match
            area_score = self._calculate_area_match(buyer_profile, property_data)
            dimension_scores[MatchDimension.AREA] = area_score
            if area_score > 0.8:
                reasons.append("المساحة مناسبة")
            
            # Rooms match
            rooms_score = self._calculate_rooms_match(buyer_profile, property_data)
            dimension_scores[MatchDimension.ROOMS] = rooms_score
            if rooms_score > 0.8:
                reasons.append("عدد الغرف مطابق")
            
            # Features match
            features_score = self._calculate_features_match(buyer_profile, property_data)
            dimension_scores[MatchDimension.FEATURES] = features_score
            
            # Purpose match
            purpose_score = self._calculate_purpose_match(buyer_profile, property_data)
            dimension_scores[MatchDimension.PURPOSE] = purpose_score
            
            # Availability
            availability_score = self._calculate_availability(property_data)
            dimension_scores[MatchDimension.AVAILABILITY] = availability_score
            if availability_score < 0.5:
                warnings.append("العقار غير متاحر حاليًا")
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(dimension_scores)
            
            # Check budget difference for warning
            if budget_status == "over":
                price = property_data.get('price', 0)
                budget = buyer_profile.budget_max or 0
                if price and budget:
                    diff = price - budget
                    warnings.append(f"أعلى من ميزانيتك بـ{diff:,.0f} دينار")
            
            return MatchScore(
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                reasons=reasons,
                warnings=warnings,
                metadata={
                    'property_id': property_data.get('id'),
                    'buyer_id': buyer_profile.buyer_id,
                    'budget_status': budget_status
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating buyer-property match: {str(e)}")
            return MatchScore(overall_score=0.0, dimension_scores={}, reasons=[], warnings=[str(e)])
    
    def _calculate_location_match(self, buyer: BuyerProfile, property: Dict) -> float:
        """Calculate location match score"""
        score = 0.0
        
        buyer_gov = buyer.preferred_governorate
        prop_gov = property.get('governorate')
        
        if buyer_gov and prop_gov:
            if buyer_gov == prop_gov:
                score += 0.9
            else:
                score += 0.1  # Different governorate
        
        buyer_district = buyer.preferred_district
        prop_district = property.get('district')
        
        if buyer_district and prop_district:
            if buyer_district == prop_district:
                score += 0.9
            else:
                score += 0.3  # Different district but same governorate
        
        return min(score, 1.0)
    
    def _calculate_budget_match(self, buyer: BuyerProfile, property: Dict) -> Tuple[float, str]:
        """Calculate budget match score and status"""
        price = property.get('price', 0)
        budget_min = buyer.budget_min or 0
        budget_max = buyer.budget_max or float('inf')
        
        if price == 0:
            return 0.5, "unknown"
        
        if budget_min <= price <= budget_max:
            return 1.0, "exact"
        elif price < budget_min:
            return 0.7, "under"
        elif price > budget_max:
            # Calculate how much over budget
            over_percentage = (price - budget_max) / budget_max if budget_max > 0 else 1.0
            if over_percentage < 0.1:  # Within 10%
                return 0.8, "near"
            elif over_percentage < 0.2:  # Within 20%
                return 0.5, "near"
            else:
                return 0.2, "over"
        
        return 0.5, "unknown"
    
    def _calculate_type_match(self, buyer: BuyerProfile, property: Dict) -> float:
        """Calculate property type match"""
        buyer_type = buyer.property_type_preference
        prop_type = property.get('property_type')
        
        if buyer_type and prop_type:
            if buyer_type == prop_type:
                return 1.0
            else:
                return 0.3
        
        return 0.5
    
    def _calculate_area_match(self, buyer: BuyerProfile, property: Dict) -> float:
        """Calculate area match score"""
        prop_area = property.get('area', 0)
        min_area = buyer.min_area or 0
        max_area = buyer.max_area or float('inf')
        
        if prop_area == 0:
            return 0.5
        
        if min_area <= prop_area <= max_area:
            return 1.0
        elif prop_area < min_area:
            return 0.4
        elif prop_area > max_area:
            return 0.4
        
        return 0.5
    
    def _calculate_rooms_match(self, buyer: BuyerProfile, property: Dict) -> float:
        """Calculate rooms match score"""
        prop_rooms = property.get('rooms', 0)
        min_rooms = buyer.min_rooms or 0
        max_rooms = buyer.max_rooms or float('inf')
        
        if prop_rooms == 0:
            return 0.5
        
        if min_rooms <= prop_rooms <= max_rooms:
            return 1.0
        elif prop_rooms < min_rooms:
            return 0.3
        elif prop_rooms > max_rooms:
            return 0.3
        
        return 0.5
    
    def _calculate_features_match(self, buyer: BuyerProfile, property: Dict) -> float:
        """Calculate features match score"""
        buyer_prefs = buyer.preferences
        prop_features = property.get('features', [])
        
        if not buyer_prefs:
            return 0.5
        
        matches = sum(1 for pref in buyer_prefs if pref in prop_features)
        score = matches / len(buyer_prefs) if buyer_prefs else 0.5
        
        return score
    
    def _calculate_purpose_match(self, buyer: BuyerProfile, property: Dict) -> float:
        """Calculate purpose match score"""
        intent = buyer.intent_type
        prop_purpose = property.get('purpose')
        
        purpose_map = {
            BuyerIntentType.FAMILY_HOME: ['residential', 'family'],
            BuyerIntentType.INVESTMENT: ['investment', 'commercial'],
            BuyerIntentType.RENTAL: ['rental'],
            BuyerIntentType.COMMERCIAL: ['commercial', 'office']
        }
        
        valid_purposes = purpose_map.get(intent, [])
        
        if prop_purpose and valid_purposes:
            if prop_purpose in valid_purposes:
                return 1.0
            else:
                return 0.3
        
        return 0.5
    
    def _calculate_availability(self, property: Dict) -> float:
        """Calculate availability score"""
        status = property.get('status', 'unknown')
        
        if status == PropertyStatus.ACTIVE.value:
            return 1.0
        elif status in [PropertyStatus.PUBLISHED.value, PropertyStatus.PENDING_REVIEW.value]:
            return 0.8
        elif status in [PropertyStatus.RESERVED.value, PropertyStatus.SOLD.value, PropertyStatus.RENTED.value]:
            return 0.0
        else:
            return 0.5
    
    def _calculate_overall_score(self, dimension_scores: Dict[MatchDimension, float]) -> float:
        """Calculate overall match score from dimensions"""
        weights = self.match_weights
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for dimension, score in dimension_scores.items():
            weight = weights.get(dimension.value, 1.0)
            weighted_sum += score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def get_market_statistics(self,
                            entity_type: str = "property",
                            filters: Dict = None,
                            database_query_func = None) -> MarketStatistics:
        """
        Get market statistics from platform data
        
        Args:
            entity_type: Type of entity (property, agent, etc.)
            filters: Filters to apply
            database_query_func: Function to query database
            
        Returns:
            Market statistics
        """
        try:
            filters = filters or {}
            
            # Check cache first
            cache_key = f"{entity_type}_{str(sorted(filters.items()))}"
            if cache_key in self.market_cache:
                return self.market_cache[cache_key]
            
            # Query database (would use actual database query in production)
            if database_query_func:
                results = database_query_func(filters)
            else:
                # Placeholder - return empty stats
                results = []
            
            # Calculate statistics
            stats = self._calculate_statistics_from_results(results, filters)
            
            # Cache the result
            self.market_cache[cache_key] = stats
            
            # Log query
            self.query_history.append({
                'timestamp': datetime.now().isoformat(),
                'entity_type': entity_type,
                'filters': filters,
                'result_count': len(results)
            })
            
            logger.info(f"Calculated market statistics for {entity_type}: {len(results)} results")
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating market statistics: {str(e)}")
            return MarketStatistics(
                entity_type=entity_type,
                filters=filters,
                count=0,
                data_confidence="low"
            )
    
    def _calculate_statistics_from_results(self, results: List[Dict], filters: Dict) -> MarketStatistics:
        """Calculate statistics from query results"""
        if not results:
            return MarketStatistics(
                entity_type="property",
                filters=filters,
                count=0,
                data_confidence="low"
            )
        
        prices = [r.get('price') for r in results if r.get('price')]
        
        stats = MarketStatistics(
            entity_type="property",
            filters=filters,
            count=len(results),
            min_price=min(prices) if prices else None,
            max_price=max(prices) if prices else None,
            median_price=statistics.median(prices) if prices else None,
            average_price=statistics.mean(prices) if prices else None,
            data_confidence="high" if len(results) >= 10 else "medium"
        )
        
        # Calculate price distribution
        if prices:
            stats.price_distribution = {
                'q1': statistics.quantiles(prices, n=4)[0] if len(prices) >= 4 else min(prices),
                'q2': statistics.median(prices),
                'q3': statistics.quantiles(prices, n=4)[2] if len(prices) >= 4 else max(prices)
            }
        
        return stats
    
    def compare_market_areas(self, 
                           area1: str, 
                           area2: str,
                           property_type: str = None) -> Dict:
        """
        Compare market prices between two areas
        
        Args:
            area1: First area (district)
            area2: Second area (district)
            property_type: Property type filter
            
        Returns:
            Comparison statistics
        """
        stats1 = self.get_market_statistics(
            filters={'district': area1, 'property_type': property_type}
        )
        
        stats2 = self.get_market_statistics(
            filters={'district': area2, 'property_type': property_type}
        )
        
        comparison = {
            'area1': area1,
            'area2': area2,
            'area1_stats': stats1.to_dict(),
            'area2_stats': stats2.to_dict(),
            'price_difference': None,
            'cheaper_area': None
        }
        
        if stats1.median_price and stats2.median_price:
            comparison['price_difference'] = stats2.median_price - stats1.median_price
            comparison['cheaper_area'] = area1 if stats1.median_price < stats2.median_price else area2
        
        return comparison
    
    def calculate_price_per_m2(self, property_data: Dict) -> float:
        """Calculate price per square meter"""
        price = property_data.get('price', 0)
        area = property_data.get('area', 0)
        
        if price > 0 and area > 0:
            return price / area
        
        return 0.0
    
    def find_similar_properties(self,
                              target_property: Dict,
                              available_properties: List[Dict],
                              max_results: int = 5) -> List[Tuple[Dict, float]]:
        """
        Find properties similar to target property
        
        Args:
            target_property: Property to match against
            available_properties: Available properties
            max_results: Maximum number of results
            
        Returns:
            List of (property, similarity_score) sorted by similarity
        """
        similarities = []
        
        for prop in available_properties:
            similarity = self._calculate_property_similarity(target_property, prop)
            similarities.append((prop, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:max_results]
    
    def _calculate_property_similarity(self, prop1: Dict, prop2: Dict) -> float:
        """Calculate similarity between two properties"""
        similarity = 0.0
        
        # Location similarity
        if prop1.get('governorate') == prop2.get('governorate'):
            similarity += 0.3
            if prop1.get('district') == prop2.get('district'):
                similarity += 0.2
        
        # Type similarity
        if prop1.get('property_type') == prop2.get('property_type'):
            similarity += 0.2
        
        # Price similarity (normalized)
        price1 = prop1.get('price', 0)
        price2 = prop2.get('price', 0)
        if price1 > 0 and price2 > 0:
            price_ratio = min(price1, price2) / max(price1, price2)
            similarity += price_ratio * 0.2
        
        # Area similarity (normalized)
        area1 = prop1.get('area', 0)
        area2 = prop2.get('area', 0)
        if area1 > 0 and area2 > 0:
            area_ratio = min(area1, area2) / max(area1, area2)
            similarity += area_ratio * 0.1
        
        # Rooms similarity
        rooms1 = prop1.get('rooms', 0)
        rooms2 = prop2.get('rooms', 0)
        if rooms1 > 0 and rooms2 > 0:
            if rooms1 == rooms2:
                similarity += 0.2
        
        return min(similarity, 1.0)
    
    def _initialize_match_weights(self) -> Dict[str, float]:
        """Initialize weights for match dimensions"""
        return {
            'location': 2.0,
            'budget': 2.5,
            'property_type': 1.5,
            'area': 1.0,
            'rooms': 1.0,
            'features': 0.8,
            'purpose': 1.0,
            'availability': 0.5
        }
    
    def create_buyer_profile(self, user_id: int, profile_data: Dict) -> BuyerProfile:
        """Create or update buyer profile"""
        profile = BuyerProfile(
            buyer_id=user_id,
            name=profile_data.get('name'),
            intent_type=BuyerIntentType(profile_data.get('intent_type', 'family_home')),
            budget_min=profile_data.get('budget_min'),
            budget_max=profile_data.get('budget_max'),
            preferred_governorate=profile_data.get('governorate'),
            preferred_district=profile_data.get('district'),
            property_type_preference=profile_data.get('property_type'),
            min_area=profile_data.get('min_area'),
            max_area=profile_data.get('max_area'),
            min_rooms=profile_data.get('min_rooms'),
            max_rooms=profile_data.get('max_rooms'),
            preferences=profile_data.get('preferences', [])
        )
        
        self.buyer_profiles[user_id] = profile
        logger.info(f"Created buyer profile for user {user_id}")
        return profile
    
    def get_buyer_profile(self, user_id: int) -> Optional[BuyerProfile]:
        """Get buyer profile for user"""
        return self.buyer_profiles.get(user_id)
    
    def get_market_summary(self) -> Dict:
        """Get overall market summary"""
        return {
            'total_buyer_profiles': len(self.buyer_profiles),
            'cached_statistics_count': len(self.market_cache),
            'query_history_count': len(self.query_history),
            'data_confidence': "high" if len(self.market_cache) > 0 else "unknown"
        }


# Global instance
market_intelligence_system = MarketIntelligenceSystem()