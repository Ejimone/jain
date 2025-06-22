from django.contrib import admin
from django.utils import timezone
from .models import (
    Content, Question, StudyMaterial, ContentCategory, Tag,
    ContentRating, ContentView, ContentDownload, UserBookmark
)


@admin.register(ContentCategory)
class ContentCategoryAdmin(admin.ModelAdmin):
    """Content category admin"""
    list_display = ('name', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Tag admin"""
    list_display = ('name', 'color')
    search_fields = ('name',)


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    """Content admin"""
    list_display = ('title', 'content_type', 'author', 'course', 'status', 'view_count', 'created_at')
    list_filter = ('content_type', 'status', 'difficulty_level', 'department', 'created_at')
    search_fields = ('title', 'description', 'topic', 'keywords')
    raw_id_fields = ('author', 'course', 'department', 'region', 'category', 'reviewed_by')
    filter_horizontal = ('tags',)
    readonly_fields = ('view_count', 'download_count', 'like_count', 'created_at', 'updated_at')
    
    actions = ['approve_content', 'reject_content']
    
    def approve_content(self, request, queryset):
        queryset.update(status='approved', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f"Approved {queryset.count()} content items.")
    approve_content.short_description = "Approve selected content"
    
    def reject_content(self, request, queryset):
        queryset.update(status='rejected', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f"Rejected {queryset.count()} content items.")
    reject_content.short_description = "Reject selected content"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Question admin"""
    list_display = ('question_text_preview', 'question_type', 'marks', 'success_rate', 'attempt_count')
    list_filter = ('question_type', 'marks', 'content__course')
    search_fields = ('question_text', 'content__title')
    raw_id_fields = ('content',)
    readonly_fields = ('attempt_count', 'correct_attempt_count', 'success_rate')
    
    def question_text_preview(self, obj):
        return obj.question_text[:100] + "..." if len(obj.question_text) > 100 else obj.question_text
    question_text_preview.short_description = "Question Text"


@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    """Study material admin"""
    list_display = ('content', 'estimated_read_time')
    search_fields = ('content__title', 'summary')
    raw_id_fields = ('content',)


@admin.register(ContentRating)
class ContentRatingAdmin(admin.ModelAdmin):
    """Content rating admin"""
    list_display = ('content', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('content__title', 'user__email')
    raw_id_fields = ('content', 'user')


@admin.register(ContentView)
class ContentViewAdmin(admin.ModelAdmin):
    """Content view admin"""
    list_display = ('content', 'user', 'viewed_at', 'duration_seconds')
    list_filter = ('viewed_at',)
    search_fields = ('content__title', 'user__email')
    raw_id_fields = ('content', 'user')


@admin.register(ContentDownload)
class ContentDownloadAdmin(admin.ModelAdmin):
    """Content download admin"""
    list_display = ('content', 'user', 'downloaded_at')
    list_filter = ('downloaded_at',)
    search_fields = ('content__title', 'user__email')
    raw_id_fields = ('content', 'user')


@admin.register(UserBookmark)
class UserBookmarkAdmin(admin.ModelAdmin):
    """User bookmark admin"""
    list_display = ('user', 'content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'content__title')
    raw_id_fields = ('user', 'content')
