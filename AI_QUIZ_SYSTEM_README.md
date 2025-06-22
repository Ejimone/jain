# AI-Powered Quiz and Past Questions System

## Overview

This comprehensive AI-powered quiz and past questions system for the Examify app provides intelligent question generation, quiz customization, performance analytics, and collaborative knowledge building. The system integrates with existing RealTimeSearch and RAG services to deliver a seamless learning experience.

## Features Implemented

### 🧠 AI-Powered Question Generation
- **Multiple AI Models**: Integrates Gemini Pro, GPT-4o-mini, and fallback mechanisms
- **Intelligent Difficulty Analysis**: Complexity analysis based on conceptual, computational, and cognitive load
- **Real-Time Sources**: Can scrape current educational content using RealTimeSearch
- **Multi-Source Generation**: Combines AI-generated, past exam questions, and user uploads

### 📚 Smart Past Questions Database
- **10-Year Range Support**: Manages questions from the last decade
- **Advanced Filtering**: Sort by year, difficulty, institution, exam type
- **Verification System**: Admin/instructor verification workflow
- **OCR Integration**: Extract text from uploaded question images

### 🎯 Customizable Quiz Engine
- **User Preferences**: Personalized quiz settings and preferences
- **Adaptive Difficulty**: AI adjusts difficulty based on user performance
- **Question Type Variety**: Multiple choice, true/false, short answer, essay, numerical, code
- **Time Management**: Intelligent time estimation and tracking

### 📊 Performance Analytics
- **Detailed Tracking**: Topic-wise, difficulty-wise, and type-wise performance
- **Trend Analysis**: Improvement rates, consistency scores, learning velocity
- **AI Recommendations**: Personalized study suggestions based on performance
- **Real-Time Progress**: Live session tracking and analytics

### 🔍 Advanced Search & Similarity
- **Embedding-Based Search**: Vector search for similar questions
- **Semantic Matching**: Find conceptually related content
- **Duplicate Detection**: Prevent redundant questions

### 🤝 Collaborative Features
- **User Contributions**: Students and instructors can upload questions
- **Community Verification**: Peer review and rating system
- **Knowledge Sharing**: Build collective question banks

## Technical Architecture

### Models

#### Core Models
- **Question**: Central question model with AI metadata
- **PastQuestion**: Past exam question with institutional metadata
- **Quiz**: AI-generated quiz containers
- **UserQuizSession**: Individual quiz attempts and progress

#### Analytics Models
- **DifficultyAnalysis**: Detailed complexity analysis
- **UserPerformanceAnalytics**: Comprehensive performance tracking
- **QuizCustomization**: User preference management

#### AI Enhancement Models
- **EmbeddingVector**: Question embeddings for similarity search
- **OnlineSource**: External educational source management

### API Endpoints

#### Question Management
```
GET    /api/v1/ai-tutor/questions/                    # List questions
POST   /api/v1/ai-tutor/questions/                    # Create question
POST   /api/v1/ai-tutor/questions/generate_ai_questions/  # AI generation
POST   /api/v1/ai-tutor/questions/upload_image/       # OCR processing
GET    /api/v1/ai-tutor/questions/search_similar/     # Similarity search
POST   /api/v1/ai-tutor/questions/{id}/rate_question/ # Rate question
```

#### Past Questions
```
GET    /api/v1/ai-tutor/past-questions/               # List past questions
GET    /api/v1/ai-tutor/past-questions/by_year_range/ # Group by year
POST   /api/v1/ai-tutor/past-questions/{id}/verify_question/ # Verify
```

#### Quiz Management
```
GET    /api/v1/ai-tutor/quizzes/                      # List quizzes
POST   /api/v1/ai-tutor/quizzes/generate_quiz/        # Generate AI quiz
POST   /api/v1/ai-tutor/quizzes/{id}/start_session/   # Start quiz session
GET    /api/v1/ai-tutor/quizzes/{id}/analytics/       # Quiz analytics
```

#### Quiz Sessions
```
GET    /api/v1/ai-tutor/quiz-sessions/                # List user sessions
POST   /api/v1/ai-tutor/quiz-sessions/{id}/submit_answer/ # Submit answer
POST   /api/v1/ai-tutor/quiz-sessions/{id}/complete_session/ # Complete
GET    /api/v1/ai-tutor/quiz-sessions/performance_analysis/ # Performance
```

#### User Preferences
```
GET    /api/v1/ai-tutor/quiz-preferences/             # Get preferences
POST   /api/v1/ai-tutor/quiz-preferences/             # Update preferences
GET    /api/v1/ai-tutor/quiz-preferences/get_or_create_preferences/ # Get/Create
```

## AI Integration

### Question Generation Process
1. **Context Preparation**: Gather course materials, topics, existing questions
2. **Real-Time Enhancement**: Optionally fetch current educational content
3. **AI Generation**: Use Gemini Pro or GPT-4o-mini with structured prompts
4. **Quality Validation**: Parse and validate generated content
5. **Embedding Creation**: Generate vector embeddings for search
6. **Difficulty Analysis**: AI-powered complexity assessment

### Image Processing Pipeline
1. **Image Upload**: Accept various image formats
2. **OCR Processing**: Extract text using pytesseract (optional)
3. **AI Analysis**: Use Gemini Vision for content understanding
4. **Question Detection**: Identify and extract questions from images
5. **Auto-Creation**: Convert detected questions to Question objects

### Performance Analytics Engine
1. **Data Collection**: Track all user interactions and performance
2. **Trend Analysis**: Calculate improvement rates and consistency
3. **AI Recommendations**: Generate personalized study suggestions
4. **Adaptive Learning**: Adjust difficulty based on performance patterns

## Configuration

### Environment Variables
```bash
# AI Models
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
SERPAPI_API_KEY=your_serpapi_key

# OCR (Optional)
TESSERACT_CMD=/usr/bin/tesseract  # Path to tesseract executable
```

### Django Settings
```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'AItutor',
]

# Cache configuration for embeddings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## Installation & Setup

### 1. Install Dependencies
```bash
# Core dependencies
pip install openai google-generativeai pillow

# OCR support (optional)
pip install pytesseract
# On macOS: brew install tesseract
# On Ubuntu: sudo apt-get install tesseract-ocr

# Vector database (for production)
pip install psycopg2  # For PostgreSQL with pgvector
# OR
pip install pinecone-client  # For Pinecone
```

### 2. Run Migrations
```bash
python manage.py makemigrations AItutor
python manage.py migrate AItutor
```

### 3. Create Superuser (if needed)
```bash
python manage.py createsuperuser
```

### 4. Configure AI Services
- Set up API keys in environment variables
- Configure rate limits and quotas
- Test AI model connectivity

## Usage Examples

### Generate AI Quiz
```python
# API Request
POST /api/v1/ai-tutor/quizzes/generate_quiz/
{
    "course_id": "uuid-here",
    "topics": ["Machine Learning", "Neural Networks"],
    "difficulty": "intermediate",
    "num_questions": 10,
    "question_types": ["multiple_choice", "short_answer"],
    "include_past_questions": true,
    "include_ai_generated": true,
    "use_real_time_sources": false
}
```

### Upload Question Image
```python
# API Request
POST /api/v1/ai-tutor/questions/upload_image/
Content-Type: multipart/form-data

image: [image_file]
course_id: "uuid-here"
extract_text: true
```

### Get Performance Analysis
```python
# API Request
GET /api/v1/ai-tutor/quiz-sessions/performance_analysis/?course_id=uuid-here

# Response includes:
# - Overall accuracy and trends
# - Weak/strong topics
# - AI-generated recommendations
# - Detailed analytics by time period
```

## Monitoring & Analytics

### Admin Interface
- Full question bank management
- User performance monitoring
- AI model usage tracking
- Source quality assessment

### Performance Metrics
- Question generation success rates
- User engagement analytics
- AI model performance comparison
- System resource utilization

## Future Enhancements

### Planned Features
1. **Voice Integration**: Speech-to-text question input
2. **Advanced Vector Search**: PostgreSQL pgvector or Pinecone integration
3. **Collaborative Filtering**: User-based recommendation system
4. **Multi-Language Support**: International question banks
5. **Mobile Optimization**: React Native integration
6. **Real-Time Collaboration**: Live quiz sessions

### AI Model Improvements
1. **Custom Fine-Tuning**: Domain-specific model training
2. **Ensemble Methods**: Combine multiple AI models
3. **Continuous Learning**: Model improvement from user feedback
4. **Explainable AI**: Transparent difficulty assessments

## Troubleshooting

### Common Issues

#### AI Engine Not Available
```python
# Check logs for:
WARNING:root:AI Quiz Engine not available - some features will be disabled

# Solutions:
1. Verify API keys are set correctly
2. Check internet connectivity
3. Ensure AI-Services directory is accessible
4. Install missing dependencies (google-generativeai, openai)
```

#### OCR Processing Fails
```python
# Check if tesseract is installed:
tesseract --version

# Install on macOS:
brew install tesseract

# Install on Ubuntu:
sudo apt-get install tesseract-ocr
```

#### Database Migration Issues
```python
# Reset migrations if needed:
python manage.py migrate AItutor zero
python manage.py makemigrations AItutor
python manage.py migrate AItutor
```

## Support & Documentation

### Additional Resources
- [Django Documentation](https://docs.djangoproject.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/)
- [Google AI Studio](https://makersuite.google.com/)
- [Tesseract OCR Documentation](https://tesseract-ocr.github.io/)

### Contact & Support
For technical support or feature requests, please refer to the project documentation or contact the development team.

---

*This system represents a comprehensive implementation of AI-powered educational technology, designed to enhance the learning experience through intelligent content generation, personalized recommendations, and detailed performance analytics.*
