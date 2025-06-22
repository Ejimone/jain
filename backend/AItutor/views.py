from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta, datetime
import logging

from .models import (
    ChatSession, ChatMessage, StudyPlan, StudyPlanTask,
    AIInteraction, AIModelUsage
)
from .serializers import (
    ChatSessionSerializer, ChatSessionListSerializer, ChatMessageSerializer,
    ChatMessageCreateSerializer, StudyPlanSerializer, StudyPlanListSerializer,
    StudyPlanCreateSerializer, StudyPlanTaskSerializer, AIInteractionSerializer,
    ChatRequestSerializer, StudyPlanGenerationSerializer, FeedbackSerializer,
    AIAnalyticsSerializer
)

logger = logging.getLogger('AIServices')


class ChatSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for chat sessions"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ChatSessionListSerializer
        return ChatSessionSerializer
    
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user).order_by('-updated_at')
    
    def perform_create(self, serializer):
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
            AIInteraction.objects.create(
                user=request.user,
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
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StudyPlanListSerializer
        elif self.action == 'create':
            return StudyPlanCreateSerializer
        return StudyPlanSerializer
    
    def get_queryset(self):
        return StudyPlan.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def generate_plan(self, request):
        """Generate AI study plan"""
        serializer = StudyPlanGenerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Generate study plan using AI
            plan_data = self.generate_ai_study_plan(serializer.validated_data)
            
            # Create study plan
            study_plan = StudyPlan.objects.create(
                user=request.user,
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
