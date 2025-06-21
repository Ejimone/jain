"""
Simplified Math Text Solver - No OCR Required

This script demonstrates how to use just the Gemini AI portion of the math solver
for solving text-based math problems without requiring OCR setup.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the AI-Services directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'AI-Services'))

# Import with proper module loading
import importlib.util
spec = importlib.util.spec_from_file_location("maths_solution", 
                                              os.path.join(os.path.dirname(__file__), 'AI-Services', 'maths-solution.py'))
maths_solution = importlib.util.module_from_spec(spec)
spec.loader.exec_module(maths_solution)

# Import the Gemini solver directly
GeminiMathSolver = maths_solution.GeminiMathSolver

# Load environment variables
load_dotenv(dotenv_path='AI-Services/.env')


async def solve_text_problems():
    """Solve math problems from text (no OCR required)"""
    
    print("Math Text Solver - Demo")
    print("=====================")
    print("Solving math problems using only Gemini AI (no OCR)")
    print()
    
    # Test problems
    problems = [
        "Solve the equation: 2x + 5 = 15",
        "Find the derivative of f(x) = x³ + 2x²",
        "What is 15% of 240?",
        "Solve the quadratic equation: x² - 7x + 12 = 0",
        "Factor the expression: x² + 5x + 6"
    ]
    
    try:
        # Initialize Gemini solver
        solver = GeminiMathSolver()
        print("✅ Gemini AI solver initialized")
        print()
        
        for i, problem in enumerate(problems, 1):
            print(f"Problem {i}: {problem}")
            print("-" * 50)
            
            try:
                # Solve the problem
                result = await solver.solve_math_problem(problem)
                
                # Display results
                print(f"✅ Problem Type: {result.get('problem_type', 'Unknown')}")
                print(f"✅ Difficulty: {result.get('difficulty', 'Unknown')}")
                print(f"✅ Final Answer: {result.get('final_answer', 'No answer')}")
                print(f"✅ Confidence: {result.get('confidence', 0):.1%}")
                
                # Show solution steps
                steps = result.get('solution_steps', [])
                if steps:
                    print("✅ Solution Steps:")
                    for j, step in enumerate(steps[:3], 1):  # Show first 3 steps
                        print(f"   {j}. {step}")
                    if len(steps) > 3:
                        print(f"   ... and {len(steps) - 3} more steps")
                
                # Show study tips
                tips = result.get('study_tips', [])
                if tips:
                    print("💡 Study Tips:")
                    for tip in tips[:2]:  # Show first 2 tips
                        print(f"   • {tip}")
                
                print()
                
            except Exception as e:
                print(f"❌ Error solving problem: {e}")
                print()
        
        print("🎉 All problems processed successfully!")
        
    except Exception as e:
        print(f"❌ Failed to initialize Gemini solver: {e}")
        print("Make sure GEMINI_API_KEY is set in AI-Services/.env")


def solve_single_problem_sync(problem_text: str):
    """Solve a single problem synchronously"""
    
    async def solve():
        try:
            solver = GeminiMathSolver()
            result = await solver.solve_math_problem(problem_text)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    return asyncio.run(solve())


def interactive_solver():
    """Interactive math problem solver"""
    
    print("Interactive Math Solver")
    print("======================")
    print("Enter math problems and get instant solutions!")
    print("Type 'quit' to exit")
    print()
    
    while True:
        try:
            problem = input("Enter a math problem: ").strip()
            
            if problem.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not problem:
                continue
            
            print("Solving...")
            result = solve_single_problem_sync(problem)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"✅ Answer: {result.get('final_answer', 'No answer found')}")
                
                # Show first solution step
                steps = result.get('solution_steps', [])
                if steps:
                    print(f"💡 Solution: {steps[0]}")
            
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("Gemini Math Solver Demo")
    print("=" * 40)
    
    # Check if API key is available
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in environment")
        print("Please add your Gemini API key to AI-Services/.env")
        sys.exit(1)
    
    print(f"✅ Gemini API key found: {api_key[:20]}...")
    print()
    
    # Choose mode
    print("Choose mode:")
    print("1. Demo with sample problems")
    print("2. Interactive solver")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            print("\nRunning demo with sample problems...")
            asyncio.run(solve_text_problems())
        elif choice == "2":
            print("\nStarting interactive solver...")
            interactive_solver()
        else:
            print("Invalid choice. Running demo...")
            asyncio.run(solve_text_problems())
            
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("This might be due to API quota limits. Try again later.")
