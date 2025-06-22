from rest_framework import generics, viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.http import Http404, HttpResponse, FileResponse
from django.shortcuts import get_object_or_404
from datetime import timedelta
import logging

from .models import (
    Content, Question, StudyMaterial, ContentCategory, Tag,
    ContentRating, ContentView, ContentDownload, UserBookmark
)
from .serializers import (
    ContentListSerializer, ContentDetailSerializer, ContentCreateSerializer,
    QuestionSerializer, StudyMaterialSerializer, ContentCategorySerializer,
    TagSerializer, ContentRatingSerializer, UserBookmarkSerializer,
    ContentStatsSerializer, QuestionAttemptSerializer, ContentSearchSerializer
)
from student.models import UserProgress

logger = logging.getLogger('AIServices')


class ContentViewSet(viewsets.ModelViewSet):
    """ViewSet for content management"""
    permission_classes = [AllowAny]  # Allow public access for testing
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ContentListSerializer
        elif self.action == 'create':
            return ContentCreateSerializer
        return ContentDetailSerializer
    
    def get_queryset(self):
        queryset = Content.objects.filter(status='approved').select_related(
            'author', 'course', 'category', 'department', 'region'
        ).prefetch_related('tags', 'ratings')
        
        # Apply filters
        content_type = self.request.query_params.get('content_type')
        course_id = self.request.query_params.get('course')
        department_id = self.request.query_params.get('department')
        semester = self.request.query_params.get('semester')
        difficulty = self.request.query_params.get('difficulty')
        search = self.request.query_params.get('search')
        
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if semester:
            queryset = queryset.filter(semester=semester)
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(topic__icontains=search) |
                Q(keywords__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve content and track view"""
        content = self.get_object()
        
        # Track view
        ContentView.objects.create(
            content=content,
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        # Update view count
        Content.objects.filter(id=content.id).update(view_count=F('view_count') + 1)
        
        serializer = self.get_serializer(content)
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """Rate content"""
        content = self.get_object()
        rating_value = request.data.get('rating')
        review_text = request.data.get('review', '')
        
        if not rating_value or not (1 <= int(rating_value) <= 5):
            return Response({'error': 'Rating must be between 1 and 5'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        rating, created = ContentRating.objects.update_or_create(
            content=content,
            user=request.user,
            defaults={'rating': rating_value, 'review': review_text}
        )
        
        # Update content average rating
        avg_rating = content.ratings.aggregate(avg=Avg('rating'))['avg']
        content.rating = round(avg_rating, 2) if avg_rating else 0
        content.save(update_fields=['rating'])
        
        serializer = ContentRatingSerializer(rating)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def bookmark(self, request, pk=None):
        """Bookmark/unbookmark content"""
        content = self.get_object()
        bookmark, created = UserBookmark.objects.get_or_create(
            user=request.user,
            content=content,
            defaults={'notes': request.data.get('notes', '')}
        )
        
        if not created:
            bookmark.delete()
            return Response({'bookmarked': False})
        
        return Response({'bookmarked': True, 'bookmark': UserBookmarkSerializer(bookmark).data})
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download content file"""
        content = self.get_object()
        
        if not content.file:
            return Response({'error': 'No file available for download'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Track download
        ContentDownload.objects.create(
            content=content,
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        # Update download count
        Content.objects.filter(id=content.id).update(download_count=F('download_count') + 1)
        
        # Return file response
        try:
            response = FileResponse(
                content.file.open('rb'),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{content.file.name}"'
            return response
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return Response({'error': 'File not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def my_content(self, request):
        """Get user's uploaded content"""
        queryset = Content.objects.filter(author=request.user).order_by('-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ContentListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ContentListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular content"""
        queryset = self.get_queryset().filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-view_count', '-rating')[:20]
        
        serializer = ContentListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """Get recommended content based on user's profile and activity"""
        user = request.user
        
        # Get user's courses and interests
        user_courses = []
        user_department = None
        
        if hasattr(user, 'student_profile'):
            profile = user.student_profile
            user_courses = list(profile.courses.values_list('id', flat=True))
            user_department = profile.department
        
        # Base queryset
        queryset = self.get_queryset()
        
        # Filter by user's courses
        if user_courses:
            queryset = queryset.filter(course_id__in=user_courses)
        elif user_department:
            queryset = queryset.filter(department=user_department)
        
        # Get recent popular content
        queryset = queryset.filter(
            created_at__gte=timezone.now() - timedelta(days=60)
        ).order_by('-rating', '-view_count')[:20]
        
        serializer = ContentListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for questions"""
    serializer_class = QuestionSerializer
    permission_classes = [AllowAny]  # Allow public access for testing
    
    def get_queryset(self):
        return Question.objects.select_related('content').filter(
            content__status='approved'
        )
    
    @action(detail=True, methods=['post'])
    def attempt(self, request, pk=None):
        """Submit answer for a question"""
        question = self.get_object()
        serializer = QuestionAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_answer = serializer.validated_data['user_answer']
        time_taken = serializer.validated_data.get('time_taken', 0)
        
        # Check if answer is correct
        is_correct = user_answer.lower().strip() == question.correct_answer.lower().strip()
        
        # Update question statistics
        Question.objects.filter(id=question.id).update(
            attempt_count=F('attempt_count') + 1,
            correct_attempt_count=F('correct_attempt_count') + (1 if is_correct else 0)
        )
        
        # Update user progress if course and topic are available
        if question.content.course and question.content.topic:
            progress, created = UserProgress.objects.get_or_create(
                user=request.user,
                course=question.content.course,
                topic=question.content.topic
            )
            progress.update_progress(1, 1 if is_correct else 0, max(1, time_taken // 60))
        
        response_data = {
            'is_correct': is_correct,
            'explanation': question.explanation,
            'correct_answer': question.correct_answer if not is_correct else None
        }
        
        logger.info(f"Question attempt by {request.user.email}: {'correct' if is_correct else 'incorrect'}")
        
        return Response(response_data)


class ContentCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for content categories"""
    queryset = ContentCategory.objects.filter(is_active=True).order_by('name')
    serializer_class = ContentCategorySerializer
    permission_classes = [AllowAny]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tags"""
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class UserBookmarkViewSet(viewsets.ModelViewSet):
    """ViewSet for user bookmarks"""
    serializer_class = UserBookmarkSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserBookmark.objects.filter(user=self.request.user).select_related(
            'content'
        ).order_by('-created_at')


class StudyMaterialViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing study materials.
    """
    queryset = StudyMaterial.objects.all()
    serializer_class = StudyMaterialSerializer
    permission_classes = [AllowAny]  # Allow public access for testing


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def content_stats(request):
    """Get content statistics"""
    # Overall stats
    total_content = Content.objects.filter(status='approved').count()
    total_questions = Content.objects.filter(status='approved', content_type='question').count()
    total_materials = Content.objects.filter(
        status='approved',
        content_type__in=['note', 'material', 'document']
    ).count()
    
    # Recent uploads (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_uploads = Content.objects.filter(
        status='approved',
        created_at__gte=week_ago
    ).count()
    
    # Top categories
    top_categories = ContentCategory.objects.annotate(
        content_count=Count('content', filter=Q(content__status='approved'))
    ).order_by('-content_count')[:5]
    
    top_categories_data = [
        {'name': cat.name, 'count': cat.content_count}
        for cat in top_categories
    ]
    
    # Popular content
    popular_content = Content.objects.filter(
        status='approved'
    ).order_by('-view_count')[:10]
    
    stats = {
        'total_content': total_content,
        'total_questions': total_questions,
        'total_materials': total_materials,
        'recent_uploads': recent_uploads,
        'top_categories': top_categories_data,
        'popular_content': ContentListSerializer(
            popular_content,
            many=True,
            context={'request': request}
        ).data
    }
    
    return Response(ContentStatsSerializer(stats).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_content(request):
    """Advanced content search"""
    serializer = ContentSearchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    query_params = serializer.validated_data
    queryset = Content.objects.filter(status='approved')
    
    # Apply filters
    if query_params.get('query'):
        search_query = query_params['query']
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(topic__icontains=search_query) |
            Q(keywords__icontains=search_query)
        )
    
    if query_params.get('content_type'):
        queryset = queryset.filter(content_type=query_params['content_type'])
    
    if query_params.get('course_id'):
        queryset = queryset.filter(course_id=query_params['course_id'])
    
    if query_params.get('department_id'):
        queryset = queryset.filter(department_id=query_params['department_id'])
    
    if query_params.get('region_id'):
        queryset = queryset.filter(region_id=query_params['region_id'])
    
    if query_params.get('category_id'):
        queryset = queryset.filter(category_id=query_params['category_id'])
    
    if query_params.get('difficulty_level'):
        queryset = queryset.filter(difficulty_level=query_params['difficulty_level'])
    
    if query_params.get('semester'):
        queryset = queryset.filter(semester=query_params['semester'])
    
    if query_params.get('tags'):
        tag_names = query_params['tags']
        queryset = queryset.filter(tags__name__in=tag_names).distinct()
    
    # Apply sorting
    sort_by = query_params.get('sort_by', '-created_at')
    queryset = queryset.order_by(sort_by)
    
    # Paginate results
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    serializer = ContentListSerializer(page_obj, many=True, context={'request': request})
    
    return Response({
        'results': serializer.data,
        'page': page_obj.number,
        'total_pages': paginator.num_pages,
        'total_results': paginator.count
    })
