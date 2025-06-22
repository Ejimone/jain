# Examify Backend API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URL and Versioning](#base-url-and-versioning)
4. [Response Format](#response-format)
5. [Error Handling](#error-handling)
6. [Student Management APIs](#student-management-apis)
7. [Content Management APIs](#content-management-apis)
8. [AI Tutor APIs](#ai-tutor-apis)
9. [AI Services APIs](#ai-services-apis)
10. [Recommendation APIs](#recommendation-apis)
11. [Data Models](#data-models)
12. [Usage Examples](#usage-examples)
13. [Development Setup](#development-setup)

## Overview

The Examify Backend API is a comprehensive RESTful API built with Django REST Framework that powers an AI-driven exam preparation platform. The API provides functionality for user management, content management, AI-powered question generation, image analysis, math problem solving, and personalized recommendations.

### Key Features
- **User Authentication & Profiles**: Token-based authentication with student profiles
- **Content Management**: Questions, study materials, courses, and departments
- **AI-Powered Features**: Question generation, image analysis, math solving
- **Quiz Management**: Create, manage, and take AI-generated quizzes
- **Recommendations**: Personalized content and study recommendations
- **Analytics**: User progress tracking and performance analytics

## Authentication

The API uses Django's Token Authentication. All authenticated endpoints require the `Authorization` header.

### Authentication Header Format
```
Authorization: Token <your_token_here>
```

### Getting a Token
1. Register a new user or login with existing credentials
2. The API returns a token in the response
3. Use this token for all subsequent authenticated requests

## Base URL and Versioning

- **Base URL**: `http://localhost:8002/api/v1/`
- **API Version**: v1
- **Content Type**: `application/json` (unless uploading files)

### API Modules
- `/api/v1/students/` - User and student management
- `/api/v1/content/` - Content and question management
- `/api/v1/ai-tutor/` - AI-powered tutoring features
- `/api/v1/services/` - AI processing services
- `/api/v1/recommendations/` - Recommendation engine

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "details": { ... }
}
```

### Paginated Response
```json
{
  "count": 100,
  "next": "http://localhost:8002/api/v1/endpoint/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

## Error Handling

### HTTP Status Codes
- `200 OK` - Success
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Common Error Responses
```json
// Authentication Error
{
  "detail": "Authentication credentials were not provided."
}

// Validation Error
{
  "email": ["This field is required."],
  "password": ["This field may not be blank."]
}

// Permission Error
{
  "detail": "You do not have permission to perform this action."
}
```

---

## Student Management APIs

### Authentication Endpoints

#### Register User
**POST** `/api/v1/students/auth/register/`

Register a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "student_profile": {
      "student_id": "GEN250001",
      "current_semester": 1,
      "enrollment_year": 2025
    }
  },
  "token": "auth_token_here",
  "message": "Registration successful"
}
```

#### Login User
**POST** `/api/v1/students/auth/login/`

Authenticate user and get access token.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "student_profile": { ... }
  },
  "token": "auth_token_here",
  "message": "Login successful"
}
```

#### Logout User
**POST** `/api/v1/students/auth/logout/`

**Headers:** `Authorization: Token <token>`

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

### Profile Management

#### Get User Profile
**GET** `/api/v1/students/profile/`

**Headers:** `Authorization: Token <token>`

**Response:**
```json
{
  "id": "uuid",
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "is_verified": false,
  "student_profile": {
    "student_id": "GEN250001",
    "region": null,
    "department": null,
    "current_semester": 1,
    "enrollment_year": 2025,
    "courses": []
  }
}
```

#### Update User Profile
**PUT/PATCH** `/api/v1/students/profile/`

**Headers:** `Authorization: Token <token>`

**Request Body:**
```json
{
  "first_name": "Johnny",
  "phone_number": "+1234567890",
  "student_profile": {
    "current_semester": 2,
    "department": "department_uuid"
  }
}
```

### Academic Data Endpoints

#### Get Regions
**GET** `/api/v1/students/regions/`

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "name": "Maharashtra",
      "code": "MH",
      "country": "India",
      "is_active": true
    }
  ]
}
```

#### Get Departments
**GET** `/api/v1/students/departments/`

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": "uuid",
      "name": "Computer Science Engineering",
      "code": "CSE",
      "description": "Computer Science and Engineering Department",
      "is_active": true
    }
  ]
}
```

#### Get Courses
**GET** `/api/v1/students/courses/`

**Query Parameters:**
- `department` - Filter by department ID
- `semester` - Filter by semester number

**Response:**
```json
{
  "count": 16,
  "results": [
    {
      "id": "uuid",
      "name": "Data Structures and Algorithms",
      "code": "DSA101",
      "department": {
        "id": "uuid",
        "name": "Computer Science Engineering",
        "code": "CSE"
      },
      "semester": 1,
      "credits": 4,
      "description": "Introduction to data structures and algorithms",
      "is_active": true
    }
  ]
}
```

#### Get Dashboard Data
**GET** `/api/v1/students/dashboard/`

**Headers:** `Authorization: Token <token>`

**Response:**
```json
{
  "user_stats": {
    "total_questions_attempted": 150,
    "average_score": 85.5,
    "study_time_hours": 45,
    "achievements": ["First Quiz", "Week Streak"]
  },
  "recent_activity": [ ... ],
  "recommended_content": [ ... ],
  "upcoming_quizzes": [ ... ]
}
```

---

## Content Management APIs

### Questions

#### Get Questions
**GET** `/api/v1/content/questions/`

**Query Parameters:**
- `course` - Filter by course ID
- `difficulty` - Filter by difficulty (easy, intermediate, hard)
- `type` - Filter by question type
- `search` - Search in question text

**Response:**
```json
{
  "count": 50,
  "results": [
    {
      "id": "uuid",
      "title": "Array Traversal",
      "question_text": "What is the time complexity of traversing an array?",
      "question_type": "multiple_choice",
      "difficulty_level": "easy",
      "answer_options": {
        "A": "O(1)",
        "B": "O(n)",
        "C": "O(n²)",
        "D": "O(log n)"
      },
      "correct_answer": "B",
      "answer_explanation": "Array traversal requires visiting each element once.",
      "created_at": "2025-06-22T10:00:00Z"
    }
  ]
}
```

#### Create Question
**POST** `/api/v1/content/questions/`

**Headers:** `Authorization: Token <token>`

**Request Body:**
```json
{
  "title": "Binary Search",
  "question_text": "What is the time complexity of binary search?",
  "question_type": "multiple_choice",
  "difficulty_level": "intermediate",
  "answer_options": {
    "A": "O(n)",
    "B": "O(log n)",
    "C": "O(n log n)",
    "D": "O(1)"
  },
  "correct_answer": "B",
  "answer_explanation": "Binary search divides the search space in half each time."
}
```

### Study Materials

#### Get Study Materials
**GET** `/api/v1/content/study-materials/`

**Query Parameters:**
- `course` - Filter by course ID
- `type` - Filter by material type (notes, slides, videos)

**Response:**
```json
{
  "count": 25,
  "results": [
    {
      "id": "uuid",
      "title": "Introduction to Algorithms",
      "description": "Comprehensive notes on algorithmic concepts",
      "material_type": "notes",
      "course": "uuid",
      "file_url": "/media/materials/algo_notes.pdf",
      "created_at": "2025-06-22T10:00:00Z"
    }
  ]
}
```

### Content Statistics

#### Get Content Stats
**GET** `/api/v1/content/stats/`

**Response:**
```json
{
  "total_questions": 1250,
  "total_materials": 450,
  "questions_by_difficulty": {
    "easy": 400,
    "intermediate": 600,
    "hard": 250
  },
  "questions_by_type": {
    "multiple_choice": 800,
    "short_answer": 300,
    "essay": 150
  }
}
```

---

## AI Tutor APIs

### Question Management with AI

#### Generate AI Questions
**POST** `/api/v1/ai-tutor/questions/generate_ai_questions/`

**Headers:** `Authorization: Token <token>`

**Request Body:**
```json
{
  "course_id": "uuid",
  "topics": ["arrays", "linked lists", "sorting"],
  "difficulty": "intermediate",
  "count": 5,
  "question_types": ["multiple_choice", "short_answer"],
  "use_real_time": false
}
```

**Response:**
```json
{
  "success": true,
  "count": 5,
  "questions": [
    {
      "id": "uuid",
      "title": "Array Implementation",
      "question_text": "How do you implement a dynamic array?",
      "question_type": "short_answer",
      "difficulty_level": "intermediate",
      "answer_explanation": "Dynamic arrays resize automatically...",
      "topics": ["arrays", "data structures"],
      "estimated_solve_time": 300,
      "ai_generated": true
    }
  ]
}
```

#### Upload Image for Analysis
**POST** `/api/v1/ai-tutor/questions/upload_image/`

**Headers:** `Authorization: Token <token>`

**Content-Type:** `multipart/form-data`

**Request Body:**
```
image: <image_file>
extract_text: true
course_id: uuid (optional)
```

**Response:**
```json
{
  "success": true,
  "extracted_text": "2x + 5 = 15\nSolve for x",
  "ai_analysis": {
    "content_type": "mathematical_equation",
    "subject_area": "algebra",
    "difficulty_level": "easy"
  },
  "questions_created": [
    {
      "question_text": "Solve the equation 2x + 5 = 15",
      "correct_answer": "x = 5",
      "answer_explanation": "Subtract 5 from both sides, then divide by 2"
    }
  ]
}
```

### Quiz Management

#### Get Quizzes
**GET** `/api/v1/ai-tutor/quizzes/`

**Headers:** `Authorization: Token <token>`

**Query Parameters:**
- `course` - Filter by course ID
- `status` - Filter by status (draft, published, archived)
- `quiz_type` - Filter by type (practice, assessment, mock_exam)

**Response:**
```json
{
  "count": 7,
  "results": [
    {
      "id": "uuid",
      "title": "Data Structures Practice Quiz",
      "description": "Practice quiz covering basic data structures",
      "quiz_type": "practice",
      "status": "published",
      "course_name": "Data Structures Test",
      "topics": ["arrays", "linked lists", "sorting"],
      "difficulty_range": {"min": 0.3, "max": 0.7},
      "question_types": ["multiple_choice", "short_answer"],
      "total_questions": 10,
      "time_limit": 30,
      "ai_generated": true,
      "is_public": true,
      "created_at": "2025-06-22T07:43:02Z"
    }
  ]
}
```

#### Create Quiz
**POST** `/api/v1/ai-tutor/quizzes/`

**Headers:** `Authorization: Token <token>`

**Request Body:**
```json
{
  "title": "Advanced Algorithms Quiz",
  "description": "Quiz on advanced algorithmic concepts",
  "course": "uuid",
  "quiz_type": "assessment",
  "topics": ["dynamic programming", "graph algorithms"],
  "difficulty_range": {"min": 0.6, "max": 0.9},
  "total_questions": 15,
  "time_limit": 60,
  "is_public": false
}
```

#### Start Quiz Session
**POST** `/api/v1/ai-tutor/quiz-sessions/`

**Headers:** `Authorization: Token <token>`

**Request Body:**
```json
{
  "quiz": "quiz_uuid"
}
```

**Response:**
```json
{
  "id": "session_uuid",
  "quiz": {
    "id": "quiz_uuid",
    "title": "Data Structures Quiz",
    "time_limit": 30
  },
  "questions": [
    {
      "id": "question_uuid",
      "question_text": "What is a linked list?",
      "question_type": "multiple_choice",
      "answer_options": { ... }
    }
  ],
  "started_at": "2025-06-22T10:00:00Z",
  "time_remaining": 1800
}
```

### Analytics

#### Get AI Analytics
**GET** `/api/v1/ai-tutor/analytics/`

**Headers:** `Authorization: Token <token>`

**Response:**
```json
{
  "total_ai_questions_generated": 500,
  "total_images_analyzed": 150,
  "average_question_quality_score": 8.5,
  "most_popular_topics": ["algorithms", "data structures", "mathematics"],
  "ai_usage_by_month": {
    "2025-06": 200,
    "2025-05": 180
  }
}
```

---

## AI Services APIs

### Math Problem Solving

#### Solve Math Problem
**POST** `/api/v1/services/math/solve/`

**Headers:** `Authorization: Token <token>`

**Request Body:**
```json
{
  "problem": "2x + 5 = 15, solve for x",
  "context": "Linear equations chapter",
  "show_steps": true
}
```

**Response:**
```json
{
  "success": true,
  "problem": "2x + 5 = 15, solve for x",
  "result": {
    "final_answer": "x = 5",
    "solution_steps": [
      "Start with: 2x + 5 = 15",
      "Subtract 5 from both sides: 2x = 10",
      "Divide both sides by 2: x = 5"
    ],
    "explanation": "This is a linear equation solved by isolating the variable x.",
    "difficulty": "easy",
    "confidence_score": 0.95,
    "processing_time": 1.2
  }
}
```

### Image Analysis

#### Analyze Image
**POST** `/api/v1/services/image/analyze/`

**Headers:** `Authorization: Token <token>`

**Request Body:**
```json
{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
  "question": "What mathematical concept is shown in this diagram?",
  "subject": "mathematics"
}
```

**Response:**
```json
{
  "success": true,
  "question": "What mathematical concept is shown in this diagram?",
  "subject": "mathematics",
  "analysis": {
    "detected_objects": ["triangle", "angles", "measurements"],
    "mathematical_concepts": ["trigonometry", "geometry"],
    "text_content": "sin(θ) = opposite/hypotenuse",
    "explanation": "This diagram shows the trigonometric relationship in a right triangle",
    "confidence": 0.92
  }
}
```

### Document Processing

#### Process Document
**POST** `/api/v1/services/document/process/`

**Headers:** `Authorization: Token <token>`

**Content-Type:** `multipart/form-data`

**Request Body:**
```
file: <document_file>
query: "What are the main concepts covered?"
extract_questions: true
```

**Response:**
```json
{
  "success": true,
  "document_summary": "This document covers fundamental concepts in computer science...",
  "key_concepts": ["algorithms", "data structures", "complexity analysis"],
  "extracted_questions": [
    {
      "question": "What is the time complexity of binary search?",
      "type": "conceptual",
      "difficulty": "intermediate"
    }
  ],
  "content_outline": [ ... ]
}
```

### Service Health

#### Health Check
**GET** `/api/v1/services/health/`

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "ai_engine": "available",
    "database": "connected",
    "file_storage": "accessible"
  },
  "version": "1.0.0",
  "timestamp": "2025-06-22T10:00:00Z"
}
```

#### Get Service Capabilities
**GET** `/api/v1/services/capabilities/`

**Response:**
```json
{
  "math_solving": {
    "available": true,
    "supported_types": ["linear_equations", "quadratic_equations", "calculus"],
    "max_complexity": "advanced"
  },
  "image_analysis": {
    "available": true,
    "supported_formats": ["jpeg", "png", "gif"],
    "max_file_size": "10MB",
    "features": ["ocr", "object_detection", "math_recognition"]
  },
  "document_processing": {
    "available": true,
    "supported_formats": ["pdf", "docx", "txt"],
    "features": ["text_extraction", "question_generation", "summarization"]
  }
}
```

---

## Recommendation APIs

### Content Recommendations

#### Get Content Recommendations
**GET** `/api/v1/recommendations/content/`

**Headers:** `Authorization: Token <token>`

**Query Parameters:**
- `course` - Course ID for targeted recommendations
- `difficulty` - Preferred difficulty level
- `limit` - Number of recommendations (default: 10)

**Response:**
```json
{
  "recommendations": [
    {
      "id": "uuid",
      "title": "Advanced Array Algorithms",
      "type": "question",
      "difficulty": "hard",
      "relevance_score": 0.95,
      "reason": "Based on your recent performance in data structures"
    }
  ],
  "recommendation_metadata": {
    "algorithm": "collaborative_filtering",
    "generated_at": "2025-06-22T10:00:00Z",
    "user_preferences": { ... }
  }
}
```

#### Get Study Recommendations
**GET** `/api/v1/recommendations/study/`

**Headers:** `Authorization: Token <token>`

**Response:**
```json
{
  "recommended_topics": [
    {
      "topic": "Graph Algorithms",
      "priority": "high",
      "estimated_study_time": "2 hours",
      "resources": [
        {
          "type": "video",
          "title": "Introduction to Graph Theory",
          "url": "/content/video/123"
        }
      ]
    }
  ],
  "study_plan": {
    "this_week": [ ... ],
    "next_week": [ ... ]
  }
}
```

### Personalized Recommendations

#### Get Personalized Recommendations
**GET** `/api/v1/recommendations/personalized/`

**Headers:** `Authorization: Token <token>`

**Response:**
```json
{
  "for_you": {
    "questions": [ ... ],
    "study_materials": [ ... ],
    "quizzes": [ ... ]
  },
  "trending": {
    "popular_this_week": [ ... ],
    "rising_topics": [ ... ]
  },
  "weakness_areas": [
    {
      "topic": "Dynamic Programming",
      "confidence": 0.4,
      "recommended_actions": ["practice", "review_theory"]
    }
  ]
}
```

---

## Data Models

### User Model
```python
{
  "id": "UUID",
  "username": "string",
  "email": "string (unique)",
  "first_name": "string",
  "last_name": "string",
  "phone_number": "string (optional)",
  "profile_picture": "URL (optional)",
  "is_student": "boolean (default: true)",
  "is_verified": "boolean (default: false)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Student Profile Model
```python
{
  "user": "User UUID",
  "student_id": "string (auto-generated)",
  "region": "Region UUID (optional)",
  "department": "Department UUID (optional)",
  "current_semester": "integer (1-10)",
  "enrollment_year": "integer",
  "courses": ["Course UUIDs"],
  "bio": "text",
  "study_preferences": "JSON",
  "performance_data": "JSON"
}
```

### Question Model
```python
{
  "id": "UUID",
  "title": "string",
  "question_text": "text",
  "question_type": "choice (multiple_choice, short_answer, essay, true_false)",
  "difficulty_level": "choice (easy, intermediate, hard)",
  "answer_options": "JSON",
  "correct_answer": "string",
  "answer_explanation": "text",
  "topics": "JSON array",
  "source_type": "choice (ai_generated, uploaded, manual)",
  "estimated_solve_time": "integer (seconds)",
  "ai_generated": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Quiz Model
```python
{
  "id": "UUID",
  "title": "string",
  "description": "text",
  "course": "Course UUID (optional)",
  "quiz_type": "choice (practice, assessment, mock_exam)",
  "status": "choice (draft, published, archived)",
  "topics": "JSON array",
  "difficulty_range": "JSON {min: float, max: float}",
  "question_types": "JSON array",
  "total_questions": "integer",
  "time_limit": "integer (minutes)",
  "ai_generated": "boolean",
  "is_public": "boolean",
  "created_by": "User UUID (optional)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## Usage Examples

### Complete Authentication Flow

```javascript
// 1. Register a new user
const registerResponse = await fetch('/api/v1/students/auth/register/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'john_doe',
    email: 'john@example.com',
    password: 'secure_password',
    first_name: 'John',
    last_name: 'Doe'
  })
});
const { token } = await registerResponse.json();

// 2. Use token for authenticated requests
const profileResponse = await fetch('/api/v1/students/profile/', {
  headers: { 'Authorization': `Token ${token}` }
});
```

### AI Question Generation Flow

```javascript
// 1. Generate AI questions
const generateResponse = await fetch('/api/v1/ai-tutor/questions/generate_ai_questions/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    topics: ['algorithms', 'data structures'],
    difficulty: 'intermediate',
    count: 5,
    question_types: ['multiple_choice']
  })
});

const { questions } = await generateResponse.json();

// 2. Create a quiz with generated questions
const quizResponse = await fetch('/api/v1/ai-tutor/quizzes/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'My Practice Quiz',
    description: 'Generated from AI questions',
    quiz_type: 'practice',
    total_questions: 5,
    time_limit: 30
  })
});
```

### Image Upload and Analysis

```javascript
// Upload image for analysis
const formData = new FormData();
formData.append('image', imageFile);
formData.append('extract_text', 'true');

const imageResponse = await fetch('/api/v1/ai-tutor/questions/upload_image/', {
  method: 'POST',
  headers: { 'Authorization': `Token ${token}` },
  body: formData
});

const analysisResult = await imageResponse.json();
console.log('Extracted text:', analysisResult.extracted_text);
console.log('AI Analysis:', analysisResult.ai_analysis);
```

### Math Problem Solving

```javascript
// Solve a math problem
const mathResponse = await fetch('/api/v1/services/math/solve/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    problem: '2x + 5 = 15, solve for x',
    context: 'Linear equations practice',
    show_steps: true
  })
});

const solution = await mathResponse.json();
console.log('Answer:', solution.result.final_answer);
console.log('Steps:', solution.result.solution_steps);
```

---

## Development Setup

### Prerequisites
- Python 3.8+
- Django 4.0+
- PostgreSQL/SQLite
- Redis (for caching)

### Environment Variables
```bash
# Django Settings
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:pass@localhost/examify

# AI Services
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
AI_SERVICES_ENABLED=True

# File Storage
MEDIA_ROOT=/path/to/media
MEDIA_URL=/media/

# Caching
REDIS_URL=redis://localhost:6379/0
```

### Installation
```bash
# 1. Clone and setup
git clone <repository>
cd examify-backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup database
python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser

# 5. Load sample data (optional)
python manage.py loaddata fixtures/sample_data.json

# 6. Run development server
python manage.py runserver 8002
```

### Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test student
python manage.py test AItutor

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### API Testing with curl

```bash
# Test authentication
curl -X POST http://localhost:8002/api/v1/students/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass"}'

# Test authenticated endpoint
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8002/api/v1/students/courses/

# Test file upload
curl -X POST http://localhost:8002/api/v1/ai-tutor/questions/upload_image/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "image=@test_image.png" \
  -F "extract_text=true"
```

---

## Rate Limiting and Performance

### Rate Limits
- Authentication endpoints: 10 requests/minute
- AI generation endpoints: 30 requests/hour
- File upload endpoints: 100 requests/hour
- Standard endpoints: 1000 requests/hour

### Performance Optimization
- Database query optimization with select_related/prefetch_related
- Redis caching for frequently accessed data
- Pagination for large datasets
- Async processing for AI operations
- File compression for uploads

### Monitoring
- Built-in Django logging
- Performance metrics collection
- Error tracking and alerts
- API usage analytics

---

## Security Considerations

### Authentication Security
- Token-based authentication
- Password hashing with Django's built-in system
- Token expiration and rotation
- Rate limiting on authentication endpoints

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection for web forms
- File upload security and validation

### API Security
- HTTPS enforcement in production
- CORS configuration
- Request size limits
- Content-type validation
- Permission-based access control

---

## Troubleshooting

### Common Issues

1. **Token Authentication Failed**
   - Ensure token is included in Authorization header
   - Check token format: `Token <token_value>`
   - Verify token hasn't expired

2. **File Upload Issues**
   - Check file size limits (10MB default)
   - Verify supported file formats
   - Ensure proper Content-Type header

3. **AI Services Unavailable**
   - Verify AI service configuration
   - Check API keys are set correctly
   - Ensure AI engine dependencies are installed

4. **Database Connection Issues**
   - Verify database credentials
   - Check database server is running
   - Run migrations if needed

### Debug Mode
Enable debug mode for detailed error information:
```python
DEBUG = True
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'AIServices': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

---

## API Changelog

### Version 1.0 (Current)
- Initial API release
- Basic CRUD operations for all entities
- Token authentication
- AI question generation
- Image upload and analysis
- Math problem solving
- Recommendation engine

### Planned Features (v1.1)
- Real-time notifications
- Advanced analytics dashboard
- Bulk operations
- API versioning
- GraphQL support
- Webhook support

---

**Last Updated:** June 22, 2025  
**API Version:** 1.0  
**Documentation Version:** 1.0