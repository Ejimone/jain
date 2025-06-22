from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'regions', views.RegionViewSet)
router.register(r'departments', views.DepartmentViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'profiles', views.StudentProfileViewSet, basename='studentprofile')
router.register(r'sessions', views.StudySessionViewSet, basename='studysession')
router.register(r'progress', views.UserProgressViewSet, basename='userprogress')

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', views.UserLoginView.as_view(), name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    
    # Profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('dashboard/', views.dashboard_data, name='dashboard'),
    
    # Include router URLs
    path('', include(router.urls)),
]
