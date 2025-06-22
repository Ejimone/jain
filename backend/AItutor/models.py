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
        if not self.created_at:
            return 0
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
        if not self.end_date:
            return None  # Return None if end_date is not set
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


class Question(models.Model):
    """Model for individual questions - both generated and uploaded"""
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
        ('fill_blank', 'Fill in the Blank'),
        ('matching', 'Matching'),
        ('numerical', 'Numerical Answer'),
        ('code', 'Code/Programming'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    SOURCE_TYPES = [
        ('ai_generated', 'AI Generated'),
        ('user_uploaded', 'User Uploaded'),
        ('admin_created', 'Admin Created'),
        ('web_scraped', 'Web Scraped'),
        ('past_exam', 'Past Exam Question'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    
    # Answer data
    correct_answer = models.TextField()
    answer_options = models.JSONField(default=dict, blank=True)  # For multiple choice, matching, etc.
    answer_explanation = models.TextField(blank=True)
    
    # Difficulty & Classification
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS)
    difficulty_score = models.FloatField(default=0.0, help_text="AI-calculated difficulty (0-1)")
    estimated_solve_time = models.PositiveIntegerField(default=60, help_text="Estimated solve time in seconds")
    actual_solve_times = models.JSONField(default=list, blank=True)  # Track user solve times
    
    # Content Classification
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    topics = models.JSONField(default=list)  # List of topics covered
    tags = models.JSONField(default=list)  # Additional tags
    
    # Source & Attribution
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    source_url = models.URLField(blank=True)
    source_reference = models.CharField(max_length=500, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Image support
    question_image = models.ImageField(upload_to='question_images/', null=True, blank=True)
    extracted_text = models.TextField(blank=True, help_text="OCR extracted text from image")
    
    # Quality & Performance
    usage_count = models.PositiveIntegerField(default=0)
    correct_answers_count = models.PositiveIntegerField(default=0)
    total_attempts = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    is_verified = models.BooleanField(default=False)
    
    # Embeddings for AI search
    question_embedding = models.JSONField(default=list, blank=True)
    answer_embedding = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_questions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'difficulty_level']),
            models.Index(fields=['question_type', 'source_type']),
            models.Index(fields=['difficulty_score', 'average_rating']),
        ]

    def __str__(self):
        return f"{self.question_type.title()}: {self.title[:50]}..."

    @property
    def success_rate(self):
        """Calculate percentage of correct answers"""
        if self.total_attempts == 0:
            return 0
        return round((self.correct_answers_count / self.total_attempts) * 100, 2)

    @property
    def average_solve_time(self):
        """Calculate average solve time from user data"""
        if not self.actual_solve_times:
            return self.estimated_solve_time
        return sum(self.actual_solve_times) / len(self.actual_solve_times)

    def update_difficulty_score(self):
        """AI-based difficulty calculation using success rate and solve time"""
        base_difficulty = 0.5
        
        # Factor in success rate (lower success = higher difficulty)
        if self.total_attempts > 5:
            success_factor = 1 - (self.success_rate / 100)
            base_difficulty += success_factor * 0.3
        
        # Factor in solve time (longer time = higher difficulty)
        if self.actual_solve_times:
            avg_time = self.average_solve_time
            time_factor = min(avg_time / 300, 1)  # Normalize to 5 minutes max
            base_difficulty += time_factor * 0.2
        
        self.difficulty_score = min(max(base_difficulty, 0.0), 1.0)
        self.save(update_fields=['difficulty_score'])


class PastQuestion(models.Model):
    """Model for past exam questions with metadata"""
    EXAM_TYPES = [
        ('midterm', 'Midterm Exam'),
        ('final', 'Final Exam'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('practice', 'Practice Test'),
        ('certification', 'Certification Exam'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='past_question_info')
    
    # Exam metadata
    exam_year = models.PositiveIntegerField()
    exam_semester = models.CharField(max_length=20, blank=True)  # "Fall 2024", "Spring 2025"
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    exam_name = models.CharField(max_length=255)
    institution = models.CharField(max_length=255, blank=True)
    instructor = models.CharField(max_length=255, blank=True)
    
    # Question specifics
    question_number = models.CharField(max_length=10, blank=True)  # "Q1a", "Part 2.3"
    total_marks = models.PositiveIntegerField(default=1)
    section = models.CharField(max_length=100, blank=True)
    
    # Upload metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    original_document = models.FileField(upload_to='past_exams/', null=True, blank=True)
    page_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_past_questions'
    )
    verification_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'past_questions'
        ordering = ['-exam_year', '-created_at']
        indexes = [
            models.Index(fields=['exam_year', 'exam_type']),
            models.Index(fields=['exam_year', 'is_verified']),
        ]

    def __str__(self):
        return f"{self.exam_name} ({self.exam_year}) - {self.question.title[:30]}..."


class Quiz(models.Model):
    """Model for AI-generated quizzes and quiz sessions"""
    QUIZ_TYPES = [
        ('practice', 'Practice Quiz'),
        ('mock_exam', 'Mock Exam'),
        ('topic_review', 'Topic Review'),
        ('difficulty_test', 'Difficulty Assessment'),
        ('past_questions', 'Past Questions Quiz'),
        ('mixed', 'Mixed Content'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Quiz configuration
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    topics = models.JSONField(default=list)  # Selected topics
    difficulty_range = models.JSONField(default=dict)  # {"min": 0.2, "max": 0.8}
    question_types = models.JSONField(default=list)  # Selected question types
    
    # Questions
    questions = models.ManyToManyField(Question, through='QuizQuestion', related_name='quizzes')
    total_questions = models.PositiveIntegerField(default=10)
    time_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Time limit in minutes")
    
    # Generation parameters
    generation_params = models.JSONField(default=dict)  # AI generation parameters
    ai_generated = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Public access
    is_public = models.BooleanField(default=False)
    access_code = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quizzes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'quiz_type']),
            models.Index(fields=['status', 'is_public']),
        ]

    def __str__(self):
        return f"{self.title} ({self.course.name})"

    def generate_access_code(self):
        """Generate a unique access code for the quiz"""
        import random
        import string
        self.access_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        self.save(update_fields=['access_code'])


class QuizQuestion(models.Model):
    """Through model for Quiz-Question relationship with ordering"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    points = models.PositiveIntegerField(default=1)
    
    # Question-specific settings for this quiz
    time_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Time limit for this question in seconds")
    is_bonus = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'quiz_questions'
        unique_together = ['quiz', 'question']
        ordering = ['order']

    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}"


class UserQuizSession(models.Model):
    """Track user quiz attempts and performance"""
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
        ('paused', 'Paused'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_sessions')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='user_sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    
    # Session data
    answers = models.JSONField(default=dict)  # {"question_id": "answer", ...}
    answer_times = models.JSONField(default=dict)  # {"question_id": seconds_taken, ...}
    current_question = models.PositiveIntegerField(default=1)
    
    # Results
    score = models.FloatField(default=0.0)
    total_points = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    total_time_spent = models.PositiveIntegerField(default=0, help_text="Total time in seconds")
    
    # Performance analytics
    difficulty_performance = models.JSONField(default=dict)  # Performance by difficulty level
    topic_performance = models.JSONField(default=dict)  # Performance by topic
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_quiz_sessions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['quiz', 'completed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} ({self.status})"

    @property
    def percentage_score(self):
        """Calculate percentage score"""
        if self.total_points == 0:
            return 0
        return round((self.score / self.total_points) * 100, 2)

    @property
    def average_time_per_question(self):
        """Calculate average time per answered question"""
        if not self.answer_times:
            return 0
        return sum(self.answer_times.values()) / len(self.answer_times)

    def calculate_final_score(self):
        """Calculate final score based on answers"""
        if self.status != 'completed':
            return
        
        total_score = 0
        total_points = 0
        correct_count = 0
        
        for quiz_question in self.quiz.quizquestion_set.all():
            question = quiz_question.question
            user_answer = self.answers.get(str(question.id))
            points = quiz_question.points
            
            total_points += points
            
            if user_answer and self._is_correct_answer(question, user_answer):
                total_score += points
                correct_count += 1
        
        self.score = total_score
        self.total_points = total_points
        self.correct_answers = correct_count
        self.save(update_fields=['score', 'total_points', 'correct_answers'])

    def _is_correct_answer(self, question, user_answer):
        """Check if user answer is correct"""
        # Implement answer checking logic based on question type
        if question.question_type == 'multiple_choice':
            return user_answer.lower().strip() == question.correct_answer.lower().strip()
        elif question.question_type == 'true_false':
            return user_answer.lower() in ['true', 'false'] and user_answer.lower() == question.correct_answer.lower()
        elif question.question_type == 'numerical':
            try:
                return abs(float(user_answer) - float(question.correct_answer)) < 0.01
            except (ValueError, TypeError):
                return False
        else:
            # For text-based answers, use fuzzy matching or AI evaluation
            return user_answer.lower().strip() == question.correct_answer.lower().strip()


class QuestionBank(models.Model):
    """Embedded knowledge base for AI learning and question generation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_hash = models.CharField(max_length=64, unique=True)  # SHA-256 hash for deduplication
    
    # Content
    source_question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='knowledge_entries')
    question_embedding = models.JSONField(default=list)  # Vector embedding of question
    answer_embedding = models.JSONField(default=list)  # Vector embedding of answer
    combined_embedding = models.JSONField(default=list)  # Combined question+answer embedding
    
    # Metadata
    embedding_model = models.CharField(max_length=50, default='text-embedding-3-small')
    embedding_dimensions = models.PositiveIntegerField(default=1536)
    
    # Usage tracking
    similarity_matches = models.PositiveIntegerField(default=0)
    used_for_generation = models.PositiveIntegerField(default=0)
    
    # Quality indicators
    source_quality_score = models.FloatField(default=0.5)  # Based on source question performance
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'question_bank'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_hash']),
            models.Index(fields=['source_quality_score']),
        ]

    def __str__(self):
        return f"Knowledge Entry: {self.source_question.title[:50]}..."

    @classmethod
    def create_from_question(cls, question):
        """Create knowledge bank entry from a question"""
        import hashlib
        
        # Create content hash
        content = f"{question.question_text}|{question.correct_answer}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Check if already exists
        if cls.objects.filter(content_hash=content_hash).exists():
            return None
        
        # Create entry (embeddings will be generated asynchronously)
        return cls.objects.create(
            content_hash=content_hash,
            source_question=question,
            source_quality_score=question.average_rating / 5.0 if question.average_rating > 0 else 0.5
        )


class DifficultyAnalysis(models.Model):
    """Model for storing detailed difficulty analysis of questions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.OneToOneField('Question', on_delete=models.CASCADE, related_name='difficulty_analysis')
    
    # Complexity Analysis
    conceptual_complexity = models.FloatField(default=0.0, help_text="Conceptual understanding required (0-1)")
    computational_complexity = models.FloatField(default=0.0, help_text="Computational steps required (0-1)")
    cognitive_load = models.FloatField(default=0.0, help_text="Mental processing load (0-1)")
    prerequisite_knowledge = models.JSONField(default=list, help_text="Required prerequisite concepts")
    
    # Solving Time Analysis
    estimated_read_time = models.PositiveIntegerField(default=30, help_text="Time to read question (seconds)")
    estimated_think_time = models.PositiveIntegerField(default=60, help_text="Time to understand/plan (seconds)")
    estimated_solve_time = models.PositiveIntegerField(default=120, help_text="Time to solve (seconds)")
    estimated_review_time = models.PositiveIntegerField(default=30, help_text="Time to review answer (seconds)")
    
    # User Performance Data
    actual_solve_times = models.JSONField(default=list, help_text="User solve times in seconds")
    success_rates_by_skill = models.JSONField(default=dict, help_text="Success rates by user skill level")
    common_mistakes = models.JSONField(default=list, help_text="Common wrong answers/mistakes")
    
    # AI Analysis Metadata
    analysis_model = models.CharField(max_length=50, default='gemini-pro')
    analysis_confidence = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'difficulty_analyses'

    def __str__(self):
        return f"Difficulty Analysis: {self.question.title[:30]}..."

    @property
    def total_estimated_time(self):
        """Total estimated time in seconds"""
        return (self.estimated_read_time + self.estimated_think_time + 
                self.estimated_solve_time + self.estimated_review_time)

    @property
    def average_actual_time(self):
        """Average actual solve time from user data"""
        if not self.actual_solve_times:
            return self.total_estimated_time
        return sum(self.actual_solve_times) / len(self.actual_solve_times)


class OnlineSource(models.Model):
    """Model for managing online educational sources for question generation"""
    SOURCE_TYPES = [
        ('educational_website', 'Educational Website'),
        ('question_bank', 'Online Question Bank'),
        ('textbook_site', 'Textbook Website'),
        ('university_site', 'University Website'),
        ('certification_site', 'Certification Website'),
        ('practice_platform', 'Practice Platform'),
    ]
    
    QUALITY_RATINGS = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    url = models.URLField()
    source_type = models.CharField(max_length=30, choices=SOURCE_TYPES)
    description = models.TextField(blank=True)
    
    # Source metadata
    domains = models.JSONField(default=list, help_text="Subject domains covered")
    languages = models.JSONField(default=list, help_text="Languages supported")
    question_types = models.JSONField(default=list, help_text="Types of questions available")
    
    # Quality and reliability
    quality_rating = models.CharField(max_length=20, choices=QUALITY_RATINGS)
    reliability_score = models.FloatField(default=0.0, help_text="AI-assessed reliability (0-1)")
    last_scraped = models.DateTimeField(null=True, blank=True)
    scrape_frequency_hours = models.PositiveIntegerField(default=24)
    
    # Access control
    requires_authentication = models.BooleanField(default=False)
    api_key_required = models.BooleanField(default=False)
    rate_limit_per_hour = models.PositiveIntegerField(default=100)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    error_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'online_sources'
        ordering = ['-quality_rating', '-reliability_score']

    def __str__(self):
        return f"{self.name} ({self.source_type})"


class EmbeddingVector(models.Model):
    """Model for storing question embeddings for AI learning and search"""
    CONTENT_TYPES = [
        ('question_answer', 'Question + Answer'),
        ('question_only', 'Question Only'),
        ('answer_only', 'Answer Only'),
        ('explanation', 'Explanation'),
        ('topic_summary', 'Topic Summary'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='embeddings')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    
    # Embedding data
    vector_data = models.JSONField(help_text="Embedding vector as JSON array")
    vector_model = models.CharField(max_length=50, default='text-embedding-3-small')
    vector_dimension = models.PositiveIntegerField(default=1536)
    
    # Content hash for duplicate detection
    content_hash = models.CharField(max_length=64, db_index=True)
    
    # Metadata
    is_cached = models.BooleanField(default=True)
    similarity_threshold = models.FloatField(default=0.8)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'embedding_vectors'
        unique_together = ['question', 'content_type']
        indexes = [
            models.Index(fields=['content_hash']),
            models.Index(fields=['vector_model', 'content_type']),
        ]

    def __str__(self):
        return f"Embedding: {self.question.title[:30]}... ({self.content_type})"


class QuizCustomization(models.Model):
    """Model for storing user quiz customization preferences"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_preferences')
    
    # Default preferences
    default_num_questions = models.PositiveIntegerField(default=10)
    default_difficulty = models.CharField(max_length=20, default='intermediate')
    default_time_limit = models.PositiveIntegerField(default=30, help_text="Default time limit in minutes")
    
    # Subject preferences
    preferred_courses = models.ManyToManyField(Course, blank=True)
    preferred_topics = models.JSONField(default=list)
    preferred_question_types = models.JSONField(default=list)
    
    # Difficulty preferences
    adaptive_difficulty = models.BooleanField(default=True)
    difficulty_adjustment_rate = models.FloatField(default=0.1)
    
    # Source preferences
    include_past_questions = models.BooleanField(default=True)
    include_ai_generated = models.BooleanField(default=True)
    include_user_uploaded = models.BooleanField(default=True)
    past_questions_weight = models.FloatField(default=0.4)
    ai_generated_weight = models.FloatField(default=0.4)
    user_uploaded_weight = models.FloatField(default=0.2)
    
    # Performance tracking preferences
    track_performance = models.BooleanField(default=True)
    show_analytics = models.BooleanField(default=True)
    get_recommendations = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quiz_customizations'

    def __str__(self):
        return f"{self.user.username} - Quiz Preferences"


class UserPerformanceAnalytics(models.Model):
    """Model for tracking detailed user performance analytics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_analytics')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='user_analytics')
    
    # Time period (for aggregated data)
    period_start = models.DateField()
    period_end = models.DateField()
    period_type = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('semester', 'Semester'),
    ])
    
    # Performance metrics
    total_questions_attempted = models.PositiveIntegerField(default=0)
    total_questions_correct = models.PositiveIntegerField(default=0)
    total_time_spent_minutes = models.PositiveIntegerField(default=0)
    
    # Topic-wise performance
    topic_performance = models.JSONField(default=dict, help_text="Performance by topic")
    difficulty_performance = models.JSONField(default=dict, help_text="Performance by difficulty")
    question_type_performance = models.JSONField(default=dict, help_text="Performance by question type")
    
    # Trends and improvements
    improvement_rate = models.FloatField(default=0.0)
    consistency_score = models.FloatField(default=0.0)
    learning_velocity = models.FloatField(default=0.0)
    
    # Weaknesses and strengths
    weak_topics = models.JSONField(default=list)
    strong_topics = models.JSONField(default=list)
    suggested_focus_areas = models.JSONField(default=list)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_performance_analytics'
        unique_together = ['user', 'course', 'period_start', 'period_type']
        ordering = ['-period_end']

    def __str__(self):
        return f"{self.user.username} - {self.course.code} ({self.period_type})"

    @property
    def accuracy_percentage(self):
        """Calculate accuracy percentage"""
        if self.total_questions_attempted == 0:
            return 0
        return round((self.total_questions_correct / self.total_questions_attempted) * 100, 2)

    @property
    def average_time_per_question(self):
        """Calculate average time per question in minutes"""
        if self.total_questions_attempted == 0:
            return 0
        return round(self.total_time_spent_minutes / self.total_questions_attempted, 2)
