"""
Django Integration Example for Simplified Math Solver

This file shows how to integrate the simplified math solver into your
Django backend for the Examify app.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.uploadhandler import TemporaryFileUploadHandler
import json
import logging
import asyncio
import sys
import os

# Add AI-Services to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'AI-Services'))

# Import the simplified solver
import importlib.util
spec = importlib.util.spec_from_file_location("simplified_math_solver", 
                                              os.path.join(os.path.dirname(__file__), '..', 'AI-Services', 'simplified_math_solver.py'))
simplified_solver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simplified_solver)

solve_math_from_image_sync = simplified_solver.solve_math_from_image_sync
solve_text_problem = simplified_solver.solve_text_problem

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def solve_math_image(request):
    """
    API endpoint to solve math problems from uploaded images
    
    Expected: Multipart form with 'image' file
    Returns: JSON with solution details
    """
    try:
        # Check if image was uploaded
        if 'image' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No image file provided'
            }, status=400)
        
        image_file = request.FILES['image']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
        if image_file.content_type not in allowed_types:
            return JsonResponse({
                'success': False,
                'error': 'Invalid file type. Please upload JPEG, PNG, or GIF images.'
            }, status=400)
        
        # Validate file size (e.g., max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if image_file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': 'File too large. Maximum size is 10MB.'
            }, status=400)
        
        # Read image data
        image_data = image_file.read()
        
        # Process with simplified math solver
        result = solve_math_from_image_sync(image_data, use_fallback=True)
        
        # Format response for frontend
        response_data = {
            'success': True,
            'data': {
                'extracted_problem': result.extracted_text,
                'problem_type': result.problem_type,
                'difficulty': result.difficulty.value,
                'final_answer': result.final_answer,
                'solution_steps': result.solution_steps,
                'explanation': result.explanation,
                'verification': result.verification,
                'study_tips': result.study_tips,
                'related_concepts': result.related_concepts,
                'confidence_score': result.confidence_score,
                'method_used': result.method_used,
                'processing_time': result.processing_time
            }
        }
        
        logger.info(f"Math problem solved successfully: {result.problem_type}")
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error solving math problem: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to process image. Please try again with a clearer image.'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def solve_math_text(request):
    """
    API endpoint to solve math problems from text input
    
    Expected: JSON with 'problem' field
    Returns: JSON with solution details
    """
    try:
        # Parse JSON body
        data = json.loads(request.body)
        problem_text = data.get('problem', '').strip()
        
        if not problem_text:
            return JsonResponse({
                'success': False,
                'error': 'No problem text provided'
            }, status=400)
        
        # Solve the text problem
        # Since solve_text_problem is async, we need to run it in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(solve_text_problem(problem_text))
        finally:
            loop.close()
        
        # Format response
        response_data = {
            'success': True,
            'data': {
                'extracted_problem': result.get('extracted_problem', problem_text),
                'problem_type': result.get('problem_type', 'unknown'),
                'difficulty': result.get('difficulty', 'unknown'),
                'final_answer': result.get('final_answer', ''),
                'solution_steps': result.get('solution_steps', []),
                'explanation': result.get('explanation', ''),
                'verification': result.get('verification', ''),
                'study_tips': result.get('study_tips', []),
                'related_concepts': result.get('related_concepts', []),
                'confidence_score': result.get('confidence', 0.0),
                'method_used': 'text_analysis'
            }
        }
        
        logger.info(f"Text problem solved successfully: {result.get('problem_type')}")
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        logger.error(f"Error solving text problem: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to process problem. Please try again.'
        }, status=500)


@require_http_methods(["GET"])
def math_solver_status(request):
    """
    API endpoint to check math solver status and capabilities
    """
    try:
        # Test solver availability
        from simplified_math_solver import MathProblemSolver
        solver = MathProblemSolver(use_vision_ocr_fallback=True)
        
        status_data = {
            'success': True,
            'status': 'available',
            'capabilities': {
                'gemini_vision': True,
                'google_vision_ocr': solver.vision_ocr.is_available() if solver.vision_ocr else False,
                'text_solving': True,
                'image_solving': True
            },
            'supported_formats': ['JPEG', 'PNG', 'GIF'],
            'max_file_size': '10MB',
            'features': [
                'Step-by-step solutions',
                'Educational explanations',
                'Study tips for exam preparation',
                'Difficulty level assessment',
                'Solution verification methods'
            ]
        }
        
        return JsonResponse(status_data)
        
    except Exception as e:
        logger.error(f"Error checking solver status: {str(e)}")
        return JsonResponse({
            'success': False,
            'status': 'unavailable',
            'error': 'Math solver service is currently unavailable'
        }, status=503)


# URL patterns (add to your urls.py)
"""
from django.urls import path
from . import math_solver_views

urlpatterns = [
    path('api/math/solve-image/', math_solver_views.solve_math_image, name='solve_math_image'),
    path('api/math/solve-text/', math_solver_views.solve_math_text, name='solve_math_text'),
    path('api/math/status/', math_solver_views.math_solver_status, name='math_solver_status'),
]
"""

# Example usage in your views.py:
"""
# For AItutor app views.py

from django.shortcuts import render
from django.http import JsonResponse
from .math_solver_views import solve_math_image, solve_math_text

class MathTutorView:
    def solve_problem(self, request):
        if request.method == 'POST':
            if 'image' in request.FILES:
                return solve_math_image(request)
            elif request.content_type == 'application/json':
                return solve_math_text(request)
        
        return JsonResponse({'error': 'Invalid request'}, status=400)
"""

# Frontend JavaScript example:
"""
// Solve from image
async function solveMathFromImage(imageFile) {
    const formData = new FormData();
    formData.append('image', imageFile);
    
    try {
        const response = await fetch('/api/math/solve-image/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            displaySolution(result.data);
        } else {
            showError(result.error);
        }
    } catch (error) {
        showError('Failed to solve problem');
    }
}

// Solve from text
async function solveMathFromText(problemText) {
    try {
        const response = await fetch('/api/math/solve-text/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ problem: problemText })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displaySolution(result.data);
        } else {
            showError(result.error);
        }
    } catch (error) {
        showError('Failed to solve problem');
    }
}

function displaySolution(data) {
    document.getElementById('problem').textContent = data.extracted_problem;
    document.getElementById('answer').textContent = data.final_answer;
    document.getElementById('explanation').textContent = data.explanation;
    
    // Display solution steps
    const stepsList = document.getElementById('solution-steps');
    stepsList.innerHTML = '';
    data.solution_steps.forEach((step, index) => {
        const li = document.createElement('li');
        li.textContent = `Step ${index + 1}: ${step}`;
        stepsList.appendChild(li);
    });
    
    // Display study tips
    const tipsList = document.getElementById('study-tips');
    tipsList.innerHTML = '';
    data.study_tips.forEach(tip => {
        const li = document.createElement('li');
        li.textContent = tip;
        tipsList.appendChild(li);
    });
}
"""
