from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'sessions', views.ChatSessionViewSet, basename='chatsession')
router.register(r'study-plans', views.StudyPlanViewSet, basename='studyplan')

urlpatterns = [
    # AI models endpoint
    path('ai-models/', views.ai_models, name='ai-models'),
    
    # Feedback and analytics endpoints
    path('feedback/', views.submit_feedback, name='ai-feedback'),
    path('analytics/', views.ai_analytics, name='ai-analytics'),
    
    # Include router URLs
    path('', include(router.urls)),
]
