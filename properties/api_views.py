"""
Production-Grade API Design
Structured API endpoints with proper error handling, validation, and documentation
"""

from rest_framework import status, viewsets, serializers
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User
from typing import Dict, List, Any, Optional
import logging
import uuid

from .models import Property, Broker, JobApplication, JobPosting, PropertyOffer, PropertyNegotiation, NegotiationMessage, PropertyReservation
from .gps_utils import GPSCalculator, NearbyPropertyFinder, LocationValidator, GeocodingService
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
    permission_classes = [IsAuthenticated]
    
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


# ==================== PROPERTY OFFER & NEGOTIATION API ====================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def property_offers_api(request, property_id=None):
    """
    API endpoint for property offers
    GET: List offers for a property (or user's offers)
    POST: Create a new offer
    """
    try:
        if request.method == 'GET':
            if property_id:
                # Get offers for a specific property
                property_obj = Property.objects.get(id=property_id)
                # Only show offers to property owner or the buyer
                if request.user != property_obj.broker.user and not request.user.is_superuser:
                    offers = property_obj.offers.filter(buyer=request.user)
                else:
                    offers = property_obj.offers.all()
            else:
                # Get user's own offers
                offers = PropertyOffer.objects.filter(buyer=request.user)
            
            offers_data = [{
                'id': offer.id,
                'property_id': offer.property_obj.id,
                'property_title': offer.property_obj.display_title,
                'offered_price': str(offer.offered_price),
                'currency': offer.currency,
                'message': offer.message,
                'status': offer.status,
                'valid_until': offer.valid_until.isoformat(),
                'is_expired': offer.is_expired,
                'is_active': offer.is_active,
                'created_at': offer.created_at.isoformat(),
                'responded_at': offer.responded_at.isoformat() if offer.responded_at else None,
                'response_message': offer.response_message,
            } for offer in offers]
            
            return APIResponse.success(
                data={'offers': offers_data},
                message="Offers retrieved successfully"
            )
        
        elif request.method == 'POST':
            # Create a new offer
            data = request.data
            
            # Validate required fields
            if 'property_id' not in data or 'offered_price' not in data:
                return APIResponse.error(
                    "Missing required fields: property_id and offered_price",
                    error_code="missing_fields"
                )
            
            property_obj = Property.objects.get(id=data['property_id'])
            
            # Check if property is available
            if property_obj.status != 'available':
                return APIResponse.error(
                    "Property is not available for offers",
                    error_code="property_not_available"
                )
            
            # Create offer
            from datetime import timedelta
            valid_until = timezone.now() + timedelta(days=7)  # Default 7 days validity
            
            offer = PropertyOffer.objects.create(
                property_obj=property_obj,
                buyer=request.user,
                offered_price=data['offered_price'],
                currency=data.get('currency', 'IQD'),
                message=data.get('message', ''),
                financing_method=data.get('financing_method', ''),
                down_payment_percent=data.get('down_payment_percent'),
                payment_timeline=data.get('payment_timeline', ''),
                contingencies=data.get('contingencies', []),
                valid_until=data.get('valid_until', valid_until),
                is_exclusive=data.get('is_exclusive', False),
            )
            
            return APIResponse.success(
                data={'offer_id': offer.id, 'status': offer.status},
                message="Offer created successfully"
            )
    
    except Property.DoesNotExist:
        return APIResponse.error(
            "Property not found",
            error_code="property_not_found"
        )
    except Exception as e:
        logger.error(f"Property offers API error: {str(e)}")
        return APIResponse.error(
            f"Failed to process offer: {str(e)}",
            error_code="offer_error"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def property_offer_action_api(request, offer_id):
    """
    API endpoint for offer actions (accept, reject, withdraw)
    """
    try:
        offer = PropertyOffer.objects.get(id=offer_id)
        action = request.data.get('action')
        response_message = request.data.get('response_message', '')
        
        # Verify permissions
        if action in ['accept', 'reject']:
            # Only property owner can accept/reject
            if request.user != offer.property_obj.broker.user and not request.user.is_superuser:
                return APIResponse.error(
                    "Not authorized to perform this action",
                    error_code="unauthorized"
                )
        elif action == 'withdraw':
            # Only buyer can withdraw
            if request.user != offer.buyer:
                return APIResponse.error(
                    "Not authorized to withdraw this offer",
                    error_code="unauthorized"
                )
        else:
            return APIResponse.error(
                "Invalid action. Use: accept, reject, or withdraw",
                error_code="invalid_action"
            )
        
        # Perform action
        if action == 'accept':
            offer.accept(response_message)
        elif action == 'reject':
            offer.reject(response_message)
        elif action == 'withdraw':
            offer.withdraw()
        
        return APIResponse.success(
            data={'offer_id': offer.id, 'status': offer.status},
            message=f"Offer {action}ed successfully"
        )
    
    except PropertyOffer.DoesNotExist:
        return APIResponse.error(
            "Offer not found",
            error_code="offer_not_found"
        )
    except Exception as e:
        logger.error(f"Offer action API error: {str(e)}")
        return APIResponse.error(
            f"Failed to perform action: {str(e)}",
            error_code="action_error"
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def property_negotiations_api(request, property_id=None):
    """
    API endpoint for property negotiations
    GET: List negotiations for a property (or user's negotiations)
    POST: Create a new negotiation
    """
    try:
        if request.method == 'GET':
            if property_id:
                # Get negotiations for a specific property
                property_obj = Property.objects.get(id=property_id)
                # Only show negotiations to property owner or the buyer
                if request.user != property_obj.broker.user and not request.user.is_superuser:
                    negotiations = property_obj.negotiations.filter(buyer=request.user)
                else:
                    negotiations = property_obj.negotiations.all()
            else:
                # Get user's own negotiations
                negotiations = PropertyNegotiation.objects.filter(buyer=request.user)
            
            negotiations_data = [{
                'id': negotiation.id,
                'property_id': negotiation.property_obj.id,
                'property_title': negotiation.property_obj.display_title,
                'status': negotiation.status,
                'initial_price': str(negotiation.initial_price),
                'current_buyer_price': str(negotiation.current_buyer_price),
                'current_seller_price': str(negotiation.current_seller_price),
                'price_gap': str(negotiation.price_gap),
                'target_price': str(negotiation.target_price) if negotiation.target_price else None,
                'rounds': negotiation.rounds,
                'final_price': str(negotiation.final_price) if negotiation.final_price else None,
                'created_at': negotiation.created_at.isoformat(),
                'updated_at': negotiation.updated_at.isoformat(),
            } for negotiation in negotiations]
            
            return APIResponse.success(
                data={'negotiations': negotiations_data},
                message="Negotiations retrieved successfully"
            )
        
        elif request.method == 'POST':
            # Create a new negotiation
            data = request.data
            
            # Validate required fields
            if 'property_id' not in data or 'target_price' not in data:
                return APIResponse.error(
                    "Missing required fields: property_id and target_price",
                    error_code="missing_fields"
                )
            
            property_obj = Property.objects.get(id=data['property_id'])
            
            # Check if property is available
            if property_obj.status != 'available':
                return APIResponse.error(
                    "Property is not available for negotiation",
                    error_code="property_not_available"
                )
            
            # Create negotiation
            negotiation = PropertyNegotiation.objects.create(
                property_obj=property_obj,
                buyer=request.user,
                seller=property_obj.broker.user,
                initial_price=property_obj.price,
                current_buyer_price=data['target_price'],
                current_seller_price=property_obj.price,
                price_gap=abs(data['target_price'] - property_obj.price),
                target_price=data['target_price'],
                status='active',
            )
            
            return APIResponse.success(
                data={'negotiation_id': negotiation.id, 'status': negotiation.status},
                message="Negotiation created successfully"
            )
    
    except Property.DoesNotExist:
        return APIResponse.error(
            "Property not found",
            error_code="property_not_found"
        )
    except Exception as e:
        logger.error(f"Property negotiations API error: {str(e)}")
        return APIResponse.error(
            f"Failed to process negotiation: {str(e)}",
            error_code="negotiation_error"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def negotiation_message_api(request, negotiation_id):
    """
    API endpoint for adding messages to a negotiation
    """
    try:
        negotiation = PropertyNegotiation.objects.get(id=negotiation_id)
        
        # Verify permissions
        if request.user != negotiation.buyer and request.user != negotiation.property_obj.broker.user and not request.user.is_superuser:
            return APIResponse.error(
                "Not authorized to participate in this negotiation",
                error_code="unauthorized"
            )
        
        # Create message
        message_text = request.data.get('message')
        if not message_text:
            return APIResponse.error(
                "Message text is required",
                error_code="missing_message"
            )
        
        message_type = request.data.get('message_type', 'info')
        is_from_buyer = (request.user == negotiation.buyer)
        
        # Determine message type based on sender
        if is_from_buyer and request.data.get('proposed_price'):
            message_type = 'offer'
        elif not is_from_buyer and request.data.get('proposed_price'):
            message_type = 'counter'
        
        message = NegotiationMessage.objects.create(
            negotiation=negotiation,
            sender=request.user,
            message_type=message_type,
            content=message_text,
            offered_price=request.data.get('proposed_price'),
        )
        
        # Update negotiation if price was proposed
        proposed_price = request.data.get('proposed_price')
        if proposed_price:
            if is_from_buyer:
                negotiation.add_buyer_offer(proposed_price, message_text)
            else:
                negotiation.add_seller_offer(proposed_price, message_text)
        
        return APIResponse.success(
            data={'message_id': message.id, 'current_buyer_price': str(negotiation.current_buyer_price), 'current_seller_price': str(negotiation.current_seller_price)},
            message="Message added successfully"
        )
    
    except PropertyNegotiation.DoesNotExist:
        return APIResponse.error(
            "Negotiation not found",
            error_code="negotiation_not_found"
        )
    except Exception as e:
        logger.error(f"Negotiation message API error: {str(e)}")
        return APIResponse.error(
            f"Failed to add message: {str(e)}",
            error_code="message_error"
        )


# ==================== PROPERTY RESERVATION API ====================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def property_reservations_api(request, property_id=None):
    """
    API endpoint for property reservations
    GET: List reservations for a property (or user's reservations)
    POST: Create a new reservation
    """
    try:
        if request.method == 'GET':
            if property_id:
                # Get reservations for a specific property
                property_obj = Property.objects.get(id=property_id)
                # Only show reservations to property owner or the user
                if request.user != property_obj.broker.user and not request.user.is_superuser:
                    reservations = property_obj.reservations.filter(user=request.user)
                else:
                    reservations = property_obj.reservations.all()
            else:
                # Get user's own reservations
                reservations = PropertyReservation.objects.filter(user=request.user)
            
            reservations_data = [{
                'id': reservation.id,
                'property_id': reservation.property_obj.id,
                'property_title': reservation.property_obj.display_title,
                'reservation_type': reservation.reservation_type,
                'duration_hours': reservation.duration_hours,
                'contact_phone': reservation.contact_phone,
                'contact_email': reservation.contact_email,
                'visit_purpose': reservation.visit_purpose,
                'preferred_date': reservation.preferred_date.isoformat(),
                'preferred_time': reservation.preferred_time.isoformat(),
                'number_of_visitors': reservation.number_of_visitors,
                'special_requirements': reservation.special_requirements,
                'status': reservation.status,
                'is_expired': reservation.is_expired,
                'is_active': reservation.is_active,
                'created_at': reservation.created_at.isoformat(),
                'expires_at': reservation.expires_at.isoformat(),
                'confirmed_at': reservation.confirmed_at.isoformat() if reservation.confirmed_at else None,
                'reservation_fee': str(reservation.reservation_fee),
                'fee_paid': reservation.fee_paid,
            } for reservation in reservations]
            
            return APIResponse.success(
                data={'reservations': reservations_data},
                message="Reservations retrieved successfully"
            )
        
        elif request.method == 'POST':
            # Create a new reservation
            data = request.data
            
            # Validate required fields
            required_fields = ['property_id', 'contact_phone', 'contact_email', 'visit_purpose', 'preferred_date', 'preferred_time']
            for field in required_fields:
                if field not in data:
                    return APIResponse.error(
                        f"Missing required field: {field}",
                        error_code="missing_field"
                    )
            
            property_obj = Property.objects.get(id=data['property_id'])
            
            # Check if property is available
            if property_obj.status != 'available':
                return APIResponse.error(
                    "Property is not available for reservation",
                    error_code="property_not_available"
                )
            
            # Calculate expiration time
            from datetime import timedelta
            duration_hours = data.get('duration_hours', 24)
            expires_at = timezone.now() + timedelta(hours=duration_hours)
            
            # Create reservation
            reservation = PropertyReservation.objects.create(
                property_obj=property_obj,
                user=request.user,
                reservation_type=data.get('reservation_type', 'viewing'),
                duration_hours=duration_hours,
                contact_phone=data['contact_phone'],
                contact_email=data['contact_email'],
                visit_purpose=data['visit_purpose'],
                preferred_date=data['preferred_date'],
                preferred_time=data['preferred_time'],
                number_of_visitors=data.get('number_of_visitors', 1),
                special_requirements=data.get('special_requirements', ''),
                expires_at=expires_at,
                reservation_fee=data.get('reservation_fee', 0),
                fee_paid=data.get('fee_paid', False),
            )
            
            return APIResponse.success(
                data={'reservation_id': reservation.id, 'status': reservation.status, 'expires_at': expires_at.isoformat()},
                message="Reservation created successfully"
            )
    
    except Property.DoesNotExist:
        return APIResponse.error(
            "Property not found",
            error_code="property_not_found"
        )
    except Exception as e:
        logger.error(f"Property reservations API error: {str(e)}")
        return APIResponse.error(
            f"Failed to process reservation: {str(e)}",
            error_code="reservation_error"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reservation_action_api(request, reservation_id):
    """
    API endpoint for reservation actions (confirm, cancel, convert_to_offer)
    """
    try:
        reservation = PropertyReservation.objects.get(id=reservation_id)
        action = request.data.get('action')
        
        # Verify permissions
        if action == 'confirm':
            # Only property owner can confirm
            if request.user != reservation.property_obj.broker.user and not request.user.is_superuser:
                return APIResponse.error(
                    "Not authorized to confirm this reservation",
                    error_code="unauthorized"
                )
        elif action == 'cancel':
            # Only user who made reservation can cancel
            if request.user != reservation.user:
                return APIResponse.error(
                    "Not authorized to cancel this reservation",
                    error_code="unauthorized"
                )
        elif action == 'convert_to_offer':
            # Only user who made reservation can convert
            if request.user != reservation.user:
                return APIResponse.error(
                    "Not authorized to convert this reservation",
                    error_code="unauthorized"
                )
        else:
            return APIResponse.error(
                "Invalid action. Use: confirm, cancel, or convert_to_offer",
                error_code="invalid_action"
            )
        
        # Perform action
        if action == 'confirm':
            reservation.confirm()
            return APIResponse.success(
                data={'reservation_id': reservation.id, 'status': reservation.status},
                message="Reservation confirmed successfully"
            )
        elif action == 'cancel':
            reason = request.data.get('reason', '')
            reservation.cancel(reason)
            return APIResponse.success(
                data={'reservation_id': reservation.id, 'status': reservation.status},
                message="Reservation cancelled successfully"
            )
        elif action == 'convert_to_offer':
            offer_price = request.data.get('offer_price')
            message = request.data.get('message', '')
            
            if not offer_price:
                return APIResponse.error(
                    "offer_price is required for conversion",
                    error_code="missing_offer_price"
                )
            
            reservation.convert_to_offer(offer_price, message)
            return APIResponse.success(
                data={'reservation_id': reservation.id, 'status': reservation.status},
                message="Reservation converted to offer successfully"
            )
    
    except PropertyReservation.DoesNotExist:
        return APIResponse.error(
            "Reservation not found",
            error_code="reservation_not_found"
        )
    except Exception as e:
        logger.error(f"Reservation action API error: {str(e)}")
        return APIResponse.error(
            f"Failed to perform action: {str(e)}",
            error_code="action_error"
        )


# ==================== GPS AND LOCATION API ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gps_nearby_properties_api(request):
    """
    API endpoint for finding properties near a GPS location
    """
    try:
        lat = float(request.query_params.get('lat'))
        lon = float(request.query_params.get('lon'))
        radius_km = float(request.query_params.get('radius_km', 5.0))
        limit = int(request.query_params.get('limit', 50))
        
        # Validate coordinates
        if not LocationValidator.validate_iraq_coordinates(lat, lon):
            return APIResponse.error(
                "Coordinates are outside Iraq bounds",
                error_code="invalid_coordinates"
            )
        
        # Build filters from query parameters
        filters = {}
        filter_params = ['property_type', 'price_min', 'price_max', 'bedrooms', 'bathrooms', 'governorate']
        for param in filter_params:
            value = request.query_params.get(param)
            if value:
                if param in ['price_min', 'price_max', 'bedrooms', 'bathrooms']:
                    filters[param] = float(value)
                else:
                    filters[param] = value
        
        # Find nearby properties
        nearby_properties = NearbyPropertyFinder.find_nearby_properties(
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            property_model=Property,
            filters=filters,
            limit=limit
        )
        
        # Format response
        properties_data = []
        for item in nearby_properties:
            prop = item['property']
            properties_data.append({
                'id': prop.id,
                'title': prop.display_title,
                'price': str(prop.price),
                'currency': prop.currency,
                'latitude': float(prop.latitude) if prop.latitude else None,
                'longitude': float(prop.longitude) if prop.longitude else None,
                'distance_km': item['distance_km'],
                'distance_miles': item['distance_miles'],
                'bearing': item['bearing'],
                'bearing_direction': item['bearing_direction'],
                'property_type': prop.property_type,
                'area': str(prop.area) if prop.area else None,
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'governorate': prop.governorate,
                'district': prop.district,
                'main_image': prop.get_main_image() if hasattr(prop, 'get_main_image') else None,
            })
        
        return APIResponse.success(
            data={
                'properties': properties_data,
                'center': {'lat': lat, 'lon': lon},
                'radius_km': radius_km,
                'total_found': len(properties_data)
            },
            message=f"Found {len(properties_data)} properties within {radius_km} km"
        )
    
    except (ValueError, TypeError) as e:
        return APIResponse.error(
            "Invalid parameters: lat and lon are required numbers",
            error_code="invalid_parameters"
        )
    except Exception as e:
        logger.error(f"GPS nearby properties API error: {str(e)}")
        return APIResponse.error(
            f"Failed to find nearby properties: {str(e)}",
            error_code="gps_error"
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gps_area_search_api(request):
    """
    API endpoint for searching properties within a rectangular area
    """
    try:
        min_lat = float(request.query_params.get('min_lat'))
        max_lat = float(request.query_params.get('max_lat'))
        min_lon = float(request.query_params.get('min_lon'))
        max_lon = float(request.query_params.get('max_lon'))
        limit = int(request.query_params.get('limit', 100))
        
        # Validate bounds
        if not (min_lat < max_lat and min_lon < max_lon):
            return APIResponse.error(
                "Invalid bounds: min values must be less than max values",
                error_code="invalid_bounds"
            )
        
        # Build filters
        filters = {}
        filter_params = ['property_type', 'price_min', 'price_max', 'bedrooms', 'bathrooms', 'governorate']
        for param in filter_params:
            value = request.query_params.get(param)
            if value:
                if param in ['price_min', 'price_max', 'bedrooms', 'bathrooms']:
                    filters[param] = float(value)
                else:
                    filters[param] = value
        
        # Find properties in area
        properties = NearbyPropertyFinder.find_properties_in_area(
            bounds=(min_lat, max_lat, min_lon, max_lon),
            property_model=Property,
            filters=filters,
            limit=limit
        )
        
        # Format response
        properties_data = []
        for prop in properties:
            properties_data.append({
                'id': prop.id,
                'title': prop.display_title,
                'price': str(prop.price),
                'currency': prop.currency,
                'latitude': float(prop.latitude) if prop.latitude else None,
                'longitude': float(prop.longitude) if prop.longitude else None,
                'property_type': prop.property_type,
                'area': str(prop.area) if prop.area else None,
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'governorate': prop.governorate,
                'district': prop.district,
                'main_image': prop.get_main_image() if hasattr(prop, 'get_main_image') else None,
            })
        
        return APIResponse.success(
            data={
                'properties': properties_data,
                'bounds': {
                    'min_lat': min_lat,
                    'max_lat': max_lat,
                    'min_lon': min_lon,
                    'max_lon': max_lon
                },
                'total_found': len(properties_data)
            },
            message=f"Found {len(properties_data)} properties in specified area"
        )
    
    except (ValueError, TypeError) as e:
        return APIResponse.error(
            "Invalid parameters: all bounds must be numbers",
            error_code="invalid_parameters"
        )
    except Exception as e:
        logger.error(f"GPS area search API error: {str(e)}")
        return APIResponse.error(
            f"Failed to search area: {str(e)}",
            error_code="area_search_error"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def gps_geocode_api(request):
    """
    API endpoint for geocoding addresses to coordinates
    """
    try:
        address = request.data.get('address')
        if not address:
            return APIResponse.error(
                "Address is required",
                error_code="missing_address"
            )
        
        coordinates = GeocodingService.geocode_address(address)
        
        if coordinates:
            lat, lon = coordinates
            # Validate coordinates are in Iraq
            if LocationValidator.validate_iraq_coordinates(lat, lon):
                return APIResponse.success(
                    data={
                        'lat': lat,
                        'lon': lon,
                        'formatted': LocationValidator.format_coordinates(lat, lon)
                    },
                    message="Address geocoded successfully"
                )
            else:
                return APIResponse.error(
                    "Geocoded coordinates are outside Iraq bounds",
                    error_code="outside_bounds"
                )
        else:
            return APIResponse.error(
                "Failed to geocode address",
                error_code="geocoding_failed"
            )
    
    except Exception as e:
        logger.error(f"GPS geocode API error: {str(e)}")
        return APIResponse.error(
            f"Geocoding failed: {str(e)}",
            error_code="geocoding_error"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def gps_reverse_geocode_api(request):
    """
    API endpoint for reverse geocoding coordinates to address
    """
    try:
        lat = float(request.data.get('lat'))
        lon = float(request.data.get('lon'))
        
        # Validate coordinates
        if not LocationValidator.validate_iraq_coordinates(lat, lon):
            return APIResponse.error(
                "Coordinates are outside Iraq bounds",
                error_code="invalid_coordinates"
            )
        
        address = GeocodingService.reverse_geocode(lat, lon)
        
        if address:
            return APIResponse.success(
                data={
                    'address': address,
                    'coordinates': {
                        'lat': lat,
                        'lon': lon,
                        'formatted': LocationValidator.format_coordinates(lat, lon)
                    }
                },
                message="Coordinates reverse geocoded successfully"
            )
        else:
            return APIResponse.error(
                "Failed to reverse geocode coordinates",
                error_code="reverse_geocoding_failed"
            )
    
    except (ValueError, TypeError) as e:
        return APIResponse.error(
            "Invalid parameters: lat and lon are required numbers",
            error_code="invalid_parameters"
        )
    except Exception as e:
        logger.error(f"GPS reverse geocode API error: {str(e)}")
        return APIResponse.error(
            f"Reverse geocoding failed: {str(e)}",
            error_code="reverse_geocoding_error"
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def gps_distance_api(request):
    """
    API endpoint for calculating distance between two points
    """
    try:
        lat1 = float(request.query_params.get('lat1'))
        lon1 = float(request.query_params.get('lon1'))
        lat2 = float(request.query_params.get('lat2'))
        lon2 = float(request.query_params.get('lon2'))
        unit = request.query_params.get('unit', 'km')
        
        if unit not in ['km', 'miles']:
            return APIResponse.error(
                "Unit must be 'km' or 'miles'",
                error_code="invalid_unit"
            )
        
        distance = GPSCalculator.haversine_distance(lat1, lon1, lat2, lon2, unit)
        bearing = GPSCalculator.calculate_bearing(lat1, lon1, lat2, lon2)
        midpoint = GPSCalculator.midpoint(lat1, lon1, lat2, lon2)
        
        return APIResponse.success(
            data={
                'distance': round(distance, 2),
                'unit': unit,
                'bearing': round(bearing, 2),
                'bearing_direction': NearbyPropertyFinder._get_bearing_direction(bearing),
                'midpoint': {
                    'lat': midpoint[0],
                    'lon': midpoint[1]
                }
            },
            message="Distance calculated successfully"
        )
    
    except (ValueError, TypeError) as e:
        return APIResponse.error(
            "Invalid parameters: all coordinates must be numbers",
            error_code="invalid_parameters"
        )
    except Exception as e:
        logger.error(f"GPS distance API error: {str(e)}")
        return APIResponse.error(
            f"Distance calculation failed: {str(e)}",
            error_code="distance_error"
        )