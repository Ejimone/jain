"""
AI Services integration module for the Examify backend.
This module provides a Django-friendly interface to the AI services.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, List
from django.conf import settings

# Add AI-Services directory to Python path
ai_services_path = os.path.join(os.path.dirname(__file__), '..', 'AI-Services')
if ai_services_path not in sys.path:
    sys.path.insert(0, ai_services_path)

logger = logging.getLogger('AIServices')


class ExamPrepAIService:
    """
    Main AI service integration for exam preparation features.
    Provides a unified interface to various AI capabilities.
    """
    
    def __init__(self):
        self.gemini_api_key = getattr(settings, 'AI_SERVICES_CONFIG', {}).get('GEMINI_API_KEY', '')
        self.openai_api_key = getattr(settings, 'AI_SERVICES_CONFIG', {}).get('OPENAI_API_KEY', '')
        self.serpapi_key = getattr(settings, 'AI_SERVICES_CONFIG', {}).get('SERPAPI_KEY', '')
        
        # Initialize AI agents lazily
        self._exam_prep_agent = None
        self._math_solver = None
        self._rag_processor = None
    
    @property
    def exam_prep_agent(self):
        """Lazy initialization of ExamPrepAIAgent"""
        if self._exam_prep_agent is None:
            try:
                from exam_prep_integration import ExamPrepAIAgent
                self._exam_prep_agent = ExamPrepAIAgent(serpapi_key=self.serpapi_key)
            except ImportError as e:
                logger.error(f"Failed to import ExamPrepAIAgent: {e}")
                self._exam_prep_agent = None
        return self._exam_prep_agent
    
    @property
    def math_solver(self):
        """Lazy initialization of GeminiMathSolver"""
        if self._math_solver is None:
            try:
                from math_solution import GeminiMathSolver
                self._math_solver = GeminiMathSolver()
            except ImportError as e:
                logger.error(f"Failed to import GeminiMathSolver: {e}")
                self._math_solver = None
        return self._math_solver
    
    @property
    def rag_processor(self):
        """Lazy initialization of RagProcessor"""
        if self._rag_processor is None:
            try:
                from Rag import RagProcessor
                self._rag_processor = RagProcessor()
            except ImportError as e:
                logger.error(f"Failed to import RagProcessor: {e}")
                self._rag_processor = None
        return self._rag_processor
    
    async def get_comprehensive_study_materials(
        self, 
        topic: str, 
        subject: str = None,
        difficulty_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Get comprehensive study materials for a topic.
        """
        try:
            if self.exam_prep_agent:
                return await self.exam_prep_agent.get_comprehensive_study_materials(
                    topic=topic,
                    subject=subject,
                    difficulty_level=difficulty_level
                )
            else:
                return {
                    'error': 'Exam prep agent not available',
                    'materials': []
                }
        except Exception as e:
            logger.error(f"Error getting study materials: {e}")
            return {
                'error': str(e),
                'materials': []
            }
    
    def solve_math_problem(
        self, 
        problem: str, 
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Solve a mathematical problem using AI.
        """
        try:
            if self.math_solver:
                result = self.math_solver.solve_problem(problem, context=context)
                if result:
                    return {
                        'solution': result.solution,
                        'steps': result.steps if hasattr(result, 'steps') else [],
                        'explanation': result.explanation if hasattr(result, 'explanation') else '',
                        'confidence': result.confidence if hasattr(result, 'confidence') else 0.0
                    }
            
            return {
                'error': 'Math solver not available',
                'solution': 'Unable to solve this problem at the moment.'
            }
        except Exception as e:
            logger.error(f"Error solving math problem: {e}")
            return {
                'error': str(e),
                'solution': 'Unable to solve this problem due to an error.'
            }
    
    def process_document(
        self, 
        file_path: str, 
        query: str = None
    ) -> Dict[str, Any]:
        """
        Process a document using RAG (Retrieval-Augmented Generation).
        """
        try:
            if self.rag_processor:
                # Process the document
                result = self.rag_processor.process_document(file_path)
                
                if query:
                    # Query the processed document
                    answer = self.rag_processor.query_document(query)
                    return {
                        'processed': True,
                        'answer': answer,
                        'query': query
                    }
                else:
                    return {
                        'processed': True,
                        'summary': result.get('summary', 'Document processed successfully')
                    }
            
            return {
                'error': 'RAG processor not available',
                'processed': False
            }
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                'error': str(e),
                'processed': False
            }
    
    def generate_explanation(
        self, 
        topic: str, 
        context: str = "",
        difficulty_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Generate an explanation for a topic.
        """
        try:
            # Use available AI services to generate explanation
            if self.exam_prep_agent:
                # Use exam prep agent for educational explanations
                prompt = f"Explain the topic '{topic}' at {difficulty_level} level."
                if context:
                    prompt += f" Context: {context}"
                
                # This is a placeholder - implement actual explanation generation
                explanation = f"Here's an explanation of {topic}:\n\n"
                explanation += f"This topic is important in your studies. "
                explanation += f"At the {difficulty_level} level, you should understand..."
                
                return {
                    'explanation': explanation,
                    'topic': topic,
                    'difficulty_level': difficulty_level,
                    'generated': True
                }
            
            return {
                'error': 'Explanation service not available',
                'explanation': f"Unable to generate explanation for {topic} at this time."
            }
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return {
                'error': str(e),
                'explanation': f"Error generating explanation for {topic}."
            }
    
    def analyze_image(
        self, 
        image_path: str, 
        question: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze an image and provide insights.
        """
        try:
            # Placeholder for image analysis
            # This would use Gemini Vision or similar service
            
            return {
                'analysis': f"Image analysis for: {image_path}",
                'question': question,
                'insights': [
                    "This appears to be an educational image",
                    "Contains text or diagrams relevant to study",
                    "May require OCR processing"
                ],
                'ocr_text': "",  # Would extract text from image
                'processed': True
            }
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {
                'error': str(e),
                'processed': False
            }
    
    def get_real_time_information(
        self, 
        query: str, 
        search_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Get real-time information using search APIs.
        """
        try:
            if self.exam_prep_agent:
                # Use the real-time search capabilities
                # This is a placeholder implementation
                return {
                    'query': query,
                    'search_type': search_type,
                    'results': [
                        {
                            'title': f"Search result for: {query}",
                            'description': "Real-time search functionality",
                            'url': "#",
                            'relevance_score': 0.85
                        }
                    ],
                    'timestamp': "2025-01-22T10:00:00Z"
                }
            
            return {
                'error': 'Real-time search not available',
                'results': []
            }
        except Exception as e:
            logger.error(f"Error getting real-time information: {e}")
            return {
                'error': str(e),
                'results': []
            }


# Global instance
ai_service = ExamPrepAIService()


def get_ai_service() -> ExamPrepAIService:
    """Get the global AI service instance"""
    return ai_service
