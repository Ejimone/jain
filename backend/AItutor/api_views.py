import sys
import os
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.core.cache import cache
from asgiref.sync import sync_to_async, async_to_sync
import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

# Add AI-Services to Python path for import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'AI-Services'))

try:
    from quiz_engine import ai_quiz_engine
    AI_ENGINE_AVAILABLE = True
except ImportError:
    AI_ENGINE_AVAILABLE = False
    ai_quiz_engine = None
    logging.warning("AI Quiz Engine not available - some features will be disabled")

from AItutor.models import (
    Question, PastQuestion, Quiz, QuizQuestion, UserQuizSession,
    QuestionBank, DifficultyAnalysis, OnlineSource, EmbeddingVector,
    QuizCustomization, UserPerformanceAnalytics
)
from AItutor.serializers import (
    QuestionSerializer, PastQuestionSerializer, QuizSerializer,
    QuizQuestionSerializer, UserQuizSessionSerializer, QuestionBankSerializer,
    QuizCustomizationSerializer, UserPerformanceAnalyticsSerializer
)
from student.models import Course, User
# Note: AI-Services import will be handled at runtime due to directory name with hyphen
# from AI-Services.quiz_engine import ai_quiz_engine

logger = logging.getLogger(__name__)


class QuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing questions with AI-powered features
    """
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        queryset = Question.objects.all()
        
        # Filter by course
        course_id = self.request.query_params.get('course', None)
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty', None)
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        # Filter by question type
        question_type = self.request.query_params.get('type', None)
        if question_type:
            queryset = queryset.filter(question_type=question_type)
        
        # Filter by source type
        source = self.request.query_params.get('source', None)
        if source:
            queryset = queryset.filter(source_type=source)
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(question_text__icontains=search) |
                Q(topics__contains=search)
            )
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def generate_ai_questions(self, request):
        """Generate questions using AI based on specified criteria"""
        if not AI_ENGINE_AVAILABLE:
            return Response({
                'success': False,
                'error': 'AI question generation is not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            data = request.data
            course_id = data.get('course_id')
            topics = data.get('topics', [])
            difficulty = data.get('difficulty', 'intermediate')
            count = min(int(data.get('count', 5)), 20)  # Max 20 questions
            question_types = data.get('question_types', [])
            use_real_time = data.get('use_real_time', False)
            
            # Get course if specified
            course = None
            if course_id:
                course = get_object_or_404(Course, id=course_id)
            
            # Run AI generation in a new thread to avoid async context issues
            def run_ai_generation():
                """Run AI generation in a new thread with its own event loop"""
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Run the async function in the new loop
                    questions_data = loop.run_until_complete(
                        ai_quiz_engine._generate_ai_questions(
                            course=course,
                            topics=topics,
                            difficulty=difficulty,
                            question_types=question_types,
                            count=count,
                            use_real_time=use_real_time
                        )
                    )
                    return questions_data
                finally:
                    loop.close()
            
            # Execute in a separate thread
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_ai_generation)
                questions_data = future.result(timeout=300)  # 5 minute timeout
            
            # Create Django Question objects from the AI-generated data
            questions = []
            for q_data in questions_data:
                try:
                    # Create the question
                    question = Question.objects.create(
                        title=q_data.get('title', '')[:500],
                        question_text=q_data.get('question_text', ''),
                        question_type=q_data.get('question_type', 'multiple_choice'),
                        correct_answer=q_data.get('correct_answer', ''),
                        answer_options=q_data.get('answer_options', {}),
                        answer_explanation=q_data.get('answer_explanation', ''),
                        difficulty_level=q_data.get('difficulty_level', 'intermediate'),
                        estimated_solve_time=q_data.get('estimated_solve_time', 120),
                        course=course,  # This can be None
                        topics=q_data.get('topics', []),
                        tags=q_data.get('tags', ['ai-generated']),
                        source_type=q_data.get('source_type', 'ai_generated'),
                        source_reference=q_data.get('source_reference', f"Generated by AI"),
                        created_by=None  # AI-generated questions don't have a human creator
                    )
                    questions.append(question)
                    
                    # Create difficulty analysis if available
                    if q_data.get('complexity_analysis'):
                        from AItutor.models import DifficultyAnalysis
                        complexity = q_data['complexity_analysis']
                        DifficultyAnalysis.objects.create(
                            question=question,
                            conceptual_complexity=complexity.get('conceptual_complexity', 0.5),
                            computational_complexity=complexity.get('computational_complexity', 0.5),
                            cognitive_load=complexity.get('cognitive_load', 0.5),
                            estimated_solve_time=q_data.get('estimated_solve_time', 120),
                            analysis_model='gemini-pro',
                            analysis_confidence=0.8
                        )
                        
                except Exception as e:
                    logger.warning(f"Failed to create question from AI data: {e}")
                    continue
            
            # Serialize and return
            serializer = QuestionSerializer(questions, many=True)
            
            return Response({
                'success': True,
                'count': len(questions),
                'questions': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"AI question generation failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def rate_question(self, request, pk=None):
        """Rate a question and provide feedback"""
        question = self.get_object()
        rating = request.data.get('rating')
        feedback = request.data.get('feedback', '')
        
        if not rating or not (1 <= int(rating) <= 5):
            return Response({
                'error': 'Rating must be between 1 and 5'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update question rating
        current_ratings = question.user_ratings or []
        current_ratings.append({
            'user_id': request.user.id,
            'rating': int(rating),
            'feedback': feedback,
            'timestamp': timezone.now().isoformat()
        })
        
        question.user_ratings = current_ratings
        question.rating_count = len(current_ratings)
        question.average_rating = sum(r['rating'] for r in current_ratings) / len(current_ratings)
        question.save()
        
        return Response({
            'success': True,
            'new_average_rating': question.average_rating
        })
    
    @action(detail=False, methods=['post'])
    def upload_image(self, request):
        """Upload and process question images with OCR"""
        if not AI_ENGINE_AVAILABLE:
            return Response({
                'success': False,
                'error': 'AI image processing is not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            image_file = request.FILES.get('image')
            if not image_file:
                return Response({
                    'error': 'No image file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            course_id = request.data.get('course_id')
            extract_text = request.data.get('extract_text', 'true').lower() == 'true'
            
            course = None
            if course_id:
                course = get_object_or_404(Course, id=course_id)
            
            # Process image asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                ai_quiz_engine.process_image_upload(
                    image_file=image_file,
                    user=request.user,
                    course=course,
                    extract_text=extract_text
                )
            )
            
            loop.close()
            
            # Return processing results
            response_data = {
                'success': result['success'],
                'extracted_text': result['extracted_text'],
                'ai_analysis': result['ai_analysis'],
            }
            
            if result['questions_found']:
                questions_serialized = QuestionSerializer(result['questions_found'], many=True)
                response_data['questions_created'] = questions_serialized.data
                response_data['questions_count'] = len(result['questions_found'])
            
            if result.get('error'):
                response_data['error'] = result['error']
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Image upload processing failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def search_similar(self, request):
        """Search for similar questions using embeddings"""
        if not AI_ENGINE_AVAILABLE:
            return Response({
                'success': False,
                'error': 'AI similarity search is not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        query = request.query_params.get('query', '')
        course_id = request.query_params.get('course_id')
        limit = min(int(request.query_params.get('limit', 10)), 50)
        
        if not query:
            return Response({
                'error': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get query embedding
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            query_embedding = loop.run_until_complete(
                ai_quiz_engine._get_text_embedding(query)
            )
            
            loop.close()
            
            if not query_embedding:
                return Response({
                    'error': 'Failed to generate query embedding'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # For now, return text-based search (vector search requires specialized DB)
            # In production, you'd use a vector database like Pinecone, Weaviate, or PostgreSQL with pgvector
            queryset = Question.objects.filter(
                Q(title__icontains=query) |
                Q(question_text__icontains=query) |
                Q(topics__contains=query)
            )
            
            if course_id:
                queryset = queryset.filter(course_id=course_id)
            
            questions = queryset[:limit]
            serializer = QuestionSerializer(questions, many=True)
            
            return Response({
                'success': True,
                'query': query,
                'count': len(questions),
                'questions': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Similar question search failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PastQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing past exam questions
    """
    serializer_class = PastQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = PastQuestion.objects.select_related('question', 'question__course')
        
        # Filter by year range
        year_from = self.request.query_params.get('year_from')
        year_to = self.request.query_params.get('year_to')
        
        if year_from:
            queryset = queryset.filter(exam_year__gte=int(year_from))
        if year_to:
            queryset = queryset.filter(exam_year__lte=int(year_to))
        
        # Filter by exam type
        exam_type = self.request.query_params.get('exam_type')
        if exam_type:
            queryset = queryset.filter(exam_type=exam_type)
        
        # Filter by institution
        institution = self.request.query_params.get('institution')
        if institution:
            queryset = queryset.filter(institution__icontains=institution)
        
        # Filter by verification status
        verified_only = self.request.query_params.get('verified_only')
        if verified_only and verified_only.lower() == 'true':
            queryset = queryset.filter(is_verified=True)
        
        # Sort by year (newest first) and difficulty
        sort_by = self.request.query_params.get('sort', 'year')
        if sort_by == 'year':
            queryset = queryset.order_by('-exam_year', '-created_at')
        elif sort_by == 'difficulty':
            queryset = queryset.order_by('question__difficulty_level', '-exam_year')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_year_range(self, request):
        """Get past questions grouped by year within specified range"""
        current_year = timezone.now().year
        year_from = int(request.query_params.get('year_from', current_year - 10))
        year_to = int(request.query_params.get('year_to', current_year))
        
        # Limit to maximum 10 years
        if year_to - year_from > 10:
            year_from = year_to - 10
        
        queryset = self.get_queryset().filter(
            exam_year__gte=year_from,
            exam_year__lte=year_to
        )
        
        # Group by year
        years_data = {}
        for past_question in queryset:
            year = past_question.exam_year
            if year not in years_data:
                years_data[year] = []
            
            serializer = PastQuestionSerializer(past_question)
            years_data[year].append(serializer.data)
        
        # Sort years in descending order
        sorted_years = sorted(years_data.keys(), reverse=True)
        result = [
            {
                'year': year,
                'count': len(years_data[year]),
                'questions': years_data[year]
            }
            for year in sorted_years
        ]
        
        return Response({
            'year_range': f"{year_from}-{year_to}",
            'total_years': len(result),
            'data': result
        })
    
    @action(detail=True, methods=['post'])
    def verify_question(self, request, pk=None):
        """Verify a past question (admin/instructor only)"""
        past_question = self.get_object()
        
        if not (request.user.is_staff or request.user.is_instructor):
            return Response({
                'error': 'Only staff or instructors can verify questions'
            }, status=status.HTTP_403_FORBIDDEN)
        
        verification_notes = request.data.get('notes', '')
        is_verified = request.data.get('verified', True)
        
        past_question.is_verified = is_verified
        past_question.verified_by = request.user
        past_question.verification_notes = verification_notes
        past_question.save()
        
        return Response({
            'success': True,
            'verified': is_verified,
            'verified_by': request.user.username
        })


class QuizViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing AI-generated quizzes
    """
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Quiz.objects.prefetch_related('questions', 'quizquestion_set')
        
        # Filter by user's quizzes or public quizzes
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(created_by=self.request.user) | Q(is_public=True)
            )
        
        # Filter by course
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        # Filter by quiz type
        quiz_type = self.request.query_params.get('type')
        if quiz_type:
            queryset = queryset.filter(quiz_type=quiz_type)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def generate_quiz(self, request):
        """Generate a new AI-powered quiz"""
        if not AI_ENGINE_AVAILABLE:
            return Response({
                'success': False,
                'error': 'AI quiz generation is not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            data = request.data
            
            # Extract parameters
            course_id = data.get('course_id')
            topics = data.get('topics', [])
            difficulty = data.get('difficulty', 'intermediate')
            num_questions = min(int(data.get('num_questions', 10)), 50)  # Max 50
            question_types = data.get('question_types', [])
            include_past_questions = data.get('include_past_questions', True)
            include_ai_generated = data.get('include_ai_generated', True)
            use_real_time_sources = data.get('use_real_time_sources', False)
            
            # Get course if specified
            course = None
            if course_id:
                course = get_object_or_404(Course, id=course_id)
            
            # Generate quiz asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            quiz = loop.run_until_complete(
                ai_quiz_engine.generate_quiz(
                    user=request.user,
                    course=course,
                    topics=topics,
                    difficulty=difficulty,
                    num_questions=num_questions,
                    question_types=question_types,
                    include_past_questions=include_past_questions,
                    include_ai_generated=include_ai_generated,
                    use_real_time_sources=use_real_time_sources
                )
            )
            
            loop.close()
            
            # Return serialized quiz
            serializer = QuizSerializer(quiz)
            
            return Response({
                'success': True,
                'quiz': serializer.data,
                'message': f'Quiz generated with {quiz.total_questions} questions'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def start_session(self, request, pk=None):
        """Start a new quiz session for the user"""
        quiz = self.get_object()
        
        # Check if user has an active session for this quiz
        active_session = UserQuizSession.objects.filter(
            user=request.user,
            quiz=quiz,
            status='in_progress'
        ).first()
        
        if active_session:
            serializer = UserQuizSessionSerializer(active_session)
            return Response({
                'success': True,
                'session': serializer.data,
                'message': 'Resumed existing session'
            })
        
        # Create new session
        session = UserQuizSession.objects.create(
            user=request.user,
            quiz=quiz,
            status='in_progress',
            started_at=timezone.now(),
            settings={
                'allow_review': request.data.get('allow_review', True),
                'show_explanations': request.data.get('show_explanations', True),
                'time_limit_enabled': request.data.get('time_limit_enabled', False)
            }
        )
        
        serializer = UserQuizSessionSerializer(session)
        
        return Response({
            'success': True,
            'session': serializer.data,
            'message': 'New quiz session started'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get quiz analytics and performance statistics"""
        quiz = self.get_object()
        
        # Check permission
        if quiz.created_by != request.user and not request.user.is_staff:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get session statistics
        sessions = UserQuizSession.objects.filter(quiz=quiz)
        completed_sessions = sessions.filter(status='completed')
        
        analytics_data = {
            'total_attempts': sessions.count(),
            'completed_attempts': completed_sessions.count(),
            'average_score': 0,
            'average_completion_time': 0,
            'difficulty_distribution': {},
            'question_type_distribution': {},
            'performance_by_topic': {}
        }
        
        if completed_sessions.exists():
            # Calculate averages
            analytics_data['average_score'] = completed_sessions.aggregate(
                Avg('score')
            )['score__avg'] or 0
            
            # Calculate average completion time
            completion_times = []
            for session in completed_sessions:
                if session.started_at and session.completed_at:
                    duration = session.completed_at - session.started_at
                    completion_times.append(duration.total_seconds() / 60)  # in minutes
            
            if completion_times:
                analytics_data['average_completion_time'] = sum(completion_times) / len(completion_times)
        
        # Question distribution
        quiz_questions = quiz.quizquestion_set.select_related('question')
        
        for quiz_question in quiz_questions:
            question = quiz_question.question
            
            # Difficulty distribution
            difficulty = question.difficulty_level
            analytics_data['difficulty_distribution'][difficulty] = \
                analytics_data['difficulty_distribution'].get(difficulty, 0) + 1
            
            # Question type distribution
            q_type = question.question_type
            analytics_data['question_type_distribution'][q_type] = \
                analytics_data['question_type_distribution'].get(q_type, 0) + 1
            
            # Topic distribution
            for topic in question.topics:
                analytics_data['performance_by_topic'][topic] = \
                    analytics_data['performance_by_topic'].get(topic, 0) + 1
        
        return Response({
            'success': True,
            'quiz_id': quiz.id,
            'analytics': analytics_data
        })


class UserQuizSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user quiz sessions
    """
    serializer_class = UserQuizSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own sessions
        return UserQuizSession.objects.filter(
            user=self.request.user
        ).select_related('quiz', 'quiz__course').order_by('-started_at')
    
    @action(detail=True, methods=['post'])
    def submit_answer(self, request, pk=None):
        """Submit an answer for a question in the session"""
        session = self.get_object()
        
        if session.status != 'in_progress':
            return Response({
                'error': 'Session is not active'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        question_id = request.data.get('question_id')
        answer = request.data.get('answer')
        time_taken = request.data.get('time_taken', 0)  # in seconds
        
        if not question_id or not answer:
            return Response({
                'error': 'question_id and answer are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the quiz question
            quiz_question = QuizQuestion.objects.get(
                quiz=session.quiz,
                question_id=question_id
            )
            
            # Check if answer is correct
            is_correct = self._check_answer(quiz_question.question, answer)
            
            # Update session answers
            if not session.answers:
                session.answers = {}
            
            session.answers[str(question_id)] = {
                'answer': answer,
                'is_correct': is_correct,
                'time_taken': time_taken,
                'timestamp': timezone.now().isoformat()
            }
            
            session.save()
            
            # Calculate current progress
            total_questions = session.quiz.total_questions
            answered_questions = len(session.answers)
            progress = (answered_questions / total_questions) * 100 if total_questions > 0 else 0
            
            return Response({
                'success': True,
                'is_correct': is_correct,
                'progress': round(progress, 2),
                'answered': answered_questions,
                'total': total_questions
            })
            
        except QuizQuestion.DoesNotExist:
            return Response({
                'error': 'Question not found in this quiz'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Failed to submit answer: {e}")
            return Response({
                'error': 'Failed to submit answer'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def complete_session(self, request, pk=None):
        """Complete the quiz session and calculate final score"""
        session = self.get_object()
        
        if session.status != 'in_progress':
            return Response({
                'error': 'Session is not active'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate final score
        if session.answers:
            correct_answers = sum(1 for ans in session.answers.values() if ans.get('is_correct', False))
            total_questions = len(session.answers)
            score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        else:
            score = 0
            correct_answers = 0
            total_questions = 0
        
        # Update session
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.score = score
        session.correct_answers = correct_answers
        session.total_questions_answered = total_questions
        session.save()
        
        # Update user performance analytics asynchronously
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(
                self._update_user_analytics(session)
            )
            
            loop.close()
        except Exception as e:
            logger.warning(f"Failed to update user analytics: {e}")
        
        return Response({
            'success': True,
            'final_score': score,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'session_id': session.id
        })
    
    def _check_answer(self, question: Question, user_answer: str) -> bool:
        """Check if the user's answer is correct"""
        correct_answer = question.correct_answer.strip().lower()
        user_answer = user_answer.strip().lower()
        
        if question.question_type == 'multiple_choice':
            return user_answer == correct_answer
        elif question.question_type == 'true_false':
            return user_answer in ['true', 'false'] and user_answer == correct_answer
        elif question.question_type in ['short_answer', 'fill_blank']:
            # Simple string matching (could be enhanced with fuzzy matching)
            return user_answer == correct_answer or correct_answer in user_answer
        elif question.question_type == 'numerical':
            try:
                return float(user_answer) == float(correct_answer)
            except ValueError:
                return False
        else:
            # For essay and code questions, manual grading required
            return False
    
    async def _update_user_analytics(self, session: UserQuizSession):
        """Update user performance analytics after session completion"""
        try:
            # Get or create daily analytics
            today = timezone.now().date()
            analytics, created = UserPerformanceAnalytics.objects.get_or_create(
                user=session.user,
                course=session.quiz.course,
                period_start=today,
                period_end=today,
                period_type='daily',
                defaults={
                    'total_questions_attempted': 0,
                    'total_questions_correct': 0,
                    'total_time_spent_minutes': 0,
                    'topic_performance': {},
                    'difficulty_performance': {},
                    'question_type_performance': {}
                }
            )
            
            # Update metrics
            analytics.total_questions_attempted += session.total_questions_answered
            analytics.total_questions_correct += session.correct_answers
            
            # Calculate time spent (if available)
            if session.started_at and session.completed_at:
                time_spent = (session.completed_at - session.started_at).total_seconds() / 60
                analytics.total_time_spent_minutes += int(time_spent)
            
            # Update topic and difficulty performance
            if session.answers:
                for question_id, answer_data in session.answers.items():
                    try:
                        question = Question.objects.get(id=question_id)
                        
                        # Topic performance
                        for topic in question.topics:
                            if topic not in analytics.topic_performance:
                                analytics.topic_performance[topic] = {'correct': 0, 'total': 0}
                            
                            analytics.topic_performance[topic]['total'] += 1
                            if answer_data.get('is_correct', False):
                                analytics.topic_performance[topic]['correct'] += 1
                        
                        # Difficulty performance
                        difficulty = question.difficulty_level
                        if difficulty not in analytics.difficulty_performance:
                            analytics.difficulty_performance[difficulty] = {'correct': 0, 'total': 0}
                        
                        analytics.difficulty_performance[difficulty]['total'] += 1
                        if answer_data.get('is_correct', False):
                            analytics.difficulty_performance[difficulty]['correct'] += 1
                        
                        # Question type performance
                        q_type = question.question_type
                        if q_type not in analytics.question_type_performance:
                            analytics.question_type_performance[q_type] = {'correct': 0, 'total': 0}
                        
                        analytics.question_type_performance[q_type]['total'] += 1
                        if answer_data.get('is_correct', False):
                            analytics.question_type_performance[q_type]['correct'] += 1
                            
                    except Question.DoesNotExist:
                        continue
            
            analytics.save()
            
        except Exception as e:
            logger.error(f"Failed to update user analytics: {e}")
    
    @action(detail=False, methods=['get'])
    def performance_analysis(self, request):
        """Get detailed performance analysis for the user"""
        if not AI_ENGINE_AVAILABLE:
            return Response({
                'success': False,
                'error': 'AI performance analysis is not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        course_id = request.query_params.get('course_id')
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            course = None
            if course_id:
                course = get_object_or_404(Course, id=course_id)
            
            analysis = loop.run_until_complete(
                ai_quiz_engine.analyze_user_performance(
                    user=request.user,
                    course=course
                )
            )
            
            loop.close()
            
            return Response(analysis)
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QuizCustomizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user quiz customization preferences
    """
    serializer_class = QuizCustomizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own preferences
        return QuizCustomization.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Ensure only one preference per user
        QuizCustomization.objects.filter(user=self.request.user).delete()
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def get_or_create_preferences(self, request):
        """Get user preferences or create default ones"""
        prefs, created = QuizCustomization.objects.get_or_create(
            user=request.user,
            defaults={
                'default_num_questions': 10,
                'default_difficulty': 'intermediate',
                'default_time_limit': 30,
                'adaptive_difficulty': True,
                'include_past_questions': True,
                'include_ai_generated': True,
                'include_user_uploaded': True,
                'track_performance': True,
                'show_analytics': True,
                'get_recommendations': True
            }
        )
        
        serializer = QuizCustomizationSerializer(prefs)
        
        return Response({
            'success': True,
            'preferences': serializer.data,
            'created': created
        })
