from django.urls import path
from . import views

urlpatterns = [
    path('personalized/', views.get_personalized_recommendations, name='personalized-recommendations'),
    path('trending/', views.get_trending_content, name='trending-content'),
    path('similar/', views.get_similar_content, name='similar-content'),
    path('study/', views.get_study_recommendations, name='study-recommendations'),
    path('exam-prep/', views.get_content_for_exam_prep, name='exam-prep-content'),
]
