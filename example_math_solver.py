"""
Example Usage of Math Problem Solver

This script demonstrates how to use the Math Problem Solver module
for the Examify AI-powered exam preparation app.
"""

import asyncio
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

# Add the AI-Services directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'AI-Services'))

# Import with proper module loading
import importlib.util
spec = importlib.util.spec_from_file_location("maths_solution", 
                                              os.path.join(os.path.dirname(__file__), 'AI-Services', 'maths-solution.py'))
maths_solution = importlib.util.module_from_spec(spec)
spec.loader.exec_module(maths_solution)

# Import the needed functions
solve_math_from_image = maths_solution.solve_math_from_image
solve_math_from_image_sync = maths_solution.solve_math_from_image_sync
OCRProvider = maths_solution.OCRProvider


def create_sample_image(math_text: str, filename: str = None) -> bytes:
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
        print(f"Sample image saved as: {filename}")
    
    return img_bytes.getvalue()


async def example_async_usage():
    """Demonstrate async usage of the math solver"""
    
    print("=== Async Math Problem Solving Examples ===\n")
    
    # Example problems of different difficulty levels
    examples = [
        ("Basic Addition", "15 + 27 = ?"),
        ("Linear Equation", "3x - 7 = 14"),
        ("Quadratic Equation", "x² - 5x + 6 = 0"),
        ("Calculus", "d/dx (x³ + 2x²)"),
        ("Integration", "∫(3x² + 2x + 1)dx")
    ]
    
    for title, problem in examples:
        print(f"\n--- {title}: {problem} ---")
        
        # Create sample image
        image_data = create_sample_image(problem)
        
        try:
            # Solve the problem
            result = await solve_math_from_image(
                image_data, 
                preferred_ocr=OCRProvider.GOOGLE_VISION  # Use Google Vision as it's more likely to be available
            )
            
            # Display results
            print(f"✓ Problem extracted: {result.extracted_text[:50]}...")
            print(f"✓ Problem type: {result.problem_type}")
            print(f"✓ Difficulty level: {result.difficulty.value}")
            print(f"✓ Final answer: {result.final_answer}")
            print(f"✓ OCR provider: {result.ocr_provider_used}")
            print(f"✓ Confidence: {result.confidence_score:.1%}")
            print(f"✓ Processing time: {result.processing_time:.2f}s")
            
            # Show solution steps (first 3)
            if result.solution_steps:
                print("✓ Solution steps:")
                for i, step in enumerate(result.solution_steps[:3], 1):
                    print(f"   {i}. {step[:80]}...")
                if len(result.solution_steps) > 3:
                    print(f"   ... and {len(result.solution_steps) - 3} more steps")
            
            # Show study tips (first 2)
            if result.study_tips:
                print("✓ Study tips:")
                for tip in result.study_tips[:2]:
                    print(f"   • {tip[:60]}...")
                    
        except Exception as e:
            print(f"✗ Error solving problem: {e}")


def example_sync_usage():
    """Demonstrate synchronous usage"""
    
    print("\n=== Synchronous Math Problem Solving Example ===\n")
    
    problem = "2x + 8 = 20"
    print(f"Solving: {problem}")
    
    # Create sample image
    image_data = create_sample_image(problem, "sample_math_problem.png")
    
    try:
        # Solve synchronously
        result = solve_math_from_image_sync(image_data)
        
        print(f"\n✓ Solution found!")
        print(f"  Answer: {result.final_answer}")
        print(f"  Explanation: {result.explanation[:100]}...")
        print(f"  Processing time: {result.processing_time:.2f}s")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def example_file_usage():
    """Demonstrate usage with actual image files"""
    
    print("\n=== File-based Math Problem Solving ===\n")
    
    # Create a sample file
    problem = "Find x: 4x - 12 = 8"
    filename = "math_problem_example.png"
    create_sample_image(problem, filename)
    
    print(f"Created sample file: {filename}")
    print(f"Problem: {problem}")
    
    async def solve_from_file():
        try:
            # Solve from file path
            result = await solve_math_from_image(filename)
            
            print(f"\n✓ Solved from file!")
            print(f"  Extracted: {result.extracted_text}")
            print(f"  Answer: {result.final_answer}")
            print(f"  Study tips: {len(result.study_tips)} tips provided")
            
            # Clean up
            if os.path.exists(filename):
                os.remove(filename)
                print(f"  Cleaned up: {filename}")
                
        except Exception as e:
            print(f"✗ Error solving from file: {e}")
    
    # Run the file example
    asyncio.run(solve_from_file())


def example_error_handling():
    """Demonstrate error handling"""
    
    print("\n=== Error Handling Examples ===\n")
    
    async def test_errors():
        # Test with invalid data
        print("Testing with invalid image data...")
        try:
            result = await solve_math_from_image(b"invalid_image_data")
            print(f"Result: {result.problem_type} - {result.explanation[:50]}...")
        except Exception as e:
            print(f"Exception handled: {e}")
        
        # Test with empty data
        print("\nTesting with empty data...")
        try:
            result = await solve_math_from_image(b"")
            print(f"Result: {result.problem_type} - {result.explanation[:50]}...")
        except Exception as e:
            print(f"Exception handled: {e}")
    
    asyncio.run(test_errors())


def main():
    """Main example runner"""
    
    print("Math Problem Solver - Example Usage")
    print("===================================")
    print("This example demonstrates the Examify Math Problem Solver")
    print("Make sure you have configured API keys in AI-Services/.env\n")
    
    # Check environment
    env_file = os.path.join(os.path.dirname(__file__), 'AI-Services', '.env')
    if not os.path.exists(env_file):
        print("⚠️  Warning: .env file not found in AI-Services/")
        print("   Please configure your API keys for full functionality\n")
    
    try:
        # Run examples
        print("1. Running async examples...")
        asyncio.run(example_async_usage())
        
        print("\n2. Running sync example...")
        example_sync_usage()
        
        print("\n3. Running file-based example...")
        example_file_usage()
        
        print("\n4. Testing error handling...")
        example_error_handling()
        
        print("\n" + "="*50)
        print("✓ All examples completed successfully!")
        print("\nTo use in your own code:")
        print("  from AI-Services.maths-solution import solve_math_from_image")
        print("  result = await solve_math_from_image('path/to/image.jpg')")
        
    except Exception as e:
        print(f"\n✗ Example execution failed: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install -r requirements.txt")


if __name__ == "__main__":
    main()
