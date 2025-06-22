from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import base64
import uuid
import os
import logging
import asyncio
from typing import Dict, Any

from .ai_services import get_ai_service

logger = logging.getLogger('AIServices')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def solve_math_problem(request):
    """
    Solve a mathematical problem using AI.
    
    Expected payload:
    {
        "problem": "2x + 5 = 15, solve for x",
        "context": "Linear equations chapter",
        "show_steps": true
    }
    """
    try:
        problem = request.data.get('problem')
        context = request.data.get('context', '')
        
        if not problem:
            return Response(
                {'error': 'Problem statement is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ai_service = get_ai_service()
        result = ai_service.solve_math_problem(problem, context)
        
        return Response({
            'success': True,
            'problem': problem,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error in solve_math_problem: {e}")
        return Response(
            {'error': 'Failed to solve math problem'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_image(request):
    """
    Analyze an uploaded image and provide insights.
    
    Expected payload:
    {
        "image_base64": "data:image/jpeg;base64,...",
        "question": "What is this diagram showing?",
        "subject": "mathematics"
    }
    """
    try:
        image_data = request.data.get('image_base64')
        question = request.data.get('question', '')
        subject = request.data.get('subject', '')
        
        if not image_data:
            return Response(
                {'error': 'Image data is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process base64 image
        if 'base64,' in image_data:
            format, imgstr = image_data.split('base64,')
            ext = format.split('/')[-1].split(';')[0]
        else:
            imgstr = image_data
            ext = 'jpg'
        
        # Save image temporarily
        img_data = base64.b64decode(imgstr)
        filename = f"temp_image_{uuid.uuid4()}.{ext}"
        file_path = default_storage.save(f"temp/{filename}", ContentFile(img_data))
        
        try:
            # Analyze image
            ai_service = get_ai_service()
            result = ai_service.analyze_image(file_path, question)
            
            return Response({
                'success': True,
                'question': question,
                'subject': subject,
                'analysis': result
            })
            
        finally:
            # Clean up temporary file
            if default_storage.exists(file_path):
                default_storage.delete(file_path)
        
    except Exception as e:
        logger.error(f"Error in analyze_image: {e}")
        return Response(
            {'error': 'Failed to analyze image'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_document(request):
    """
    Process an uploaded document using RAG.
    
    Expected payload:
    {
        "file": <file upload>,
        "query": "What are the main concepts in this document?",
        "extract_questions": true
    }
    """
    try:
        uploaded_file = request.FILES.get('file')
        query = request.data.get('query', '')
        extract_questions = request.data.get('extract_questions', False)
        
        if not uploaded_file:
            return Response(
                {'error': 'File is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check file type
        allowed_extensions = getattr(settings, 'AI_SERVICES_CONFIG', {}).get(
            'ALLOWED_FILE_TYPES', 
            ['pdf', 'docx', 'txt']
        )
        
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext not in allowed_extensions:
            return Response(
                {'error': f'File type not supported. Allowed: {", ".join(allowed_extensions)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save uploaded file temporarily
        filename = f"upload_{uuid.uuid4()}_{uploaded_file.name}"
        file_path = default_storage.save(f"uploads/{filename}", uploaded_file)
        
        try:
            # Process document
            ai_service = get_ai_service()
            result = ai_service.process_document(file_path, query)
            
            response_data = {
                'success': True,
                'filename': uploaded_file.name,
                'query': query,
                'result': result
            }
            
            if extract_questions:
                # TODO: Implement question extraction
                response_data['extracted_questions'] = []
            
            return Response(response_data)
            
        finally:
            # Clean up temporary file
            if default_storage.exists(file_path):
                default_storage.delete(file_path)
        
    except Exception as e:
        logger.error(f"Error in process_document: {e}")
        return Response(
            {'error': 'Failed to process document'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_study_materials(request):
    """
    Get comprehensive study materials for a topic.
    
    Expected payload:
    {
        "topic": "Linear Algebra",
        "subject": "Mathematics",
        "difficulty_level": "intermediate",
        "include_videos": true,
        "include_practice": true
    }
    """
    try:
        topic = request.data.get('topic')
        subject = request.data.get('subject', '')
        difficulty_level = request.data.get('difficulty_level', 'intermediate')
        
        if not topic:
            return Response(
                {'error': 'Topic is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ai_service = get_ai_service()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                ai_service.get_comprehensive_study_materials(
                    topic=topic,
                    subject=subject,
                    difficulty_level=difficulty_level
                )
            )
        finally:
            loop.close()
        
        return Response({
            'success': True,
            'topic': topic,
            'subject': subject,
            'difficulty_level': difficulty_level,
            'materials': result
        })
        
    except Exception as e:
        logger.error(f"Error in get_study_materials: {e}")
        return Response(
            {'error': 'Failed to get study materials'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_explanation(request):
    """
    Generate an explanation for a topic or concept.
    
    Expected payload:
    {
        "topic": "Photosynthesis",
        "context": "High school biology",
        "difficulty_level": "beginner",
        "explanation_type": "detailed"
    }
    """
    try:
        topic = request.data.get('topic')
        context = request.data.get('context', '')
        difficulty_level = request.data.get('difficulty_level', 'intermediate')
        explanation_type = request.data.get('explanation_type', 'detailed')
        
        if not topic:
            return Response(
                {'error': 'Topic is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ai_service = get_ai_service()
        result = ai_service.generate_explanation(
            topic=topic,
            context=context,
            difficulty_level=difficulty_level
        )
        
        return Response({
            'success': True,
            'topic': topic,
            'explanation_type': explanation_type,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error in generate_explanation: {e}")
        return Response(
            {'error': 'Failed to generate explanation'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_real_time(request):
    """
    Search for real-time information on a topic.
    
    Expected payload:
    {
        "query": "latest developments in quantum computing",
        "search_type": "academic",
        "num_results": 10
    }
    """
    try:
        query = request.data.get('query')
        search_type = request.data.get('search_type', 'general')
        num_results = request.data.get('num_results', 10)
        
        if not query:
            return Response(
                {'error': 'Query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ai_service = get_ai_service()
        result = ai_service.get_real_time_information(query, search_type)
        
        return Response({
            'success': True,
            'query': query,
            'search_type': search_type,
            'num_results': num_results,
            'results': result
        })
        
    except Exception as e:
        logger.error(f"Error in search_real_time: {e}")
        return Response(
            {'error': 'Failed to perform real-time search'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for AI services.
    """
    try:
        # Simple health check without initializing AI services
        return Response({
            'status': 'healthy',
            'message': 'AI Services backend is running',
            'services': {
                'exam_prep_agent': 'available',
                'math_solver': 'available',
                'rag_processor': 'available',
            },
            'timestamp': '2025-06-22T05:26:00Z'
        })
        
    except Exception as e:
        logger.error(f"Error in health_check: {e}")
        return Response(
            {'status': 'unhealthy', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_service_capabilities(request):
    """
    Get information about available AI service capabilities.
    """
    try:
        capabilities = {
            'math_solving': {
                'available': True,
                'description': 'Solve mathematical problems with step-by-step solutions',
                'supported_types': ['algebra', 'calculus', 'geometry', 'statistics']
            },
            'image_analysis': {
                'available': True,
                'description': 'Analyze educational images and diagrams',
                'supported_formats': ['jpg', 'jpeg', 'png']
            },
            'document_processing': {
                'available': True,
                'description': 'Process and extract information from documents',
                'supported_formats': ['pdf', 'docx', 'txt']
            },
            'study_materials': {
                'available': True,
                'description': 'Generate comprehensive study materials for topics',
                'features': ['explanations', 'examples', 'practice_questions']
            },
            'real_time_search': {
                'available': True,
                'description': 'Search for current information and research',
                'search_types': ['general', 'academic', 'news']
            }
        }
        
        return Response({
            'success': True,
            'capabilities': capabilities
        })
        
    except Exception as e:
        logger.error(f"Error in get_service_capabilities: {e}")
        return Response(
            {'error': 'Failed to get service capabilities'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
