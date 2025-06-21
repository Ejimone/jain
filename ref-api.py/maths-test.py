# Django/Flask endpoint example
from AI_Services.maths_solution import solve_math_from_image_sync

def solve_math_endpoint(request):
    image_file = request.FILES['math_image']
    result = solve_math_from_image_sync(image_file.read())
    
    return JsonResponse({
        'success': True,
        'problem': result.extracted_text,
        'answer': result.final_answer,
        'explanation': result.explanation,
        'steps': result.solution_steps,
        'study_tips': result.study_tips,
        'difficulty': result.difficulty.value,
        'confidence': result.confidence_score
    })