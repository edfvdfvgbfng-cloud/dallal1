import logging
import json
import uuid
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import random
import time
from django.db.models import Q, Count, Avg, Sum, F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Property, Broker, BrokerChannel, BrokerJoinRequest, HotelPage, HotelRoom, ServiceProviderPage
from .models import BuildingAdvertisement, AdResponse

# Import new AI components
from .ai_conversation_manager import conversation_manager
from .ai_nlp_layer import nlp_manager
from .ai_intent_classifier import intent_classifier
from .ai_entity_extraction import entity_extractor
from .ai_context_engine import context_manager

logger = logging.getLogger('properties')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_chatbot_api(request):
    """AI Chatbot main API endpoint - Using AI Agent with tool calling and voice support"""
    try:
        data = request.data
        message = data.get('message', '')
        conversation_id = data.get('conversation_id', str(uuid.uuid4()))
        is_voice = data.get('is_voice', False)
        
        # Get current user if authenticated
        user = request.user if request.user.is_authenticated else None
        
        logger.info(f"AI Chatbot request: {message[:100]}... (Voice: {is_voice})")
        
        # Use the AI Agent for advanced processing
        response = conversation_manager.process_message(message, conversation_id, user, is_voice)
        
        return Response(response)
        
    except Exception as e:
        logger.error(f"AI Chatbot error: {str(e)}")
        return Response({
            'success': False,
            'error': 'حدث خطأ في معالجة الرسالة',
            'response': 'عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.'
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_confirmation_api(request):
    """API for handling user confirmations for AI Agent operations"""
    try:
        data = request.data
        conversation_id = data.get('conversation_id')
        confirmed = data.get('confirmed', False)
        
        # Get current user if authenticated
        user = request.user if request.user.is_authenticated else None
        
        if conversation_id is not None:
            result = conversation_manager.handle_confirmation(conversation_id, confirmed, user)
            return Response(result)
        else:
            return Response({
                'success': False,
                'message': 'يرجى توفير معرف المحادثة'
            })
            
    except Exception as e:
        logger.error(f"AI confirmation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'حدث خطأ في معالجة التأكيد'
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_feedback_api(request):
    """API for recording user feedback on AI responses"""
    try:
        data = request.data
        conversation_id = data.get('conversation_id')
        feedback = data.get('feedback')  # 'positive' or 'negative'
        message = data.get('message', '')
        
        if conversation_id and feedback:
            result = conversation_manager.record_feedback(conversation_id, feedback, message)
            return Response(result)
        else:
            return Response({
                'success': False,
                'message': 'يرجى توفير معرف المحادثة والملاحظة'
            })
            
    except Exception as e:
        logger.error(f"AI feedback error: {str(e)}")
        return Response({
            'success': False,
            'error': 'حدث خطأ في تسجيل الملاحظات'
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_correction_api(request):
    """API for recording user corrections"""
    try:
        data = request.data
        conversation_id = data.get('conversation_id')
        original_intent = data.get('original_intent')
        corrected_intent = data.get('corrected_intent')
        message = data.get('message', '')
        
        if conversation_id and original_intent and corrected_intent:
            context = context_manager.get_context(conversation_id)
            
            # Record correction in conversation learner
            conversation_manager.conversation_learner.record_correction(
                original_intent,
                corrected_intent,
                context.get_complete_context().get('entities', {}),
                context.get_complete_context().get('entities', {}),
                message
            )
            
            # Update context with corrected intent
            context.update_intent(corrected_intent, 1.0)
            
            return Response({
                'success': True,
                'message': 'تم تسجيل التصحيح، شكراً لك!'
            })
        else:
            return Response({
                'success': False,
                'message': 'يرجى توفير معلومات التصحيح الكاملة'
            })
            
    except Exception as e:
        logger.error(f"AI correction error: {str(e)}")
        return Response({
            'success': False,
            'error': 'حدث خطأ في تسجيل التصحيح'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_statistics_api(request):
    """API for getting AI system statistics"""
    try:
        stats = conversation_manager.get_statistics()
        
        return Response({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"AI statistics error: {str(e)}")
        return Response({
            'success': False,
            'error': 'حدث خطأ في جلب الإحصائيات'
        }, status=500)