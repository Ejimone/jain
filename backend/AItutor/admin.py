from django.contrib import admin
from .models import (
    ChatSession, ChatMessage, StudyPlan, StudyPlanTask,
    AIInteraction, AIModelUsage
)


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """Chat session admin"""
    list_display = ('user', 'title', 'topic', 'is_active', 'total_messages', 'duration_minutes', 'created_at')
    list_filter = ('is_active', 'created_at', 'course')
    search_fields = ('user__email', 'title', 'topic')
    raw_id_fields = ('user', 'course')
    readonly_fields = ('total_messages', 'total_tokens_used', 'duration_minutes')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Chat message admin"""
    list_display = ('session', 'message_type', 'content_preview', 'ai_model', 'user_rating', 'created_at')
    list_filter = ('message_type', 'ai_model', 'user_rating', 'created_at')
    search_fields = ('content', 'session__title')
    raw_id_fields = ('session',)
    readonly_fields = ('tokens_used', 'response_time_ms', 'confidence_score')
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = "Content Preview"


@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    """Study plan admin"""
    list_display = ('user', 'title', 'plan_type', 'status', 'progress_percentage', 'start_date', 'end_date')
    list_filter = ('plan_type', 'status', 'ai_generated', 'created_at')
    search_fields = ('user__email', 'title', 'description')
    raw_id_fields = ('user',)
    filter_horizontal = ('courses',)
    readonly_fields = ('total_tasks', 'completed_tasks', 'progress_percentage', 'days_remaining')


@admin.register(StudyPlanTask)
class StudyPlanTaskAdmin(admin.ModelAdmin):
    """Study plan task admin"""
    list_display = ('study_plan', 'title', 'task_type', 'status', 'scheduled_date', 'progress_percentage')
    list_filter = ('task_type', 'status', 'scheduled_date')
    search_fields = ('title', 'description', 'topic')
    raw_id_fields = ('study_plan', 'content')


@admin.register(AIInteraction)
class AIInteractionAdmin(admin.ModelAdmin):
    """AI interaction admin"""
    list_display = ('user', 'interaction_type', 'ai_model', 'user_rating', 'response_time_ms', 'created_at')
    list_filter = ('interaction_type', 'ai_model', 'user_rating', 'created_at')
    search_fields = ('user__email', 'topic', 'user_input')
    raw_id_fields = ('user', 'session', 'course')
    readonly_fields = ('response_time_ms', 'tokens_used', 'confidence_score')


@admin.register(AIModelUsage)
class AIModelUsageAdmin(admin.ModelAdmin):
    """AI model usage admin"""
    list_display = ('model_name', 'date', 'total_requests', 'success_rate', 'average_response_time_ms')
    list_filter = ('model_name', 'date')
    readonly_fields = ('average_response_time_ms',)
