"""
Test and Demo for Simplified Math Solver

This script demonstrates the simplified math solver that uses only Google Vision
and Gemini for solving math problems from images.
"""

import asyncio
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

# Add the AI-Services directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'AI-Services'))

# Import the simplified solver
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("simplified_math_solver", 
                                                  os.path.join(os.path.dirname(__file__), 'AI-Services', 'simplified_math_solver.py'))
    simplified_solver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(simplified_solver)
    
    # Import the needed functions
    solve_math_from_image = simplified_solver.solve_math_from_image
    solve_math_from_image_sync = simplified_solver.solve_math_from_image_sync
    solve_text_problem = simplified_solver.solve_text_problem
    MathProblemSolver = simplified_solver.MathProblemSolver
    
    print("✅ Simplified math solver imported successfully")
except ImportError as e:
    print(f"❌ Error importing simplified solver: {e}")
    sys.exit(1)

from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='AI-Services/.env')


def create_sample_math_image(math_text: str, filename: str = None) -> bytes:
    """Create a sample image with mathematical text"""
    
    # Create image
    width, height = 600, 150
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to get a good font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Times.ttc", 32)
    except:
        font = ImageFont.load_default()
    
    # Center the text
    bbox = draw.textbbox((0, 0), math_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), math_text, fill='black', font=font)
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    
    # Optionally save to file
    if filename:
        image.save(filename)
        print(f"✅ Sample image saved as: {filename}")
    
    return img_bytes.getvalue()


async def test_text_solving():
    """Test text-based problem solving"""
    print("=== Testing Text-Based Math Solving ===\n")
    
    problems = [
        "Solve for x: 2x + 5 = 15",
        "Find the derivative of f(x) = x² + 3x",
        "What is 25% of 80?",
        "Factor: x² - 9",
        "Solve: 3x - 7 = 2x + 8"
    ]
    
    for i, problem in enumerate(problems, 1):
        print(f"Problem {i}: {problem}")
        try:
            result = await solve_text_problem(problem)
            print(f"✅ Answer: {result.get('final_answer', 'No answer')}")
            print(f"✅ Method: Text analysis")
            print(f"✅ Confidence: {result.get('confidence', 0):.1%}")
            print()
        except Exception as e:
            print(f"❌ Error: {e}")
            print()


async def test_image_solving():
    """Test image-based problem solving"""
    print("=== Testing Image-Based Math Solving ===\n")
    
    # Create sample images with math problems
    test_cases = [
        ("Linear Equation", "3x - 12 = 9"),
        ("Quadratic", "x² - 4x + 4 = 0"),
        ("Fraction", "3/4 + 2/3 = ?"),
        ("Percentage", "15% of 200 = ?")
    ]
    
    for title, problem in test_cases:
        print(f"Testing: {title} - {problem}")
        
        # Create sample image
        image_data = create_sample_math_image(problem)
        
        try:
            # Solve using the simplified solver
            result = await solve_math_from_image(image_data, use_fallback=True)
            
            print(f"✅ Extracted: {result.extracted_text[:50]}...")
            print(f"✅ Problem Type: {result.problem_type}")
            print(f"✅ Difficulty: {result.difficulty.value}")
            print(f"✅ Answer: {result.final_answer}")
            print(f"✅ Method: {result.method_used}")
            print(f"✅ Confidence: {result.confidence_score:.1%}")
            print(f"✅ Processing Time: {result.processing_time:.2f}s")
            
            # Show first solution step
            if result.solution_steps:
                print(f"💡 First Step: {result.solution_steps[0][:80]}...")
            
            print()
            
        except Exception as e:
            print(f"❌ Error solving {title}: {e}")
            print()


def test_sync_wrapper():
    """Test synchronous wrapper"""
    print("=== Testing Synchronous Wrapper ===\n")
    
    problem = "Solve: 5x + 10 = 25"
    print(f"Problem: {problem}")
    
    # Create sample image
    image_data = create_sample_math_image(problem, "sync_test.png")
    
    try:
        # Test synchronous solving
        result = solve_math_from_image_sync(image_data)
        
        print(f"✅ Sync Solution: {result.final_answer}")
        print(f"✅ Method: {result.method_used}")
        print(f"✅ Processing Time: {result.processing_time:.2f}s")
        
        # Clean up
        if os.path.exists("sync_test.png"):
            os.remove("sync_test.png")
            print("✅ Cleaned up test file")
        
    except Exception as e:
        print(f"❌ Sync test error: {e}")


def test_configuration():
    """Test API configuration"""
    print("=== Testing Configuration ===\n")
    
    # Check required API keys
    gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    
    if gemini_key:
        print(f"✅ Gemini API Key: Found ({gemini_key[:20]}...)")
    else:
        print("❌ Gemini API Key: Missing")
        print("   Add GEMINI_API_KEY or GOOGLE_API_KEY to .env file")
    
    # Test solver initialization
    try:
        solver = MathProblemSolver(use_vision_ocr_fallback=True)
        print("✅ Solver initialized successfully")
        
        # Check Vision OCR availability
        if solver.vision_ocr and solver.vision_ocr.is_available():
            print("✅ Google Vision OCR: Available")
        else:
            print("⚠️  Google Vision OCR: Not available (will use Gemini Vision only)")
        
    except Exception as e:
        print(f"❌ Solver initialization failed: {e}")


async def interactive_demo():
    """Interactive demo for testing"""
    print("=== Interactive Math Solver Demo ===\n")
    print("Choose an option:")
    print("1. Solve a text problem")
    print("2. Create and solve an image problem")
    print("3. Test with your own image file")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            problem = input("Enter a math problem: ").strip()
            if problem:
                print("Solving...")
                result = await solve_text_problem(problem)
                print(f"\n✅ Answer: {result.get('final_answer')}")
                print(f"✅ Explanation: {result.get('explanation', 'No explanation')[:100]}...")
        
        elif choice == "2":
            problem = input("Enter a math problem to create as image: ").strip()
            if problem:
                print("Creating image and solving...")
                image_data = create_sample_math_image(problem, f"demo_{problem[:10]}.png")
                result = await solve_math_from_image(image_data)
                print(f"\n✅ Answer: {result.final_answer}")
                print(f"✅ Method: {result.method_used}")
        
        elif choice == "3":
            file_path = input("Enter path to image file: ").strip()
            if os.path.exists(file_path):
                print("Solving from file...")
                result = await solve_math_from_image(file_path)
                print(f"\n✅ Answer: {result.final_answer}")
                print(f"✅ Extracted: {result.extracted_text[:50]}...")
            else:
                print("❌ File not found")
        
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nDemo interrupted")
    except Exception as e:
        print(f"❌ Demo error: {e}")


async def run_all_tests():
    """Run comprehensive tests"""
    print("Simplified Math Solver - Comprehensive Tests")
    print("=" * 50)
    
    # Test configuration first
    test_configuration()
    print()
    
    # Test text solving
    await test_text_solving()
    
    # Test image solving
    await test_image_solving()
    
    # Test sync wrapper
    test_sync_wrapper()
    
    print("=" * 50)
    print("✅ All tests completed!")


def main():
    """Main test runner"""
    print("Simplified Math Solver - Test Suite")
    print("Uses Google Vision + Gemini Vision only")
    print("No Mathpix or PDF processing required")
    print()
    
    # Check environment
    env_file = os.path.join(os.path.dirname(__file__), 'AI-Services', '.env')
    if not os.path.exists(env_file):
        print("⚠️  Warning: .env file not found in AI-Services/")
        print("   Please add your Gemini API key for full functionality\n")
    
    print("Choose test mode:")
    print("1. Run all tests")
    print("2. Test configuration only")
    print("3. Interactive demo")
    print("4. Quick text problem test")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            asyncio.run(run_all_tests())
        elif choice == "2":
            test_configuration()
        elif choice == "3":
            asyncio.run(interactive_demo())
        elif choice == "4":
            asyncio.run(test_text_solving())
        else:
            print("Invalid choice. Running all tests...")
            asyncio.run(run_all_tests())
            
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        print("Make sure your Gemini API key is configured in .env")


if __name__ == "__main__":
    main()
