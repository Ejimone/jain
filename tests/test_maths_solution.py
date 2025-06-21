"""
Test suite for Math Problem Solver Module

This test file provides comprehensive testing for the math solution module,
including unit tests, integration tests, and example usage demonstrations.
"""

import os
import sys
import asyncio
import tempfile
import base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

# Add the AI-Services directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AI-Services'))

try:
    # Import with the correct module name (using hyphen, so we need to import as string)
    import importlib.util
    spec = importlib.util.spec_from_file_location("maths_solution", 
                                                  os.path.join(os.path.dirname(__file__), '..', 'AI-Services', 'maths-solution.py'))
    maths_solution = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(maths_solution)
    
    # Import the needed classes and functions
    MathProblemSolver = maths_solution.MathProblemSolver
    OCRProvider = maths_solution.OCRProvider
    MathDifficulty = maths_solution.MathDifficulty
    solve_math_from_image = maths_solution.solve_math_from_image
    solve_math_from_image_sync = maths_solution.solve_math_from_image_sync
    MathpixOCR = maths_solution.MathpixOCR
    GoogleVisionOCR = maths_solution.GoogleVisionOCR
    GeminiMathSolver = maths_solution.GeminiMathSolver
except ImportError as e:
    print(f"Error importing maths_solution module: {e}")
    print("Make sure the module is correctly named and located in AI-Services/")
    sys.exit(1)

from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='../AI-Services/.env')


def create_sample_math_image(text: str, output_path: str = None) -> bytes:
    """Create a sample image with mathematical text for testing"""
    
    # Create a white image
    width, height = 800, 200
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a better font, fallback to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Times.ttc", 36)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except:
            font = ImageFont.load_default()
    
    # Calculate text position (center)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw the text
    draw.text((x, y), text, fill='black', font=font)
    
    # Save to bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Optionally save to file
    if output_path:
        image.save(output_path)
        print(f"Sample image saved to: {output_path}")
    
    return img_bytes.getvalue()


async def test_ocr_providers():
    """Test individual OCR providers"""
    print("\n=== Testing OCR Providers ===")
    
    # Create sample math image
    sample_text = "2x + 5 = 15"
    image_data = create_sample_math_image(sample_text)
    
    # Test Mathpix OCR
    print("\n--- Testing Mathpix OCR ---")
    mathpix = MathpixOCR()
    print(f"Mathpix available: {mathpix.is_available()}")
    
    if mathpix.is_available():
        mathpix_result = await mathpix.extract_math(image_data)
        print(f"Success: {mathpix_result.success}")
        print(f"Text: {mathpix_result.text}")
        print(f"LaTeX: {mathpix_result.latex}")
        print(f"Confidence: {mathpix_result.confidence}")
        if not mathpix_result.success:
            print(f"Error: {mathpix_result.error}")
    
    # Test Google Vision OCR
    print("\n--- Testing Google Vision OCR ---")
    google_vision = GoogleVisionOCR()
    print(f"Google Vision available: {google_vision.is_available()}")
    
    if google_vision.is_available():
        vision_result = await google_vision.extract_math(image_data)
        print(f"Success: {vision_result.success}")
        print(f"Text: {vision_result.text}")
        print(f"Confidence: {vision_result.confidence}")
        if not vision_result.success:
            print(f"Error: {vision_result.error}")


async def test_gemini_solver():
    """Test Gemini math solver"""
    print("\n=== Testing Gemini Math Solver ===")
    
    try:
        solver = GeminiMathSolver()
        
        # Test with a simple math problem
        test_problem = "Solve the equation: 2x + 5 = 15"
        result = await solver.solve_math_problem(test_problem)
        
        print(f"Problem type: {result.get('problem_type')}")
        print(f"Difficulty: {result.get('difficulty')}")
        print(f"Solution steps: {result.get('solution_steps')}")
        print(f"Final answer: {result.get('final_answer')}")
        print(f"Confidence: {result.get('confidence')}")
        
    except Exception as e:
        print(f"Error testing Gemini solver: {e}")


async def test_full_math_solver():
    """Test the complete math problem solver"""
    print("\n=== Testing Complete Math Problem Solver ===")
    
    # Test problems with different difficulty levels
    test_problems = [
        ("2 + 3 = ?", "elementary_addition.png"),
        ("2x + 5 = 15", "linear_equation.png"),
        ("Find the derivative of f(x) = x²", "calculus_derivative.png"),
        ("∫(2x + 1)dx", "integration.png")
    ]
    
    for problem_text, filename in test_problems:
        print(f"\n--- Testing: {problem_text} ---")
        
        # Create sample image
        image_data = create_sample_math_image(problem_text)
        
        # Test with different OCR providers
        for provider in [OCRProvider.MATHPIX, OCRProvider.GOOGLE_VISION, OCRProvider.BOTH]:
            print(f"\nUsing OCR Provider: {provider.value}")
            
            try:
                result = await solve_math_from_image(image_data, preferred_ocr=provider)
                
                print(f"Extracted text: {result.extracted_text[:100]}...")
                print(f"Problem type: {result.problem_type}")
                print(f"Difficulty: {result.difficulty.value}")
                print(f"Final answer: {result.final_answer}")
                print(f"OCR provider used: {result.ocr_provider_used}")
                print(f"Confidence: {result.confidence_score:.2f}")
                print(f"Processing time: {result.processing_time:.2f}s")
                print(f"Number of solution steps: {len(result.solution_steps)}")
                print(f"Study tips: {len(result.study_tips)} tips provided")
                
                # Print first few solution steps
                if result.solution_steps:
                    print("Solution steps (first 2):")
                    for i, step in enumerate(result.solution_steps[:2]):
                        print(f"  {i+1}. {step[:100]}...")
                
            except Exception as e:
                print(f"Error with {provider.value}: {e}")


def test_synchronous_wrapper():
    """Test the synchronous wrapper function"""
    print("\n=== Testing Synchronous Wrapper ===")
    
    try:
        # Create a simple math problem image
        problem_text = "5 + 3 = ?"
        image_data = create_sample_math_image(problem_text)
        
        # Test synchronous function
        result = solve_math_from_image_sync(image_data, OCRProvider.GOOGLE_VISION)
        
        print(f"Sync result - Problem type: {result.problem_type}")
        print(f"Sync result - Final answer: {result.final_answer}")
        print(f"Sync result - Processing time: {result.processing_time:.2f}s")
        
    except Exception as e:
        print(f"Error in synchronous test: {e}")


async def test_error_handling():
    """Test error handling scenarios"""
    print("\n=== Testing Error Handling ===")
    
    # Test with invalid image data
    print("\n--- Testing with invalid image data ---")
    try:
        invalid_data = b"not an image"
        result = await solve_math_from_image(invalid_data)
        print(f"Result for invalid data: {result.problem_type}")
        print(f"Error handling worked: {result.explanation[:100]}...")
    except Exception as e:
        print(f"Exception (expected): {e}")
    
    # Test with empty image
    print("\n--- Testing with empty data ---")
    try:
        empty_data = b""
        result = await solve_math_from_image(empty_data)
        print(f"Result for empty data: {result.problem_type}")
        print(f"Error handling worked: {result.explanation[:100]}...")
    except Exception as e:
        print(f"Exception (expected): {e}")


def test_configuration():
    """Test configuration and environment setup"""
    print("\n=== Testing Configuration ===")
    
    required_vars = [
        'GEMINI_API_KEY',
        'GOOGLE_API_KEY',
    ]
    
    optional_vars = [
        'MATHPIX_APP_ID',
        'MATHPIX_APP_KEY',
        'GOOGLE_CLOUD_VISION_CREDENTIALS_PATH'
    ]
    
    print("Required environment variables:")
    for var in required_vars:
        value = os.getenv(var)
        status = "✓ Set" if value else "✗ Missing"
        print(f"  {var}: {status}")
        if value:
            print(f"    Value: {value[:20]}...")
    
    print("\nOptional environment variables:")
    for var in optional_vars:
        value = os.getenv(var)
        status = "✓ Set" if value else "✗ Not set"
        print(f"  {var}: {status}")
        if value and len(value) > 20:
            print(f"    Value: {value[:20]}...")


async def run_comprehensive_tests():
    """Run all tests"""
    print("Starting Comprehensive Math Problem Solver Tests")
    print("=" * 60)
    
    # Test configuration
    test_configuration()
    
    # Test individual components
    await test_ocr_providers()
    await test_gemini_solver()
    
    # Test full integration
    await test_full_math_solver()
    
    # Test synchronous wrapper
    test_synchronous_wrapper()
    
    # Test error handling
    await test_error_handling()
    
    print("\n" + "=" * 60)
    print("All tests completed!")


def demo_usage():
    """Demonstrate basic usage of the module"""
    print("\n=== Usage Demonstration ===")
    
    demo_code = '''
# Basic usage example
import asyncio
from maths_solution import solve_math_from_image, OCRProvider

async def solve_math_problem():
    # Solve from image file
    result = await solve_math_from_image(
        "path/to/math_image.jpg", 
        preferred_ocr=OCRProvider.MATHPIX
    )
    
    print(f"Problem: {result.extracted_text}")
    print(f"Solution: {result.final_answer}")
    print(f"Explanation: {result.explanation}")
    
    # Print solution steps
    for i, step in enumerate(result.solution_steps, 1):
        print(f"{i}. {step}")

# Run the example
asyncio.run(solve_math_problem())

# Synchronous usage
from maths_solution import solve_math_from_image_sync

result = solve_math_from_image_sync("path/to/math_image.jpg")
print(result.final_answer)
'''
    
    print("Example usage:")
    print(demo_code)


if __name__ == "__main__":
    print("Math Problem Solver Test Suite")
    print("This will test the OCR and AI integration functionality")
    print("Make sure you have configured the API keys in .env file")
    
    # Ask user what to run
    print("\nSelect test mode:")
    print("1. Run all tests")
    print("2. Test configuration only")
    print("3. Show usage examples")
    print("4. Test specific component")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            asyncio.run(run_comprehensive_tests())
        elif choice == "2":
            test_configuration()
        elif choice == "3":
            demo_usage()
        elif choice == "4":
            print("\nSpecific component tests:")
            print("a. OCR providers")
            print("b. Gemini solver")
            print("c. Error handling")
            
            sub_choice = input("Enter choice (a-c): ").strip().lower()
            
            if sub_choice == "a":
                asyncio.run(test_ocr_providers())
            elif sub_choice == "b":
                asyncio.run(test_gemini_solver())
            elif sub_choice == "c":
                asyncio.run(test_error_handling())
            else:
                print("Invalid choice")
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        print(f"\nTest execution error: {e}")
