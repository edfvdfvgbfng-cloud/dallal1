"""
AI Travel Itinerary Generator
Generates personalized travel itineraries using AI
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


def generate_itinerary(destination, duration, interests, budget):
    """
    Generate a personalized travel itinerary using AI
    
    Args:
        destination (str): Travel destination
        duration (int): Duration in days
        interests (list): List of user interests
        budget (Decimal): Budget limit
    
    Returns:
        dict: Generated itinerary with daily activities
    """
    
    try:
        # This is a simplified AI itinerary generator
        # In production, this would use advanced AI models like GPT-4
        
        itinerary = {
            'destination': destination,
            'duration': duration,
            'total_budget': str(budget),
            'daily_budget': str(budget / duration),
            'interests': interests,
            'ai_confidence': 0.85,
            'generated_at': datetime.now().isoformat(),
            'days': []
        }
        
        # Generate daily activities based on interests
        activities_map = {
            'culture': ['متحف', 'معلم تاريخي', 'قصر', 'موقع أثري'],
            'nature': ['حديقة', 'منتزه', 'جبل', 'شاطئ', 'غابة'],
            'food': ['مطعم محلي', 'سوق غذائي', 'تجربة طعام تقليدية'],
            'adventure': ['نشاط خارجي', 'رياضة مائية', 'تسلق', 'رحلة'],
            'shopping': ['مركز تسوق', 'سوق محلي', 'متجر حرفي'],
            'nightlife': ['نادي ليلي', 'حفلة موسيقية', 'مقهى ليلي'],
            'history': ['موقع تاريخي', 'متحف', 'قصر قديم'],
            'relaxation': ['سبا', 'ماساج', 'حديقة هادئة', 'يوجا']
        }
        
        for day in range(1, duration + 1):
            day_plan = {
                'day_number': day,
                'date': (datetime.now() + timedelta(days=day-1)).strftime('%Y-%m-%d'),
                'theme': get_day_theme(day, interests),
                'morning': generate_activity('morning', interests, activities_map),
                'afternoon': generate_activity('afternoon', interests, activities_map),
                'evening': generate_activity('evening', interests, activities_map),
                'meals': generate_meals(day, interests),
                'transportation': get_transportation(day, destination),
                'accommodation': get_accommodation(day, destination),
                'estimated_cost': str(budget / duration),
                'tips': get_day_tips(day, destination)
            }
            
            itinerary['days'].append(day_plan)
        
        # Add overall recommendations
        itinerary['recommendations'] = generate_recommendations(destination, interests, budget)
        
        # Add packing list
        itinerary['packing_list'] = generate_packing_list(destination, duration, interests)
        
        return itinerary
        
    except Exception as e:
        logger.error(f"Error generating itinerary: {e}")
        return get_fallback_itinerary(destination, duration, budget)


def get_day_theme(day, interests):
    """Get theme for each day"""
    themes = ['استكشاف', 'ثقافة', 'طبيعة', 'مغامرة', 'استرخاء', 'تسوق', 'طعام', 'ترفيه']
    return themes[(day - 1) % len(themes)]


def generate_activity(time_of_day, interests, activities_map):
    """Generate activity for specific time of day"""
    activities = []
    
    for interest in interests:
        if interest in activities_map:
            interest_activities = activities_map[interest]
            if interest_activities:
                import random
                activities.append(random.choice(interest_activities))
    
    if not activities:
        # Fallback activities
        fallback_activities = {
            'morning': ['استكشاف المدينة', 'زيارة معلم سياحي', 'جولة في الحديقة'],
            'afternoon': ['زيارة متحف', 'تسوق محلي', 'استراحة في مقهى'],
            'evening': ['عشاء في مطعم', 'مشاهدة غروب الشمس', 'تجربة ثقافية']
        }
        activities = fallback_activities.get(time_of_day, ['استكشاف المدينة'])
    
    return activities[0] if activities else 'استكشاف المدينة'


def generate_meals(day, interests):
    """Generate meal recommendations"""
    meals = {
        'breakfast': 'فطور فندقي',
        'lunch': 'غداء في مطعم محلي',
        'dinner': 'عشاء في مطعم متخصص'
    }
    
    if 'food' in interests:
        meals['breakfast'] = 'فطور تقليدي محلي'
        meals['lunch'] = 'تجربة أطباق شعبية'
        meals['dinner'] = 'عشاء في مطعم مشهور'
    
    return meals


def get_transportation(day, destination):
    """Get transportation recommendation"""
    transport_options = [
        'نقل فندقي',
        'تاكسي',
        'نقل عام',
        'مشي',
        'تأجير سيارة'
    ]
    
    return transport_options[(day - 1) % len(transport_options)]


def get_accommodation(day, destination):
    """Get accommodation recommendation"""
    accommodations = [
        'فندق 4 نجوم',
        'فندق 3 نجوم',
        'فندق فاخر',
        'منتجع',
        'شقة مفروشة'
    ]
    
    return accommodations[(day - 1) % len(accommodations)]


def get_day_tips(day, destination):
    """Get tips for each day"""
    tips = [
        'ابدأ مبكراً لتجنب الزحام',
        'احمل معك الماء والوجبات الخفيفة',
        'ارتدِ ملابس مريحة للمشي',
        'استخدم تطبيقات الترجمة إذا لزم الأمر',
        'احتفظ بنسخة من وثائق سفرك',
        'تعلم بعض الكلمات المحلية الأساسية',
        'احترم العادات والتقاليد المحلية',
        'استفسر عن الأسعار قبل الشراء'
    ]
    
    return tips[(day - 1) % len(tips)]


def generate_recommendations(destination, interests, budget):
    """Generate overall recommendations"""
    recommendations = [
        f'حجز الفندق قبل الوقت للحصول على أفضل الأسعار',
        f'ابحث عن العروض الخاصة والخصومات في {destination}',
        f'قم بتبادل العملة المحلي للوصول على أفضل سعر',
        f'حمل تطبيقات التنقل والخرائط المحلية',
        f'احصل على تأمين سفر شامل',
        f'احتفظ بنسخة احتياطية من وثائق سفرك',
        f'تعرف على أرقام الطوارئ المحلية المهمة'
    ]
    
    if budget < 1000:
        recommendations.append('ابحث عن خيارات الإقامة الاقتصادية والمطاعم المحلية')
    elif budget > 5000:
        recommendations.append('يمكنك الاستمتاع بالفنادق الفاخرة والأنشطة الحصرية')
    
    return recommendations


def generate_packing_list(destination, duration, interests):
    """Generate packing list"""
    packing_list = {
        'essential': [
            'جواز سفر صالح',
            'تأشيرة دخول (إذا لزم الأمر)',
            'تذاكر طيران',
            'حجز فندق',
            'تأمين سفر',
            'نقد وبطاقات بنكية',
            'هاتف محمول وشاحن',
            'أدوية شخصية',
            'أغراض النظافة الشخصية'
        ],
        'clothing': [
            'ملابس مريحة حسب الطقس',
            'أحذية مناسبة للمشي',
            'ملابس رسمية (للمطاعم والمراكز الفاخرة)',
            'ملابس رياضية (للأنشطة الخارجية)',
            'ملابس داخلية',
            'ملابس سباحة (إذا لزم الأمر)',
            'ملابس إضافية'
        ],
        'electronics': [
            'شاحن سفر',
            'محول كهربائي',
            'كاميرا وعدسات',
            'هاتف محمول',
            'سماعات',
            'قارئ إلكتروني',
            'لابتوب (إذا لزم الأمر)'
        ],
        'health': [
            'مجموعة إسعافات أولية',
            'واقي شمسي',
            'واقي من الحشرات',
            'أدوية الحساسية',
            'أدوية الصداع',
            'أدوية الألم',
            'فيتامينات'
        ],
        'documents': [
            'نسخة من جواز السفر',
            'تأشيرة الدخول',
            'تذاكر الطيران',
            'حجز الفندق',
            'بطاقة تأمين السفر',
            'رخصة القيادة الدولية (إذا لزم الأمر)',
            'عناوين مهمة',
            'قائمة جهات الاتصال'
        ]
    }
    
    # Add interest-specific items
    if 'adventure' in interests:
        packing_list['clothing'].extend(['ملابس رياضية إضافية', 'أحذية تسلق', 'قفازات'])
        packing_list['electronics'].extend(['كاميرا عمل', 'عدسات'])
    
    if 'nature' in interests:
        packing_list['clothing'].extend(['ملابس ضد الماء', 'أحذية للمشي'])
        packing_list['health'].extend(['واقي من الحشرات', 'طارد الحشرات'])
    
    if 'beach' in interests:
        packing_list['clothing'].extend(['ملابس سباحة', 'نظارات شمسية', 'قبعة'])
        packing_list['health'].extend(['واقي شمسي', 'طارد الحشرات'])
    
    return packing_list


def get_fallback_itinerary(destination, duration, budget):
    """Get fallback itinerary if AI generation fails"""
    return {
        'destination': destination,
        'duration': duration,
        'total_budget': str(budget),
        'daily_budget': str(budget / duration),
        'interests': [],
        'ai_confidence': 0.5,
        'generated_at': datetime.now().isoformat(),
        'days': [
            {
                'day_number': 1,
                'date': (datetime.now()).strftime('%Y-%m-%d'),
                'theme': 'وصول واستكشاف',
                'morning': 'الوصول والاستقرار في الفندق',
                'afternoon': 'استكشاف المنطقة المحيطة',
                'evening': 'عشاء في مطعم محلي',
                'meals': {
                    'breakfast': 'فطور في الفندق',
                    'lunch': 'غداء في مطعم محلي',
                    'dinner': 'عشاء في مطعم محلي'
                },
                'transportation': 'نقل من المطار',
                'accommodation': 'فندق',
                'estimated_cost': str(budget / duration),
                'tips': 'استرح بعد السفر الطويل'
            }
        ],
        'recommendations': [
            'استكشف المدينة بمعدك',
            'جرب المطاعم المحلية',
            'زور المعالم السياحية',
            'احترم العادات المحلية'
        ],
        'packing_list': {
            'essential': ['جواز سفر', 'تأشيرة', 'تذاكر'],
            'clothing': ['ملابس مناسبة', 'أحذية مريحة'],
            'electronics': ['هاتف محمول', 'شاحن'],
            'health': ['أدوية شخصية', 'أغراض نظافة'],
            'documents': ['نسخة وثائق السفر']
        }
    }


def analyze_itinerary_complexity(itinerary):
    """Analyze the complexity of generated itinerary"""
    total_activities = 0
    for day in itinerary.get('days', []):
        total_activities += 3  # morning, afternoon, evening
    
    if total_activities <= 3:
        return 'سهل'
    elif total_activities <= 6:
        return 'متوسط'
    else:
        return 'معقد'


def estimate_itinerary_cost(itinerary):
    """Estimate total cost of itinerary"""
    try:
        base_budget = Decimal(itinerary.get('total_budget', 0))
        duration = len(itinerary.get('days', 1))
        
        # Add contingency (10%)
        contingency = base_budget * Decimal('0.1')
        estimated_total = base_budget + contingency
        
        return {
            'base_budget': str(base_budget),
            'contingency': str(contingency),
            'estimated_total': str(estimated_total),
            'duration': duration,
            'daily_average': str(estimated_total / duration)
        }
    except Exception as e:
        logger.error(f"Error estimating itinerary cost: {e}")
        return {
            'base_budget': 'غير محدد',
            'contingency': 'غير محدد',
            'estimated_total': 'غير محدد',
            'duration': duration,
            'daily_average': 'غير محدد'
        }