from django.urls import path
from . import views

urlpatterns = [
    # AI service endpoints
    path('math/solve/', views.solve_math_problem, name='solve-math-problem'),
    path('image/analyze/', views.analyze_image, name='analyze-image'),
    path('document/process/', views.process_document, name='process-document'),
    path('materials/get/', views.get_study_materials, name='get-study-materials'),
    path('explanation/generate/', views.generate_explanation, name='generate-explanation'),
    path('search/real-time/', views.search_real_time, name='search-real-time'),
    
    # System endpoints
    path('health/', views.health_check, name='health-check'),
    path('capabilities/', views.get_service_capabilities, name='service-capabilities'),
]
