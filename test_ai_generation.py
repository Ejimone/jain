#!/usr/bin/env python3
"""
Test AI question generation functionality
"""

import requests
import json

# Test AI question generation
def test_ai_generation():
    print("🤖 Testing AI Question Generation...")
    
    # Authentication (get fresh token)
    auth_response = requests.post(
        'http://127.0.0.1:8001/admin/login/',
        data={
            'username': 'comprehensive_test@example.com',
            'password': 'testpassword123'
        }
    )
    
    # Get fresh token via Django (simplified approach for testing)
    headers = {
        'Authorization': 'Token 0435adef50035b10fe2d6a3e',  # Using existing token
        'Content-Type': 'application/json'
    }
    
    # Test data for AI generation
    payload = {
        "topics": ["Data Structures", "Arrays"],
        "difficulty_level": "intermediate",
        "total_questions": 2,
        "question_types": ["multiple_choice"],
        "quiz_type": "practice"
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:8001/api/v1/ai-tutor/questions/generate_ai_questions/',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            print(f"✅ Success! Generated {data.get('count', 0)} questions")
            
            if data.get('questions'):
                for i, question in enumerate(data['questions'], 1):
                    print(f"\n📝 Question {i}:")
                    print(f"   Title: {question.get('title', 'N/A')}")
                    print(f"   Type: {question.get('question_type', 'N/A')}")
                    print(f"   Text: {question.get('question_text', 'N/A')[:100]}...")
            else:
                print("⚠️ No questions generated")
                
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response text: {response.text}")
                
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - AI generation might be slow")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_ai_generation()
