from rest_framework import serializers
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db.models import Avg
import base64
import uuid

from .models import (
    ChatSession, ChatMessage, StudyPlan, StudyPlanTask,
    AIInteraction, AIModelUsage, Question, PastQuestion, 
    Quiz, QuizQuestion, UserQuizSession, QuestionBank,
    DifficultyAnalysis, OnlineSource, EmbeddingVector,
    QuizCustomization, UserPerformanceAnalytics
)
from student.serializers import UserProfileSerializer, CourseSerializer
from content.serializers import ContentListSerializer


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""
    related_content = ContentListSerializer(many=True, read_only=True)
    attachment_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = '__all__'
        read_only_fields = ('session', 'tokens_used', 'response_time_ms', 'confidence_score')
    
    def get_attachment_url(self, obj):
        if obj.attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attachment.url)
        return None


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat messages"""
    attachment_base64 = serializers.CharField(write_only=True, required=False)
    attachment_name = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = ChatMessage
        fields = ['content', 'message_format', 'attachment_base64', 'attachment_name']
    
    def create(self, validated_data):
        attachment_base64 = validated_data.pop('attachment_base64', None)
        attachment_name = validated_data.pop('attachment_name', None)
        
        if attachment_base64 and attachment_name:
            # Decode base64 file
            try:
                file_data = base64.b64decode(attachment_base64)
                file_content = ContentFile(file_data, name=attachment_name)
                validated_data['attachment'] = file_content
            except Exception:
                pass  # Skip if decoding fails
        
        return super().create(validated_data)


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for chat sessions"""
    user = UserProfileSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    messages = ChatMessageSerializer(many=True, read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = '__all__'
        read_only_fields = ('user', 'total_messages', 'total_tokens_used')
    
    def get_message_count(self, obj):
        return obj.messages.count()


class ChatSessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for chat session lists"""
    user = serializers.StringRelatedField()
    course = serializers.StringRelatedField()
    duration_minutes = serializers.ReadOnlyField()
    message_count = serializers.SerializerMethodField()
    last_message_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'topic', 'user', 'course', 'is_active',
            'duration_minutes', 'message_count', 'last_message_preview',
            'created_at', 'updated_at'
        ]
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_last_message_preview(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return {
                'content': last_message.content[:100] + "..." if len(last_message.content) > 100 else last_message.content,
                'message_type': last_message.message_type,
                'created_at': last_message.created_at
            }
        return None


class StudyPlanTaskSerializer(serializers.ModelSerializer):
    """Serializer for study plan tasks"""
    content = ContentListSerializer(read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = StudyPlanTask
        fields = '__all__'
        read_only_fields = ('study_plan',)
    
    def get_is_overdue(self, obj):
        from django.utils import timezone
        if obj.due_date and obj.status != 'completed':
            return obj.due_date < timezone.now().date()
        return False


class StudyPlanSerializer(serializers.ModelSerializer):
    """Serializer for study plans"""
    user = UserProfileSerializer(read_only=True)
    courses = CourseSerializer(many=True, read_only=True)
    tasks = StudyPlanTaskSerializer(many=True, read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = StudyPlan
        fields = '__all__'
        read_only_fields = ('user', 'total_tasks', 'completed_tasks', 'ai_generated')


class StudyPlanListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for study plan lists"""
    user = serializers.StringRelatedField()
    course_count = serializers.SerializerMethodField()
    progress_percentage = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = StudyPlan
        fields = [
            'id', 'title', 'description', 'plan_type', 'status',
            'user', 'course_count', 'progress_percentage', 'days_remaining',
            'start_date', 'end_date', 'created_at'
        ]
    
    def get_course_count(self, obj):
        return obj.courses.count()


class StudyPlanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating study plans"""
    course_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = StudyPlan
        fields = [
            'title', 'description', 'plan_type', 'topics', 'goals',
            'start_date', 'end_date', 'course_ids'
        ]
    
    def create(self, validated_data):
        course_ids = validated_data.pop('course_ids', [])
        validated_data['user'] = self.context['request'].user
        
        study_plan = StudyPlan.objects.create(**validated_data)
        
        if course_ids:
            from student.models import Course
            courses = Course.objects.filter(id__in=course_ids)
            study_plan.courses.set(courses)
        
        return study_plan


class AIInteractionSerializer(serializers.ModelSerializer):
    """Serializer for AI interactions"""
    user = UserProfileSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    
    class Meta:
        model = AIInteraction
        fields = '__all__'
        read_only_fields = ('user', 'response_time_ms', 'tokens_used', 'confidence_score')


class AIModelUsageSerializer(serializers.ModelSerializer):
    """Serializer for AI model usage statistics"""
    average_response_time_ms = serializers.ReadOnlyField()
    
    class Meta:
        model = AIModelUsage
        fields = '__all__'


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for chat requests to AI"""
    message = serializers.CharField()
    session_id = serializers.UUIDField(required=False)
    course_id = serializers.UUIDField(required=False)
    topic = serializers.CharField(required=False, allow_blank=True)
    message_format = serializers.ChoiceField(
        choices=ChatMessage.MESSAGE_FORMATS,
        default='text'
    )
    attachment_base64 = serializers.CharField(required=False)
    attachment_name = serializers.CharField(required=False)
    ai_model = serializers.ChoiceField(
        choices=[
            ('gemini-pro', 'Gemini Pro'),
            ('gemini-pro-vision', 'Gemini Pro Vision'),
            ('gpt-4', 'GPT-4'),
            ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
        ],
        default='gemini-pro'
    )


class StudyPlanGenerationSerializer(serializers.Serializer):
    """Serializer for study plan generation requests"""
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    course_ids = serializers.ListField(child=serializers.UUIDField())
    topics = serializers.ListField(child=serializers.CharField(), required=False)
    goals = serializers.DictField(required=False)
    duration_weeks = serializers.IntegerField(min_value=1, max_value=52)
    study_hours_per_day = serializers.IntegerField(min_value=1, max_value=12)
    difficulty_level = serializers.ChoiceField(
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        default='intermediate'
    )
    exam_date = serializers.DateField(required=False)
    preferences = serializers.DictField(required=False)


class FeedbackSerializer(serializers.Serializer):
    """Serializer for user feedback on AI responses"""
    interaction_id = serializers.UUIDField(required=False)
    message_id = serializers.UUIDField(required=False)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    feedback = serializers.CharField(required=False, allow_blank=True)
    is_helpful = serializers.BooleanField(required=False)


class AIAnalyticsSerializer(serializers.Serializer):
    """Serializer for AI analytics data"""
    total_interactions = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    total_tokens_used = serializers.IntegerField()
    average_response_time = serializers.FloatField()
    user_satisfaction_rate = serializers.FloatField()
    most_used_models = serializers.ListField(child=serializers.DictField())
    interaction_types_breakdown = serializers.DictField()
    weekly_usage = serializers.DictField()
    top_topics = serializers.ListField(child=serializers.DictField())


# New Serializers for Quiz and Question Management

class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for questions"""
    success_rate = serializers.ReadOnlyField()
    average_solve_time = serializers.ReadOnlyField()
    course_name = serializers.CharField(source='course.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    question_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = '__all__'
        read_only_fields = (
            'id', 'difficulty_score', 'usage_count', 'correct_answers_count',
            'total_attempts', 'average_rating', 'question_embedding', 'answer_embedding',
            'created_at', 'updated_at'
        )
    
    def get_question_image_url(self, obj):
        if obj.question_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.question_image.url)
        return None


class QuestionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating questions with image upload support"""
    image_base64 = serializers.CharField(write_only=True, required=False)
    image_name = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Question
        fields = [
            'title', 'question_text', 'question_type', 'correct_answer',
            'answer_options', 'answer_explanation', 'difficulty_level',
            'course', 'topics', 'tags', 'source_type', 'source_url',
            'source_reference', 'image_base64', 'image_name'
        ]
    
    def create(self, validated_data):
        image_base64 = validated_data.pop('image_base64', None)
        image_name = validated_data.pop('image_name', None)
        
        if image_base64 and image_name:
            try:
                image_data = base64.b64decode(image_base64)
                image_content = ContentFile(image_data, name=image_name)
                validated_data['question_image'] = image_content
            except Exception:
                pass  # Skip invalid image data
        
        return super().create(validated_data)


class QuestionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for question lists"""
    success_rate = serializers.ReadOnlyField()
    course_name = serializers.CharField(source='course.name', read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'title', 'question_type', 'difficulty_level', 'difficulty_score',
            'success_rate', 'course_name', 'topics', 'tags', 'source_type',
            'is_verified', 'average_rating', 'created_at'
        ]


class PastQuestionSerializer(serializers.ModelSerializer):
    """Serializer for past questions"""
    question = QuestionSerializer(read_only=True)
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    verified_by_username = serializers.CharField(source='verified_by.username', read_only=True)
    
    class Meta:
        model = PastQuestion
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class PastQuestionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating past questions"""
    question_data = QuestionCreateSerializer(write_only=True)
    document_base64 = serializers.CharField(write_only=True, required=False)
    document_name = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = PastQuestion
        fields = [
            'exam_year', 'exam_semester', 'exam_type', 'exam_name',
            'institution', 'instructor', 'question_number', 'total_marks',
            'section', 'page_number', 'question_data', 'document_base64',
            'document_name'
        ]
    
    def create(self, validated_data):
        question_data = validated_data.pop('question_data')
        document_base64 = validated_data.pop('document_base64', None)
        document_name = validated_data.pop('document_name', None)
        
        # Create the question first
        question_serializer = QuestionCreateSerializer(data=question_data)
        question_serializer.is_valid(raise_exception=True)
        question = question_serializer.save()
        
        # Handle document upload
        if document_base64 and document_name:
            try:
                doc_data = base64.b64decode(document_base64)
                doc_content = ContentFile(doc_data, name=document_name)
                validated_data['original_document'] = doc_content
            except Exception:
                pass  # Skip invalid document data
        
        # Create past question
        validated_data['question'] = question
        return super().create(validated_data)


class QuizQuestionSerializer(serializers.ModelSerializer):
    """Serializer for quiz questions"""
    question = QuestionListSerializer(read_only=True)
    
    class Meta:
        model = QuizQuestion
        fields = '__all__'


class QuizSerializer(serializers.ModelSerializer):
    """Serializer for quizzes"""
    questions_detail = QuizQuestionSerializer(source='quizquestion_set', many=True, read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Quiz
        fields = '__all__'
        read_only_fields = ('id', 'access_code', 'created_at', 'updated_at')


class QuizCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating quizzes"""
    question_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Quiz
        fields = [
            'title', 'description', 'quiz_type', 'course', 'topics',
            'difficulty_range', 'question_types', 'total_questions',
            'time_limit', 'generation_params', 'is_public', 'question_ids'
        ]
    
    def create(self, validated_data):
        question_ids = validated_data.pop('question_ids', [])
        quiz = super().create(validated_data)
        
        # Add questions to quiz
        if question_ids:
            for i, question_id in enumerate(question_ids):
                try:
                    question = Question.objects.get(id=question_id)
                    QuizQuestion.objects.create(
                        quiz=quiz,
                        question=question,
                        order=i + 1
                    )
                except Question.DoesNotExist:
                    continue
        
        return quiz


class QuizListSerializer(serializers.ModelSerializer):
    """Simplified serializer for quiz lists"""
    course_name = serializers.CharField(source='course.name', read_only=True)
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'quiz_type', 'status', 'course_name',
            'total_questions', 'question_count', 'time_limit', 'is_public',
            'created_at'
        ]
    
    def get_question_count(self, obj):
        return obj.questions.count()


class UserQuizSessionSerializer(serializers.ModelSerializer):
    """Serializer for user quiz sessions"""
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    percentage_score = serializers.ReadOnlyField()
    average_time_per_question = serializers.ReadOnlyField()
    
    class Meta:
        model = UserQuizSession
        fields = '__all__'
        read_only_fields = (
            'id', 'score', 'total_points', 'correct_answers',
            'difficulty_performance', 'topic_performance',
            'started_at', 'completed_at', 'last_activity'
        )


class UserQuizSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for starting a quiz session"""
    
    class Meta:
        model = UserQuizSession
        fields = ['quiz']


class QuizAnswerSubmissionSerializer(serializers.Serializer):
    """Serializer for submitting quiz answers"""
    question_id = serializers.UUIDField()
    answer = serializers.CharField()
    time_taken = serializers.IntegerField(min_value=1, help_text="Time taken in seconds")


class QuizGenerationRequestSerializer(serializers.Serializer):
    """Serializer for AI quiz generation requests"""
    course_id = serializers.UUIDField()
    topics = serializers.ListField(child=serializers.CharField(), required=False)
    question_types = serializers.ListField(child=serializers.CharField(), required=False)
    difficulty_level = serializers.ChoiceField(
        choices=['beginner', 'intermediate', 'advanced', 'expert'],
        required=False
    )
    total_questions = serializers.IntegerField(min_value=1, max_value=50, default=10)
    time_limit = serializers.IntegerField(min_value=1, required=False)
    include_past_questions = serializers.BooleanField(default=True)
    online_content = serializers.BooleanField(default=False)
    quiz_type = serializers.ChoiceField(
        choices=['practice', 'mock_exam', 'topic_review', 'difficulty_test'],
        default='practice'
    )


class QuestionSearchSerializer(serializers.Serializer):
    """Serializer for question search parameters"""
    query = serializers.CharField(required=False)
    course_id = serializers.UUIDField(required=False)
    topics = serializers.ListField(child=serializers.CharField(), required=False)
    question_types = serializers.ListField(child=serializers.CharField(), required=False)
    difficulty_levels = serializers.ListField(child=serializers.CharField(), required=False)
    source_types = serializers.ListField(child=serializers.CharField(), required=False)
    year_range = serializers.DictField(required=False)  # {"min": 2020, "max": 2025}
    verified_only = serializers.BooleanField(default=False)
    min_rating = serializers.FloatField(min_value=0, max_value=5, required=False)


class QuestionBankSerializer(serializers.ModelSerializer):
    """Serializer for question bank entries"""
    question_title = serializers.CharField(source='source_question.title', read_only=True)
    
    class Meta:
        model = QuestionBank
        fields = [
            'id', 'question_title', 'embedding_model', 'embedding_dimensions',
            'similarity_matches', 'used_for_generation', 'source_quality_score',
            'created_at'
        ]
        read_only_fields = '__all__'


class UserProgressAnalyticsSerializer(serializers.Serializer):
    """Serializer for user progress analytics"""
    total_quizzes_taken = serializers.IntegerField()
    average_score = serializers.FloatField()
    improvement_trend = serializers.FloatField()
    strong_topics = serializers.ListField(child=serializers.DictField())
    weak_topics = serializers.ListField(child=serializers.DictField())
    difficulty_performance = serializers.DictField()
    recent_sessions = serializers.ListField(child=serializers.DictField())
    recommendations = serializers.ListField(child=serializers.CharField())


class DifficultyAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for question difficulty analysis"""
    
    class Meta:
        model = DifficultyAnalysis
        fields = '__all__'
        read_only_fields = ('question', 'last_updated')


class OnlineSourceSerializer(serializers.ModelSerializer):
    """Serializer for online educational sources"""
    
    class Meta:
        model = OnlineSource
        fields = '__all__'
        read_only_fields = ('last_scraped', 'error_count', 'last_error')


class EmbeddingVectorSerializer(serializers.ModelSerializer):
    """Serializer for question embeddings"""
    
    class Meta:
        model = EmbeddingVector
        fields = '__all__'
        read_only_fields = ('question', 'content_hash', 'created_at', 'updated_at')


class QuizCustomizationSerializer(serializers.ModelSerializer):
    """Serializer for user quiz customization preferences"""
    preferred_courses = CourseSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuizCustomization
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


class UserPerformanceAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for detailed user performance analytics"""
    accuracy_percentage = serializers.ReadOnlyField()
    average_time_per_question = serializers.ReadOnlyField()
    course = CourseSerializer(read_only=True)
    
    class Meta:
        model = UserPerformanceAnalytics
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


class QuestionDetailSerializer(QuestionSerializer):
    """Extended question serializer with full details"""
    difficulty_analysis = DifficultyAnalysisSerializer(read_only=True)
    embeddings = EmbeddingVectorSerializer(many=True, read_only=True)
    past_question_info = serializers.SerializerMethodField()
    
    class Meta(QuestionSerializer.Meta):
        fields = '__all__'
    
    def get_past_question_info(self, obj):
        if hasattr(obj, 'past_question_info'):
            return PastQuestionSerializer(obj.past_question_info).data
        return None


class QuizDetailSerializer(QuizSerializer):
    """Extended quiz serializer with full details including questions"""
    quiz_questions = QuizQuestionSerializer(source='quizquestion_set', many=True, read_only=True)
    analytics_data = serializers.SerializerMethodField()
    
    class Meta(QuizSerializer.Meta):
        fields = '__all__'
    
    def get_analytics_data(self, obj):
        """Get basic analytics for the quiz"""
        sessions = obj.user_sessions.filter(status='completed')
        if sessions.exists():
            return {
                'total_attempts': sessions.count(),
                'average_score': sessions.aggregate(avg_score=Avg('score'))['avg_score'] or 0,
                'completion_rate': (sessions.count() / obj.user_sessions.count()) * 100 if obj.user_sessions.exists() else 0
            }
        return {'total_attempts': 0, 'average_score': 0, 'completion_rate': 0}


class UserQuizSessionDetailSerializer(UserQuizSessionSerializer):
    """Extended session serializer with detailed information"""
    quiz = QuizSerializer(read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    time_spent_minutes = serializers.SerializerMethodField()
    
    class Meta(UserQuizSessionSerializer.Meta):
        fields = '__all__'
    
    def get_progress_percentage(self, obj):
        """Calculate completion percentage"""
        if obj.answers:
            answered = len(obj.answers)
            total = obj.quiz.total_questions
            return (answered / total) * 100 if total > 0 else 0
        return 0
    
    def get_time_spent_minutes(self, obj):
        """Calculate time spent in minutes"""
        if obj.started_at:
            end_time = obj.completed_at or timezone.now()
            duration = end_time - obj.started_at
            return round(duration.total_seconds() / 60, 2)
        return 0


