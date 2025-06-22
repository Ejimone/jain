from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register(r'sessions', views.ChatSessionViewSet, basename='chatsession')
router.register(r'study-plans', views.StudyPlanViewSet, basename='studyplan')

# New AI-powered Quiz and Question Management endpoints
router.register(r'questions', api_views.QuestionViewSet, basename='question')
router.register(r'past-questions', api_views.PastQuestionViewSet, basename='pastquestion')
router.register(r'quizzes', api_views.QuizViewSet, basename='quiz')
router.register(r'quiz-sessions', api_views.UserQuizSessionViewSet, basename='quizsession')
router.register(r'quiz-preferences', api_views.QuizCustomizationViewSet, basename='quizpreferences')

urlpatterns = [
    # AI models endpoint
    path('ai-models/', views.ai_models, name='ai-models'),
    
    # Feedback and analytics endpoints
    path('feedback/', views.submit_feedback, name='ai-feedback'),
    path('analytics/', views.ai_analytics, name='ai-analytics'),
    
    # User progress analytics
    path('user-analytics/', views.user_progress_analytics, name='user-analytics'),
    
    # Include router URLs
    path('', include(router.urls)),
]
