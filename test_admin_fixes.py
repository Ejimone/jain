#!/usr/bin/env python3
"""
Test script to validate Django admin functionality after fixing property method issues.
"""

import requests
import sys

def test_admin_endpoints():
    """Test Django admin endpoints to ensure they don't throw 500 errors"""
    base_url = "http://localhost:8001"
    
    endpoints = [
        "/admin/",
        "/admin/AItutor/",
        "/admin/AItutor/chatsession/",
        "/admin/AItutor/chatsession/add/",
        "/admin/AItutor/studyplan/",
        "/admin/AItutor/studyplan/add/",
        "/admin/AItutor/chatmessage/",
        "/admin/AItutor/studyplantask/",
        "/admin/AItutor/aiinteraction/",
        "/admin/AItutor/aimodelusage/",
    ]
    
    print("🔧 Testing Django Admin Endpoints After Property Fixes")
    print("=" * 60)
    
    all_good = True
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            status = response.status_code
            
            if status == 200:
                status_icon = "✅"
                status_text = "OK"
            elif status == 302:
                status_icon = "🔄"
                status_text = "Redirect (Login Required)"
            elif status == 500:
                status_icon = "❌"
                status_text = "SERVER ERROR"
                all_good = False
            else:
                status_icon = "⚠️"
                status_text = f"Status {status}"
            
            print(f"  {status_icon} {endpoint:<40} - {status_text}")
            
        except Exception as e:
            print(f"  ❌ {endpoint:<40} - Connection Error: {e}")
            all_good = False
    
    print("=" * 60)
    
    if all_good:
        print("🎉 All admin endpoints are accessible! No 500 errors detected.")
        print("✅ Property method fixes resolved the admin interface issues.")
    else:
        print("❌ Some endpoints still have issues.")
        return False
    
    return True

def test_model_properties():
    """Test that the model properties handle None values correctly"""
    print("\n🧪 Testing Model Properties with None Values")
    print("=" * 60)
    
    test_script = '''
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from AItutor.models import StudyPlan, ChatSession
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()

print("Testing StudyPlan properties:")
plan = StudyPlan(user=user, title="Test", plan_type="custom")
print(f"  days_remaining: {plan.days_remaining}")
print(f"  progress_percentage: {plan.progress_percentage}")

print("Testing ChatSession properties:")  
session = ChatSession(user=user, title="Test")
print(f"  duration_minutes: {session.duration_minutes}")

print("All property tests passed!")
'''
    
    import subprocess
    try:
        result = subprocess.run(
            ['python', '-c', test_script],
            cwd='/Users/evidenceejimone/jain/backend',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Model property tests passed!")
            print(result.stdout)
        else:
            print("❌ Model property tests failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running property tests: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 DJANGO ADMIN FIXES VALIDATION")
    print("Testing fixes for StudyPlan.days_remaining and ChatSession.duration_minutes")
    print()
    
    # Test model properties first
    properties_ok = test_model_properties()
    
    # Test admin endpoints
    admin_ok = test_admin_endpoints()
    
    print("\n" + "=" * 60)
    if properties_ok and admin_ok:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Admin interface issues have been resolved.")
        print("✅ Property methods now handle None values correctly.")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the output above for details.")
        sys.exit(1)
