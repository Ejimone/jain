from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'content', views.ContentViewSet, basename='content')
router.register(r'questions', views.QuestionViewSet, basename='question')
router.register(r'study-materials', views.StudyMaterialViewSet, basename='studymaterial')
router.register(r'categories', views.ContentCategoryViewSet)
router.register(r'tags', views.TagViewSet)
router.register(r'bookmarks', views.UserBookmarkViewSet, basename='bookmark')

urlpatterns = [
    # Statistics and search endpoints
    path('stats/', views.content_stats, name='content-stats'),
    path('search/', views.search_content, name='content-search'),
    
    # Include router URLs
    path('', include(router.urls)),
]
