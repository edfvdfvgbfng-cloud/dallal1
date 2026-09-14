"""
أدوات الإعلانات المستهدفة للبناء
Targeted Advertising Utilities for Building Projects
"""

from django.db.models import Q, Sum
from django.utils import timezone
from .models import BuildingAdvertisement, AdMatch, Property, Broker
from .constants import IRAQ_GOVERNORATES


def match_advertisement_with_targets(advertisement):
    """
    مطابقة إعلان البناء مع الأهداف المحتملة (عقارات، دلالين، مستخدمين)
    Match building advertisement with potential targets (properties, brokers, users)
    """
    matches = []
    
    # Match with properties
    property_matches = match_with_properties(advertisement)
    matches.extend(property_matches)
    
    # Match with brokers
    broker_matches = match_with_brokers(advertisement)
    matches.extend(broker_matches)
    
    # Save matches
    for match_data in matches:
        AdMatch.objects.create(
            advertisement=advertisement,
            **match_data
        )
    
    # Update match count
    advertisement.increment_matches()
    
    return matches


def match_with_properties(advertisement):
    """
    مطابقة إعلان البناء مع العقارات المتاحة
    Match building advertisement with available properties
    """
    matches = []
    
    # Build query for matching properties
    query = Q()
    
    # Location matching
    if advertisement.governorate:
        query &= Q(governorate=advertisement.governorate)
    
    if advertisement.city:
        query &= Q(city__icontains=advertisement.city)
    
    if advertisement.district:
        query &= Q(district__icontains=advertisement.district)
    
    # Property type matching
    property_type_mapping = {
        'house': ['house', 'villa'],
        'apartment': ['apartment'],
        'villa': ['villa', 'house'],
        'building': ['building', 'land'],
        'commercial': ['commercial', 'shop', 'office'],
    }
    
    if advertisement.property_type in property_type_mapping:
        query &= Q(type__in=property_type_mapping[advertisement.property_type])
    
    # Budget matching (property price should be within ad budget range)
    if advertisement.min_budget and advertisement.max_budget:
        query &= Q(price__gte=advertisement.min_budget, price__lte=advertisement.max_budget)
    
    # Only match with available properties
    query &= Q(status='available')
    
    # Get matching properties
    matching_properties = Property.objects.filter(query)[:20]  # Limit to top 20 matches
    
    for property_obj in matching_properties:
        match_score = calculate_property_match_score(advertisement, property_obj)
        
        if match_score > 0:
            match_reasons = {
                'location_match': check_location_match(advertisement, property_obj),
                'budget_match': check_budget_match(advertisement, property_obj),
                'type_match': check_type_match(advertisement, property_obj),
                'area_match': check_area_match(advertisement, property_obj),
            }
            
            matches.append({
                'matched_property': property_obj,
                'match_score': match_score,
                'match_reasons': match_reasons,
            })
    
    return matches


def match_with_brokers(advertisement):
    """
    مطابقة إعلان البناء مع الدلالين
    Match building advertisement with brokers
    """
    matches = []
    
    # Build query for matching brokers
    query = Q()
    
    # Location matching
    if advertisement.governorate:
        query &= Q(governorate=advertisement.governorate)
    
    # Only match with active and verified brokers
    query &= Q(is_active=True, is_verified=True)
    
    # Get matching brokers
    matching_brokers = Broker.objects.filter(query)[:10]  # Limit to top 10 matches
    
    for broker in matching_brokers:
        match_score = calculate_broker_match_score(advertisement, broker)
        
        if match_score > 0:
            match_reasons = {
                'location_match': check_broker_location_match(advertisement, broker),
                'experience_match': check_broker_experience_match(advertisement, broker),
                'specialization_match': check_broker_specialization_match(advertisement, broker),
            }
            
            matches.append({
                'matched_broker': broker,
                'match_score': match_score,
                'match_reasons': match_reasons,
            })
    
    return matches


def calculate_property_match_score(advertisement, property_obj):
    """
    حساب درجة تطابق العقار مع إعلان البناء
    Calculate property match score with building advertisement
    """
    score = 0
    
    # Location match (weight: 2)
    if advertisement.governorate == property_obj.governorate:
        score += 2
        if advertisement.city and property_obj.city and advertisement.city.lower() in property_obj.city.lower():
            score += 1
        if advertisement.district and property_obj.district and advertisement.district.lower() in property_obj.district.lower():
            score += 1
    
    # Budget match (weight: 2)
    if advertisement.min_budget and advertisement.max_budget:
        if advertisement.min_budget <= property_obj.price <= advertisement.max_budget:
            score += 2
        elif property_obj.price < advertisement.min_budget:
            score += 1  # Property is cheaper than minimum budget (good for buyer)
    
    # Type match (weight: 1)
    type_mapping = {
        'house': ['house', 'villa'],
        'apartment': ['apartment'],
        'villa': ['villa', 'house'],
        'building': ['building', 'land'],
        'commercial': ['commercial', 'shop', 'office'],
    }
    
    if advertisement.property_type in type_mapping:
        if property_obj.type in type_mapping[advertisement.property_type]:
            score += 1
    
    # Area match (weight: 1)
    if advertisement.estimated_area and property_obj.area:
        area_diff = abs(advertisement.estimated_area - property_obj.area)
        if area_diff <= (advertisement.estimated_area * 0.2):  # Within 20% difference
            score += 1
    
    return min(score, 5)  # Maximum score is 5


def calculate_broker_match_score(advertisement, broker):
    """
    حساب درجة تطابق الدلال مع إعلان البناء
    Calculate broker match score with building advertisement
    """
    score = 0
    
    # Location match (weight: 2)
    if advertisement.governorate == broker.governorate:
        score += 2
    
    # Experience match (weight: 1)
    if broker.experience_years and broker.experience_years >= 3:
        score += 1
    
    # Specialization match (weight: 1)
    if broker.specialization and 'building' in broker.specialization.lower():
        score += 1
    
    # Rating match (weight: 1)
    if broker.rating and broker.rating >= 4.0:
        score += 1
    
    return min(score, 5)  # Maximum score is 5


def check_location_match(advertisement, property_obj):
    """التحقق من تطابق الموقع"""
    if advertisement.governorate == property_obj.governorate:
        return True
    return False


def check_budget_match(advertisement, property_obj):
    """التحقق من تطابق الميزانية"""
    if advertisement.min_budget and advertisement.max_budget:
        return advertisement.min_budget <= property_obj.price <= advertisement.max_budget
    return False


def check_type_match(advertisement, property_obj):
    """التحقق من تطابق نوع العقار"""
    type_mapping = {
        'house': ['house', 'villa'],
        'apartment': ['apartment'],
        'villa': ['villa', 'house'],
        'building': ['building', 'land'],
        'commercial': ['commercial', 'shop', 'office'],
    }
    
    if advertisement.property_type in type_mapping:
        return property_obj.type in type_mapping[advertisement.property_type]
    return False


def check_area_match(advertisement, property_obj):
    """التحقق من تطابق المساحة"""
    if advertisement.estimated_area and property_obj.area:
        area_diff = abs(advertisement.estimated_area - property_obj.area)
        return area_diff <= (advertisement.estimated_area * 0.2)
    return False


def check_broker_location_match(advertisement, broker):
    """التحقق من تطابق موقع الدلال"""
    return advertisement.governorate == broker.governorate


def check_broker_experience_match(advertisement, broker):
    """التحقق من تطابق خبرة الدلال"""
    return broker.experience_years and broker.experience_years >= 3


def check_broker_specialization_match(advertisement, broker):
    """التحقق من تطابق تخصص الدلال"""
    return broker.specialization and 'building' in broker.specialization.lower()


def get_advertisement_statistics(advertisement):
    """
    الحصول على إحصائيات إعلان البناء
    Get building advertisement statistics
    """
    stats = {
        'total_views': advertisement.views_count,
        'total_responses': advertisement.responses_count,
        'total_matches': advertisement.matched_count,
        'accepted_responses': advertisement.responses.filter(status='accepted').count(),
        'rejected_responses': advertisement.responses.filter(status='rejected').count(),
        'pending_responses': advertisement.responses.filter(status='pending').count(),
        'viewed_matches': advertisement.matches.filter(is_viewed=True).count(),
        'contacted_matches': advertisement.matches.filter(is_contacted=True).count(),
        'converted_matches': advertisement.matches.filter(is_converted=True).count(),
    }
    
    return stats


def get_user_advertisement_statistics(user):
    """
    الحصول على إحصائيات إعلانات المستخدم
    Get user's advertisements statistics
    """
    advertisements = BuildingAdvertisement.objects.filter(user=user)
    
    stats = {
        'total_ads': advertisements.count(),
        'active_ads': advertisements.filter(status='active').count(),
        'pending_ads': advertisements.filter(status='pending').count(),
        'completed_ads': advertisements.filter(status='completed').count(),
        'total_views': advertisements.aggregate(total_views=models.Sum('views_count'))['total_views'] or 0,
        'total_responses': advertisements.aggregate(total_responses=models.Sum('responses_count'))['total_responses'] or 0,
        'total_matches': advertisements.aggregate(total_matches=models.Sum('matched_count'))['total_matches'] or 0,
    }
    
    return stats


def expire_old_advertisements():
    """
    إنهاء الإعلانات القديمة المنتهية صلاحيتها
    Expire old advertisements that have passed their expiration date
    """
    expired_ads = BuildingAdvertisement.objects.filter(
        status='active',
        expires_at__lt=timezone.now()
    )
    
    count = expired_ads.update(status='expired')
    
    return count


def cleanup_old_matches():
    """
    تنظيف المطابقات القديمة
    Cleanup old matches
    """
    # Delete matches older than 90 days that haven't been converted
    old_matches = AdMatch.objects.filter(
        created_at__lt=timezone.now() - timezone.timedelta(days=90),
        is_converted=False
    )
    
    count = old_matches.count()
    old_matches.delete()
    
    return count