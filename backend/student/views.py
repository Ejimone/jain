from rest_framework import generics, status, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import login, logout
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta, datetime
import logging

from .models import (
    User, StudentProfile, Region, Department, Course, 
    StudySession, UserProgress
)
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    StudentProfileSerializer, RegionSerializer, DepartmentSerializer,
    CourseSerializer, StudySessionSerializer, UserProgressSerializer,
    UserStatsSerializer, ProfileSetupSerializer
)

logger = logging.getLogger('AIServices')


class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create auth token
        token, created = Token.objects.get_or_create(user=user)
        
        # Create empty student profile
        StudentProfile.objects.create(
            user=user,
            current_semester=1,
            enrollment_year=timezone.now().year
        )
        
        logger.info(f"New user registered: {user.email}")
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'token': token.key,
            'message': 'Registration successful'
        }, status=status.HTTP_201_CREATED)


class UserLoginView(generics.GenericAPIView):
    """User login endpoint"""
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Get or create token
        token, created = Token.objects.get_or_create(user=user)
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        logger.info(f"User logged in: {user.email}")
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'token': token.key,
            'message': 'Login successful'
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """User logout endpoint"""
    try:
        request.user.auth_token.delete()
        logger.info(f"User logged out: {request.user.email}")
        return Response({'message': 'Successfully logged out'})
    except:
        return Response({'error': 'Error logging out'}, 
                       status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile management"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for regions"""
    queryset = Region.objects.filter(is_active=True)
    serializer_class = RegionSerializer
    permission_classes = [AllowAny]


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for departments"""
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for courses"""
    queryset = Course.objects.filter(is_active=True)
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        department_id = self.request.query_params.get('department', None)
        semester = self.request.query_params.get('semester', None)
        
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if semester:
            queryset = queryset.filter(semester=semester)
            
        return queryset


class StudentProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for student profiles"""
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return StudentProfile.objects.all()
        return StudentProfile.objects.filter(user=self.request.user)

    def get_object(self):
        if hasattr(self.request.user, 'student_profile'):
            return self.request.user.student_profile
        return StudentProfile.objects.create(
            user=self.request.user,
            current_semester=1,
            enrollment_year=timezone.now().year
        )

    @action(detail=False, methods=['post'])
    def setup_profile(self, request):
        """Initial profile setup for new students"""
        serializer = ProfileSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        profile = self.get_object()
        profile.region_id = serializer.validated_data['region_id']
        profile.department_id = serializer.validated_data['department_id']
        profile.current_semester = serializer.validated_data['current_semester']
        profile.bio = serializer.validated_data.get('bio', '')
        profile.study_preferences = serializer.validated_data.get('study_preferences', {})
        profile.save()
        
        # Set courses
        course_ids = serializer.validated_data['course_ids']
        profile.courses.set(Course.objects.filter(id__in=course_ids))
        
        logger.info(f"Profile setup completed for user: {request.user.email}")
        
        return Response({
            'profile': StudentProfileSerializer(profile).data,
            'message': 'Profile setup completed successfully'
        })


class StudySessionViewSet(viewsets.ModelViewSet):
    """ViewSet for study sessions"""
    serializer_class = StudySessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StudySession.objects.filter(student=self.request.user)

    @action(detail=True, methods=['patch'])
    def end_session(self, request, pk=None):
        """End a study session and calculate duration"""
        session = self.get_object()
        
        if session.end_time:
            return Response({'error': 'Session already ended'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        session.end_time = timezone.now()
        duration = session.end_time - session.start_time
        session.duration_minutes = int(duration.total_seconds() / 60)
        session.save()
        
        # Update user progress if course and topic are available
        if session.course and session.topic:
            progress, created = UserProgress.objects.get_or_create(
                user=session.student,
                course=session.course,
                topic=session.topic
            )
            progress.update_progress(
                session.questions_attempted,
                session.questions_correct,
                session.duration_minutes
            )
        
        logger.info(f"Study session ended for user: {request.user.email}")
        
        return Response(StudySessionSerializer(session).data)


class UserProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user progress tracking"""
    serializer_class = UserProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive user statistics"""
        user = request.user
        
        # Calculate overall stats
        progress_data = UserProgress.objects.filter(user=user).aggregate(
            total_time=Sum('total_study_time_minutes'),
            total_attempted=Sum('total_questions_attempted'),
            total_correct=Sum('total_questions_correct'),
            avg_mastery=Avg('mastery_level')
        )
        
        # Recent sessions for streak calculation
        recent_sessions = StudySession.objects.filter(
            student=user,
            end_time__isnull=False,
            start_time__gte=timezone.now() - timedelta(days=30)
        ).order_by('-start_time')
        
        # Calculate current streak
        current_streak = 0
        today = timezone.now().date()
        for i in range(30):
            check_date = today - timedelta(days=i)
            if recent_sessions.filter(start_time__date=check_date).exists():
                current_streak += 1
            else:
                break
        
        # Top subjects by study time
        top_progress = UserProgress.objects.filter(user=user).order_by(
            '-total_study_time_minutes'
        )[:5]
        
        # Weekly activity
        week_ago = timezone.now() - timedelta(days=7)
        weekly_sessions = StudySession.objects.filter(
            student=user,
            start_time__gte=week_ago
        ).extra(
            select={'day': 'date(start_time)'}
        ).values('day').annotate(
            session_count=Count('id'),
            total_time=Sum('duration_minutes')
        )
        
        weekly_activity = {}
        for session in weekly_sessions:
            weekly_activity[session['day'].strftime('%Y-%m-%d')] = {
                'sessions': session['session_count'],
                'minutes': session['total_time'] or 0
            }
        
        overall_accuracy = 0
        if progress_data['total_attempted']:
            overall_accuracy = (progress_data['total_correct'] / progress_data['total_attempted']) * 100
        
        stats = {
            'total_study_time': progress_data['total_time'] or 0,
            'total_questions_attempted': progress_data['total_attempted'] or 0,
            'total_questions_correct': progress_data['total_correct'] or 0,
            'overall_accuracy': round(overall_accuracy, 2),
            'current_streak': current_streak,
            'favorite_subjects': [p.course.name for p in top_progress],
            'recent_progress': UserProgressSerializer(top_progress, many=True).data,
            'weekly_activity': weekly_activity
        }
        
        return Response(UserStatsSerializer(stats).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    """Get dashboard data for student"""
    user = request.user
    
    # Recent study sessions
    recent_sessions = StudySession.objects.filter(
        student=user,
        end_time__isnull=False
    ).order_by('-start_time')[:5]
    
    # Current progress
    current_progress = UserProgress.objects.filter(user=user).order_by('-last_activity')[:10]
    
    # Weekly stats
    week_ago = timezone.now() - timedelta(days=7)
    weekly_stats = StudySession.objects.filter(
        student=user,
        start_time__gte=week_ago,
        end_time__isnull=False
    ).aggregate(
        total_sessions=Count('id'),
        total_time=Sum('duration_minutes'),
        total_questions=Sum('questions_attempted'),
        total_correct=Sum('questions_correct')
    )
    
    return Response({
        'recent_sessions': StudySessionSerializer(recent_sessions, many=True).data,
        'current_progress': UserProgressSerializer(current_progress, many=True).data,
        'weekly_stats': weekly_stats,
        'profile': StudentProfileSerializer(user.student_profile).data if hasattr(user, 'student_profile') else None
    })
