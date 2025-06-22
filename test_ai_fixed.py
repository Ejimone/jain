#!/usr/bin/env python3
"""
Test the fixed AI question generation endpoint
"""

import requests
import json
import os
import sys

# Add backend to path for models
sys.path.append('/Users/evidenceejimone/jain/backend')

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()

from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

BASE_URL = 'http://127.0.0.1:8002'

def get_auth_token():
    """Get or create a test user and token"""
    User = get_user_model()
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='testuser_ai',
        defaults={
            'email': 'test_ai@example.com',
            'first_name': 'Test',
            'last_name': 'AI User'
        }
    )
    
    # Get or create token
    token, created = Token.objects.get_or_create(user=user)
    return token.key

def test_ai_question_generation():
    """Test AI question generation with the async fix"""
    print("🤖 Testing AI Question Generation (Fixed Async)...")
    
    # Get authentication token
    token = get_auth_token()
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    # Test data for AI generation
    test_data = {
        'topics': ['calculus', 'derivatives', 'limits'],
        'difficulty': 'intermediate',
        'count': 3,
        'question_types': ['multiple_choice', 'short_answer'],
        'use_real_time': False
    }
    
    print(f"📤 Requesting {test_data['count']} AI questions...")
    print(f"   Topics: {test_data['topics']}")
    print(f"   Difficulty: {test_data['difficulty']}")
    print(f"   Types: {test_data['question_types']}")
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/v1/ai-tutor/questions/generate_ai_questions/',
            json=test_data,
            headers=headers,
            timeout=300  # 5 minute timeout for AI generation
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ AI Generation Success!")
            print(f"   Generated: {data.get('count', 0)} questions")
            
            # Show generated questions
            for i, question in enumerate(data.get('questions', []), 1):
                print(f"\n   Question {i}:")
                print(f"      Type: {question.get('question_type')}")
                print(f"      Difficulty: {question.get('difficulty')}")
                print(f"      Text: {question.get('question_text', '')[:100]}...")
                print(f"      Source: {question.get('source', 'AI Generated')}")
                
                # Show options for MCQ
                if question.get('question_type') == 'multiple_choice':
                    options = question.get('options', [])
                    if options:
                        print(f"      Options: {len(options)} choices")
                        for j, option in enumerate(options[:2], 1):  # Show first 2 options
                            print(f"         {j}. {option[:50]}...")
            
            return True
            
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            print(f"❌ AI Generation Failed: {error_data}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - AI generation taking too long")
        return False
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def test_simple_ai_generation():
    """Test with minimal parameters"""
    print("\n🧪 Testing Simple AI Generation...")
    
    token = get_auth_token()
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    # Minimal test data
    test_data = {
        'topics': ['mathematics'],
        'count': 1,
        'difficulty': 'easy'
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/v1/ai-tutor/questions/generate_ai_questions/',
            json=test_data,
            headers=headers,
            timeout=180  # 3 minute timeout
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Simple Generation Success: {data.get('count', 0)} questions")
            return True
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            print(f"❌ Simple Generation Failed: {error_data}")
            return False
            
    except Exception as e:
        print(f"❌ Simple generation failed: {str(e)}")
        return False

if __name__ == '__main__':
    print("🚀 Testing Fixed AI Question Generation Endpoint")
    print("=" * 60)
    
    # Test comprehensive AI generation
    success1 = test_ai_question_generation()
    
    # Test simple AI generation
    success2 = test_simple_ai_generation()
    
    print("\n" + "=" * 60)
    if success1 or success2:
        print("✅ AI Generation Tests: SOME PASSED")
        if success1 and success2:
            print("🎉 Both comprehensive and simple AI generation working!")
        elif success1:
            print("🎯 Comprehensive AI generation working!")
        else:
            print("🎯 Simple AI generation working!")
    else:
        print("❌ AI Generation Tests: ALL FAILED")
        print("🔧 Check server logs for detailed error information")
    
    print("\n💡 Next steps:")
    print("   - If successful: Test with different topics and difficulty levels")
    print("   - If failed: Check Django server logs for async/threading errors")
    print("   - Consider implementing question validation and error handling")
