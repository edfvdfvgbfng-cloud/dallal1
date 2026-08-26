"""
Multimodal API Views
REST API endpoints for multimodal AI processing
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
import logging

from .ai_unified_multimodal import unified_multimodal_pipeline
from .ai_multimodal_input import (
    MultimodalInputManager, ImageData, DocumentData, VoiceData, LocationData,
    ImageCategory, DocumentType
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def multimodal_chat(request):
    """
    Process multimodal chat query
    Accepts text, images, documents, voice, and location
    """
    try:
        user_id = request.user.id
        conversation_id = request.data.get('conversation_id')
        text = request.data.get('text')
        
        # Process images
        images = []
        for image_data in request.FILES.getlist('images', []):
            image = ImageData(
                data=image_data.read(),
                mime_type=image_data.content_type,
                filename=image_data.name
            )
            images.append(image)
        
        # Process documents
        documents = []
        for doc_data in request.FILES.getlist('documents', []):
            doc_type = DocumentType.CV if 'cv' in doc_data.name.lower() else DocumentType.OTHER
            document = DocumentData(
                data=doc_data.read(),
                mime_type=doc_data.content_type,
                filename=doc_data.name,
                document_type=doc_type
            )
            documents.append(document)
        
        # Process voice
        voice_data = None
        voice_file = request.FILES.get('voice')
        if voice_file:
            voice_data = VoiceData(
                data=voice_file.read(),
                mime_type=voice_file.content_type,
                filename=voice_file.name
            )
        
        # Process location
        location_data = None
        if request.data.get('latitude') and request.data.get('longitude'):
            location_data = LocationData(
                latitude=float(request.data['latitude']),
                longitude=float(request.data['longitude']),
                address=request.data.get('address'),
                radius=float(request.data.get('radius')) if request.data.get('radius') else None
            )
        
        # Process through pipeline
        response = unified_multimodal_pipeline.process_multimodal_query(
            text=text,
            images=images,
            documents=documents,
            voice_data=voice_data,
            location_data=location_data,
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        return Response(response, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in multimodal chat: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def image_similarity_search(request):
    """
    Search for properties visually similar to uploaded image
    """
    try:
        user_id = request.user.id
        
        # Get query image
        image_file = request.FILES.get('image')
        if not image_file:
            return Response(
                {'error': 'No image provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create image data
        query_image = ImageData(
            data=image_file.read(),
            mime_type=image_file.content_type,
            filename=image_file.name
        )
        
        # Get constraints
        constraints = {
            'governorate': request.data.get('governorate'),
            'max_price': request.data.get('max_price')
        }
        
        # Get property data (would query database)
        property_data = []  # Placeholder
        
        # Process similarity search
        response = unified_multimodal_pipeline.process_image_similarity_search(
            query_image, property_data, constraints
        )
        
        return Response(response, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in image similarity search: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cv_job_matching(request):
    """
    Upload CV and match with job listings
    """
    try:
        user_id = request.user.id
        
        # Get CV file
        cv_file = request.FILES.get('cv')
        if not cv_file:
            return Response(
                {'error': 'No CV provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create document data
        cv_document = DocumentData(
            data=cv_file.read(),
            mime_type=cv_file.content_type,
            filename=cv_file.name,
            document_type=DocumentType.CV
        )
        
        # Get job listings (would query database)
        job_listings = []  # Placeholder
        
        # Process CV matching
        response = unified_multimodal_pipeline.process_cv_job_matching(
            cv_document, job_listings
        )
        
        return Response(response, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in CV job matching: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def document_qa(request):
    """
    Upload document and ask questions about it
    """
    try:
        user_id = request.user.id
        
        # Get document file
        doc_file = request.FILES.get('document')
        if not doc_file:
            return Response(
                {'error': 'No document provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get question
        question = request.data.get('question')
        if not question:
            return Response(
                {'error': 'No question provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create document data
        document = DocumentData(
            data=doc_file.read(),
            mime_type=doc_file.content_type,
            filename=doc_file.name,
            document_type=DocumentType.OTHER
        )
        
        # Process document QA
        response = unified_multimodal_pipeline.process_document_qa(document, question)
        
        return Response(response, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in document QA: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pipeline_statistics(request):
    """
    Get pipeline statistics (admin/debug only)
    """
    try:
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = unified_multimodal_pipeline.get_pipeline_statistics()
        
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting pipeline statistics: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )