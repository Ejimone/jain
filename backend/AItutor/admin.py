from django.contrib import admin
from .models import (
    ChatSession, ChatMessage, StudyPlan, StudyPlanTask,
    AIInteraction, AIModelUsage, Question, PastQuestion,
    Quiz, QuizQuestion, UserQuizSession, QuestionBank,
    DifficultyAnalysis, OnlineSource, EmbeddingVector,
    QuizCustomization, UserPerformanceAnalytics
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
    list_display = ('user', 'title', 'plan_type', 'status', 'progress_percentage', 'start_date', 'end_date', 'days_remaining_display')
    list_filter = ('plan_type', 'status', 'ai_generated', 'created_at')
    search_fields = ('user__email', 'title', 'description')
    raw_id_fields = ('user',)
    filter_horizontal = ('courses',)
    readonly_fields = ('total_tasks', 'completed_tasks', 'progress_percentage', 'days_remaining_display')
    
    def days_remaining_display(self, obj):
        """Display days remaining with None handling"""
        days = obj.days_remaining
        if days is None:
            return "Not set"
        return f"{days} days"
    days_remaining_display.short_description = "Days Remaining"


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


# New Admin Classes for Quiz and Question Management

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Question admin"""
    list_display = (
        'title', 'question_type', 'difficulty_level', 'course', 
        'source_type', 'success_rate', 'is_verified', 'created_at'
    )
    list_filter = ('question_type', 'difficulty_level', 'source_type', 'is_verified', 'course')
    search_fields = ('title', 'question_text', 'topics', 'tags')
    raw_id_fields = ('course', 'created_by')
    readonly_fields = (
        'difficulty_score', 'usage_count', 'correct_answers_count', 
        'total_attempts', 'average_rating', 'success_rate', 'average_solve_time',
        'question_embedding', 'answer_embedding'
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'question_text', 'question_type', 'question_image')
        }),
        ('Answer Information', {
            'fields': ('correct_answer', 'answer_options', 'answer_explanation')
        }),
        ('Classification', {
            'fields': ('course', 'topics', 'tags', 'difficulty_level')
        }),
        ('Source & Attribution', {
            'fields': ('source_type', 'source_url', 'source_reference', 'created_by')
        }),
        ('Quality & Performance', {
            'fields': ('is_verified', 'difficulty_score', 'usage_count', 'success_rate', 'average_rating'),
            'classes': ('collapse',)
        }),
        ('AI Data', {
            'fields': ('extracted_text', 'question_embedding', 'answer_embedding'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['verify_questions', 'calculate_difficulty']
    
    def verify_questions(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"Verified {queryset.count()} questions.")
    verify_questions.short_description = "Verify selected questions"
    
    def calculate_difficulty(self, request, queryset):
        for question in queryset:
            question.update_difficulty_score()
        self.message_user(request, f"Updated difficulty scores for {queryset.count()} questions.")
    calculate_difficulty.short_description = "Recalculate difficulty scores"


@admin.register(PastQuestion)
class PastQuestionAdmin(admin.ModelAdmin):
    """Past question admin"""
    list_display = (
        'exam_name', 'exam_year', 'exam_type', 'question_number',
        'institution', 'is_verified', 'created_at'
    )
    list_filter = ('exam_year', 'exam_type', 'is_verified', 'institution')
    search_fields = ('exam_name', 'institution', 'instructor', 'question__title')
    raw_id_fields = ('question', 'uploaded_by', 'verified_by')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Exam Information', {
            'fields': ('exam_name', 'exam_year', 'exam_semester', 'exam_type')
        }),
        ('Institution Details', {
            'fields': ('institution', 'instructor')
        }),
        ('Question Details', {
            'fields': ('question', 'question_number', 'total_marks', 'section')
        }),
        ('Upload Information', {
            'fields': ('uploaded_by', 'original_document', 'page_number')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_by', 'verification_notes')
        })
    )


class QuizQuestionInline(admin.TabularInline):
    """Inline for quiz questions"""
    model = QuizQuestion
    extra = 0
    raw_id_fields = ('question',)
    fields = ('question', 'order', 'points', 'time_limit', 'is_bonus')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Quiz admin"""
    list_display = (
        'title', 'quiz_type', 'course', 'total_questions', 
        'status', 'is_public', 'created_at'
    )
    list_filter = ('quiz_type', 'status', 'is_public', 'course', 'ai_generated')
    search_fields = ('title', 'description', 'topics')
    raw_id_fields = ('course', 'created_by')
    readonly_fields = ('access_code', 'created_at', 'updated_at')
    inlines = [QuizQuestionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'quiz_type', 'status')
        }),
        ('Content', {
            'fields': ('course', 'topics', 'total_questions', 'time_limit')
        }),
        ('Configuration', {
            'fields': ('difficulty_range', 'question_types', 'generation_params')
        }),
        ('Access & Permissions', {
            'fields': ('is_public', 'access_code', 'created_by')
        }),
        ('AI Generation', {
            'fields': ('ai_generated',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['make_public', 'make_private', 'generate_access_codes']
    
    def make_public(self, request, queryset):
        queryset.update(is_public=True)
        self.message_user(request, f"Made {queryset.count()} quizzes public.")
    make_public.short_description = "Make selected quizzes public"
    
    def make_private(self, request, queryset):
        queryset.update(is_public=False)
        self.message_user(request, f"Made {queryset.count()} quizzes private.")
    make_private.short_description = "Make selected quizzes private"
    
    def generate_access_codes(self, request, queryset):
        for quiz in queryset:
            quiz.generate_access_code()
        self.message_user(request, f"Generated access codes for {queryset.count()} quizzes.")
    generate_access_codes.short_description = "Generate new access codes"


@admin.register(UserQuizSession)
class UserQuizSessionAdmin(admin.ModelAdmin):
    """User quiz session admin"""
    list_display = (
        'user', 'quiz', 'status', 'percentage_score', 
        'correct_answers', 'total_time_spent', 'started_at'
    )
    list_filter = ('status', 'quiz__quiz_type', 'started_at', 'completed_at')
    search_fields = ('user__email', 'quiz__title')
    raw_id_fields = ('user', 'quiz')
    readonly_fields = (
        'percentage_score', 'average_time_per_question', 'started_at', 
        'completed_at', 'last_activity'
    )
    
    fieldsets = (
        ('Session Information', {
            'fields': ('user', 'quiz', 'status', 'current_question')
        }),
        ('Results', {
            'fields': ('score', 'total_points', 'percentage_score', 'correct_answers')
        }),
        ('Timing', {
            'fields': ('total_time_spent', 'average_time_per_question', 'started_at', 'completed_at')
        }),
        ('Performance Data', {
            'fields': ('answers', 'answer_times', 'difficulty_performance', 'topic_performance'),
            'classes': ('collapse',)
        })
    )


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    """Question bank admin"""
    list_display = (
        'source_question', 'embedding_model', 'similarity_matches',
        'used_for_generation', 'source_quality_score', 'created_at'
    )
    list_filter = ('embedding_model', 'created_at')
    search_fields = ('source_question__title', 'content_hash')
    raw_id_fields = ('source_question',)
    readonly_fields = (
        'content_hash', 'question_embedding', 'answer_embedding', 
        'combined_embedding', 'created_at', 'updated_at'
    )
    
    fieldsets = (
        ('Source Information', {
            'fields': ('source_question', 'content_hash', 'source_quality_score')
        }),
        ('Embedding Data', {
            'fields': ('embedding_model', 'embedding_dimensions')
        }),
        ('Usage Statistics', {
            'fields': ('similarity_matches', 'used_for_generation')
        }),
        ('Vector Data', {
            'fields': ('question_embedding', 'answer_embedding', 'combined_embedding'),
            'classes': ('collapse',)
        })
    )


@admin.register(DifficultyAnalysis)
class DifficultyAnalysisAdmin(admin.ModelAdmin):
    """Difficulty analysis admin"""
    list_display = ('question', 'conceptual_complexity', 'computational_complexity', 'cognitive_load', 'analysis_model', 'last_updated')
    list_filter = ('analysis_model', 'last_updated')
    search_fields = ('question__title',)
    raw_id_fields = ('question',)
    readonly_fields = ('last_updated',)
    
    fieldsets = (
        ('Question Info', {
            'fields': ('question',)
        }),
        ('Complexity Analysis', {
            'fields': ('conceptual_complexity', 'computational_complexity', 'cognitive_load', 'prerequisite_knowledge')
        }),
        ('Time Estimates', {
            'fields': ('estimated_read_time', 'estimated_think_time', 'estimated_solve_time', 'estimated_review_time')
        }),
        ('Performance Data', {
            'fields': ('actual_solve_times', 'success_rates_by_skill', 'common_mistakes'),
            'classes': ('collapse',)
        }),
        ('AI Metadata', {
            'fields': ('analysis_model', 'analysis_confidence', 'last_updated'),
            'classes': ('collapse',)
        })
    )


@admin.register(OnlineSource)
class OnlineSourceAdmin(admin.ModelAdmin):
    """Online source admin"""
    list_display = ('name', 'source_type', 'quality_rating', 'is_active', 'is_verified', 'last_scraped', 'error_count')
    list_filter = ('source_type', 'quality_rating', 'is_active', 'is_verified', 'created_at')
    search_fields = ('name', 'url', 'description')
    readonly_fields = ('last_scraped', 'error_count', 'last_error', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'url', 'source_type', 'description')
        }),
        ('Content Classification', {
            'fields': ('domains', 'languages', 'question_types')
        }),
        ('Quality & Reliability', {
            'fields': ('quality_rating', 'reliability_score', 'is_verified')
        }),
        ('Scraping Configuration', {
            'fields': ('scrape_frequency_hours', 'last_scraped', 'requires_authentication', 'api_key_required', 'rate_limit_per_hour')
        }),
        ('Status & Errors', {
            'fields': ('is_active', 'error_count', 'last_error'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(EmbeddingVector)
class EmbeddingVectorAdmin(admin.ModelAdmin):
    """Embedding vector admin"""
    list_display = ('question', 'content_type', 'vector_model', 'vector_dimension', 'is_cached', 'created_at')
    list_filter = ('content_type', 'vector_model', 'is_cached', 'created_at')
    search_fields = ('question__title', 'content_hash')
    raw_id_fields = ('question',)
    readonly_fields = ('content_hash', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Question Info', {
            'fields': ('question', 'content_type')
        }),
        ('Vector Data', {
            'fields': ('vector_model', 'vector_dimension', 'similarity_threshold'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('content_hash', 'is_cached', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(QuizCustomization)
class QuizCustomizationAdmin(admin.ModelAdmin):
    """Quiz customization admin"""
    list_display = ('user', 'default_num_questions', 'default_difficulty', 'adaptive_difficulty', 'track_performance', 'created_at')
    list_filter = ('default_difficulty', 'adaptive_difficulty', 'track_performance', 'created_at')
    search_fields = ('user__email', 'user__username')
    raw_id_fields = ('user',)
    filter_horizontal = ('preferred_courses',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Default Settings', {
            'fields': ('default_num_questions', 'default_difficulty', 'default_time_limit')
        }),
        ('Preferences', {
            'fields': ('preferred_courses', 'preferred_topics', 'preferred_question_types')
        }),
        ('Difficulty Settings', {
            'fields': ('adaptive_difficulty', 'difficulty_adjustment_rate')
        }),
        ('Source Preferences', {
            'fields': ('include_past_questions', 'include_ai_generated', 'include_user_uploaded',
                      'past_questions_weight', 'ai_generated_weight', 'user_uploaded_weight')
        }),
        ('Performance Tracking', {
            'fields': ('track_performance', 'show_analytics', 'get_recommendations')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(UserPerformanceAnalytics)
class UserPerformanceAnalyticsAdmin(admin.ModelAdmin):
    """User performance analytics admin"""
    list_display = ('user', 'course', 'period_type', 'accuracy_percentage', 'total_questions_attempted', 'improvement_rate', 'period_end')
    list_filter = ('period_type', 'period_end', 'course')
    search_fields = ('user__email', 'user__username', 'course__name')
    raw_id_fields = ('user', 'course')
    readonly_fields = ('accuracy_percentage', 'average_time_per_question', 'created_at', 'updated_at')
    date_hierarchy = 'period_end'
    
    fieldsets = (
        ('User & Course', {
            'fields': ('user', 'course')
        }),
        ('Time Period', {
            'fields': ('period_start', 'period_end', 'period_type')
        }),
        ('Performance Metrics', {
            'fields': ('total_questions_attempted', 'total_questions_correct', 'total_time_spent_minutes',
                      'accuracy_percentage', 'average_time_per_question')
        }),
        ('Detailed Performance', {
            'fields': ('topic_performance', 'difficulty_performance', 'question_type_performance'),
            'classes': ('collapse',)
        }),
        ('Trends & Analysis', {
            'fields': ('improvement_rate', 'consistency_score', 'learning_velocity'),
            'classes': ('collapse',)
        }),
        ('Recommendations', {
            'fields': ('weak_topics', 'strong_topics', 'suggested_focus_areas'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
