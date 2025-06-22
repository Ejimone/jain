from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import logging
import random

from content.models import Content, ContentRating, ContentView
from content.serializers import ContentListSerializer
from student.models import UserProgress, StudySession
from AItutor.models import AIInteraction

logger = logging.getLogger('AIServices')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_personalized_recommendations(request):
    """Get personalized content recommendations for the user"""
    user = request.user
    limit = int(request.GET.get('limit', 10))
    
    try:
        # Get user's profile and preferences
        user_profile = getattr(user, 'student_profile', None)
        user_courses = []
        user_department = None
        user_semester = None
        
        if user_profile:
            user_courses = list(user_profile.courses.values_list('id', flat=True))
            user_department = user_profile.department
            user_semester = user_profile.current_semester
        
        # Get user's interaction history
        user_progress = UserProgress.objects.filter(user=user)
        recent_topics = list(user_progress.values_list('topic', flat=True).distinct())
        
        # Get recently viewed content types
        recent_views = ContentView.objects.filter(
            user=user,
            viewed_at__gte=timezone.now() - timedelta(days=30)
        ).values_list('content__content_type', flat=True)
        preferred_content_types = list(set(recent_views))
        
        # Build recommendation query
        recommendations = Content.objects.filter(status='approved')
        
        # Filter by user's academic context
        if user_courses:
            recommendations = recommendations.filter(
                Q(course_id__in=user_courses) |
                Q(department=user_department) |
                Q(semester=user_semester)
            )
        elif user_department:
            recommendations = recommendations.filter(department=user_department)
        
        # Boost content related to user's topics of interest
        if recent_topics:
            topic_boost = Q()
            for topic in recent_topics[:5]:  # Limit to top 5 topics
                topic_boost |= Q(topic__icontains=topic)
            recommendations = recommendations.filter(topic_boost)
        
        # Prefer user's preferred content types
        if preferred_content_types:
            recommendations = recommendations.filter(content_type__in=preferred_content_types)
        
        # Exclude already viewed content (recent views)
        recent_viewed_ids = ContentView.objects.filter(
            user=user,
            viewed_at__gte=timezone.now() - timedelta(days=7)
        ).values_list('content_id', flat=True)
        recommendations = recommendations.exclude(id__in=recent_viewed_ids)
        
        # Order by relevance and popularity
        recommendations = recommendations.annotate(
            rating_score=Avg('ratings__rating'),
            view_score=Count('views')
        ).order_by('-rating_score', '-view_score', '-created_at')[:limit]
        
        serializer = ContentListSerializer(
            recommendations, 
            many=True, 
            context={'request': request}
        )
        
        return Response({
            'recommendations': serializer.data,
            'recommendation_basis': {
                'user_courses': len(user_courses),
                'recent_topics': len(recent_topics),
                'preferred_content_types': preferred_content_types
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating recommendations for user {user.email}: {e}")
        return Response({'error': 'Failed to generate recommendations'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_trending_content(request):
    """Get trending content based on recent activity"""
    limit = int(request.GET.get('limit', 10))
    days = int(request.GET.get('days', 7))
    
    try:
        # Calculate trending score based on recent views and ratings
        since_date = timezone.now() - timedelta(days=days)
        
        trending = Content.objects.filter(
            status='approved',
            created_at__gte=since_date - timedelta(days=30)  # Content from last 30 days
        ).annotate(
            recent_views=Count(
                'views',
                filter=Q(views__viewed_at__gte=since_date)
            ),
            recent_ratings=Count(
                'ratings',
                filter=Q(ratings__created_at__gte=since_date)
            ),
            avg_rating=Avg('ratings__rating')
        ).filter(
            recent_views__gt=0
        ).order_by('-recent_views', '-avg_rating')[:limit]
        
        serializer = ContentListSerializer(
            trending, 
            many=True, 
            context={'request': request}
        )
        
        return Response({
            'trending': serializer.data,
            'period_days': days
        })
        
    except Exception as e:
        logger.error(f"Error getting trending content: {e}")
        return Response({'error': 'Failed to get trending content'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_similar_content(request):
    """Get content similar to a specific piece of content"""
    content_id = request.GET.get('content_id')
    limit = int(request.GET.get('limit', 5))
    
    if not content_id:
        return Response({'error': 'content_id parameter required'}, status=400)
    
    try:
        # Get the reference content
        reference_content = Content.objects.get(id=content_id, status='approved')
        
        # Find similar content based on various criteria
        similar = Content.objects.filter(
            status='approved'
        ).exclude(
            id=content_id
        )
        
        # Same course and topic
        course_topic_match = similar.filter(
            course=reference_content.course,
            topic=reference_content.topic
        )
        
        # Same department and difficulty
        dept_difficulty_match = similar.filter(
            department=reference_content.department,
            difficulty_level=reference_content.difficulty_level,
            semester=reference_content.semester
        )
        
        # Same content type and tags
        type_tag_match = similar.filter(
            content_type=reference_content.content_type
        ).filter(
            tags__in=reference_content.tags.all()
        ).distinct()
        
        # Combine and rank results
        similar_content = []
        
        # Add exact matches first
        similar_content.extend(list(course_topic_match[:3]))
        
        # Add department/difficulty matches
        for content in dept_difficulty_match:
            if content not in similar_content and len(similar_content) < limit:
                similar_content.append(content)
        
        # Add type/tag matches
        for content in type_tag_match:
            if content not in similar_content and len(similar_content) < limit:
                similar_content.append(content)
        
        serializer = ContentListSerializer(
            similar_content[:limit], 
            many=True, 
            context={'request': request}
        )
        
        return Response({
            'similar_content': serializer.data,
            'reference_content': {
                'id': reference_content.id,
                'title': reference_content.title,
                'topic': reference_content.topic,
                'course': str(reference_content.course) if reference_content.course else None
            }
        })
        
    except Content.DoesNotExist:
        return Response({'error': 'Content not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting similar content: {e}")
        return Response({'error': 'Failed to get similar content'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_study_recommendations(request):
    """Get study recommendations based on user's weak areas"""
    user = request.user
    limit = int(request.GET.get('limit', 10))
    
    try:
        # Get user's progress data to identify weak areas
        user_progress = UserProgress.objects.filter(user=user)
        
        # Find topics with low mastery levels
        weak_areas = user_progress.filter(
            mastery_level__lt=60  # Less than 60% mastery
        ).order_by('mastery_level')
        
        # Find topics with low accuracy
        low_accuracy_areas = user_progress.filter(
            total_questions_attempted__gt=5  # At least 5 attempts
        ).extra(
            select={
                'accuracy': 'CASE WHEN total_questions_attempted > 0 THEN (total_questions_correct * 100.0 / total_questions_attempted) ELSE 0 END'
            }
        ).extra(
            where=['(total_questions_correct * 100.0 / total_questions_attempted) < 70']
        ).order_by('accuracy')
        
        # Get recent AI interactions to understand user's interests
        recent_interactions = AIInteraction.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(days=14)
        ).values_list('topic', flat=True).distinct()
        
        # Build recommendations
        recommendations = []
        
        # Recommend content for weak areas
        for progress in weak_areas[:5]:
            if progress.course and progress.topic:
                weak_area_content = Content.objects.filter(
                    status='approved',
                    course=progress.course,
                    topic__icontains=progress.topic,
                    content_type__in=['question', 'material', 'note']
                ).order_by('-rating', '-view_count')[:2]
                
                recommendations.extend(weak_area_content)
        
        # Recommend content for low accuracy areas
        for progress in low_accuracy_areas[:3]:
            if progress.course and progress.topic:
                practice_content = Content.objects.filter(
                    status='approved',
                    course=progress.course,
                    topic__icontains=progress.topic,
                    content_type='question'  # Focus on practice questions
                ).order_by('-rating')[:2]
                
                recommendations.extend(practice_content)
        
        # Remove duplicates and limit results
        unique_recommendations = []
        seen_ids = set()
        
        for content in recommendations:
            if content.id not in seen_ids:
                unique_recommendations.append(content)
                seen_ids.add(content.id)
                
                if len(unique_recommendations) >= limit:
                    break
        
        serializer = ContentListSerializer(
            unique_recommendations, 
            many=True, 
            context={'request': request}
        )
        
        # Prepare improvement suggestions
        improvement_suggestions = []
        for progress in weak_areas[:3]:
            improvement_suggestions.append({
                'topic': progress.topic,
                'course': str(progress.course) if progress.course else None,
                'current_mastery': progress.mastery_level,
                'suggestion': f"Focus on {progress.topic} - current mastery is {progress.mastery_level}%"
            })
        
        return Response({
            'study_recommendations': serializer.data,
            'improvement_suggestions': improvement_suggestions,
            'weak_areas_count': weak_areas.count(),
            'low_accuracy_areas_count': low_accuracy_areas.count()
        })
        
    except Exception as e:
        logger.error(f"Error getting study recommendations for user {user.email}: {e}")
        return Response({'error': 'Failed to get study recommendations'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_content_for_exam_prep(request):
    """Get content recommendations for exam preparation"""
    user = request.user
    course_id = request.GET.get('course_id')
    exam_date = request.GET.get('exam_date')  # YYYY-MM-DD format
    limit = int(request.GET.get('limit', 15))
    
    try:
        # Get user's profile
        user_profile = getattr(user, 'student_profile', None)
        
        # Build base query
        exam_content = Content.objects.filter(status='approved')
        
        # Filter by course if provided
        if course_id:
            exam_content = exam_content.filter(course_id=course_id)
        elif user_profile:
            # Use user's enrolled courses
            user_courses = user_profile.courses.all()
            exam_content = exam_content.filter(course__in=user_courses)
        
        # If exam date is provided, prioritize based on time remaining
        if exam_date:
            try:
                from datetime import datetime
                exam_dt = datetime.strptime(exam_date, '%Y-%m-%d').date()
                today = timezone.now().date()
                days_until_exam = (exam_dt - today).days
                
                if days_until_exam <= 7:
                    # Last week: Focus on revision materials and important questions
                    exam_content = exam_content.filter(
                        Q(content_type__in=['question', 'note']) |
                        Q(topic__icontains='revision') |
                        Q(topic__icontains='important') |
                        Q(difficulty_level='intermediate')
                    )
                elif days_until_exam <= 30:
                    # Last month: Practice questions and comprehensive materials
                    exam_content = exam_content.filter(
                        content_type__in=['question', 'material']
                    )
                else:
                    # More than a month: All types of content
                    pass
                    
            except ValueError:
                pass  # Invalid date format, ignore
        
        # Get user's weak areas for targeted recommendations
        if user_profile:
            user_progress = UserProgress.objects.filter(
                user=user,
                mastery_level__lt=70  # Focus on areas needing improvement
            )
            weak_topics = list(user_progress.values_list('topic', flat=True))
            
            if weak_topics:
                # Boost content for weak topics
                weak_topic_filter = Q()
                for topic in weak_topics[:5]:
                    weak_topic_filter |= Q(topic__icontains=topic)
                exam_content = exam_content.filter(weak_topic_filter)
        
        # Order by importance for exam prep
        exam_content = exam_content.annotate(
            rating_score=Avg('ratings__rating'),
            popularity_score=Count('views')
        ).order_by(
            '-rating_score',
            '-popularity_score',
            '-created_at'
        )[:limit]
        
        serializer = ContentListSerializer(
            exam_content, 
            many=True, 
            context={'request': request}
        )
        
        # Prepare study strategy
        study_strategy = {
            'total_items': len(serializer.data),
            'recommended_daily_items': max(1, len(serializer.data) // 7),  # Spread over a week
            'focus_areas': [
                'Review weak topics',
                'Practice previous year questions',
                'Focus on high-weightage topics',
                'Regular revision'
            ]
        }
        
        if exam_date:
            try:
                exam_dt = datetime.strptime(exam_date, '%Y-%m-%d').date()
                days_remaining = (exam_dt - timezone.now().date()).days
                study_strategy['days_until_exam'] = max(0, days_remaining)
                study_strategy['intensity'] = 'high' if days_remaining <= 7 else 'medium' if days_remaining <= 30 else 'normal'
            except:
                pass
        
        return Response({
            'exam_prep_content': serializer.data,
            'study_strategy': study_strategy
        })
        
    except Exception as e:
        logger.error(f"Error getting exam prep content for user {user.email}: {e}")
        return Response({'error': 'Failed to get exam preparation content'}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])  # Allow public access for testing
def get_content_recommendations(request):
    """
    Get content recommendations for a user.
    """
    # Mock recommendation data for testing
    recommendations = [
        {
            'id': 1,
            'title': 'Advanced Mathematics Problems',
            'type': 'study_material',
            'difficulty': 'hard',
            'score': 0.95
        },
        {
            'id': 2,
            'title': 'Physics Past Papers 2023',
            'type': 'past_paper',
            'difficulty': 'medium',
            'score': 0.88
        }
    ]
    
    return Response({
        'recommendations': recommendations,
        'total': len(recommendations)
    })


@api_view(['GET'])
@permission_classes([AllowAny])  # Allow public access for testing
def get_course_recommendations(request):
    """
    Get course recommendations for a user.
    """
    # Mock course recommendation data for testing
    recommendations = [
        {
            'id': 1,
            'title': 'Data Structures',
            'department': 'Computer Science Engineering',
            'semester': 3,
            'score': 0.92
        },
        {
            'id': 2,
            'title': 'Linear Algebra',
            'department': 'Mathematics',
            'semester': 2,
            'score': 0.85
        }
    ]
    
    return Response({
        'recommendations': recommendations,
        'total': len(recommendations)
    })
