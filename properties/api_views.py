"""
Production-Grade API Design
Structured API endpoints with proper error handling, validation, and documentation
"""

from rest_framework import status, viewsets, serializers
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User
from typing import Dict, List, Any, Optional
import logging
import uuid

from .models import Property, Broker, JobApplication, JobPosting
from .ai_conversation_manager import conversation_manager
from .ai_agent_loop import ai_agent
from .ai_voice_provider import voice_analytics
from .ai_learning_pipeline import data_collector, health_checker
from .feature_flags import feature_flags
from .monitoring import ai_service_monitor


class PropertySerializer(serializers.ModelSerializer):
    """Basic property serializer for API compatibility"""
    class Meta:
        model = Property
        fields = ['id', 'title', 'price', 'area', 'governorate', 'district', 
                 'property_type', 'status', 'created_at']


class PropertyViewSet(viewsets.ModelViewSet):
    """Basic Property ViewSet for API compatibility"""
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = Property.objects.filter(status='available')
        
        # Apply filters
        governorate = self.request.query_params.get('governorate')
        if governorate:
            queryset = queryset.filter(governorate=governorate)
        
        property_type = self.request.query_params.get('property_type')
        if property_type:
            queryset = queryset.filter(property_type=property_type)
        
        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        
        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset

logger = logging.getLogger(__name__)


class APIResponse:
    """Standardized API response format"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = 200) -> JsonResponse:
        """Return successful API response"""
        return JsonResponse({
            'success': True,
            'message': message,
            'data': data,
            'timestamp': timezone.now().isoformat()
        }, status=status_code)
    
    @staticmethod
    def error(message: str, error_code: str = None, status_code: int = 400, details: Any = None) -> JsonResponse:
        """Return error API response"""
        response_data = {
            'success': False,
            'message': message,
            'timestamp': timezone.now().isoformat()
        }
        
        if error_code:
            response_data['error_code'] = error_code
        
        if details:
            response_data['details'] = details
        
        return JsonResponse(response_data, status=status_code)
    
    @staticmethod
    def paginated(data: List, page: int, per_page: int, total: int) -> JsonResponse:
        """Return paginated API response"""
        return JsonResponse({
            'success': True,
            'data': data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page,
                'has_next': page * per_page < total,
                'has_prev': page > 1
            },
            'timestamp': timezone.now().isoformat()
        })


class AIChatAPISerializer(serializers.Serializer):
    """Standardized request/response structure for AI Chat API"""
    message = serializers.CharField(max_length=5000)
    conversation_id = serializers.CharField(max_length=100, required=False)
    state = serializers.JSONField(required=False)
    is_voice = serializers.BooleanField(default=False)
    context = serializers.JSONField(required=False)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_chat_production_api(request):
    """
    Production-grade AI Chat API with proper error handling and monitoring
    POST /api/ai/chat
    """
    try:
        # Validate request
        serializer = AIChatAPISerializer(data=request.data)
        if not serializer.is_valid():
            return APIResponse.error(
                "Invalid request data",
                error_code="validation_error",
                details=serializer.errors
            )
        
        message = serializer.validated_data['message']
        conversation_id = serializer.validated_data.get('conversation_id', str(uuid.uuid4()))
        is_voice = serializer.validated_data.get('is_voice', False)
        user_context = serializer.validated_data.get('context', {})
        
        # Record AI usage
        start_time = timezone.now()
        
        # Process with conversation manager
        response = conversation_manager.process_message(
            message=message,
            conversation_id=conversation_id,
            user=request.user,
            is_voice=is_voice
        )
        
        # Calculate processing time
        duration_ms = (timezone.now() - start_time).total_seconds() * 1000
        
        # Estimate token usage (rough estimate: 1 token ≈ 4 characters)
        estimated_tokens = len(message) // 4 + len(response.get('response', '')) // 4
        
        # Record AI service usage
        ai_service_monitor.record_ai_request(
            request_type='chat',
            tokens_used=estimated_tokens,
            duration_ms=duration_ms,
            user_id=request.user.id,
            model='production'
        )
        
        # Check if AI should be enabled
        if not feature_flags.is_enabled('voice_ai', request.user):
            response['voice_disabled'] = True
            response['voice_message'] = 'الصوت غير متاح حاليً'
        
        # Add production metadata
        response['metadata'] = {
            'request_id': str(uuid.uuid4())[:8],
            'processing_time_ms': round(duration_ms, 2),
            'user_id': request.user.id,
            'conversation_id': conversation_id,
            'feature_flags': feature_flags.get_user_flags(request.user)
        }
        
        return APIResponse.success(data=response, message="AI response generated")
        
    except Exception as e:
        logger.error(f"AI Chat API error: {str(e)}")
        return APIResponse.error(
            "AI processing failed",
            error_code="ai_processing_error",
            status_code=500
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_conversation_history_api(request):
    """
    Get user's conversation history with pagination
    GET /api/ai/conversations
    """
    try:
        from .ai_training_models import ConversationLog
        
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        conversations = ConversationLog.objects.filter(
            user=request.user
        ).order_by('-started_at')
        
        total = conversations.count()
        start = (page - 1) * per_page
        end = start + per_page
        
        conversations_page = conversations[start:end]
        
        conversations_data = []
        for conv in conversations_page:
            conversations_data.append({
                'conversation_id': conv.conversation_id,
                'final_intent': conv.final_intent,
                'resolved': conv.resolved,
                'started_at': conv.started_at.isoformat() if conv.started_at else None,
                'message_count': len(conv.messages) if conv.messages else 0
            })
        
        return APIResponse.paginated(
            data=conversations_data,
            page=page,
            per_page=per_page,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Conversation history API error: {str(e)}")
        return APIResponse.error(
            "Failed to fetch conversation history",
            error_code="conversation_fetch_error"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_conversation_persistence_api(request):
    """
    Save and restore conversation state for better UX
    POST /api/ai/conversation/persist
    """
    try:
        conversation_id = request.data.get('conversation_id')
        state = request.data.get('state')
        
        if not conversation_id or not state:
            return APIResponse.error(
                "Missing conversation_id or state",
                error_code="missing_parameters"
            )
        
        # Save state to cache or database
        cache_key = f"conversation_state_{request.user.id}_{conversation_id}"
        cache.set(cache_key, state, timeout=86400)  # 24 hours
        
        return APIResponse.success(
            data={'conversation_id': conversation_id},
            message="Conversation state saved"
        )
        
    except Exception as e:
        logger.error(f"Conversation persistence error: {str(e)}")
        return APIResponse.error(
            "Failed to save conversation state",
            error_code="persistence_error"
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_conversation_restore_api(request):
    """
    Restore conversation state
    GET /api/ai/conversation/restore?conversation_id=...
    """
    try:
        conversation_id = request.GET.get('conversation_id')
        
        if not conversation_id:
            return APIResponse.error(
                "Missing conversation_id",
                error_code="missing_parameters"
            )
        
        cache_key = f"conversation_state_{request.user.id}_{conversation_id}"
        state = cache.get(cache_key)
        
        if state:
            return APIResponse.success(
                data={'conversation_id': conversation_id, 'state': state},
                message="Conversation state restored"
            )
        else:
            return APIResponse.error(
                "Conversation state not found",
                error_code="state_not_found",
                status_code=404
            )
        
    except Exception as e:
        logger.error(f"Conversation restore error: {str(e)}")
        return APIResponse.error(
            "Failed to restore conversation state",
            error_code="restore_error"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_saved_search_api(request):
    """
    Save search criteria for later use
    POST /api/ai/saved-search
    """
    try:
        search_criteria = request.data.get('criteria')
        name = request.data.get('name', 'محفوظة بحث')
        
        if not search_criteria:
            return APIResponse.error(
                "Missing search criteria",
                error_code="missing_criteria"
            )
        
        # Save to user's saved searches
        cache_key = f"saved_searches_{request.user.id}"
        saved_searches = cache.get(cache_key, [])
        
        saved_search = {
            'id': str(uuid.uuid4()),
            'name': name,
            'criteria': search_criteria,
            'created_at': timezone.now().isoformat()
        }
        
        saved_searches.append(saved_search)
        cache.set(cache_key, saved_searches, timeout=2592000)  # 30 days
        
        return APIResponse.success(
            data={'saved_search': saved_search},
            message="Search saved successfully"
        )
        
    except Exception as e:
        logger.error(f"Saved search API error: {str(e)}")
        return APIResponse.error(
            "Failed to save search",
            error_code="save_search_error"
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_saved_searches_api(request):
    """
    Get user's saved searches
    GET /api/ai/saved-searches
    """
    try:
        cache_key = f"saved_searches_{request.user.id}"
        saved_searches = cache.get(cache_key, [])
        
        return APIResponse.success(
            data={'saved_searches': saved_searches},
            message="Saved searches retrieved"
        )
        
    except Exception as e:
        logger.error(f"Get saved searches error: {str(e)}")
        return APIResponse.error(
            "Failed to retrieve saved searches",
            error_code="fetch_searches_error"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_property_alert_api(request):
    """
    Create property alert for when matching properties become available
    POST /api/ai/property-alert
    """
    try:
        if not feature_flags.is_enabled('auto_notifications', request.user):
            return APIResponse.error(
                "Property alerts are not available",
                error_code="feature_disabled"
            )
        
        filters = request.data.get('filters')
        enabled = request.data.get('enabled', True)
        
        # Save alert configuration
        cache_key = f"property_alerts_{request.user.id}"
        alerts = cache.get(cache_key, [])
        
        alert = {
            'id': str(uuid.uuid4()),
            'filters': filters,
            'enabled': enabled,
            'created_at': timezone.now().isoformat()
        }
        
        alerts.append(alert)
        cache.set(cache_key, alerts, timeout=2592000)  # 30 days
        
        return APIResponse.success(
            data={'alert': alert},
            message="Property alert created"
        )
        
    except Exception as e:
        logger.error(f"Property alert API error: {str(e)}")
        return APIResponse.error(
            "Failed to create property alert",
            error_code="alert_creation_error"
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_user_analytics_api(request):
    """
    Get user-specific AI analytics and usage statistics
    GET /api/ai/user-analytics
    """
    try:
        user_id = request.user.id
        
        # Get AI usage stats
        ai_usage = ai_service_monitor.get_user_usage(user_id)
        
        # Get conversation statistics
        from .ai_training_models import ConversationLog
        conversation_stats = ConversationLog.objects.filter(user=request.user).aggregate(
            total_conversations=Count('id'),
            resolved_conversations=Count('id', filter=Q(resolved=True))
        )
        
        # Get voice analytics
        voice_stats = voice_analytics.get_statistics()
        
        return APIResponse.success(
            data={
                'ai_usage': ai_usage,
                'conversation_stats': conversation_stats,
                'voice_stats': voice_stats,
                'feature_flags': feature_flags.get_user_flags(request.user)
            },
            message="User analytics retrieved"
        )
        
    except Exception as e:
        logger.error(f"User analytics API error: {str(e)}")
        return APIResponse.error(
            "Failed to retrieve user analytics",
            error_code="analytics_error"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_property_comparison_api(request):
    """
    Compare multiple properties with detailed analysis
    POST /api/ai/property-comparison
    """
    try:
        if not feature_flags.is_enabled('property_comparison', request.user):
            return APIResponse.error(
                "Property comparison is not available",
                error_code="feature_disabled"
            )
        
        property_ids = request.data.get('property_ids', [])
        
        if not property_ids or len(property_ids) < 2:
            return APIResponse(
                "At least 2 property IDs required for comparison",
                error_code="insufficient_properties"
            )
        
        # Fetch properties
        properties = Property.objects.filter(id__in=property_ids)
        
        if properties.count() != len(property_ids):
            return APIResponse.error(
                "One or more properties not found",
                error_code="properties_not_found"
            )
        
        # Generate comparison data
        comparison_data = []
        for prop in properties:
            comparison_data.append({
                'id': prop.id,
                'title': prop.title,
                'price': prop.price,
                'area': prop.area,
                'governorate': prop.governorate,
                'district': prop.district,
                'property_type': prop.property_type,
                'status': prop.status
            })
        
        return APIResponse.success(
            data={'comparison': comparison_data},
            message="Property comparison generated"
        )
        
    except Exception as e:
        logger.error(f"Property comparison API error: {str(e)}")
        return APIResponse.error(
            "Failed to compare properties",
            error_code="comparison_error"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_buyer_profile_create_api(request):
    """
    Create and manage buyer profiles for personalized recommendations
    POST /api/ai/buyer-profile
    """
    try:
        if not feature_flags.is_enabled('buyer_profile', request.user):
            return APIResponse.error(
                "Buyer profile is not available",
                error_code="feature_disabled"
            )
        
        profile_data = request.data.get('profile')
        
        # Save buyer profile
        cache_key = f"buyer_profile_{request.user.id}"
        cache.set(cache_key, profile_data, timeout=2592000)  # 30 days
        
        return APIResponse.success(
            data={'profile': profile_data},
            message="Buyer profile saved"
        )
        
    except Exception as e:
        logger.error(f"Buyer profile API error: {str(e)}")
        return APIResponse.error(
            "Failed to save buyer profile",
            error_code="profile_error"
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_buyer_profile_get_api(request):
    """
    Get user's buyer profile
    GET /api/ai/buyer-profile
    """
    try:
        cache_key = f"buyer_profile_{request.user.id}"
        profile = cache.get(cache_key)
        
        if profile:
            return APIResponse.success(
                data={'profile': profile},
                message="Buyer profile retrieved"
            )
        else:
            return APIResponse.error(
                "Buyer profile not found",
                error_code="profile_not_found",
                status_code=404
            )
        
    except Exception as e:
        logger.error(f"Get buyer profile error: {str(e)}")
        return APIResponse.error(
            "Failed to retrieve buyer profile",
            error_code="profile_fetch_error"
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_recommendations_api(request):
    """
    Get personalized property recommendations based on user profile and history
    GET /api/ai/recommendations
    """
    try:
        if not feature_flags.is_enabled('recommendations', request.user):
            return APIResponse.error(
                "Recommendations are not available",
                error_code="feature_disabled"
            )
        
        # Get user's buyer profile
        cache_key = f"buyer_profile_{request.user.id}"
        profile = cache.get(cache_key)
        
        if not profile:
            return APIResponse.error(
                "No buyer profile found. Please complete your preferences first.",
                error_code="no_profile"
            )
        
        # Generate recommendations based on profile
        # This would integrate with the recommendation system
        recommendations = _generate_recommendations(profile, request.user)
        
        return APIResponse.success(
            data={'recommendations': recommendations},
            message="Recommendations generated"
        )
        
    except Exception as e:
        logger.error(f"Recommendations API error: {str(e)}")
        return APIResponse.error(
            "Failed to generate recommendations",
            error_code="recommendation_error"
        )


def _generate_recommendations(profile: Dict, user: User) -> List[Dict]:
    """
    Generate personalized recommendations based on buyer profile
    This is a placeholder - would integrate with the recommendation system
    """
    # Extract preferences from profile
    budget = profile.get('budget')
    location = profile.get('location')
    property_type = profile.get('property_type')
    preferences = profile.get('preferences', [])
    
    # Query properties based on profile
    from .models import Property
    
    query = Property.objects.filter(status='available')
    
    if budget:
        if budget.get('max'):
            query = query.filter(price__lte=budget['max'])
        if budget.get('min'):
            query = query.filter(price__gte=budget['min'])
    
    if location:
        if location.get('governorate'):
            query = query.filter(governorate=location['governorate'])
        if location.get('district'):
            query = query.filter(district=location['district'])
    
    if property_type:
        query = query.filter(property_type=property_type)
    
    # Apply preference filters
    if 'quiet' in preferences:
        # Add quiet area logic
        pass
    
    if 'near_schools' in preferences:
        # Add near schools logic
        pass
    
    # Get properties and sort by match score
    properties = query.order_by('-created_at')[:10]
    
    recommendations = []
    for prop in properties:
        recommendations.append({
            'id': prop.id,
            'title': prop.title,
            'price': prop.price,
            'area': prop.area,
            'governorate': prop.governorate,
            'district': prop.district,
            'match_score': 0.85,  # Placeholder score
            'match_reasons': ['الموقع متطابق', 'الميزانية مناسبة']
        })
    
    return recommendations