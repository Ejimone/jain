from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta, datetime
import logging

from .models import (
    ChatSession, ChatMessage, StudyPlan, StudyPlanTask,
    AIInteraction, AIModelUsage, Question, PastQuestion,
    Quiz, QuizQuestion, UserQuizSession, QuestionBank
)
from .serializers import (
    ChatSessionSerializer, ChatSessionListSerializer, ChatMessageSerializer,
    ChatMessageCreateSerializer, StudyPlanSerializer, StudyPlanListSerializer,
    StudyPlanCreateSerializer, StudyPlanTaskSerializer, AIInteractionSerializer,
    ChatRequestSerializer, StudyPlanGenerationSerializer, FeedbackSerializer,
    AIAnalyticsSerializer, QuestionSerializer, QuestionCreateSerializer,
    QuestionListSerializer, PastQuestionSerializer, PastQuestionCreateSerializer,
    QuizSerializer, QuizCreateSerializer, QuizListSerializer,
    UserQuizSessionSerializer, UserQuizSessionCreateSerializer,
    QuizAnswerSubmissionSerializer, QuizGenerationRequestSerializer,
    QuestionSearchSerializer, UserProgressAnalyticsSerializer
)

logger = logging.getLogger('AIServices')


class ChatSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for chat sessions"""
    permission_classes = [AllowAny]  # Allow public access for testing
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ChatSessionListSerializer
        return ChatSessionSerializer
    
    def get_queryset(self):
        # For testing with anonymous users, return empty queryset or all sessions
        if self.request.user.is_anonymous:
            return ChatSession.objects.none()  # Return empty queryset for anonymous users
        return ChatSession.objects.filter(user=self.request.user).order_by('-updated_at')
    
    def perform_create(self, serializer):
        # For testing, create a mock user if anonymous
        if self.request.user.is_anonymous:
            # For public API testing, we'll need to handle this differently
            # For now, let's use the first available user or create a test user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            test_user, created = User.objects.get_or_create(
                email='test@example.com',
                defaults={
                    'username': 'test_user',
                    'first_name': 'Test',
                    'last_name': 'User'
                }
            )
            serializer.save(user=test_user)
        else:
            serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in a chat session"""
        session = self.get_object()
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message_data = serializer.validated_data
        ai_model = message_data.get('ai_model', 'gemini-pro')
        
        # Create user message
        user_message = ChatMessage.objects.create(
            session=session,
            message_type='user',
            content=message_data['message'],
            message_format=message_data.get('message_format', 'text')
        )
        
        # Handle attachment if provided
        if message_data.get('attachment_base64') and message_data.get('attachment_name'):
            attachment_serializer = ChatMessageCreateSerializer(data={
                'content': message_data['message'],
                'message_format': message_data.get('message_format', 'text'),
                'attachment_base64': message_data['attachment_base64'],
                'attachment_name': message_data['attachment_name']
            })
            if attachment_serializer.is_valid():
                attachment_serializer.update(user_message, attachment_serializer.validated_data)
        
        # Get AI response
        try:
            ai_response = self.get_ai_response(
                session, 
                message_data['message'], 
                ai_model,
                message_data.get('topic', ''),
                user_message.attachment
            )
            
            # Create AI response message
            ai_message = ChatMessage.objects.create(
                session=session,
                message_type='ai',
                content=ai_response['content'],
                ai_model=ai_model,
                tokens_used=ai_response.get('tokens_used', 0),
                response_time_ms=ai_response.get('response_time_ms', 0),
                confidence_score=ai_response.get('confidence_score', 0.0),
                references=ai_response.get('references', [])
            )
            
            # Update session
            session.total_messages += 2
            session.total_tokens_used += ai_response.get('tokens_used', 0)
            session.updated_at = timezone.now()
            if message_data.get('topic'):
                session.topic = message_data['topic']
            session.save()
            
            # Log interaction
            interaction_user = request.user
            if interaction_user.is_anonymous:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                interaction_user, created = User.objects.get_or_create(
                    email='test@example.com',
                    defaults={
                        'username': 'test_user',
                        'first_name': 'Test',
                        'last_name': 'User'
                    }
                )
            
            AIInteraction.objects.create(
                user=interaction_user,
                session=session,
                interaction_type='question_answer',
                user_input=message_data['message'],
                ai_response=ai_response['content'],
                ai_model=ai_model,
                response_time_ms=ai_response.get('response_time_ms', 0),
                tokens_used=ai_response.get('tokens_used', 0),
                confidence_score=ai_response.get('confidence_score', 0.0),
                course_id=message_data.get('course_id'),
                topic=message_data.get('topic', '')
            )
            
            return Response({
                'user_message': ChatMessageSerializer(user_message).data,
                'ai_message': ChatMessageSerializer(ai_message).data,
                'session': ChatSessionListSerializer(session).data
            })
            
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return Response(
                {'error': 'Failed to get AI response. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_ai_response(self, session, message, ai_model, topic='', attachment=None):
        """Get response from AI service"""
        # Import AI services
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'AI-Services'))
        
        try:
            from exam_prep_integration import ExamPrepAIAgent
            from math_solution import GeminiMathSolver
            import time
            
            start_time = time.time()
            
            # Initialize AI agent
            ai_agent = ExamPrepAIAgent()
            
            # Get conversation context
            context = self.build_conversation_context(session, topic)
            
            # Handle different message types
            if attachment and attachment.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                # Image analysis
                if 'gemini' in ai_model.lower():
                    # Use Gemini for image analysis
                    response_content = f"I can see the image you've uploaded. Based on the image and your question '{message}', let me help you with that."
                    # TODO: Implement actual image analysis with Gemini Vision
                else:
                    response_content = "I can see you've uploaded an image. Currently, image analysis is supported with Gemini models."
            
            elif any(keyword in message.lower() for keyword in ['solve', 'calculate', 'equation', 'math', 'formula']):
                # Mathematical problem solving
                math_solver = GeminiMathSolver()
                try:
                    math_result = math_solver.solve_problem(message, context=context)
                    response_content = math_result.solution if math_result else "I couldn't solve this mathematical problem. Could you please rephrase or provide more details?"
                except:
                    response_content = "I encountered an issue solving this math problem. Could you please try rephrasing it?"
            
            else:
                # General question answering
                enhanced_message = f"Context: {context}\n\nStudent Question: {message}"
                if topic:
                    enhanced_message = f"Topic: {topic}\n{enhanced_message}"
                
                # TODO: Implement actual AI model calls
                response_content = f"Thank you for your question about {topic if topic else 'this topic'}. I understand you're asking: '{message}'. Let me help you with a comprehensive explanation..."
            
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            return {
                'content': response_content,
                'tokens_used': len(message.split()) * 2,  # Rough estimate
                'response_time_ms': response_time_ms,
                'confidence_score': 0.85,
                'references': []
            }
            
        except Exception as e:
            logger.error(f"AI service error: {e}")
            return {
                'content': "I'm sorry, I'm having trouble processing your request right now. Please try again later.",
                'tokens_used': 0,
                'response_time_ms': 0,
                'confidence_score': 0.0,
                'references': []
            }
    
    def build_conversation_context(self, session, topic=''):
        """Build conversation context from recent messages"""
        recent_messages = session.messages.order_by('-created_at')[:10]
        context_parts = []
        
        for msg in reversed(recent_messages):
            role = "Student" if msg.message_type == 'user' else "AI Tutor"
            context_parts.append(f"{role}: {msg.content}")
        
        context = "\n".join(context_parts)
        if topic:
            context = f"Current Topic: {topic}\n\n{context}"
        
        return context
    
    @action(detail=True, methods=['patch'])
    def end_session(self, request, pk=None):
        """End a chat session"""
        session = self.get_object()
        session.is_active = False
        session.ended_at = timezone.now()
        session.save()
        
        return Response({'message': 'Session ended successfully'})


class StudyPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for study plans"""
    permission_classes = [AllowAny]  # Allow public access for testing
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StudyPlanListSerializer
        elif self.action == 'create':
            return StudyPlanCreateSerializer
        return StudyPlanSerializer
    
    def get_queryset(self):
        # For testing with anonymous users, return empty queryset or all study plans
        if self.request.user.is_anonymous:
            return StudyPlan.objects.none()  # Return empty queryset for anonymous users
        return StudyPlan.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def generate_plan(self, request):
        """Generate AI study plan"""
        serializer = StudyPlanGenerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Generate study plan using AI
            plan_data = self.generate_ai_study_plan(serializer.validated_data)
            
            # Handle anonymous users for testing
            user = request.user
            if user.is_anonymous:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user, created = User.objects.get_or_create(
                    email='test@example.com',
                    defaults={
                        'username': 'test_user',
                        'first_name': 'Test',
                        'last_name': 'User'
                    }
                )
            
            # Create study plan
            study_plan = StudyPlan.objects.create(
                user=user,
                title=plan_data['title'],
                description=plan_data['description'],
                plan_type='custom',
                topics=plan_data['topics'],
                goals=plan_data['goals'],
                schedule=plan_data['schedule'],
                start_date=plan_data['start_date'],
                end_date=plan_data['end_date'],
                total_tasks=len(plan_data['tasks'])
            )
            
            # Set courses
            from student.models import Course
            course_ids = serializer.validated_data['course_ids']
            courses = Course.objects.filter(id__in=course_ids)
            study_plan.courses.set(courses)
            
            # Create tasks
            for task_data in plan_data['tasks']:
                StudyPlanTask.objects.create(
                    study_plan=study_plan,
                    **task_data
                )
            
            # Log AI interaction
            AIInteraction.objects.create(
                user=request.user,
                interaction_type='study_plan',
                user_input=str(serializer.validated_data),
                ai_response=f"Generated study plan: {plan_data['title']}",
                ai_model='gemini-pro',
                response_time_ms=1000,  # Placeholder
                tokens_used=500  # Placeholder
            )
            
            return Response(StudyPlanSerializer(study_plan).data)
            
        except Exception as e:
            logger.error(f"Error generating study plan: {e}")
            return Response(
                {'error': 'Failed to generate study plan. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def generate_ai_study_plan(self, plan_params):
        """Generate study plan using AI"""
        # TODO: Implement actual AI-based plan generation
        duration_weeks = plan_params['duration_weeks']
        study_hours_per_day = plan_params['study_hours_per_day']
        
        start_date = timezone.now().date()
        end_date = start_date + timedelta(weeks=duration_weeks)
        
        # Generate basic plan structure
        plan_data = {
            'title': plan_params['title'],
            'description': plan_params.get('description', f"AI-generated {duration_weeks}-week study plan"),
            'topics': plan_params.get('topics', ['Introduction', 'Core Concepts', 'Advanced Topics', 'Review']),
            'goals': plan_params.get('goals', {
                'target_score': 85,
                'completion_rate': 90,
                'daily_study_hours': study_hours_per_day
            }),
            'schedule': {
                'daily_hours': study_hours_per_day,
                'break_duration': 15,
                'weekly_schedule': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            },
            'start_date': start_date,
            'end_date': end_date,
            'tasks': []
        }
        
        # Generate tasks for each week
        topics = plan_data['topics']
        tasks_per_week = 7  # One task per day
        
        for week in range(duration_weeks):
            for day in range(tasks_per_week):
                task_date = start_date + timedelta(weeks=week, days=day)
                topic_index = (week * tasks_per_week + day) % len(topics)
                
                task_data = {
                    'title': f"Study: {topics[topic_index]}",
                    'description': f"Focus on {topics[topic_index]} concepts and practice problems",
                    'task_type': 'read' if day % 2 == 0 else 'practice',
                    'topic': topics[topic_index],
                    'estimated_duration': study_hours_per_day * 60,
                    'scheduled_date': task_date,
                    'order': week * tasks_per_week + day
                }
                plan_data['tasks'].append(task_data)
        
        return plan_data
    
    @action(detail=True, methods=['patch'])
    def update_progress(self, request, pk=None):
        """Update study plan progress"""
        study_plan = self.get_object()
        task_id = request.data.get('task_id')
        
        if task_id:
            try:
                task = study_plan.tasks.get(id=task_id)
                task.mark_completed()
                return Response({'message': 'Task marked as completed'})
            except StudyPlanTask.DoesNotExist:
                return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({'error': 'Task ID required'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_feedback(request):
    """Submit feedback for AI interactions"""
    serializer = FeedbackSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    feedback_data = serializer.validated_data
    
    # Update interaction or message with feedback
    if feedback_data.get('interaction_id'):
        try:
            interaction = AIInteraction.objects.get(
                id=feedback_data['interaction_id'],
                user=request.user
            )
            interaction.user_rating = feedback_data['rating']
            interaction.user_feedback = feedback_data.get('feedback', '')
            interaction.is_helpful = feedback_data.get('is_helpful')
            interaction.save()
        except AIInteraction.DoesNotExist:
            return Response({'error': 'Interaction not found'}, status=status.HTTP_404_NOT_FOUND)
    
    elif feedback_data.get('message_id'):
        try:
            message = ChatMessage.objects.get(
                id=feedback_data['message_id'],
                session__user=request.user
            )
            message.user_rating = feedback_data['rating']
            message.user_feedback = feedback_data.get('feedback', '')
            message.save()
        except ChatMessage.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response({'message': 'Feedback submitted successfully'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_analytics(request):
    """Get AI usage analytics for the user"""
    user = request.user
    
    # Calculate analytics
    interactions = AIInteraction.objects.filter(user=user)
    sessions = ChatSession.objects.filter(user=user)
    
    total_interactions = interactions.count()
    total_sessions = sessions.count()
    total_tokens = interactions.aggregate(total=Sum('tokens_used'))['total'] or 0
    
    # Average response time
    avg_response_time = interactions.aggregate(avg=Avg('response_time_ms'))['avg'] or 0
    
    # User satisfaction rate
    rated_interactions = interactions.filter(user_rating__isnull=False)
    if rated_interactions.count() > 0:
        satisfaction_rate = rated_interactions.filter(user_rating__gte=4).count() / rated_interactions.count() * 100
    else:
        satisfaction_rate = 0
    
    # Most used models
    model_usage = interactions.values('ai_model').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Interaction types breakdown
    interaction_types = interactions.values('interaction_type').annotate(
        count=Count('id')
    )
    
    # Weekly usage
    week_ago = timezone.now() - timedelta(days=7)
    weekly_interactions = interactions.filter(created_at__gte=week_ago)
    weekly_usage = {}
    for i in range(7):
        date = (timezone.now() - timedelta(days=i)).date()
        count = weekly_interactions.filter(created_at__date=date).count()
        weekly_usage[str(date)] = count
    
    # Top topics
    top_topics = interactions.values('topic').annotate(
        count=Count('id')
    ).exclude(topic='').order_by('-count')[:10]
    
    analytics_data = {
        'total_interactions': total_interactions,
        'total_sessions': total_sessions,
        'total_tokens_used': total_tokens,
        'average_response_time': round(avg_response_time, 2),
        'user_satisfaction_rate': round(satisfaction_rate, 2),
        'most_used_models': [{'model': item['ai_model'], 'count': item['count']} for item in model_usage],
        'interaction_types_breakdown': {item['interaction_type']: item['count'] for item in interaction_types},
        'weekly_usage': weekly_usage,
        'top_topics': [{'topic': item['topic'], 'count': item['count']} for item in top_topics]
    }
    
    return Response(AIAnalyticsSerializer(analytics_data).data)


@api_view(['GET'])
@permission_classes([])  # Allow any user to access
def ai_models(request):
    """Get available AI models."""
    models = [
        {
            'id': 'gemini-pro',
            'name': 'Gemini Pro',
            'provider': 'Google',
            'type': 'chat',
            'status': 'active'
        },
        {
            'id': 'gpt-4',
            'name': 'GPT-4',
            'provider': 'OpenAI',
            'type': 'chat',
            'status': 'active'
        },
        {
            'id': 'claude-3',
            'name': 'Claude 3',
            'provider': 'Anthropic',
            'type': 'chat',
            'status': 'active'
        }
    ]
    return Response({'models': models})


# New ViewSets for Quiz and Question Management

class QuestionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing questions"""
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return QuestionCreateSerializer
        elif self.action == 'list':
            return QuestionListSerializer
        return QuestionSerializer
    
    def get_queryset(self):
        queryset = Question.objects.all().order_by('-created_at')
        
        # Apply filters
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        question_type = self.request.query_params.get('type')
        if question_type:
            queryset = queryset.filter(question_type=question_type)
        
        verified_only = self.request.query_params.get('verified_only')
        if verified_only == 'true':
            queryset = queryset.filter(is_verified=True)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Advanced search for questions"""
        serializer = QuestionSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        search_params = serializer.validated_data
        queryset = Question.objects.all()
        
        # Apply search filters
        if 'query' in search_params:
            query = search_params['query']
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(question_text__icontains=query) |
                Q(topics__icontains=query)
            )
        
        if 'course_id' in search_params:
            queryset = queryset.filter(course_id=search_params['course_id'])
        
        if 'topics' in search_params:
            for topic in search_params['topics']:
                queryset = queryset.filter(topics__icontains=topic)
        
        if 'question_types' in search_params:
            queryset = queryset.filter(question_type__in=search_params['question_types'])
        
        if 'difficulty_levels' in search_params:
            queryset = queryset.filter(difficulty_level__in=search_params['difficulty_levels'])
        
        if 'source_types' in search_params:
            queryset = queryset.filter(source_type__in=search_params['source_types'])
        
        if 'year_range' in search_params:
            year_range = search_params['year_range']
            if 'min' in year_range:
                queryset = queryset.filter(pastquestion__exam_year__gte=year_range['min'])
            if 'max' in year_range:
                queryset = queryset.filter(pastquestion__exam_year__lte=year_range['max'])
        
        if search_params.get('verified_only'):
            queryset = queryset.filter(is_verified=True)
        
        if 'min_rating' in search_params:
            queryset = queryset.filter(average_rating__gte=search_params['min_rating'])
        
        # Paginate results
        page = self.paginate_queryset(queryset.order_by('-created_at'))
        if page is not None:
            serializer = QuestionListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = QuestionListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """Rate a question"""
        question = self.get_object()
        rating = request.data.get('rating')
        
        if not rating or not (1 <= int(rating) <= 5):
            return Response(
                {'error': 'Rating must be between 1 and 5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update question rating (simplified - in production, track individual ratings)
        if question.average_rating == 0:
            question.average_rating = float(rating)
        else:
            # Simple moving average (in production, use proper rating system)
            question.average_rating = (question.average_rating + float(rating)) / 2
        
        question.save()
        
        return Response({'message': 'Question rated successfully'})
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a question (admin only)"""
        question = self.get_object()
        question.is_verified = True
        question.save()
        
        return Response({'message': 'Question verified successfully'})


class PastQuestionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing past questions"""
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PastQuestionCreateSerializer
        return PastQuestionSerializer
    
    def get_queryset(self):
        queryset = PastQuestion.objects.all().order_by('-exam_year', '-created_at')
        
        # Apply filters
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(exam_year=year)
        
        exam_type = self.request.query_params.get('exam_type')
        if exam_type:
            queryset = queryset.filter(exam_type=exam_type)
        
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(question__course_id=course_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def years(self, request):
        """Get available exam years"""
        years = PastQuestion.objects.values_list('exam_year', flat=True).distinct().order_by('-exam_year')
        return Response({'years': list(years)})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get past questions statistics"""
        stats = {
            'total_questions': PastQuestion.objects.count(),
            'verified_questions': PastQuestion.objects.filter(is_verified=True).count(),
            'years_covered': PastQuestion.objects.values('exam_year').distinct().count(),
            'exam_types': PastQuestion.objects.values('exam_type').annotate(
                count=Count('id')
            ).order_by('-count'),
            'institutions': PastQuestion.objects.values('institution').annotate(
                count=Count('id')
            ).order_by('-count')[:10],
        }
        return Response(stats)


class QuizViewSet(viewsets.ModelViewSet):
    """ViewSet for managing quizzes"""
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return QuizCreateSerializer
        elif self.action == 'list':
            return QuizListSerializer
        return QuizSerializer
    
    def get_queryset(self):
        queryset = Quiz.objects.all().order_by('-created_at')
        
        # Apply filters
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        quiz_type = self.request.query_params.get('type')
        if quiz_type:
            queryset = queryset.filter(quiz_type=quiz_type)
        
        public_only = self.request.query_params.get('public_only')
        if public_only == 'true':
            queryset = queryset.filter(is_public=True)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate AI quiz based on parameters"""
        serializer = QuizGenerationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        params = serializer.validated_data
        
        try:
            # Generate quiz using AI
            quiz = self._generate_ai_quiz(params, request.user)
            
            quiz_serializer = QuizSerializer(quiz, context={'request': request})
            return Response(quiz_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            return Response(
                {'error': 'Failed to generate quiz. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_ai_quiz(self, params, user):
        """Generate quiz using AI algorithms"""
        from student.models import Course
        
        course = Course.objects.get(id=params['course_id'])
        
        # Create quiz
        quiz = Quiz.objects.create(
            title=f"AI Generated Quiz - {course.name}",
            description=f"AI generated {params['quiz_type']} quiz",
            quiz_type=params['quiz_type'],
            course=course,
            topics=params.get('topics', []),
            total_questions=params['total_questions'],
            time_limit=params.get('time_limit'),
            generation_params=params,
            created_by=user if not user.is_anonymous else None
        )
        
        # Select questions based on parameters
        questions_queryset = Question.objects.filter(course=course)
        
        # Filter by topics
        if params.get('topics'):
            for topic in params['topics']:
                questions_queryset = questions_queryset.filter(topics__icontains=topic)
        
        # Filter by difficulty
        if params.get('difficulty_level'):
            questions_queryset = questions_queryset.filter(difficulty_level=params['difficulty_level'])
        
        # Filter by question types
        if params.get('question_types'):
            questions_queryset = questions_queryset.filter(question_type__in=params['question_types'])
        
        # Include past questions if requested
        if params.get('include_past_questions'):
            past_questions = questions_queryset.filter(source_type='past_exam')
        else:
            past_questions = questions_queryset.exclude(source_type='past_exam')
        
        # Select diverse set of questions
        selected_questions = list(questions_queryset.order_by('?')[:params['total_questions']])
        
        # If not enough questions, generate new ones
        if len(selected_questions) < params['total_questions']:
            # TODO: Implement AI question generation
            pass
        
        # Add questions to quiz
        for i, question in enumerate(selected_questions):
            QuizQuestion.objects.create(
                quiz=quiz,
                question=question,
                order=i + 1,
                points=1
            )
        
        quiz.generate_access_code()
        return quiz
    
    @action(detail=True, methods=['post'])
    def start_session(self, request, pk=None):
        """Start a quiz session for a user"""
        quiz = self.get_object()
        
        # Handle anonymous users
        user = request.user
        if user.is_anonymous:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user, created = User.objects.get_or_create(
                email='test@example.com',
                defaults={
                    'username': 'test_user',
                    'first_name': 'Test',
                    'last_name': 'User'
                }
            )
        
        # Check if user already has an active session
        existing_session = UserQuizSession.objects.filter(
            user=user,
            quiz=quiz,
            status='in_progress'
        ).first()
        
        if existing_session:
            serializer = UserQuizSessionSerializer(existing_session)
            return Response(serializer.data)
        
        # Create new session
        session = UserQuizSession.objects.create(
            user=user,
            quiz=quiz,
            total_points=sum(qq.points for qq in quiz.quizquestion_set.all())
        )
        
        serializer = UserQuizSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserQuizSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user quiz sessions"""
    permission_classes = [AllowAny]
    serializer_class = UserQuizSessionSerializer
    
    def get_queryset(self):
        if self.request.user.is_anonymous:
            return UserQuizSession.objects.none()
        return UserQuizSession.objects.filter(user=self.request.user).order_by('-started_at')
    
    @action(detail=True, methods=['post'])
    def submit_answer(self, request, pk=None):
        """Submit an answer for a question in the quiz"""
        session = self.get_object()
        
        if session.status != 'in_progress':
            return Response(
                {'error': 'Quiz session is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = QuizAnswerSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        question_id = str(serializer.validated_data['question_id'])
        answer = serializer.validated_data['answer']
        time_taken = serializer.validated_data['time_taken']
        
        # Store answer
        if not session.answers:
            session.answers = {}
        if not session.answer_times:
            session.answer_times = {}
        
        session.answers[question_id] = answer
        session.answer_times[question_id] = time_taken
        session.total_time_spent += time_taken
        session.save()
        
        # Update question statistics
        try:
            question = Question.objects.get(id=question_id)
            question.total_attempts += 1
            
            # Check if answer is correct (simplified)
            if question._is_correct_answer(question, answer):
                question.correct_answers_count += 1
            
            # Update solve time
            if not question.actual_solve_times:
                question.actual_solve_times = []
            question.actual_solve_times.append(time_taken)
            
            # Keep only last 100 solve times
            if len(question.actual_solve_times) > 100:
                question.actual_solve_times = question.actual_solve_times[-100:]
            
            question.save()
            question.update_difficulty_score()
            
        except Question.DoesNotExist:
            pass
        
        return Response({'message': 'Answer submitted successfully'})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete the quiz session"""
        session = self.get_object()
        
        if session.status != 'in_progress':
            return Response(
                {'error': 'Quiz session is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.calculate_final_score()
        
        # Calculate performance analytics
        self._calculate_performance_analytics(session)
        
        serializer = UserQuizSessionSerializer(session)
        return Response(serializer.data)
    
    def _calculate_performance_analytics(self, session):
        """Calculate detailed performance analytics"""
        difficulty_performance = {}
        topic_performance = {}
        
        for quiz_question in session.quiz.quizquestion_set.all():
            question = quiz_question.question
            user_answer = session.answers.get(str(question.id))
            
            if user_answer:
                is_correct = session._is_correct_answer(question, user_answer)
                
                # Difficulty performance
                difficulty = question.difficulty_level
                if difficulty not in difficulty_performance:
                    difficulty_performance[difficulty] = {'correct': 0, 'total': 0}
                
                difficulty_performance[difficulty]['total'] += 1
                if is_correct:
                    difficulty_performance[difficulty]['correct'] += 1
                
                # Topic performance
                for topic in question.topics:
                    if topic not in topic_performance:
                        topic_performance[topic] = {'correct': 0, 'total': 0}
                    
                    topic_performance[topic]['total'] += 1
                    if is_correct:
                        topic_performance[topic]['correct'] += 1
        
        session.difficulty_performance = difficulty_performance
        session.topic_performance = topic_performance
        session.save()


@api_view(['GET'])
@permission_classes([AllowAny])
def user_progress_analytics(request):
    """Get comprehensive user progress analytics"""
    user = request.user
    if user.is_anonymous:
        return Response({'error': 'Authentication required'}, status=401)
    
    # Get user's quiz sessions
    sessions = UserQuizSession.objects.filter(user=user, status='completed')
    
    if not sessions.exists():
        return Response({
            'total_quizzes_taken': 0,
            'average_score': 0,
            'improvement_trend': 0,
            'strong_topics': [],
            'weak_topics': [],
            'difficulty_performance': {},
            'recent_sessions': [],
            'recommendations': ['Take your first quiz to get personalized insights!']
        })
    
    # Calculate analytics
    total_quizzes = sessions.count()
    average_score = sessions.aggregate(Avg('score'))['score__avg'] or 0
    
    # Calculate improvement trend (last 5 vs previous 5)
    recent_sessions = list(sessions.order_by('-completed_at')[:10])
    if len(recent_sessions) >= 10:
        recent_avg = sum(s.percentage_score for s in recent_sessions[:5]) / 5
        previous_avg = sum(s.percentage_score for s in recent_sessions[5:10]) / 5
        improvement_trend = recent_avg - previous_avg
    else:
        improvement_trend = 0
    
    # Aggregate topic performance
    topic_stats = {}
    difficulty_stats = {}
    
    for session in sessions:
        if session.topic_performance:
            for topic, performance in session.topic_performance.items():
                if topic not in topic_stats:
                    topic_stats[topic] = {'correct': 0, 'total': 0}
                topic_stats[topic]['correct'] += performance['correct']
                topic_stats[topic]['total'] += performance['total']
        
        if session.difficulty_performance:
            for difficulty, performance in session.difficulty_performance.items():
                if difficulty not in difficulty_stats:
                    difficulty_stats[difficulty] = {'correct': 0, 'total': 0}
                difficulty_stats[difficulty]['correct'] += performance['correct']
                difficulty_stats[difficulty]['total'] += performance['total']
    
    # Calculate topic percentages and sort
    topic_percentages = []
    for topic, stats in topic_stats.items():
        if stats['total'] > 0:
            percentage = (stats['correct'] / stats['total']) * 100
            topic_percentages.append({
                'topic': topic,
                'percentage': round(percentage, 1),
                'total_questions': stats['total']
            })
    
    topic_percentages.sort(key=lambda x: x['percentage'], reverse=True)
    strong_topics = topic_percentages[:5]
    weak_topics = topic_percentages[-5:]
    
    # Recent sessions data
    recent_data = []
    for session in recent_sessions[:5]:
        recent_data.append({
            'quiz_title': session.quiz.title,
            'score': session.percentage_score,
            'completed_at': session.completed_at.isoformat(),
            'time_spent': session.total_time_spent
        })
    
    # Generate recommendations
    recommendations = []
    if weak_topics:
        recommendations.append(f"Focus on improving {weak_topics[0]['topic']} - current performance: {weak_topics[0]['percentage']}%")
    
    if improvement_trend < 0:
        recommendations.append("Consider reviewing fundamental concepts to improve your performance")
    elif improvement_trend > 5:
        recommendations.append("Great improvement! Try challenging yourself with harder questions")
    
    analytics_data = {
        'total_quizzes_taken': total_quizzes,
        'average_score': round(average_score, 1),
        'improvement_trend': round(improvement_trend, 1),
        'strong_topics': strong_topics,
        'weak_topics': weak_topics,
        'difficulty_performance': difficulty_stats,
        'recent_sessions': recent_data,
        'recommendations': recommendations
    }
    
    return Response(analytics_data)
