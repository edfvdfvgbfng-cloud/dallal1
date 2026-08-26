"""
Property Intelligence System - Specialized Real Estate AI
Buyer profiles, property comparison, personalized recommendations, and advanced property analysis
"""

from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Q, Count, Avg, F, Value
from django.db.models.functions import Concat
from django.core.cache import cache
from django.utils import timezone
import logging
import json

from .models import Property, Broker
from .ai_arabic_normalizer import normalize_arabic_text, convert_arabic_numbers
from .ai_semantic_search import hybrid_search_engine

logger = logging.getLogger(__name__)


class BuyerProfileManager:
    """
    Manage buyer profiles for personalized property recommendations
    """
    
    def __init__(self):
        self.profile_cache_ttl = 86400  # 24 hours
    
    def create_profile(self, user_id: int, profile_data: Dict) -> Dict:
        """
        Create or update buyer profile
        
        Args:
            user_id: User ID
            profile_data: Profile information including preferences, budget, etc.
            
        Returns:
            Created/updated profile
        """
        try:
            # Normalize and validate profile data
            normalized_profile = self._normalize_profile_data(profile_data)
            
            # Calculate user preferences weights
            preference_weights = self._calculate_preference_weights(normalized_profile)
            
            # Complete profile structure
            complete_profile = {
                'user_id': user_id,
                'created_at': timezone.now().isoformat(),
                'updated_at': timezone.now().isoformat(),
                'profile_data': normalized_profile,
                'preference_weights': preference_weights,
                'search_history': [],
                'interaction_history': []
            }
            
            # Cache the profile
            cache_key = f"buyer_profile_{user_id}"
            cache.set(cache_key, complete_profile, timeout=self.profile_cache_ttl)
            
            logger.info(f"Buyer profile created/updated for user {user_id}")
            return complete_profile
            
        except Exception as e:
            logger.error(f"Error creating buyer profile: {str(e)}")
            return {'error': str(e)}
    
    def get_profile(self, user_id: int) -> Optional[Dict]:
        """Get buyer profile for user"""
        cache_key = f"buyer_profile_{user_id}"
        return cache.get(cache_key)
    
    def update_search_history(self, user_id: int, search_params: Dict):
        """Update user's search history"""
        profile = self.get_profile(user_id)
        if not profile:
            return
        
        search_entry = {
            'timestamp': timezone.now().isoformat(),
            'params': search_params
        }
        
        profile['search_history'].append(search_entry)
        
        # Keep only last 50 searches
        if len(profile['search_history']) > 50:
            profile['search_history'] = profile['search_history'][-50:]
        
        # Update cache
        cache_key = f"buyer_profile_{user_id}"
        cache.set(cache_key, profile, timeout=self.profile_cache_ttl)
    
    def _normalize_profile_data(self, profile_data: Dict) -> Dict:
        """Normalize and validate profile data"""
        normalized = {}
        
        # Handle budget
        if 'budget' in profile_data:
            budget = profile_data['budget']
            normalized['budget'] = {
                'min': self._normalize_price(budget.get('min')),
                'max': self._normalize_price(budget.get('max')),
                'currency': budget.get('currency', 'IQD')
            }
        
        # Handle location preferences
        if 'location' in profile_data:
            location = profile_data['location']
            normalized['location'] = {
                'governorate': normalize_arabic_text(location.get('governorate', '')),
                'district': normalize_arabic_text(location.get('district', '')),
                'area': location.get('area')
            }
        
        # Handle property type
        if 'property_type' in profile_data:
            normalized['property_type'] = profile_data['property_type']
        
        # Handle preferences
        if 'preferences' in profile_data:
            normalized['preferences'] = profile_data['preferences']
        
        # Handle purpose
        if 'purpose' in profile_data:
            normalized['purpose'] = profile_data['purpose']
        
        return normalized
    
    def _normalize_price(self, price: Any) -> Optional[int]:
        """Normalize price to integer"""
        if price is None:
            return None
        
        try:
            # Convert to integer
            return int(float(str(price).replace(',', '').replace('٬', '')))
        except (ValueError, TypeError):
            return None
    
    def _calculate_preference_weights(self, profile: Dict) -> Dict[str, float]:
        """
        Calculate preference weights based on user behavior and stated preferences
        """
        weights = {
            'location': 0.25,
            'budget': 0.25,
            'property_type': 0.15,
            'area': 0.15,
            'rooms': 0.10,
            'amenities': 0.10
        }
        
        # Adjust weights based on purpose
        purpose = profile.get('purpose', 'personal')
        if purpose == 'investment':
            weights['budget'] = 0.35  # Higher weight on budget for investment
            weights['location'] = 0.20
        elif purpose == 'family':
            weights['area'] = 0.20  # Higher weight on area for family
            weights['rooms'] = 0.15
        
        # Adjust based on stated preferences
        preferences = profile.get('preferences', [])
        if 'price_sensitive' in preferences:
            weights['budget'] = 0.35
        if 'location_important' in preferences:
            weights['location'] = 0.35
        if 'space_important' in preferences:
            weights['area'] = 0.25
        
        return weights


class PropertyComparisonEngine:
    """
    Compare multiple properties with detailed analysis
    """
    
    def compare_properties(self, property_ids: List[int], user_profile: Dict = None) -> Dict:
        """
        Compare multiple properties
        
        Args:
            property_ids: List of property IDs to compare
            user_profile: Optional user profile for personalized comparison
            
        Returns:
            Detailed comparison results
        """
        try:
            # Fetch properties
            properties = Property.objects.filter(id__in=property_ids, status='available')
            
            if len(properties) != len(property_ids):
                return {'error': 'Some properties not found or unavailable'}
            
            # Build comparison data
            comparison_data = {
                'properties': [],
                'analysis': {},
                'recommendations': []
            }
            
            for prop in properties:
                property_data = self._build_property_comparison_data(prop)
                comparison_data['properties'].append(property_data)
            
            # Analyze comparison
            comparison_data['analysis'] = self._analyze_comparison(comparison_data['properties'])
            
            # Add personalized recommendations if profile provided
            if user_profile:
                comparison_data['recommendations'] = self._generate_comparison_recommendations(
                    comparison_data['properties'], user_profile
                )
            
            return comparison_data
            
        except Exception as e:
            logger.error(f"Error comparing properties: {str(e)}")
            return {'error': str(e)}
    
    def _build_property_comparison_data(self, property: Property) -> Dict:
        """Build comparison data for a single property"""
        return {
            'id': property.id,
            'title': property.title,
            'price': property.price,
            'price_per_m2': self._calculate_price_per_m2(property),
            'area': property.area,
            'governorate': property.governorate,
            'district': property.district,
            'property_type': property.property_type,
            'rooms': property.bedrooms if hasattr(property, 'bedrooms') else None,
            'bathrooms': property.bathrooms if hasattr(property, 'bathrooms') else None,
            'age': self._calculate_property_age(property),
            'amenities': self._extract_amenities(property),
            'data_quality_score': self._calculate_data_quality_score(property)
        }
    
    def _calculate_price_per_m2(self, property: Property) -> Optional[float]:
        """Calculate price per square meter"""
        if property.area and property.area > 0 and property.price:
            return round(property.price / property.area, 2)
        return None
    
    def _calculate_property_age(self, property: Property) -> Optional[int]:
        """Calculate property age in years"""
        if property.created_at:
            age = (timezone.now().date() - property.created_at.date()).days // 365
            return age
        return None
    
    def _extract_amenities(self, property: Property) -> List[str]:
        """Extract amenities from property"""
        amenities = []
        
        # Extract from description or dedicated amenities field
        if hasattr(property, 'amenities'):
            amenities = [str(amenity) for amenity in property.amenities.all()]
        
        # Extract from description keywords
        if property.description:
            amenity_keywords = ['موقف سيارات', 'حديقة', 'مسبح', 'مصعد', 'تكييف', 'شرفة']
            for keyword in amenity_keywords:
                if keyword in property.description:
                    amenities.append(keyword)
        
        return list(set(amenities))  # Remove duplicates
    
    def _calculate_data_quality_score(self, property: Property) -> float:
        """Calculate data quality score (0-1) based on completeness"""
        score = 0.0
        total_checks = 0
        
        # Check essential fields
        if property.title: score += 0.15
        total_checks += 0.15
        
        if property.price: score += 0.20
        total_checks += 0.20
        
        if property.area: score += 0.15
        total_checks += 0.15
        
        if property.governorate: score += 0.10
        total_checks += 0.10
        
        if property.district: score += 0.10
        total_checks += 0.10
        
        if property.description: score += 0.10
        total_checks += 0.10
        
        # Check images
        if hasattr(property, 'images') and property.images.exists():
            score += 0.10
        total_checks += 0.10
        
        # Check contact info
        if property.user or property.broker:
            score += 0.10
        total_checks += 0.10
        
        return round(score / total_checks, 2) if total_checks > 0 else 0.0
    
    def _analyze_comparison(self, properties_data: List[Dict]) -> Dict:
        """Analyze comparison results"""
        analysis = {
            'price_range': {
                'min': min(p['price'] for p in properties_data if p['price']),
                'max': max(p['price'] for p in properties_data if p['price']),
                'avg': sum(p['price'] for p in properties_data if p['price']) / len(properties_data)
            },
            'area_range': {
                'min': min(p['area'] for p in properties_data if p['area']),
                'max': max(p['area'] for p in properties_data if p['area']),
                'avg': sum(p['area'] for p in properties_data if p['area']) / len(properties_data)
            },
            'best_value': self._find_best_value(properties_data),
            'most_complete': self._find_most_complete(properties_data),
            'price_leaders': self._find_price_leaders(properties_data)
        }
        
        return analysis
    
    def _find_best_value(self, properties_data: List[Dict]) -> Dict:
        """Find best value property based on price per m2"""
        valid_properties = [p for p in properties_data if p.get('price_per_m2')]
        
        if not valid_properties:
            return None
        
        best_value = min(valid_properties, key=lambda x: x['price_per_m2'])
        return {
            'property_id': best_value['id'],
            'price_per_m2': best_value['price_per_m2'],
            'title': best_value['title']
        }
    
    def _find_most_complete(self, properties_data: List[Dict]) -> Dict:
        """Find property with highest data quality score"""
        most_complete = max(properties_data, key=lambda x: x.get('data_quality_score', 0))
        return {
            'property_id': most_complete['id'],
            'data_quality_score': most_complete['data_quality_score'],
            'title': most_complete['title']
        }
    
    def _find_price_leaders(self, properties_data: List[Dict]) -> Dict:
        """Find cheapest and most expensive properties"""
        valid_properties = [p for p in properties_data if p.get('price')]
        
        if not valid_properties:
            return {}
        
        cheapest = min(valid_properties, key=lambda x: x['price'])
        most_expensive = max(valid_properties, key=lambda x: x['price'])
        
        return {
            'cheapest': {
                'property_id': cheapest['id'],
                'price': cheapest['price'],
                'title': cheapest['title']
            },
            'most_expensive': {
                'property_id': most_expensive['id'],
                'price': most_expensive['price'],
                'title': most_expensive['title']
            }
        }
    
    def _generate_comparison_recommendations(self, properties_data: List[Dict], user_profile: Dict) -> List[Dict]:
        """Generate personalized recommendations based on comparison"""
        recommendations = []
        preference_weights = user_profile.get('preference_weights', {})
        
        for prop in properties_data:
            score = 0.0
            reasons = []
            
            # Budget fit
            user_budget = user_profile.get('profile_data', {}).get('budget', {})
            if user_budget.get('max') and prop['price'] <= user_budget['max']:
                score += preference_weights.get('budget', 0.25)
                reasons.append('الميزانية مناسبة')
            
            # Location match
            user_location = user_profile.get('profile_data', {}).get('location', {})
            if user_location.get('governorate') == prop['governorate']:
                score += preference_weights.get('location', 0.25)
                reasons.append('الموقع متطابق')
            
            # Property type match
            user_property_type = user_profile.get('profile_data', {}).get('property_type')
            if user_property_type == prop['property_type']:
                score += preference_weights.get('property_type', 0.15)
                reasons.append('نوع العقار متطابق')
            
            # Area fit
            if prop['area']:
                score += preference_weights.get('area', 0.15)
                reasons.append('المساحة مناسبة')
            
            # Data quality bonus
            score += prop['data_quality_score'] * 0.10
            
            recommendations.append({
                'property_id': prop['id'],
                'title': prop['title'],
                'match_score': round(score, 2),
                'reasons': reasons
            })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        return recommendations


class PropertyRecommendationEngine:
    """
    Personalized property recommendation engine
    """
    
    def __init__(self):
        self.buyer_profile_manager = BuyerProfileManager()
        self.comparison_engine = PropertyComparisonEngine()
    
    def get_recommendations(self, user_id: int, limit: int = 10) -> Dict:
        """
        Get personalized property recommendations
        
        Args:
            user_id: User ID
            limit: Maximum number of recommendations
            
        Returns:
            Personalized recommendations
        """
        try:
            # Get user profile
            profile = self.buyer_profile_manager.get_profile(user_id)
            if not profile:
                return {'error': 'No buyer profile found'}
            
            # Get profile data
            profile_data = profile.get('profile_data', {})
            preference_weights = profile.get('preference_weights', {})
            
            # Build query based on profile
            properties = self._build_recommendation_query(profile_data)
            
            # Apply personalized ranking
            ranked_properties = self._apply_personalized_ranking(
                properties, profile_data, preference_weights
            )
            
            # Generate recommendations
            recommendations = []
            for prop in ranked_properties[:limit]:
                recommendation = self._build_recommendation(prop, profile_data, preference_weights)
                recommendations.append(recommendation)
            
            return {
                'recommendations': recommendations,
                'profile_used': profile_data,
                'total_found': len(ranked_properties)
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {'error': str(e)}
    
    def _build_recommendation_query(self, profile_data: Dict):
        """Build property query based on profile"""
        from .models import Property
        
        queryset = Property.objects.filter(status='available')
        
        # Filter by budget
        budget = profile_data.get('budget', {})
        if budget.get('max'):
            queryset = queryset.filter(price__lte=budget['max'])
        if budget.get('min'):
            queryset = queryset.filter(price__gte=budget['min'])
        
        # Filter by location
        location = profile_data.get('location', {})
        if location.get('governorate'):
            queryset = queryset.filter(governorate=location['governorate'])
        if location.get('district'):
            queryset = queryset.filter(district=location['district'])
        
        # Filter by property type
        if profile_data.get('property_type'):
            queryset = queryset.filter(property_type=profile_data['property_type'])
        
        # Optimize query
        queryset = queryset.select_related('user', 'broker').prefetch_related('images')
        
        return queryset
    
    def _apply_personalized_ranking(self, properties, profile_data: Dict, weights: Dict) -> List:
        """Apply personalized ranking to properties"""
        ranked_properties = []
        
        for prop in properties:
            score = 0.0
            
            # Calculate match score based on weights
            if profile_data.get('budget', {}).get('max') and prop.price <= profile_data['budget']['max']:
                score += weights.get('budget', 0.25)
            
            if profile_data.get('location', {}).get('governorate') == prop.governorate:
                score += weights.get('location', 0.25)
            
            if profile_data.get('property_type') == prop.property_type:
                score += weights.get('property_type', 0.15)
            
            if profile_data.get('preferences'):
                # Additional preference matching
                if 'quiet' in profile_data['preferences']:
                    score += 0.05
                if 'near_schools' in profile_data['preferences']:
                    score += 0.05
            
            # Add data quality score
            quality_score = self.comparison_engine._calculate_data_quality_score(prop)
            score += quality_score * 0.10
            
            ranked_properties.append({
                'property': prop,
                'match_score': score
            })
        
        # Sort by match score
        ranked_properties.sort(key=lambda x: x['match_score'], reverse=True)
        
        return [item['property'] for item in ranked_properties]
    
    def _build_recommendation(self, property, profile_data: Dict, weights: Dict) -> Dict:
        """Build recommendation object"""
        score = 0.0
        reasons = []
        
        # Calculate match score and reasons
        if profile_data.get('budget', {}).get('max') and property.price <= profile_data['budget']['max']:
            score += weights.get('budget', 0.25)
            reasons.append('الميزانية مناسبة')
        
        if profile_data.get('location', {}).get('governorate') == property.governorate:
            score += weights.get('location', 0.25)
            reasons.append('الموقع متطابق')
        
        if profile_data.get('property_type') == property.property_type:
            score += weights.get('property_type', 0.15)
            reasons.append('نوع العقار متطابق')
        
        # Calculate price per m2
        price_per_m2 = None
        if property.area and property.area > 0:
            price_per_m2 = round(property.price / property.area, 2)
        
        return {
            'id': property.id,
            'title': property.title,
            'price': property.price,
            'price_per_m2': price_per_m2,
            'area': property.area,
            'governorate': property.governorate,
            'district': property.district,
            'property_type': property.property_type,
            'match_score': round(score, 2),
            'match_reasons': reasons,
            'created_at': property.created_at.isoformat() if property.created_at else None
        }


class PropertyQAEngine:
    """
    Property Q&A engine for answering specific questions about properties
    """
    
    def answer_property_question(self, property_id: int, question: str) -> Dict:
        """
        Answer a specific question about a property
        
        Args:
            property_id: Property ID
            question: User's question
            
        Returns:
            Answer to the question
        """
        try:
            # Get property
            property = Property.objects.filter(id=property_id).first()
            if not property:
                return {'error': 'Property not found'}
            
            # Normalize question
            normalized_question = normalize_arabic_text(question.lower())
            
            # Extract question type
            question_type = self._classify_question(normalized_question)
            
            # Generate answer based on question type
            answer = self._generate_answer(property, question_type, normalized_question)
            
            return {
                'property_id': property_id,
                'question': question,
                'answer': answer,
                'question_type': question_type
            }
            
        except Exception as e:
            logger.error(f"Error answering property question: {str(e)}")
            return {'error': str(e)}
    
    def _classify_question(self, question: str) -> str:
        """Classify the type of question"""
        question_patterns = {
            'price': ['سعر', 'كم', 'شكد', 'بكام', 'ثمن'],
            'area': ['مساحة', 'كم متر', 'شكد متر', 'كبير'],
            'location': ['وين', 'أين', 'موقع', 'محافظة', 'منطقة'],
            'rooms': ['غرف', 'كم غرفة', 'عدد الغرف'],
            'contact': ['اتصال', 'تواصل', 'رقم', 'دلال'],
            'amenities': ['مواصفات', 'مميزات', 'خدمات'],
            'status': ['متاح', 'مباع', 'حالة']
        }
        
        for question_type, patterns in question_patterns.items():
            if any(pattern in question for pattern in patterns):
                return question_type
        
        return 'general'
    
    def _generate_answer(self, property: Property, question_type: str, question: str) -> str:
        """Generate answer based on question type"""
        if question_type == 'price':
            if property.price:
                return f"سعر هذا العقار هو {property.price:,} دينار"
            else:
                return "السعر غير محدد في الإعلان"
        
        elif question_type == 'area':
            if property.area:
                return f"مساحة العقار هي {property.area} متر مربع"
            else:
                return "المساحة غير محددة في الإعلان"
        
        elif question_type == 'location':
            location_parts = []
            if property.governorate:
                location_parts.append(f"محافظة {property.governorate}")
            if property.district:
                location_parts.append(f"منطقة {property.district}")
            
            if location_parts:
                return f"العقار موجود في {' - '.join(location_parts)}"
            else:
                return "الموقع غير محدد بالكامل في الإعلان"
        
        elif question_type == 'rooms':
            if hasattr(property, 'bedrooms') and property.bedrooms:
                return f"العقار يحتوي على {property.bedrooms} غرفة"
            else:
                return "عدد الغرف غير محدد في الإعلان"
        
        elif question_type == 'contact':
            if property.broker:
                return f"يمكنك التواصل مع الدلال {property.broker.name} للاستفسار عن هذا العقار"
            elif property.user:
                return f"يمكنك التواصل مع المالك للاستفسار عن هذا العقار"
            else:
                return "معلومات الاتصال غير متوفرة في الإعلان"
        
        elif question_type == 'amenities':
            amenities = self.comparison_engine._extract_amenities(property)
            if amenities:
                return f"مواصفات العقار تشمل: {', '.join(amenities)}"
            else:
                return "المواصفات التفصيلية غير مذكورة في الإعلان"
        
        elif question_type == 'status':
            return f"حالة العقار: {property.status}"
        
        else:
            return "أحتاج مزيد من التفاصيل للإجابة على سؤالك. هل يمكنك أن تكون أكثر تحديدًا؟"


# Global instances
buyer_profile_manager = BuyerProfileManager()
property_comparison_engine = PropertyComparisonEngine()
property_recommendation_engine = PropertyRecommendationEngine()
property_qa_engine = PropertyQAEngine()