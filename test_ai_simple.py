#!/usr/bin/env python3
"""
Simple AI test using Django environment
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to the Python path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from student.models import Course

User = get_user_model()

def test_ai_generation():
    """Test AI generation directly"""
    print("🤖 Testing AI Generation with Django Client...")
    
    # Get existing user and token
    try:
        user = User.objects.get(email="comprehensive_test@example.com")
        token, _ = Token.objects.get_or_create(user=user)
        
        # Setup API client
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        print(f"✅ Using token: {token.key[:20]}...")
        
        # Get a course for the test
        course = Course.objects.filter(name__icontains="Test").first()
        if course:
            print(f"✅ Using course: {course.name}")
        else:
            print("❌ No test course found")
            return
        
        # Test AI generation
        payload = {
            "course_id": str(course.id),
            "topics": ["Arrays", "Data Structures"],
            "difficulty_level": "intermediate",
            "total_questions": 1,  # Just one question for testing
            "question_types": ["multiple_choice"]
        }
        
        print("🔄 Requesting AI generation...")
        response = client.post('/api/v1/ai-tutor/questions/generate_ai_questions/', data=payload, format='json')
        
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Success! Generated {data.get('count', 0)} questions")
            
            questions = data.get('questions', [])
            if questions:
                for i, q in enumerate(questions, 1):
                    print(f"\n📝 Question {i}:")
                    print(f"   Title: {q.get('title', 'N/A')}")
                    print(f"   Text: {q.get('question_text', 'N/A')[:150]}...")
                    print(f"   Type: {q.get('question_type', 'N/A')}")
                    print(f"   Difficulty: {q.get('difficulty_level', 'N/A')}")
                    if q.get('answer_options'):
                        print(f"   Options: {len(q['answer_options'])} choices")
            else:
                print("⚠️ No questions in response")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.json()}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_generation()
