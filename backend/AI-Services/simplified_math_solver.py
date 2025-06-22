"""
Simplified Math Problem Solver Module for Examify AI-powered Exam Preparation App

This module uses Google Vision API for basic OCR and Google Gemini's vision capabilities
to directly analyze mathematical content from images and provide comprehensive solutions.

Features:
- Google Vision API for basic text detection
- Gemini Vision for direct image analysis and math problem solving
- Educational focus with study tips and explanations
- Robust error handling and fallback mechanisms
- Async/sync support for web applications

Author: Examify AI Team
Version: 2.0.0 (Simplified)
"""

import os
import io
import base64
import logging
import asyncio
from typing import Union, Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import json
import time

# Core dependencies
import google.generativeai as genai
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MathDifficulty(Enum):
    """Math problem difficulty levels"""
    ELEMENTARY = "elementary"
    MIDDLE_SCHOOL = "middle_school"
    HIGH_SCHOOL = "high_school"
    COLLEGE = "college"
    ADVANCED = "advanced"


@dataclass
class MathSolutionResult:
    """Complete math solution result"""
    extracted_text: str
    problem_type: str
    difficulty: MathDifficulty
    solution_steps: List[str]
    final_answer: str
    explanation: str
    verification: str
    study_tips: List[str]
    related_concepts: List[str]
    confidence_score: float
    processing_time: float
    method_used: str  # "gemini_vision" or "vision_ocr_gemini"


class GoogleVisionOCR:
    """Google Cloud Vision OCR for basic text extraction"""
    
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
    
    async def extract_text(self, image_data: bytes) -> Dict[str, Any]:
        """Extract text using Google Cloud Vision OCR"""
        if not self.is_available():
            return {
                "success": False,
                "text": "",
                "error": "Google Vision client not initialized"
            }
        
        try:
            image = vision.Image(content=image_data)
            
            # Perform text detection
            response = self.client.text_detection(image=image)
            
            if response.error.message:
                return {
                    "success": False,
                    "text": "",
                    "error": response.error.message
                }
            
            # Extract text from response
            texts = response.text_annotations
            if texts:
                detected_text = texts[0].description
                
                return {
                    "success": True,
                    "text": detected_text,
                    "confidence": 0.85  # Placeholder confidence for Google Vision
                }
            else:
                return {
                    "success": False,
                    "text": "",
                    "error": "No text detected in image"
                }
                
        except Exception as e:
            logger.error(f"Google Vision OCR error: {str(e)}")
            return {
                "success": False,
                "text": "",
                "error": str(e)
            }


class GeminiVisionSolver:
    """Google Gemini with Vision capabilities for direct image analysis"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize vision model
        self.vision_model = genai.GenerativeModel('gemini-1.5-pro')
        
    def _create_vision_prompt(self) -> str:
        """Create a comprehensive prompt for direct image analysis"""
        return """
You are an expert mathematics tutor for the Examify exam preparation platform. 
Analyze this image containing a mathematical problem and provide a comprehensive solution.

Please examine the image carefully and:

1. IDENTIFY the mathematical problem shown in the image
2. EXTRACT any mathematical expressions, equations, or diagrams
3. DETERMINE the type and difficulty level of the problem
4. PROVIDE a complete step-by-step solution
5. INCLUDE educational insights for exam preparation

Format your response as a valid JSON object with this exact structure:
{
    "extracted_problem": "The mathematical problem you can see in the image",
    "problem_type": "algebra|geometry|calculus|arithmetic|trigonometry|statistics|other",
    "difficulty": "elementary|middle_school|high_school|college|advanced", 
    "solution_steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
    "final_answer": "The final answer with units if applicable",
    "explanation": "Detailed explanation of the solution process",
    "verification": "How to verify this answer is correct",
    "study_tips": ["Tip 1 for similar problems", "Tip 2 for exam preparation"],
    "related_concepts": ["Related concept 1", "Related concept 2"],
    "confidence": 0.95
}

Focus on:
- Clear step-by-step explanations suitable for students
- Educational value for exam preparation
- Common mistakes to avoid
- Alternative solution methods when applicable
- Practical study tips for similar problems

If the image doesn't contain a clear mathematical problem, set "extracted_problem" to "No clear mathematical problem detected" and provide guidance on what makes a good math problem image.
"""
    
    async def solve_from_image(self, image_data: bytes) -> Dict[str, Any]:
        """Solve math problem directly from image using Gemini Vision"""
        try:
            # Convert image data to PIL Image for Gemini
            image = Image.open(io.BytesIO(image_data))
            
            # Create the prompt
            prompt = self._create_vision_prompt()
            
            # Generate response using Gemini Vision
            response = self.vision_model.generate_content(
                [prompt, image],
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
                    result["method"] = "gemini_vision"
                    return result
                else:
                    # If no JSON found, create structured response
                    return self._parse_unstructured_response(response_text)
                    
            except json.JSONDecodeError:
                return self._parse_unstructured_response(response_text)
                
        except Exception as e:
            logger.error(f"Gemini Vision solving error: {str(e)}")
            return {
                "extracted_problem": "Error occurred during processing",
                "problem_type": "error",
                "difficulty": "unknown", 
                "solution_steps": [f"Error occurred: {str(e)}"],
                "final_answer": "Unable to solve due to error",
                "explanation": f"An error occurred while processing the image: {str(e)}",
                "verification": "Unable to verify due to error",
                "study_tips": ["Please try again with a clearer image"],
                "related_concepts": [],
                "confidence": 0.0,
                "method": "gemini_vision"
            }
    
    def _parse_unstructured_response(self, response_text: str) -> Dict[str, Any]:
        """Parse unstructured response and create JSON structure"""
        return {
            "extracted_problem": "Problem extracted from image",
            "problem_type": "general",
            "difficulty": "unknown",
            "solution_steps": [response_text],
            "final_answer": "See solution steps above",
            "explanation": response_text,
            "verification": "Please verify the solution manually",
            "study_tips": ["Review the complete solution provided"],
            "related_concepts": [],
            "confidence": 0.7,
            "method": "gemini_vision"
        }


class MathProblemSolver:
    """Main class for solving math problems from images using Vision + Gemini"""
    
    def __init__(self, use_vision_ocr_fallback: bool = True):
        """
        Initialize the math problem solver
        
        Args:
            use_vision_ocr_fallback: If True, will fallback to Vision OCR + text analysis
                                   if direct Gemini Vision fails
        """
        self.use_vision_ocr_fallback = use_vision_ocr_fallback
        self.gemini_vision = GeminiVisionSolver()
        
        if use_vision_ocr_fallback:
            self.vision_ocr = GoogleVisionOCR()
            logger.info(f"Math solver initialized with Vision OCR fallback: {self.vision_ocr.is_available()}")
        else:
            self.vision_ocr = None
            logger.info("Math solver initialized with Gemini Vision only")
    
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
    
    async def _solve_with_vision_ocr_fallback(self, image_data: bytes) -> Dict[str, Any]:
        """Fallback method using Vision OCR + Gemini text analysis"""
        if not self.vision_ocr or not self.vision_ocr.is_available():
            raise Exception("Vision OCR fallback not available")
        
        # Extract text using Vision OCR
        ocr_result = await self.vision_ocr.extract_text(image_data)
        
        if not ocr_result["success"]:
            raise Exception(f"OCR failed: {ocr_result['error']}")
        
        # Use the text solver to analyze the extracted text
        text_solver = GeminiTextSolver()
        result = await text_solver.solve_text_problem(ocr_result["text"])
        result["method"] = "vision_ocr_gemini"
        result["extracted_problem"] = ocr_result["text"]
        
        return result
    
    async def solve_from_image(self, image_input: Union[str, bytes, io.BytesIO]) -> MathSolutionResult:
        """
        Main method to solve math problems from images
        
        Args:
            image_input: Image file path, bytes, or BytesIO object
            
        Returns:
            MathSolutionResult: Complete solution with explanations
        """
        start_time = time.time()
        
        try:
            # Load image data
            image_data = self._load_image(image_input)
            logger.info(f"Image loaded, size: {len(image_data)} bytes")
            
            # Primary method: Use Gemini Vision directly
            try:
                solution_data = await self.gemini_vision.solve_from_image(image_data)
                logger.info("Successfully solved using Gemini Vision")
            except Exception as vision_error:
                logger.warning(f"Gemini Vision failed: {vision_error}")
                
                # Fallback method: Use Vision OCR + Gemini text analysis
                if self.use_vision_ocr_fallback:
                    logger.info("Attempting Vision OCR fallback...")
                    solution_data = await self._solve_with_vision_ocr_fallback(image_data)
                    logger.info("Successfully solved using Vision OCR fallback")
                else:
                    raise vision_error
            
            # Map difficulty string to enum
            difficulty_map = {
                'elementary': MathDifficulty.ELEMENTARY,
                'middle_school': MathDifficulty.MIDDLE_SCHOOL,
                'high_school': MathDifficulty.HIGH_SCHOOL,
                'college': MathDifficulty.COLLEGE,
                'advanced': MathDifficulty.ADVANCED
            }
            
            difficulty = difficulty_map.get(
                solution_data.get('difficulty', 'high_school'),
                MathDifficulty.HIGH_SCHOOL
            )
            
            processing_time = time.time() - start_time
            
            return MathSolutionResult(
                extracted_text=solution_data.get('extracted_problem', ''),
                problem_type=solution_data.get('problem_type', 'unknown'),
                difficulty=difficulty,
                solution_steps=solution_data.get('solution_steps', []),
                final_answer=solution_data.get('final_answer', ''),
                explanation=solution_data.get('explanation', ''),
                verification=solution_data.get('verification', ''),
                study_tips=solution_data.get('study_tips', []),
                related_concepts=solution_data.get('related_concepts', []),
                confidence_score=solution_data.get('confidence', 0.0),
                processing_time=processing_time,
                method_used=solution_data.get('method', 'gemini_vision')
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Math problem solving failed: {str(e)}")
            
            return MathSolutionResult(
                extracted_text="",
                problem_type="error",
                difficulty=MathDifficulty.HIGH_SCHOOL,
                solution_steps=[f"Error occurred: {str(e)}"],
                final_answer="Unable to solve",
                explanation=f"An error occurred while processing the image: {str(e)}",
                verification="Unable to verify",
                study_tips=["Please try with a clearer image", "Ensure the image contains mathematical content"],
                related_concepts=[],
                confidence_score=0.0,
                processing_time=processing_time,
                method_used="error"
            )


# Convenience functions for easy usage

async def solve_math_from_image(
    image_input: Union[str, bytes, io.BytesIO],
    use_fallback: bool = True
) -> MathSolutionResult:
    """
    Convenience function to solve math problems from images
    
    Args:
        image_input: Image file path, bytes, or BytesIO object
        use_fallback: Whether to use Vision OCR fallback if Gemini Vision fails
        
    Returns:
        MathSolutionResult: Complete solution with explanations
    """
    solver = MathProblemSolver(use_vision_ocr_fallback=use_fallback)
    return await solver.solve_from_image(image_input)


def solve_math_from_image_sync(
    image_input: Union[str, bytes, io.BytesIO],
    use_fallback: bool = True
) -> MathSolutionResult:
    """
    Synchronous wrapper for solve_math_from_image
    
    Args:
        image_input: Image file path, bytes, or BytesIO object
        use_fallback: Whether to use Vision OCR fallback if Gemini Vision fails
        
    Returns:
        MathSolutionResult: Complete solution with explanations
    """
    return asyncio.run(solve_math_from_image(image_input, use_fallback))


# Text-only solver for cases where you already have the problem text
class GeminiTextSolver:
    """Gemini solver for text-based math problems"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    async def solve_text_problem(self, problem_text: str) -> Dict[str, Any]:
        """Solve a text-based math problem"""
        prompt = f"""
You are an expert mathematics tutor for the Examify exam preparation platform. 
Solve this mathematical problem with comprehensive explanations suitable for students preparing for exams.

PROBLEM: {problem_text}

Please provide a complete solution with the following structure as a JSON object:
{{
    "extracted_problem": "{problem_text}",
    "problem_type": "algebra|geometry|calculus|arithmetic|trigonometry|statistics|other",
    "difficulty": "elementary|middle_school|high_school|college|advanced",
    "solution_steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
    "final_answer": "The final answer with units if applicable",
    "explanation": "Detailed explanation of the solution process",
    "verification": "How to verify this answer is correct",
    "study_tips": ["Tip 1 for similar problems", "Tip 2 for exam preparation"],
    "related_concepts": ["Related concept 1", "Related concept 2"],
    "confidence": 0.95
}}
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=4096,
                )
            )
            
            response_text = response.text
            
            # Extract JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return {
                    "extracted_problem": problem_text,
                    "problem_type": "general",
                    "difficulty": "unknown",
                    "solution_steps": [response_text],
                    "final_answer": "See solution above",
                    "explanation": response_text,
                    "verification": "Please verify manually",
                    "study_tips": ["Review the solution provided"],
                    "related_concepts": [],
                    "confidence": 0.7
                }
                
        except Exception as e:
            logger.error(f"Text problem solving error: {e}")
            return {
                "extracted_problem": problem_text,
                "problem_type": "error",
                "difficulty": "unknown",
                "solution_steps": [f"Error: {str(e)}"],
                "final_answer": "Unable to solve",
                "explanation": f"Error occurred: {str(e)}",
                "verification": "Unable to verify",
                "study_tips": ["Please try again"],
                "related_concepts": [],
                "confidence": 0.0
            }


async def solve_text_problem(problem_text: str) -> Dict[str, Any]:
    """Convenience function to solve text-based math problems"""
    solver = GeminiTextSolver()
    return await solver.solve_text_problem(problem_text)


# Example usage and testing
if __name__ == "__main__":
    async def test_simplified_solver():
        """Test the simplified math solver"""
        
        print("Testing Simplified Math Problem Solver...")
        print("Using Google Vision + Gemini Vision")
        
        # Test text problem first
        print("\n=== Testing Text Problem ===")
        text_result = await solve_text_problem("Solve: 2x + 5 = 15")
        print(f"Text Problem: {text_result.get('final_answer')}")
        
        # Test with image (would need actual image)
        print("\n=== Image Solver Ready ===")
        solver = MathProblemSolver(use_vision_ocr_fallback=True)
        print(f"Gemini Vision available: ✓")
        print(f"Vision OCR fallback available: {solver.vision_ocr.is_available() if solver.vision_ocr else False}")
        
        print("\nReady to process math images!")
        print("Usage: result = await solve_math_from_image('path/to/math_image.jpg')")
    
    # Run the test
    asyncio.run(test_simplified_solver())
