from rest_framework import serializers
from django.core.files.base import ContentFile
import base64
import uuid

from .models import (
    ChatSession, ChatMessage, StudyPlan, StudyPlanTask,
    AIInteraction, AIModelUsage
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
