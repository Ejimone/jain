"""
Test script to verify the Django backend APIs are working correctly.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8001"

def test_api_endpoints():
    """Test basic API endpoints."""
    print("Testing Examify Django Backend APIs...")
    print("=" * 50)
    
    # Test student endpoints
    print("\n1. Testing Student API endpoints:")
    
    # Test regions
    try:
        response = requests.get(f"{BASE_URL}/api/v1/students/regions/")
        if response.status_code == 200:
            print(f"✅ GET /api/v1/students/regions/ - {len(response.json())} regions found")
        else:
            print(f"❌ GET /api/v1/students/regions/ - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ GET /api/v1/students/regions/ - Error: {e}")
    
    # Test departments
    try:
        response = requests.get(f"{BASE_URL}/api/v1/students/departments/")
        if response.status_code == 200:
            print(f"✅ GET /api/v1/students/departments/ - {len(response.json())} departments found")
        else:
            print(f"❌ GET /api/v1/students/departments/ - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ GET /api/v1/students/departments/ - Error: {e}")
    
    # Test courses
    try:
        response = requests.get(f"{BASE_URL}/api/v1/students/courses/")
        if response.status_code == 200:
            print(f"✅ GET /api/v1/students/courses/ - {len(response.json())} courses found")
        else:
            print(f"❌ GET /api/v1/students/courses/ - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ GET /api/v1/students/courses/ - Error: {e}")
    
    # Test content endpoints
    print("\n2. Testing Content API endpoints:")
    
    # Test categories
    try:
        response = requests.get(f"{BASE_URL}/api/v1/content/categories/")
        if response.status_code == 200:
            print(f"✅ GET /api/v1/content/categories/ - {len(response.json())} categories found")
        else:
            print(f"❌ GET /api/v1/content/categories/ - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ GET /api/v1/content/categories/ - Error: {e}")
    
    # Test tags
    try:
        response = requests.get(f"{BASE_URL}/api/v1/content/tags/")
        if response.status_code == 200:
            print(f"✅ GET /api/v1/content/tags/ - {len(response.json())} tags found")
        else:
            print(f"❌ GET /api/v1/content/tags/ - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ GET /api/v1/content/tags/ - Error: {e}")
    
    # Test AI tutor endpoints
    print("\n3. Testing AI Tutor API endpoints:")
    
    # Test AI models
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ai-tutor/ai-models/")
        if response.status_code == 200:
            print(f"✅ GET /api/v1/ai-tutor/ai-models/ - Response received")
        else:
            print(f"❌ GET /api/v1/ai-tutor/ai-models/ - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ GET /api/v1/ai-tutor/ai-models/ - Error: {e}")
    
    # Test AI services endpoints
    print("\n4. Testing AI Services API endpoints:")
    
    # Test health check
    try:
        response = requests.get(f"{BASE_URL}/api/v1/services/health/")
        if response.status_code == 200:
            print(f"✅ GET /api/v1/services/health/ - {response.json()}")
        else:
            print(f"❌ GET /api/v1/services/health/ - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ GET /api/v1/services/health/ - Error: {e}")
    
    print("\n" + "=" * 50)
    print("API testing completed!")

if __name__ == "__main__":
    test_api_endpoints()
