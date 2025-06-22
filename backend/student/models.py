from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Extended user model for students and admins"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_student = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class Region(models.Model):
    """Model for academic regions/states"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    country = models.CharField(max_length=50, default='India')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'regions'
        ordering = ['name']

    def __str__(self):
        return self.name


class Department(models.Model):
    """Model for academic departments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'departments'
        ordering = ['name']
        unique_together = ['name', 'code']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Course(models.Model):
    """Model for academic courses"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    semester = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    credits = models.PositiveIntegerField(default=3)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'courses'
        ordering = ['department', 'semester', 'name']
        unique_together = ['code', 'department']

    def __str__(self):
        return f"{self.name} ({self.code}) - Sem {self.semester}"


class StudentProfile(models.Model):
    """Extended profile for students with academic information"""
    SEMESTER_CHOICES = [(i, f"Semester {i}") for i in range(1, 11)]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    current_semester = models.PositiveIntegerField(
        choices=SEMESTER_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    enrollment_year = models.PositiveIntegerField(default=timezone.now().year)
    courses = models.ManyToManyField(Course, blank=True, related_name='enrolled_students')
    bio = models.TextField(max_length=500, blank=True)
    study_preferences = models.JSONField(default=dict, blank=True)  # Store study preferences as JSON
    performance_data = models.JSONField(default=dict, blank=True)  # Store performance analytics
    
    class Meta:
        db_table = 'student_profiles'
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'

    def __str__(self):
        return f"{self.user.full_name} - {self.student_id}"

    def save(self, *args, **kwargs):
        if not self.student_id:
            # Generate student ID based on department and year
            dept_code = self.department.code if self.department else 'GEN'
            year = str(self.enrollment_year)[-2:]
            # Get count of students in same dept and year
            count = StudentProfile.objects.filter(
                department=self.department,
                enrollment_year=self.enrollment_year
            ).count() + 1
            self.student_id = f"{dept_code}{year}{count:04d}"
        super().save(*args, **kwargs)


class StudySession(models.Model):
    """Model to track student study sessions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    topic = models.CharField(max_length=200)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    questions_attempted = models.PositiveIntegerField(default=0)
    questions_correct = models.PositiveIntegerField(default=0)
    ai_interactions = models.PositiveIntegerField(default=0)
    session_data = models.JSONField(default=dict, blank=True)  # Store detailed session data

    class Meta:
        db_table = 'study_sessions'
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.student.full_name} - {self.topic} ({self.start_time.date()})"

    @property
    def accuracy_percentage(self):
        if self.questions_attempted == 0:
            return 0
        return round((self.questions_correct / self.questions_attempted) * 100, 2)


class UserProgress(models.Model):
    """Model to track user progress across different topics and courses"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    topic = models.CharField(max_length=200)
    total_questions_attempted = models.PositiveIntegerField(default=0)
    total_questions_correct = models.PositiveIntegerField(default=0)
    total_study_time_minutes = models.PositiveIntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    mastery_level = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    
    class Meta:
        db_table = 'user_progress'
        unique_together = ['user', 'course', 'topic']
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.user.full_name} - {self.course.name} - {self.topic}"

    @property
    def accuracy_percentage(self):
        if self.total_questions_attempted == 0:
            return 0
        return round((self.total_questions_correct / self.total_questions_attempted) * 100, 2)

    def update_progress(self, questions_attempted, questions_correct, study_time_minutes):
        """Update progress with new session data"""
        self.total_questions_attempted += questions_attempted
        self.total_questions_correct += questions_correct
        self.total_study_time_minutes += study_time_minutes
        
        # Calculate mastery level based on accuracy and study time
        accuracy = self.accuracy_percentage
        time_factor = min(self.total_study_time_minutes / 60, 10) * 10  # Max 100 points for 10+ hours
        self.mastery_level = min((accuracy * 0.7) + (time_factor * 0.3), 100)
        
        self.save()
