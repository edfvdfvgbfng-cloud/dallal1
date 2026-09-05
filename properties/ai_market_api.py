"""
Market Intelligence API Views
REST API endpoints for market intelligence and buyer-seller matching
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging

from .ai_market_orchestrator import market_intelligence_orchestrator
from .ai_market_intelligence import market_intelligence_system, BuyerIntentType
from .ai_agent_matching import agent_matching_system
from .ai_safe_analytics import safe_analytics_layer, QueryType, MetricType
from .permissions_centralized import rate_limit

logger = logging.getLogger(__name__)


@rate_limit(max_requests=20, period=60)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def market_query(request):
    """
    Process market-related query
    Handles analytics, buy/sell requests, and comparisons
    """
    try:
        user_id = request.user.id
        user_input = request.data.get('input')
        context = request.data.get('context', {})
        
        if not user_input:
            return Response(
                {'error': 'No input provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process through orchestrator
        response = market_intelligence_orchestrator.process_market_query(
            user_input=user_input,
            user_id=user_id,
            context=context
        )
        
        return Response(response, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in market query: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@rate_limit(max_requests=20, period=60)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_property_match(request):
    """
    Calculate match score for property against buyer profile
    """
    try:
        user_id = request.user.id
        property_data = request.data.get('property')
        
        if not property_data:
            return Response(
                {'error': 'No property data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate match
        match_score = market_intelligence_orchestrator.calculate_property_match(
            user_id=user_id,
            property_data=property_data
        )
        
        return Response(match_score.to_dict(), status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error calculating property match: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@rate_limit(max_requests=20, period=60)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def match_agents(request):
    """
    Match agents for seller requirements
    """
    try:
        seller_requirements = request.data.get('requirements')
        
        if not seller_requirements:
            return Response(
                {'error': 'No requirements provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Match agents
        matches = agent_matching_system.match_agent_for_seller(seller_requirements)
        
        return Response({
            'matches': [m.to_dict() for m in matches],
            'total': len(matches)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error matching agents: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@rate_limit(max_requests=20, period=60)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def market_analytics(request):
    """
    Execute safe market analytics query
    """
    try:
        user_id = request.user.id
        entity = request.data.get('entity', 'property')
        metric = request.data.get('metric', 'price')
        query_type = request.data.get('query_type', 'median')
        filters = request.data.get('filters', {})
        
        # Convert strings to enums
        metric_enum = MetricType(metric)
        query_type_enum = QueryType(query_type)
        
        # Create query
        query = safe_analytics_layer.create_query(
            entity=entity,
            metric=metric_enum,
            query_type=query_type_enum,
            filters=filters,
            user_id=user_id
        )
        
        # Execute query
        result = safe_analytics_layer.execute_query(query)
        
        return Response(result.to_dict(), status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in market analytics: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@rate_limit(max_requests=30, period=60)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def market_summary(request):
    """
    Get overall market intelligence summary
    """
    try:
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        summary = market_intelligence_orchestrator.get_market_summary()
        
        return Response(summary, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting market summary: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )