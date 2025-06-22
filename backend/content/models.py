from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
from student.models import User, Course, Department, Region
import uuid
import os


def content_upload_path(instance, filename):
    """Generate upload path for content files"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"content/{instance.content_type}/{instance.course.code if instance.course else 'general'}/{filename}"


class ContentCategory(models.Model):
    """Categories for organizing content"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'content_categories'
        verbose_name_plural = 'Content Categories'
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Tag(models.Model):
    """Tags for content organization"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color code
    
    class Meta:
        db_table = 'tags'
        ordering = ['name']

    def __str__(self):
        return self.name


class Content(models.Model):
    """Base model for all content types"""
    CONTENT_TYPES = [
        ('question', 'Question'),
        ('note', 'Study Note'),
        ('material', 'Study Material'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('image', 'Image'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Relationships
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_content')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='content')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(ContentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='content')
    
    # File upload
    file = models.FileField(
        upload_to=content_upload_path,
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'txt', 'jpg', 'png', 'jpeg', 'mp4', 'avi', 'mov'])]
    )
    
    # Metadata
    difficulty_level = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        default='intermediate'
    )
    semester = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    topic = models.CharField(max_length=200, blank=True)
    keywords = models.TextField(blank=True, help_text="Comma-separated keywords for search")
    
    # Engagement metrics
    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Review fields
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_content'
    )
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'content'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'status']),
            models.Index(fields=['course', 'semester']),
            models.Index(fields=['difficulty_level']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()})"

    def save(self, *args, **kwargs):
        if self.status == 'approved' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def file_size(self):
        """Get file size in MB"""
        if self.file:
            return round(self.file.size / (1024 * 1024), 2)
        return 0

    @property
    def file_extension(self):
        """Get file extension"""
        if self.file:
            return os.path.splitext(self.file.name)[1][1:].upper()
        return None


class Question(models.Model):
    """Model for exam questions"""
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('short_answer', 'Short Answer'),
        ('long_answer', 'Long Answer'),
        ('numerical', 'Numerical'),
        ('true_false', 'True/False'),
    ]

    content = models.OneToOneField(Content, on_delete=models.CASCADE, related_name='question_detail')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    
    # Multiple choice options
    option_a = models.TextField(blank=True)
    option_b = models.TextField(blank=True)
    option_c = models.TextField(blank=True)
    option_d = models.TextField(blank=True)
    
    # Answer and explanation
    correct_answer = models.TextField()
    explanation = models.TextField(blank=True)
    
    # Question metadata
    marks = models.PositiveIntegerField(default=1)
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    exam_type = models.CharField(max_length=100, blank=True)  # e.g., "Mid-term", "Final", "Assignment"
    
    # Analytics
    attempt_count = models.PositiveIntegerField(default=0)
    correct_attempt_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'questions'

    def __str__(self):
        return f"Question: {self.question_text[:100]}..."

    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.attempt_count == 0:
            return 0
        return round((self.correct_attempt_count / self.attempt_count) * 100, 2)

    @property
    def options_list(self):
        """Get list of non-empty options"""
        options = []
        for label, text in [('A', self.option_a), ('B', self.option_b), ('C', self.option_c), ('D', self.option_d)]:
            if text.strip():
                options.append({'label': label, 'text': text})
        return options


class StudyMaterial(models.Model):
    """Model for study materials and notes"""
    content = models.OneToOneField(Content, on_delete=models.CASCADE, related_name='study_material_detail')
    material_content = models.TextField()
    summary = models.TextField(blank=True)
    
    # Additional metadata
    estimated_read_time = models.PositiveIntegerField(help_text="Estimated reading time in minutes")
    references = models.TextField(blank=True, help_text="External references and citations")

    class Meta:
        db_table = 'study_materials'

    def __str__(self):
        return f"Material: {self.content.title}"


class ContentRating(models.Model):
    """User ratings for content"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_ratings')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'content_ratings'
        unique_together = ['content', 'user']

    def __str__(self):
        return f"{self.user.username} rated {self.content.title}: {self.rating}/5"


class ContentView(models.Model):
    """Track content views for analytics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_views', null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'content_views'
        indexes = [
            models.Index(fields=['content', 'viewed_at']),
        ]

    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{username} viewed {self.content.title}"


class ContentDownload(models.Model):
    """Track content downloads"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='downloads')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_downloads')
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()

    class Meta:
        db_table = 'content_downloads'
        unique_together = ['content', 'user', 'downloaded_at']

    def __str__(self):
        return f"{self.user.username} downloaded {self.content.title}"


class UserBookmark(models.Model):
    """User bookmarks for content"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'user_bookmarks'
        unique_together = ['user', 'content']

    def __str__(self):
        return f"{self.user.username} bookmarked {self.content.title}"
