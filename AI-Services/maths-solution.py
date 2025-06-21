"""
Math Problem Solver Module for Examify AI-powered Exam Preparation App

This module integrates OCR technology (Mathpix and Google Vision API) with 
Google Gemini AI to extract mathematical content from images and provide 
comprehensive solutions and explanations.

Features:
- Multiple OCR providers (Mathpix, Google Vision)
- Intelligent fallback mechanisms
- Comprehensive math problem solving using Gemini AI
- Structured response format
- Error handling and logging
- Educational focus for exam preparation

Author: Examify AI Team
Version: 1.0.0
"""

import os
import io
import base64
import logging
import asyncio
from typing import Union, Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

# Core dependencies
import google.generativeai as genai
from openai import OpenAI
from google.cloud import vision
from google.oauth2 import service_account
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCRProvider(Enum):
    """Available OCR providers"""
    MATHPIX = "mathpix"
    GOOGLE_VISION = "google_vision"
    BOTH = "both"


class MathDifficulty(Enum):
    """Math problem difficulty levels"""
    ELEMENTARY = "elementary"
    MIDDLE_SCHOOL = "middle_school"
    HIGH_SCHOOL = "high_school"
    COLLEGE = "college"
    ADVANCED = "advanced"


@dataclass
class OCRResult:
    """OCR extraction result"""
    provider: str
    success: bool
    text: str
    latex: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None
    raw_response: Optional[Dict] = None


@dataclass
class MathSolutionResult:
    """Complete math solution result"""
    extracted_text: str
    extracted_latex: Optional[str]
    problem_type: str
    difficulty: MathDifficulty
    solution_steps: List[str]
    final_answer: str
    explanation: str
    verification: str
    study_tips: List[str]
    related_concepts: List[str]
    ocr_provider_used: str
    confidence_score: float
    processing_time: float


class MathpixOCR:
    """Mathpix OCR integration"""
    
    def __init__(self):
        self.app_id = os.getenv('MATHPIX_APP_ID')
        self.app_key = os.getenv('MATHPIX_APP_KEY')
        self.base_url = "https://api.mathpix.com/v3"
        
        if not self.app_id or not self.app_key:
            logger.warning("Mathpix credentials not found. Mathpix OCR will be disabled.")
    
    def is_available(self) -> bool:
        """Check if Mathpix OCR is available"""
        return bool(self.app_id and self.app_key)
    
    async def extract_math(self, image_data: bytes) -> OCRResult:
        """Extract math content using Mathpix OCR"""
        if not self.is_available():
            return OCRResult(
                provider="mathpix",
                success=False,
                text="",
                error="Mathpix credentials not configured"
            )
        
        try:
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            headers = {
                'app_id': self.app_id,
                'app_key': self.app_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'src': f'data:image/jpeg;base64,{image_base64}',
                'formats': ['text', 'latex_simplified', 'latex_styled'],
                'data_options': {
                    'include_asciimath': True,
                    'include_latex': True,
                    'include_mathml': False
                }
            }
            
            response = requests.post(
                f"{self.base_url}/text",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return OCRResult(
                    provider="mathpix",
                    success=True,
                    text=result.get('text', ''),
                    latex=result.get('latex_simplified', ''),
                    confidence=result.get('confidence', 0.0),
                    raw_response=result
                )
            else:
                return OCRResult(
                    provider="mathpix",
                    success=False,
                    text="",
                    error=f"Mathpix API error: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            logger.error(f"Mathpix OCR error: {str(e)}")
            return OCRResult(
                provider="mathpix",
                success=False,
                text="",
                error=str(e)
            )


class GoogleVisionOCR:
    """Google Cloud Vision OCR integration"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Vision client"""
        try:
            # Try to use service account credentials if provided
            credentials_path = os.getenv('GOOGLE_CLOUD_VISION_CREDENTIALS_PATH')
            if credentials_path and os.path.exists(credentials_path):
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
            else:
                # Use default authentication (Application Default Credentials)
                self.client = vision.ImageAnnotatorClient()
            logger.info("Google Vision OCR client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Google Vision OCR: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Google Vision OCR is available"""
        return self.client is not None
    
    async def extract_math(self, image_data: bytes) -> OCRResult:
        """Extract text using Google Cloud Vision OCR"""
        if not self.is_available():
            return OCRResult(
                provider="google_vision",
                success=False,
                text="",
                error="Google Vision client not initialized"
            )
        
        try:
            image = vision.Image(content=image_data)
            
            # Perform text detection
            response = self.client.text_detection(image=image)
            
            if response.error.message:
                return OCRResult(
                    provider="google_vision",
                    success=False,
                    text="",
                    error=response.error.message
                )
            
            # Extract text from response
            texts = response.text_annotations
            if texts:
                detected_text = texts[0].description
                
                # Calculate confidence (average of all detected text blocks)
                confidence = 0.0
                if len(texts) > 1:
                    confidences = []
                    for text in texts[1:]:  # Skip the first one as it's the combined text
                        # Google Vision doesn't provide confidence directly,
                        # we'll estimate based on bounding box quality
                        confidences.append(0.85)  # Placeholder confidence
                    confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                return OCRResult(
                    provider="google_vision",
                    success=True,
                    text=detected_text,
                    confidence=confidence,
                    raw_response={
                        'full_text_annotation': response.full_text_annotation,
                        'text_annotations': [
                            {
                                'description': text.description,
                                'bounding_poly': text.bounding_poly
                            } for text in texts
                        ]
                    }
                )
            else:
                return OCRResult(
                    provider="google_vision",
                    success=False,
                    text="",
                    error="No text detected in image"
                )
                
        except Exception as e:
            logger.error(f"Google Vision OCR error: {str(e)}")
            return OCRResult(
                provider="google_vision",
                success=False,
                text="",
                error=str(e)
            )


class GeminiMathSolver:
    """Google Gemini AI integration for solving math problems"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Alternative OpenAI-compatible client for Gemini
        self.openai_client = OpenAI(
            api_key=self.api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/"
        )
    
    def _create_math_prompt(self, math_content: str, latex_content: Optional[str] = None) -> str:
        """Create a comprehensive prompt for math problem solving"""
        prompt = f"""
You are an expert mathematics tutor for the Examify exam preparation platform. 
Analyze and solve the following mathematical problem with comprehensive explanations 
suitable for students preparing for exams.

EXTRACTED MATH CONTENT:
{math_content}
"""
        
        if latex_content:
            prompt += f"""
LATEX REPRESENTATION:
{latex_content}
"""
        
        prompt += """
Please provide a complete solution with the following structure:

1. PROBLEM ANALYSIS:
   - Identify the type of mathematical problem
   - Determine the difficulty level (elementary/middle_school/high_school/college/advanced)
   - List the key concepts involved

2. STEP-BY-STEP SOLUTION:
   - Break down the solution into clear, logical steps
   - Show all work and calculations
   - Explain the reasoning behind each step

3. FINAL ANSWER:
   - Provide the final answer clearly marked
   - Include units if applicable

4. VERIFICATION:
   - Show how to verify the answer
   - Explain alternative solution methods if applicable

5. EDUCATIONAL INSIGHTS:
   - Explain key concepts and formulas used
   - Provide study tips for similar problems
   - Suggest related topics to review

6. EXAM PREPARATION TIPS:
   - Common mistakes to avoid
   - Time-saving techniques
   - Similar problem variations

Format your response as a valid JSON object with the following structure:
{
    "problem_type": "string",
    "difficulty": "elementary|middle_school|high_school|college|advanced",
    "solution_steps": ["step1", "step2", ...],
    "final_answer": "string",
    "explanation": "detailed explanation",
    "verification": "verification method and alternative approaches",
    "study_tips": ["tip1", "tip2", ...],
    "related_concepts": ["concept1", "concept2", ...],
    "exam_tips": ["tip1", "tip2", ...],
    "confidence": 0.95
}
"""
        return prompt
    
    async def solve_math_problem(self, math_content: str, latex_content: Optional[str] = None) -> Dict[str, Any]:
        """Solve math problem using Gemini AI"""
        try:
            prompt = self._create_math_prompt(math_content, latex_content)
            
            # Generate response using Gemini
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,  # Lower temperature for more consistent mathematical solutions
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=4096,
                )
            )
            
            # Parse the response
            response_text = response.text
            
            # Try to extract JSON from the response
            try:
                # Look for JSON block in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    result = json.loads(json_str)
                    return result
                else:
                    # If no JSON found, create structured response
                    return self._parse_unstructured_response(response_text)
                    
            except json.JSONDecodeError:
                return self._parse_unstructured_response(response_text)
                
        except Exception as e:
            logger.error(f"Gemini math solving error: {str(e)}")
            return {
                "problem_type": "unknown",
                "difficulty": "unknown", 
                "solution_steps": [f"Error occurred: {str(e)}"],
                "final_answer": "Unable to solve due to error",
                "explanation": f"An error occurred while processing: {str(e)}",
                "verification": "Unable to verify due to error",
                "study_tips": ["Please try again with a clearer image"],
                "related_concepts": [],
                "exam_tips": [],
                "confidence": 0.0
            }
    
    def _parse_unstructured_response(self, response_text: str) -> Dict[str, Any]:
        """Parse unstructured response and create JSON structure"""
        # This is a fallback method for when Gemini doesn't return proper JSON
        return {
            "problem_type": "general",
            "difficulty": "unknown",
            "solution_steps": [response_text],
            "final_answer": "See solution steps",
            "explanation": response_text,
            "verification": "Please verify the solution manually",
            "study_tips": ["Review the complete solution provided"],
            "related_concepts": [],
            "exam_tips": ["Practice similar problems"],
            "confidence": 0.7
        }


class MathProblemSolver:
    """Main class for solving math problems from images"""
    
    def __init__(self, preferred_ocr: OCRProvider = OCRProvider.MATHPIX):
        self.preferred_ocr = preferred_ocr
        self.mathpix_ocr = MathpixOCR()
        self.google_vision_ocr = GoogleVisionOCR()
        self.gemini_solver = GeminiMathSolver()
        
        logger.info(f"MathProblemSolver initialized with preferred OCR: {preferred_ocr.value}")
        logger.info(f"Mathpix available: {self.mathpix_ocr.is_available()}")
        logger.info(f"Google Vision available: {self.google_vision_ocr.is_available()}")
    
    def _load_image(self, image_input: Union[str, bytes, io.BytesIO]) -> bytes:
        """Load image from various input types"""
        if isinstance(image_input, str):
            # File path
            with open(image_input, 'rb') as f:
                return f.read()
        elif isinstance(image_input, bytes):
            # Raw bytes
            return image_input
        elif isinstance(image_input, io.BytesIO):
            # BytesIO object
            return image_input.getvalue()
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")
    
    async def _perform_ocr(self, image_data: bytes) -> Tuple[OCRResult, Optional[OCRResult]]:
        """Perform OCR using preferred provider with fallback"""
        primary_result = None
        fallback_result = None
        
        if self.preferred_ocr == OCRProvider.MATHPIX and self.mathpix_ocr.is_available():
            primary_result = await self.mathpix_ocr.extract_math(image_data)
            if not primary_result.success and self.google_vision_ocr.is_available():
                fallback_result = await self.google_vision_ocr.extract_math(image_data)
        
        elif self.preferred_ocr == OCRProvider.GOOGLE_VISION and self.google_vision_ocr.is_available():
            primary_result = await self.google_vision_ocr.extract_math(image_data)
            if not primary_result.success and self.mathpix_ocr.is_available():
                fallback_result = await self.mathpix_ocr.extract_math(image_data)
        
        elif self.preferred_ocr == OCRProvider.BOTH:
            # Run both OCR providers
            if self.mathpix_ocr.is_available():
                primary_result = await self.mathpix_ocr.extract_math(image_data)
            if self.google_vision_ocr.is_available():
                fallback_result = await self.google_vision_ocr.extract_math(image_data)
        
        else:
            # Fallback to any available provider
            if self.mathpix_ocr.is_available():
                primary_result = await self.mathpix_ocr.extract_math(image_data)
            elif self.google_vision_ocr.is_available():
                primary_result = await self.google_vision_ocr.extract_math(image_data)
        
        return primary_result, fallback_result
    
    def _select_best_ocr_result(self, primary: Optional[OCRResult], fallback: Optional[OCRResult]) -> OCRResult:
        """Select the best OCR result based on success and confidence"""
        if not primary and not fallback:
            return OCRResult(
                provider="none",
                success=False,
                text="",
                error="No OCR providers available"
            )
        
        if primary and primary.success:
            if fallback and fallback.success:
                # Compare confidence scores if both succeeded
                primary_conf = primary.confidence or 0.0
                fallback_conf = fallback.confidence or 0.0
                return primary if primary_conf >= fallback_conf else fallback
            return primary
        
        if fallback and fallback.success:
            return fallback
        
        # Return primary even if failed (for error reporting)
        return primary or fallback
    
    async def solve_from_image(self, image_input: Union[str, bytes, io.BytesIO]) -> MathSolutionResult:
        """
        Main method to solve math problems from images
        
        Args:
            image_input: Image file path, bytes, or BytesIO object
            
        Returns:
            MathSolutionResult: Complete solution with explanations
        """
        import time
        start_time = time.time()
        
        try:
            # Load image data
            image_data = self._load_image(image_input)
            logger.info(f"Image loaded, size: {len(image_data)} bytes")
            
            # Perform OCR
            primary_result, fallback_result = await self._perform_ocr(image_data)
            best_ocr_result = self._select_best_ocr_result(primary_result, fallback_result)
            
            if not best_ocr_result.success:
                raise Exception(f"OCR failed: {best_ocr_result.error}")
            
            logger.info(f"OCR successful using {best_ocr_result.provider}")
            logger.info(f"Extracted text: {best_ocr_result.text[:100]}...")
            
            # Solve using Gemini AI
            solution_data = await self.gemini_solver.solve_math_problem(
                best_ocr_result.text,
                best_ocr_result.latex
            )
            
            # Map difficulty string to enum
            difficulty_map = {
                'elementary': MathDifficulty.ELEMENTARY,
                'middle_school': MathDifficulty.MIDDLE_SCHOOL,
                'high_school': MathDifficulty.HIGH_SCHOOL,
                'college': MathDifficulty.COLLEGE,
                'advanced': MathDifficulty.ADVANCED
            }
            
            difficulty = difficulty_map.get(
                solution_data.get('difficulty', 'unknown'),
                MathDifficulty.HIGH_SCHOOL
            )
            
            processing_time = time.time() - start_time
            
            return MathSolutionResult(
                extracted_text=best_ocr_result.text,
                extracted_latex=best_ocr_result.latex,
                problem_type=solution_data.get('problem_type', 'unknown'),
                difficulty=difficulty,
                solution_steps=solution_data.get('solution_steps', []),
                final_answer=solution_data.get('final_answer', ''),
                explanation=solution_data.get('explanation', ''),
                verification=solution_data.get('verification', ''),
                study_tips=solution_data.get('study_tips', []) + solution_data.get('exam_tips', []),
                related_concepts=solution_data.get('related_concepts', []),
                ocr_provider_used=best_ocr_result.provider,
                confidence_score=solution_data.get('confidence', best_ocr_result.confidence or 0.0),
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Math problem solving failed: {str(e)}")
            
            return MathSolutionResult(
                extracted_text="",
                extracted_latex=None,
                problem_type="error",
                difficulty=MathDifficulty.HIGH_SCHOOL,
                solution_steps=[f"Error occurred: {str(e)}"],
                final_answer="Unable to solve",
                explanation=f"An error occurred while processing the image: {str(e)}",
                verification="Unable to verify",
                study_tips=["Please try with a clearer image", "Ensure the image contains mathematical content"],
                related_concepts=[],
                ocr_provider_used="error",
                confidence_score=0.0,
                processing_time=processing_time
            )


# Convenience functions for easy usage

async def solve_math_from_image(
    image_input: Union[str, bytes, io.BytesIO],
    preferred_ocr: OCRProvider = OCRProvider.MATHPIX
) -> MathSolutionResult:
    """
    Convenience function to solve math problems from images
    
    Args:
        image_input: Image file path, bytes, or BytesIO object
        preferred_ocr: Preferred OCR provider (default: Mathpix)
        
    Returns:
        MathSolutionResult: Complete solution with explanations
    """
    solver = MathProblemSolver(preferred_ocr=preferred_ocr)
    return await solver.solve_from_image(image_input)


def solve_math_from_image_sync(
    image_input: Union[str, bytes, io.BytesIO],
    preferred_ocr: OCRProvider = OCRProvider.MATHPIX
) -> MathSolutionResult:
    """
    Synchronous wrapper for solve_math_from_image
    
    Args:
        image_input: Image file path, bytes, or BytesIO object
        preferred_ocr: Preferred OCR provider (default: Mathpix)
        
    Returns:
        MathSolutionResult: Complete solution with explanations
    """
    return asyncio.run(solve_math_from_image(image_input, preferred_ocr))


# Example usage and testing
if __name__ == "__main__":
    async def test_math_solver():
        """Test the math solver with a sample image"""
        
        # Example usage
        print("Testing Math Problem Solver...")
        
        # Test with different OCR providers
        for provider in [OCRProvider.MATHPIX, OCRProvider.GOOGLE_VISION, OCRProvider.BOTH]:
            print(f"\n=== Testing with {provider.value} ===")
            
            solver = MathProblemSolver(preferred_ocr=provider)
            
            # Test with a sample math problem (you would provide an actual image file)
            # result = await solver.solve_from_image("path/to/math_image.jpg")
            
            # For demonstration, we'll create a mock result
            print(f"OCR Provider: {provider.value}")
            print(f"Mathpix Available: {solver.mathpix_ocr.is_available()}")
            print(f"Google Vision Available: {solver.google_vision_ocr.is_available()}")
    
    # Run the test
    asyncio.run(test_math_solver())
