"""
AI Smart Assistant API
REST API endpoints for the smart AI assistant
Integrates intent detection, search, and conversation management
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging
from django.conf import settings

from .ai_smart_conversation_handler import smart_conversation_manager
from .ai_result_renderer import result_renderer
from .ai_smart_intent_detection import Intent

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smart_assistant_chat(request):
    """
    Smart AI Assistant Chat Endpoint
    Processes user messages and returns intelligent responses
    
    Request body:
    {
        "message": "User message text",
        "conversation_id": "conversation-uuid",
        "render_results": true  # Optional, render results as cards
    }
    
    Response:
    {
        "response": "AI response text",
        "action": "suggested_action",
        "results": [...],  // Rendered result cards if render_results=true
        "metadata": {...}
    }
    """
    try:
        # Get request data
        message = request.data.get('message', '').strip()
        conversation_id = request.data.get('conversation_id')
        render_results = request.data.get('render_results', True)
        
        if not message:
            return Response(
                {'success': False, 'error': 'No message provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate conversation ID if not provided
        if not conversation_id:
            import uuid
            conversation_id = str(uuid.uuid4())
        
        # Get current user
        user = request.user if request.user.is_authenticated else None
        user_id = user.id if user else None
        
        # Log the request
        logger.info(f"Smart Assistant chat request: user_id={user_id}, conversation_id={conversation_id}, message={message[:100]}...")
        
        # Process message through conversation manager
        response_data = smart_conversation_manager.process_message(
            message, conversation_id, user_id
        )
        
        # Render results if requested and available
        if render_results and response_data.get('results'):
            response_data['rendered_results'] = result_renderer.render_results(
                response_data['results']
            )
        
        # Add conversation ID to response
        response_data['conversation_id'] = conversation_id
        
        # Log the response
        results = response_data.get('results') or []
        logger.info(f"Smart Assistant response: action={response_data.get('action')}, results_count={len(results)}")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Smart Assistant error: {str(e)}", exc_info=True)
        return Response(
            {
                'success': False,
                'error': 'An error occurred processing your request',
                'details': str(e) if settings.DEBUG else None
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smart_assistant_reset(request):
    """
    Reset smart assistant conversation
    Clears conversation state and starts fresh
    
    Request body:
    {
        "conversation_id": "conversation-uuid"
    }
    """
    try:
        conversation_id = request.data.get('conversation_id')
        
        if not conversation_id:
            return Response(
                {'success': False, 'error': 'conversation_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user
        user = request.user if request.user.is_authenticated else None
        user_id = user.id if user else None
        
        # Reset conversation
        state = smart_conversation_manager.get_or_create_state(conversation_id, user_id)
        state.reset()
        smart_conversation_manager.save_state(state)
        
        logger.info(f"Reset conversation: conversation_id={conversation_id}, user_id={user_id}")
        
        return Response({
            'success': True,
            'message': 'Conversation reset successfully',
            'conversation_id': conversation_id
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Reset conversation error: {str(e)}", exc_info=True)
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def smart_assistant_state(request):
    """
    Get current conversation state
    
    Query params:
    - conversation_id: conversation UUID
    """
    try:
        conversation_id = request.query_params.get('conversation_id')
        
        if not conversation_id:
            return Response(
                {'success': False, 'error': 'conversation_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user
        user = request.user if request.user.is_authenticated else None
        user_id = user.id if user else None
        
        # Get state
        state = smart_conversation_manager.get_or_create_state(conversation_id, user_id)
        
        return Response({
            'success': True,
            'state': state.to_dict()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get state error: {str(e)}", exc_info=True)
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smart_assistant_confirm(request):
    """
    Handle user confirmation for pending actions
    
    Request body:
    {
        "conversation_id": "conversation-uuid",
        "confirmed": true/false
    }
    """
    try:
        conversation_id = request.data.get('conversation_id')
        confirmed = request.data.get('confirmed', False)
        
        if not conversation_id:
            return Response(
                {'success': False, 'error': 'conversation_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user
        user = request.user if request.user.is_authenticated else None
        user_id = user.id if user else None
        
        # Get state
        state = smart_conversation_manager.get_or_create_state(conversation_id, user_id)
        
        if not state.awaiting_confirmation:
            return Response(
                {'success': False, 'error': 'No pending confirmation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process confirmation
        if confirmed:
            message = "نعم"
        else:
            message = "لا"
        
        response_data = smart_conversation_manager._handle_confirmation(state, message)
        smart_conversation_manager.save_state(state)
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Confirm action error: {str(e)}", exc_info=True)
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smart_assistant_suggest_alternatives(request):
    """
    Suggest alternative search results with broader criteria
    
    Request body:
    {
        "conversation_id": "conversation-uuid"
    }
    """
    try:
        conversation_id = request.data.get('conversation_id')
        
        if not conversation_id:
            return Response(
                {'success': False, 'error': 'conversation_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user
        user = request.user if request.user.is_authenticated else None
        user_id = user.id if user else None
        
        # Get state
        state = smart_conversation_manager.get_or_create_state(conversation_id, user_id)
        
        if not state.collected_filters:
            return Response(
                {'success': False, 'error': 'No search criteria to expand'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Expand filters (remove price constraint, increase area range, etc.)
        expanded_filters = state.collected_filters.copy()
        
        # Remove price constraint
        if 'price' in expanded_filters:
            del expanded_filters['price']
        
        # Add nearby locations
        if 'location' in expanded_filters:
            # Could add nearby cities here
            pass
        
        # Perform new search
        from .ai_search_service import ai_search_service
        search_results = ai_search_service.search(
            state.current_intent,
            expanded_filters,
            user_id
        )
        
        # Render results
        rendered_results = result_renderer.render_results(search_results['results'])
        
        return Response({
            'success': True,
            'response': f'وجدت {len(rendered_results)} نتيجة إضافية مع معايير أوسع:',
            'results': rendered_results,
            'metadata': search_results['metadata']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Suggest alternatives error: {str(e)}", exc_info=True)
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
