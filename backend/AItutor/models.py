from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from student.models import User, Course
from content.models import Content
import uuid
import json


class ChatSession(models.Model):
    """Model for AI tutor chat sessions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=255, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.CharField(max_length=200, blank=True)
    
    # Session metadata
    is_active = models.BooleanField(default=True)
    session_data = models.JSONField(default=dict, blank=True)  # Store session context
    total_messages = models.PositiveIntegerField(default=0)
    total_tokens_used = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title or 'Chat Session'}"

    @property
    def duration_minutes(self):
        """Calculate session duration in minutes"""
        end_time = self.ended_at or timezone.now()
        duration = end_time - self.created_at
        return int(duration.total_seconds() / 60)


class ChatMessage(models.Model):
    """Model for individual chat messages"""
    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('ai', 'AI Response'),
        ('system', 'System Message'),
    ]
    
    MESSAGE_FORMATS = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('code', 'Code'),
        ('math', 'Mathematical Expression'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    message_format = models.CharField(max_length=10, choices=MESSAGE_FORMATS, default='text')
    
    # File attachments
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    
    # AI response metadata
    ai_model = models.CharField(max_length=50, blank=True)  # e.g., 'gemini-pro', 'gpt-4'
    tokens_used = models.PositiveIntegerField(default=0)
    response_time_ms = models.PositiveIntegerField(default=0)
    confidence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # References and citations
    related_content = models.ManyToManyField(Content, blank=True, related_name='referenced_in_chat')
    references = models.JSONField(default=list, blank=True)  # External references
    
    # User feedback
    user_rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    user_feedback = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_message_type_display()}: {self.content[:50]}..."


class StudyPlan(models.Model):
    """AI-generated study plans for users"""
    PLAN_TYPES = [
        ('exam_prep', 'Exam Preparation'),
        ('topic_mastery', 'Topic Mastery'),
        ('revision', 'Revision Plan'),
        ('custom', 'Custom Plan'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_plans')
    title = models.CharField(max_length=255)
    description = models.TextField()
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Plan content
    courses = models.ManyToManyField(Course, related_name='study_plans')
    topics = models.JSONField(default=list)  # List of topics to cover
    goals = models.JSONField(default=dict)  # Learning goals and targets
    schedule = models.JSONField(default=dict)  # Study schedule
    
    # Progress tracking
    total_tasks = models.PositiveIntegerField(default=0)
    completed_tasks = models.PositiveIntegerField(default=0)
    
    # AI metadata
    ai_generated = models.BooleanField(default=True)
    generation_params = models.JSONField(default=dict)  # Parameters used for generation
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        db_table = 'study_plans'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    @property
    def progress_percentage(self):
        """Calculate completion percentage"""
        if self.total_tasks == 0:
            return 0
        return round((self.completed_tasks / self.total_tasks) * 100, 2)

    @property
    def days_remaining(self):
        """Calculate days remaining for the plan"""
        today = timezone.now().date()
        if self.end_date < today:
            return 0
        return (self.end_date - today).days


class StudyPlanTask(models.Model):
    """Individual tasks within a study plan"""
    TASK_TYPES = [
        ('read', 'Reading'),
        ('practice', 'Practice Questions'),
        ('video', 'Watch Video'),
        ('review', 'Review Notes'),
        ('assignment', 'Assignment'),
        ('quiz', 'Quiz'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    study_plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Task content
    content = models.ForeignKey(Content, on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.CharField(max_length=200)
    estimated_duration = models.PositiveIntegerField(help_text="Estimated duration in minutes")
    actual_duration = models.PositiveIntegerField(default=0, help_text="Actual time spent in minutes")
    
    # Scheduling
    scheduled_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    # Progress
    progress_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'study_plan_tasks'
        ordering = ['scheduled_date', 'order']

    def __str__(self):
        return f"{self.study_plan.title} - {self.title}"

    def mark_completed(self):
        """Mark task as completed"""
        self.status = 'completed'
        self.progress_percentage = 100
        self.completed_at = timezone.now()
        self.save()
        
        # Update study plan progress
        self.study_plan.completed_tasks = self.study_plan.tasks.filter(status='completed').count()
        self.study_plan.save()


class AIInteraction(models.Model):
    """Model to track AI interactions and performance"""
    INTERACTION_TYPES = [
        ('question_answer', 'Question & Answer'),
        ('explanation', 'Explanation'),
        ('problem_solving', 'Problem Solving'),
        ('study_plan', 'Study Plan Generation'),
        ('content_summary', 'Content Summary'),
        ('image_analysis', 'Image Analysis'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_interactions')
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, null=True, blank=True)
    interaction_type = models.CharField(max_length=30, choices=INTERACTION_TYPES)
    
    # Input data
    user_input = models.TextField()
    input_context = models.JSONField(default=dict)  # Additional context data
    
    # AI response
    ai_response = models.TextField()
    ai_model = models.CharField(max_length=50)
    response_metadata = models.JSONField(default=dict)  # Model-specific metadata
    
    # Performance metrics
    response_time_ms = models.PositiveIntegerField()
    tokens_used = models.PositiveIntegerField(default=0)
    confidence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # User feedback
    user_rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    user_feedback = models.TextField(blank=True)
    is_helpful = models.BooleanField(null=True, blank=True)
    
    # Context
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.CharField(max_length=200, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_interactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['ai_model', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_interaction_type_display()}"


class AIModelUsage(models.Model):
    """Track usage statistics for different AI models"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_name = models.CharField(max_length=50)
    date = models.DateField(default=timezone.now)
    
    # Usage statistics
    total_requests = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    total_response_time_ms = models.PositiveBigIntegerField(default=0)
    
    # Performance metrics
    success_rate = models.FloatField(default=0.0)
    average_confidence = models.FloatField(default=0.0)
    average_user_rating = models.FloatField(default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_model_usage'
        unique_together = ['model_name', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.model_name} - {self.date}"

    @property
    def average_response_time_ms(self):
        """Calculate average response time"""
        if self.total_requests == 0:
            return 0
        return self.total_response_time_ms / self.total_requests
