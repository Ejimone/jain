from django.urls import path
from . import views

urlpatterns = [
    path('content/', views.get_content_recommendations, name='content-recommendations'),
    path('courses/', views.get_course_recommendations, name='course-recommendations'),
    path('personalized/', views.get_personalized_recommendations, name='personalized-recommendations'),
    path('trending/', views.get_trending_content, name='trending-content'),
    path('similar/', views.get_similar_content, name='similar-content'),
    path('study/', views.get_study_recommendations, name='study-recommendations'),
    path('exam-prep/', views.get_content_for_exam_prep, name='exam-prep-content'),
]
