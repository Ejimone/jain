# Simplified Math Problem Solver - Documentation

## Overview

The Simplified Math Problem Solver is a streamlined version that uses only Google Vision API and Google Gemini's vision capabilities to solve mathematical problems from images. This version eliminates the need for Mathpix and PDF processing, making it easier to set up and use.

## Key Features

- 🎯 **Gemini Vision Direct Processing**: Uses Gemini's multimodal capabilities to analyze images directly
- 🔍 **Google Vision OCR Fallback**: Backup OCR using Google Cloud Vision API
- 📚 **Educational Focus**: Provides study tips, explanations, and exam preparation guidance
- ⚡ **Simplified Setup**: Only requires Gemini API key to get started
- 🔄 **Async/Sync Support**: Both asynchronous and synchronous interfaces
- 🛡️ **Robust Error Handling**: Graceful failure handling with fallback mechanisms

## Architecture

```
User Image → Gemini Vision (Primary) → Solution
     ↓              ↓ (if fails)
Google Vision OCR → Gemini Text Analysis → Solution
```

## Quick Setup

### 1. Required API Key

You only need one API key to get started:

```env
# Add to AI-Services/.env
GEMINI_API_KEY="your_gemini_api_key_here"
```

Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

### 2. Dependencies

All required dependencies are already in your `requirements.txt`:
```bash
pip install -r requirements.txt
```

Key packages used:
- `google-generativeai` - For Gemini AI
- `google-cloud-vision` - For Vision OCR fallback
- `pillow` - For image processing
- `python-dotenv` - For environment variables

## Usage Examples

### Basic Image Solving

```python
import asyncio
from AI_Services.simplified_math_solver import solve_math_from_image

async def solve_problem():
    # Solve from image file
    result = await solve_math_from_image("math_problem.jpg")
    
    print(f"Problem: {result.extracted_text}")
    print(f"Answer: {result.final_answer}")
    print(f"Method: {result.method_used}")
    print(f"Steps: {len(result.solution_steps)} steps")

asyncio.run(solve_problem())
```

### Synchronous Usage

```python
from AI_Services.simplified_math_solver import solve_math_from_image_sync

# For synchronous code (like Django views)
result = solve_math_from_image_sync("math_problem.jpg")
print(f"Answer: {result.final_answer}")
```

### Text-Only Problem Solving

```python
import asyncio
from AI_Services.simplified_math_solver import solve_text_problem

async def solve_text():
    result = await solve_text_problem("Solve: 2x + 5 = 15")
    print(f"Answer: {result['final_answer']}")
    print(f"Steps: {result['solution_steps']}")

asyncio.run(solve_text())
```

### Advanced Configuration

```python
from AI_Services.simplified_math_solver import MathProblemSolver

# Create solver with specific configuration
solver = MathProblemSolver(use_vision_ocr_fallback=True)

# Solve with custom settings
result = await solver.solve_from_image("image.jpg")
```

## API Response Format

### MathSolutionResult Object

```python
@dataclass
class MathSolutionResult:
    extracted_text: str           # Text extracted from image
    problem_type: str            # Type of math problem
    difficulty: MathDifficulty   # Difficulty level enum
    solution_steps: List[str]    # Step-by-step solution
    final_answer: str           # Final answer
    explanation: str            # Detailed explanation
    verification: str           # How to verify the answer
    study_tips: List[str]       # Study tips for similar problems
    related_concepts: List[str] # Related mathematical concepts
    confidence_score: float    # Confidence in solution (0-1)
    processing_time: float     # Time taken to process
    method_used: str          # "gemini_vision" or "vision_ocr_gemini"
```

### JSON Response Example

```json
{
    "extracted_text": "2x + 5 = 15",
    "problem_type": "linear_equation",
    "difficulty": "high_school",
    "solution_steps": [
        "Start with the equation: 2x + 5 = 15",
        "Subtract 5 from both sides: 2x = 10", 
        "Divide both sides by 2: x = 5"
    ],
    "final_answer": "x = 5",
    "explanation": "This is a linear equation solved by isolating the variable x...",
    "verification": "Substitute x = 5 back into the original equation: 2(5) + 5 = 15 ✓",
    "study_tips": [
        "Always perform the same operation on both sides",
        "Check your answer by substituting back"
    ],
    "related_concepts": ["linear equations", "algebraic manipulation"],
    "confidence_score": 0.95,
    "processing_time": 2.3,
    "method_used": "gemini_vision"
}
```

## Django Integration

### View Example

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from AI_Services.simplified_math_solver import solve_math_from_image_sync

@csrf_exempt
def solve_math_endpoint(request):
    if request.method == 'POST':
        image_file = request.FILES['image']
        
        try:
            result = solve_math_from_image_sync(image_file.read())
            
            return JsonResponse({
                'success': True,
                'problem': result.extracted_text,
                'answer': result.final_answer,
                'explanation': result.explanation,
                'steps': result.solution_steps,
                'study_tips': result.study_tips,
                'difficulty': result.difficulty.value,
                'confidence': result.confidence_score,
                'method': result.method_used
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
```

### Frontend JavaScript

```javascript
async function solveMathProblem(imageFile) {
    const formData = new FormData();
    formData.append('image', imageFile);
    
    try {
        const response = await fetch('/api/solve-math/', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            displaySolution(result);
        } else {
            showError(result.error);
        }
    } catch (error) {
        showError('Failed to solve problem');
    }
}
```

## Testing

### Run Tests

```bash
# Test the simplified solver
python test_simplified_solver.py

# Choose from options:
# 1. Run all tests
# 2. Test configuration only  
# 3. Interactive demo
# 4. Quick text problem test
```

### Quick Test

```python
import asyncio
from AI_Services.simplified_math_solver import solve_text_problem

# Test with a simple problem
result = asyncio.run(solve_text_problem("What is 2 + 3?"))
print(result['final_answer'])  # Should output: "5"
```

## Error Handling

The solver handles errors gracefully:

```python
try:
    result = await solve_math_from_image("image.jpg")
    
    if result.problem_type == "error":
        print(f"Error occurred: {result.explanation}")
    else:
        print(f"Solution: {result.final_answer}")
        
except Exception as e:
    print(f"Failed to process: {e}")
```

## Performance & Limits

### Gemini API Limits
- **Free Tier**: 1,000 requests per day
- **Rate Limit**: 15 requests per minute
- **Image Size**: Max 20MB per image
- **Context**: Up to 2 million tokens

### Best Practices
1. **Image Quality**: Use clear, high-contrast images
2. **File Size**: Keep images under 5MB for faster processing
3. **Error Handling**: Always handle potential API failures
4. **Caching**: Cache results for identical problems
5. **Async Usage**: Use async functions in web applications

## Troubleshooting

### Common Issues

1. **"Gemini API quota exceeded"**
   - Wait for quota reset (daily)
   - Upgrade to paid tier
   - Implement request throttling

2. **"No clear mathematical problem detected"**
   - Ensure image contains visible math content
   - Improve image quality/contrast
   - Try cropping to focus on the problem

3. **"Vision OCR fallback not available"**
   - Expected if Google Cloud Vision not configured
   - Solver will use Gemini Vision only
   - Add Vision API credentials for fallback

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run your solver - you'll see detailed logs
result = await solve_math_from_image("image.jpg")
```

## Comparison with Original Version

| Feature | Original | Simplified |
|---------|----------|------------|
| **OCR Providers** | Mathpix + Google Vision | Google Vision (fallback only) |
| **Primary Method** | OCR → Text Analysis | Direct Vision Analysis |
| **Setup Complexity** | Multiple API keys needed | Single Gemini API key |
| **Math Accuracy** | High (Mathpix specialized) | Very Good (Gemini Vision) |
| **Dependencies** | More complex | Simplified |
| **PDF Support** | Yes | No (images only) |
| **Maintenance** | Higher | Lower |

## Migration from Original

If migrating from the original `maths-solution.py`:

1. **Update imports:**
   ```python
   # Old
   from maths_solution import solve_math_from_image
   
   # New  
   from simplified_math_solver import solve_math_from_image
   ```

2. **Remove OCR provider parameter:**
   ```python
   # Old
   result = await solve_math_from_image(image, OCRProvider.MATHPIX)
   
   # New
   result = await solve_math_from_image(image)
   ```

3. **Update response handling:**
   ```python
   # New field available
   print(f"Method used: {result.method_used}")
   ```

## Future Enhancements

Planned improvements:
- Support for handwritten math recognition
- Batch processing for multiple images
- Integration with more educational features
- Performance optimizations
- Enhanced error recovery

## Support

For issues:
1. Check this documentation
2. Run the test suite: `python test_simplified_solver.py`
3. Verify API key configuration
4. Check Gemini API quota status
5. Review error logs for specific issues

The simplified math solver provides a robust, easy-to-use solution for integrating math problem solving into your Examify app with minimal setup requirements.
