"""
AI Services API Endpoints
Provides API endpoints for AI-powered services
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
import json
import logging

from .ai_duplicate_detector import duplicate_detector
from .ai_hotel_travel_assistant import hotel_travel_assistant
from .ai_match_engine import ai_match_engine
from .models import Property, HotelPage
from .permissions_centralized import rate_limit, get_client_ip

logger = logging.getLogger(__name__)


@rate_limit(max_requests=20, period=60)
@csrf_protect
@require_http_methods(["POST"])
@login_required
def api_detect_duplicate_images(request):
    """
    API endpoint to detect duplicate images
    """
    try:
        data = json.loads(request.body)
        property_images = data.get('property_images', [])

        # Convert to required format
        image_data = []
        for prop_img in property_images:
            property_id = prop_img.get('property_id')
            image_bytes = prop_img.get('image_data')
            if property_id and image_bytes:
                image_data.append((property_id, image_bytes))

        # Detect duplicates
        findings = duplicate_detector.detect_duplicate_images(image_data)

        return JsonResponse({
            'success': True,
            'findings': [f.to_dict() for f in findings],
            'total_duplicates': len(findings)
        })

    except Exception as e:
        logger.error(f"Error detecting duplicate images: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@rate_limit(max_requests=20, period=60)
@csrf_protect
@require_http_methods(["POST"])
@login_required
def api_detect_suspicious_listings(request):
    """
    API endpoint to detect suspicious listings
    """
    try:
        data = json.loads(request.body)
        property_data = data.get('property_data', [])

        # Detect suspicious patterns
        suspicious_listings = duplicate_detector.detect_suspicious_patterns(property_data)

        return JsonResponse({
            'success': True,
            'suspicious_listings': [s.to_dict() for s in suspicious_listings],
            'total_suspicious': len(suspicious_listings)
        })

    except Exception as e:
        logger.error(f"Error detecting suspicious listings: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@rate_limit(max_requests=15, period=60)
@csrf_protect
@require_http_methods(["POST"])
@login_required
def api_analyze_property_images(request):
    """
    API endpoint to analyze property images for quality
    """
    try:
        data = json.loads(request.body)
        property_id = data.get('property_id')
        images = data.get('images', [])

        # Analyze images
        analysis = duplicate_detector.analyze_property_images(property_id, images)

        return JsonResponse({
            'success': True,
            'analysis': analysis
        })

    except Exception as e:
        logger.error(f"Error analyzing property images: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@rate_limit(max_requests=15, period=60)
@csrf_protect
@require_http_methods(["POST"])
@login_required
def api_travel_planner(request):
    """
    API endpoint for travel planning assistant
    """
    try:
        data = json.loads(request.body)
        user_text = data.get('user_text', '')
        user_id = request.user.id if request.user.is_authenticated else None

        # Parse travel request
        travel_request = hotel_travel_assistant.parse_travel_request(user_text, user_id)

        # Get available hotels (mock data for now)
        available_hotels = data.get('available_hotels', [])

        # Generate travel plan
        travel_plan = hotel_travel_assistant.generate_travel_plan(travel_request, available_hotels)

        # Generate response
        response_text = hotel_travel_assistant.generate_response(travel_request, travel_plan)

        return JsonResponse({
            'success': True,
            'travel_request': travel_request.to_dict(),
            'travel_plan': travel_plan.to_dict(),
            'response': response_text
        })

    except Exception as e:
        logger.error(f"Error in travel planner: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@rate_limit(max_requests=15, period=60)
@csrf_protect
@require_http_methods(["POST"])
@login_required
def api_ai_match_properties(request):
    """
    API endpoint for AI property matching
    """
    try:
        data = json.loads(request.body)
        user_request = data.get('user_request', '')
        user_id = request.user.id if request.user.is_authenticated else None

        # Get available properties
        available_properties = data.get('available_properties', [])

        # Match properties
        matches = ai_match_engine.match_properties(user_request, available_properties, user_id)

        # Generate summary
        summary = ai_match_engine.generate_match_summary(matches)

        return JsonResponse({
            'success': True,
            'matches': [m.to_dict() for m in matches],
            'summary': summary
        })

    except Exception as e:
        logger.error(f"Error in AI match: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@rate_limit(max_requests=15, period=60)
@csrf_protect
@require_http_methods(["POST"])
@login_required
def api_ai_match_explanation(request):
    """
    API endpoint to get explanation for a specific match
    """
    try:
        data = json.loads(request.body)
        match_data = data.get('match_data')

        # Create match object from data
        from .ai_match_engine import PropertyMatch, MatchScore

        match_score = MatchScore(
            overall_score=match_data.get('match_score', {}).get('overall_score', 0),
            criteria_scores=match_data.get('match_score', {}).get('criteria_scores', {}),
            match_reasons=match_data.get('match_score', {}).get('match_reasons', []),
            mismatch_reasons=match_data.get('match_score', {}).get('mismatch_reasons', []),
            confidence=match_data.get('match_score', {}).get('confidence', 0)
        )

        property_match = PropertyMatch(
            property_id=match_data.get('property_id'),
            property_data=match_data.get('property_data'),
            match_score=match_score,
            rank=match_data.get('rank', 0),
            recommendation_level=match_data.get('recommendation_level', 'fair')
        )

        # Generate explanation
        explanation = ai_match_engine.get_match_explanation(property_match)

        return JsonResponse({
            'success': True,
            'explanation': explanation
        })

    except Exception as e:
        logger.error(f"Error generating match explanation: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@rate_limit(max_requests=30, period=60)
@csrf_protect
@require_http_methods(["GET"])
def api_ai_capabilities(request):
    """
    API endpoint to get available AI capabilities
    """
    capabilities = {
        'duplicate_detection': {
            'available': True,
            'description': 'كشف الصور المكررة والمشبوهة',
            'endpoints': [
                '/api/ai/detect-duplicate-images/',
                '/api/ai/detect-suspicious-listings/',
                '/api/ai/analyze-property-images/'
            ]
        },
        'travel_planning': {
            'available': True,
            'description': 'مساعد السفر والفنادق الذكي',
            'endpoints': [
                '/api/ai/travel-planner/'
            ]
        },
        'ai_matching': {
            'available': True,
            'description': 'مطابقة العقارات الذكية',
            'endpoints': [
                '/api/ai/match-properties/',
                '/api/ai/match-explanation/'
            ]
        },
        'arabic_normalization': {
            'available': True,
            'description': 'تطبيع النصوص العربية واللهجة العراقية',
            'features': [
                'تصحيح الأخطاء الإملائية',
                'فهم اللهجة العراقية',
                'تحويل الأرقام النصية',
                'استخراج الميزانية والمساحة'
            ]
        },
        'intent_detection': {
            'available': True,
            'description': 'اكتشاف نوايا المستخدم',
            'supported_intents': [
                'شراء عقار',
                'بيع عقار',
                'إيجار عقار',
                'البحث عن فندق',
                'البحث عن وظيفة',
                'البحث عن خدمة'
            ]
        }
    }

    return JsonResponse({
        'success': True,
        'capabilities': capabilities
    })
