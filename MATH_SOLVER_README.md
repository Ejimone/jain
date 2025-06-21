# Math Problem Solver Module Documentation

## Overview

The Math Problem Solver module is a comprehensive solution for extracting mathematical content from images and providing detailed solutions using OCR technology and AI. It's designed specifically for the Examify AI-powered exam preparation app.

## Features

- **Multiple OCR Providers**: Supports both Mathpix OCR (specialized for math) and Google Cloud Vision API
- **Intelligent Fallback**: Automatically switches between OCR providers for optimal results
- **AI-Powered Solutions**: Uses Google Gemini AI for comprehensive problem solving
- **Educational Focus**: Provides study tips, explanations, and exam preparation guidance
- **Flexible Input**: Accepts images as file paths, bytes, or BytesIO objects
- **Async/Sync Support**: Both asynchronous and synchronous interfaces available
- **Error Handling**: Robust error handling with detailed feedback

## Installation

### 1. Install Required Dependencies

```bash
pip install -r requirements.txt
```

The module requires these key packages:
- `google-generativeai` - For Gemini AI integration
- `google-cloud-vision` - For Google Vision OCR
- `mpxpy` - For Mathpix OCR (optional)
- `openai` - For alternative Gemini access
- `pillow` - For image processing
- `python-dotenv` - For environment variables

### 2. Configure API Keys

Create or update the `.env` file in the `AI-Services/` directory:

```env
# Required for AI problem solving
GEMINI_API_KEY="your_gemini_api_key_here"
GOOGLE_API_KEY="your_google_api_key_here"

# Optional: For Mathpix OCR (recommended for best math OCR)
MATHPIX_APP_ID="your_mathpix_app_id"
MATHPIX_APP_KEY="your_mathpix_app_key"

# Optional: For Google Vision OCR with service account
GOOGLE_CLOUD_VISION_CREDENTIALS_PATH="/path/to/service_account.json"
```

### 3. API Key Setup Guide

#### Google Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your `.env` file

#### Mathpix OCR (Recommended)
1. Sign up at [Mathpix](https://mathpix.com/)
2. Get your App ID and App Key from the dashboard
3. Add them to your `.env` file

#### Google Cloud Vision (Alternative OCR)
1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Vision API
3. Create a service account and download credentials JSON
4. Set the path in your `.env` file

## Usage

### Basic Usage

```python
import asyncio
from AI_Services.maths_solution import solve_math_from_image, OCRProvider

async def solve_problem():
    # Solve from image file
    result = await solve_math_from_image(
        "path/to/math_image.jpg",
        preferred_ocr=OCRProvider.MATHPIX
    )
    
    print(f"Problem: {result.extracted_text}")
    print(f"Answer: {result.final_answer}")
    print(f"Explanation: {result.explanation}")

# Run the example
asyncio.run(solve_problem())
```

### Synchronous Usage

```python
from AI_Services.maths_solution import solve_math_from_image_sync

# For synchronous code
result = solve_math_from_image_sync("math_image.jpg")
print(result.final_answer)
```

### Advanced Usage

```python
from AI_Services.maths_solution import MathProblemSolver, OCRProvider

# Create solver with specific configuration
solver = MathProblemSolver(preferred_ocr=OCRProvider.BOTH)

# Solve from bytes data
with open("math_image.jpg", "rb") as f:
    image_data = f.read()

result = await solver.solve_from_image(image_data)

# Access detailed results
print(f"Problem type: {result.problem_type}")
print(f"Difficulty: {result.difficulty.value}")
print(f"OCR provider used: {result.ocr_provider_used}")
print(f"Confidence: {result.confidence_score:.1%}")
print(f"Processing time: {result.processing_time:.2f}s")

# Solution steps
for i, step in enumerate(result.solution_steps, 1):
    print(f"{i}. {step}")

# Study tips
for tip in result.study_tips:
    print(f"💡 {tip}")
```

## API Reference

### Main Functions

#### `solve_math_from_image(image_input, preferred_ocr=OCRProvider.MATHPIX)`

Solve math problems from images (async).

**Parameters:**
- `image_input`: Image file path (str), bytes, or BytesIO object
- `preferred_ocr`: OCR provider preference (OCRProvider enum)

**Returns:** `MathSolutionResult` object

#### `solve_math_from_image_sync(image_input, preferred_ocr=OCRProvider.MATHPIX)`

Synchronous wrapper for `solve_math_from_image`.

### Classes

#### `MathProblemSolver`

Main class for solving math problems.

```python
solver = MathProblemSolver(preferred_ocr=OCRProvider.MATHPIX)
result = await solver.solve_from_image(image_input)
```

#### `OCRProvider` (Enum)

Available OCR providers:
- `OCRProvider.MATHPIX` - Mathpix OCR (best for math)
- `OCRProvider.GOOGLE_VISION` - Google Cloud Vision
- `OCRProvider.BOTH` - Try both providers

#### `MathSolutionResult` (Dataclass)

Result object containing:
- `extracted_text`: OCR extracted text
- `extracted_latex`: LaTeX representation (if available)
- `problem_type`: Type of math problem
- `difficulty`: Problem difficulty level
- `solution_steps`: List of solution steps
- `final_answer`: Final answer
- `explanation`: Detailed explanation
- `verification`: Verification method
- `study_tips`: Study tips and exam advice
- `related_concepts`: Related mathematical concepts
- `ocr_provider_used`: OCR provider that was used
- `confidence_score`: Confidence in the solution
- `processing_time`: Time taken to process

### Error Handling

The module handles errors gracefully:

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

## Integration with Examify

### Backend Integration

```python
# In your Django/Flask view
from AI_Services.maths_solution import solve_math_from_image_sync

def solve_math_endpoint(request):
    if request.method == 'POST':
        image_file = request.FILES['math_image']
        
        # Solve the problem
        result = solve_math_from_image_sync(
            image_file.read(),
            preferred_ocr=OCRProvider.MATHPIX
        )
        
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
```

### API Response Format

```json
{
  "success": true,
  "extracted_text": "2x + 5 = 15",
  "problem_type": "linear_equation",
  "difficulty": "high_school",
  "final_answer": "x = 5",
  "solution_steps": [
    "Start with the equation: 2x + 5 = 15",
    "Subtract 5 from both sides: 2x = 10",
    "Divide both sides by 2: x = 5"
  ],
  "explanation": "This is a linear equation that can be solved by isolating the variable x...",
  "study_tips": [
    "Remember to perform the same operation on both sides of the equation",
    "Check your answer by substituting back into the original equation"
  ],
  "confidence_score": 0.95,
  "processing_time": 2.34
}
```

## Testing

Run the test suite:

```bash
# Run comprehensive tests
python tests/test_maths_solution.py

# Run example demonstrations
python example_math_solver.py
```

Test individual components:

```bash
# Test just configuration
python -c "from tests.test_maths_solution import test_configuration; test_configuration()"
```

## Performance Tips

1. **Use Mathpix for Math**: Mathpix OCR is specifically designed for mathematical content and will give better results than general OCR
2. **Image Quality**: Ensure images are clear and high contrast for better OCR results
3. **Async Operations**: Use async functions for better performance in web applications
4. **Caching**: Consider caching results for identical images
5. **Error Handling**: Always handle potential errors from OCR and AI services

## Troubleshooting

### Common Issues

1. **"No OCR providers available"**
   - Check that API keys are configured in `.env`
   - Verify that at least one OCR service is properly set up

2. **"Gemini API error"**
   - Verify `GEMINI_API_KEY` is correct
   - Check API quotas and billing in Google Cloud Console

3. **Poor OCR results**
   - Ensure image quality is good (clear, high contrast)
   - Try different OCR providers
   - Consider image preprocessing

4. **Import errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check that the module path is correct

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run your code - you'll see detailed logs
result = await solve_math_from_image("image.jpg")
```

## Best Practices

1. **Always use try-catch blocks** around OCR and AI operations
2. **Validate image inputs** before processing
3. **Set reasonable timeouts** for API calls
4. **Monitor API usage** to avoid quota limits
5. **Cache results** when possible to improve performance
6. **Use appropriate OCR provider** for your use case
7. **Handle network failures** gracefully
8. **Validate results** before presenting to users

## Future Enhancements

Planned improvements:
- Support for handwritten math
- Additional OCR providers
- Math step-by-step visualization
- Integration with more AI models
- Enhanced error recovery
- Batch processing capabilities

## Support

For issues and questions:
1. Check this documentation
2. Run the test suite to verify setup
3. Check the example usage files
4. Review error logs for specific issues
5. Ensure API keys and dependencies are properly configured
