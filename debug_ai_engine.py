#!/usr/bin/env python3
"""
Debug script to test AI Quiz Engine import and initialization
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to the Python path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))
sys.path.append(str(backend_path / 'AI-Services'))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

print("🔧 Testing AI Quiz Engine Import...")

try:
    print("1. Testing basic import...")
    from quiz_engine import AIQuizEngine
    print("   ✅ AIQuizEngine class imported successfully")
    
    print("2. Testing instance creation...")
    engine = AIQuizEngine()
    print("   ✅ AIQuizEngine instance created successfully")
    
    print("3. Testing AI models availability...")
    if hasattr(engine, 'ai_models_available'):
        print(f"   AI Models Available: {engine.ai_models_available}")
    
    print("4. Testing pre-created instance import...")
    from quiz_engine import ai_quiz_engine
    if ai_quiz_engine:
        print("   ✅ Pre-created ai_quiz_engine instance imported successfully")
    else:
        print("   ❌ Pre-created ai_quiz_engine instance is None")
        
    print("5. Testing environment variables...")
    from django.conf import settings
    ai_config = getattr(settings, 'AI_SERVICES_CONFIG', {})
    
    openai_key = ai_config.get('OPENAI_API_KEY', 'Not found')
    gemini_key = ai_config.get('GEMINI_API_KEY', 'Not found')
    
    print(f"   OPENAI_API_KEY: {'✅ Set' if openai_key and openai_key != 'Not found' else '❌ Missing'}")
    print(f"   GEMINI_API_KEY: {'✅ Set' if gemini_key and gemini_key != 'Not found' else '❌ Missing'}")
    
    if openai_key != 'Not found':
        print(f"   OpenAI Key (first 20 chars): {openai_key[:20]}...")
    if gemini_key != 'Not found':
        print(f"   Gemini Key (first 20 chars): {gemini_key[:20]}...")
        
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\nDebugging import issues...")
    
    # Check if the file exists
    quiz_engine_path = backend_path / 'AI-Services' / 'quiz_engine.py'
    print(f"Quiz engine file exists: {quiz_engine_path.exists()}")
    
    # Check what's in the AI-Services directory
    ai_services_path = backend_path / 'AI-Services'
    if ai_services_path.exists():
        print(f"AI-Services directory contents: {list(ai_services_path.iterdir())}")
    
except Exception as e:
    print(f"❌ General Error: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 AI Quiz Engine Debug Complete")
