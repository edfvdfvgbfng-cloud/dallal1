"""
AI Gateway API Views
REST API endpoints for the unified AI gateway
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging
from datetime import datetime

from .ai_gateway import ai_gateway
from .ai_conversation_state_manager import conversation_state_manager
from .ai_conversation_manager import conversation_manager

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_chat(request):
    """
    Unified AI chat endpoint - Bridge to conversation_manager
    Routes to appropriate AI subsystem based on context
    Compatible with existing frontend contract
    """
    try:
        # Get message (support both 'message' and 'input' for compatibility)
        message = request.data.get('message') or request.data.get('input', '')
        conversation_id = request.data.get('conversation_id')
        is_voice = request.data.get('is_voice', False)
        context = request.data.get('context', {})
        
        # Get current user if authenticated
        user = request.user if request.user.is_authenticated else None
        user_id = user.id if user else None
        
        if not conversation_id:
            import uuid
            conversation_id = str(uuid.uuid4())
        
        if not message:
            return Response(
                {'success': False, 'error': 'No message provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log the request
        logger.info(f"AI Gateway chat request: user_id={user_id}, conversation_id={conversation_id}, message={message[:100]}...")
        
        # For now, bridge to conversation_manager (existing system)
        # This maintains compatibility while we gradually migrate
        try:
            response = conversation_manager.process_message(message, conversation_id, user, is_voice)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as conversation_error:
            logger.error(f"Conversation manager error: {str(conversation_error)}", exc_info=True)
            # Return a fallback response instead of error
            return Response({
                'success': True,
                'response': 'أهلاً بك! أنا مساعد ذكاء اصطناعي لمساعدتك في البحث عن العقارات. حالياً هناك مشكلة في معالجة طلبك، لكن يمكنك استخدام البحث المتقدم في الموقع.',
                'state': {'intent': 'error', 'entities': {}}
            }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in AI chat: {str(e)}", exc_info=True)
        return Response({
            'success': True,  # Return success to avoid breaking the UI
            'response': 'أهلاً بك! أنا مساعد ذكاء اصطناعي لمساعدتك في البحث عن العقارات. حالياً هناك مشكلة في الاتصال، يرجى المحاولة مرة أخرى.',
            'state': {'intent': 'error', 'entities': {}}
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_multimodal(request):
    """
    Multimodal AI endpoint
    Handles text, voice, image, document, location inputs
    """
    try:
        user_id = request.user.id
        conversation_id = request.data.get('conversation_id')
        input_type = request.data.get('input_type', 'text')
        content = request.data.get('content')
        context = request.data.get('context', {})
        
        if not conversation_id:
            conversation_id = f"conv_{user_id}_{datetime.now().timestamp()}"
        
        if not content:
            return Response(
                {'error': 'No content provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process through AI gateway
        response = ai_gateway.process_request(
            request_type='multimodal',
            user_id=user_id,
            conversation_id=conversation_id,
            input_data={'input_type': input_type, 'content': content},
            context=context
        )
        
        return Response(response, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in AI multimodal: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_market(request):
    """
    Market intelligence endpoint
    Handles market analytics and buyer-seller matching
    """
    try:
        user_id = request.user.id
        conversation_id = request.data.get('conversation_id')
        query = request.data.get('query')
        context = request.data.get('context', {})
        
        if not conversation_id:
            conversation_id = f"conv_{user_id}_{datetime.now().timestamp()}"
        
        if not query:
            return Response(
                {'error': 'No query provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process through AI gateway
        response = ai_gateway.process_request(
            request_type='market',
            user_id=user_id,
            conversation_id=conversation_id,
            input_data={'query': query},
            context=context
        )
        
        return Response(response, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in AI market: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_autonomous(request):
    """
    Autonomous agent endpoint
    Handles multi-step task execution
    """
    try:
        user_id = request.user.id
        conversation_id = request.data.get('conversation_id')
        user_input = request.data.get('input')
        context = request.data.get('context', {})
        
        if not conversation_id:
            conversation_id = f"conv_{user_id}_{datetime.now().timestamp()}"
        
        if not user_input:
            return Response(
                {'error': 'No input provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process through AI gateway
        response = ai_gateway.process_request(
            request_type='autonomous',
            user_id=user_id,
            conversation_id=conversation_id,
            input_data={'input': user_input},
            context=context
        )
        
        return Response(response, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in AI autonomous: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_state(request):
    """
    Get conversation state
    """
    try:
        conversation_id = request.query_params.get('conversation_id')
        
        if not conversation_id:
            return Response(
                {'error': 'conversation_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        state = ai_gateway.get_conversation_state(conversation_id)
        
        if not state:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(state.to_dict(), status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting conversation state: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_conversation(request):
    """
    Clear conversation state
    """
    try:
        conversation_id = request.data.get('conversation_id')
        
        if not conversation_id:
            return Response(
                {'error': 'conversation_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ai_gateway.clear_conversation_state(conversation_id)
        
        return Response({'success': True}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_chatbot_legacy(request):
    """
    Legacy endpoint - Compatibility wrapper for /api/chatbot/
    Redirects to AI Gateway chat endpoint
    Maintains backward compatibility with existing frontend
    """
    try:
        # Simply forward to ai_chat
        return ai_chat(request)
        
    except Exception as e:
        logger.error(f"Error in legacy chatbot endpoint: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': 'حدث خطأ في معالجة الرسالة',
            'response': 'عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)