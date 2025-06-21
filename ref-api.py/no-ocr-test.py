# Text-based problem solving (no OCR needed)
from AI_Services.maths_solution import GeminiMathSolver
import asyncio

async def solve_problem():
    solver = GeminiMathSolver()
    result = await solver.solve_math_problem("Solve: 2x + 5 = 15")
    print(f"Answer: {result['final_answer']}")
    print(f"Steps: {result['solution_steps']}")

asyncio.run(solve_problem())