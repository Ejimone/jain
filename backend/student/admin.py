from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, StudentProfile, Region, Department, Course, StudySession, UserProgress


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin"""
    list_display = ('email', 'first_name', 'last_name', 'is_student', 'is_verified', 'created_at')
    list_filter = ('is_student', 'is_verified', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'profile_picture', 'is_student', 'is_verified')
        }),
    )


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    """Region admin"""
    list_display = ('name', 'code', 'country', 'is_active')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'code')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Department admin"""
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Course admin"""
    list_display = ('name', 'code', 'department', 'semester', 'credits', 'is_active')
    list_filter = ('department', 'semester', 'is_active')
    search_fields = ('name', 'code')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Student profile admin"""
    list_display = ('user', 'student_id', 'department', 'current_semester', 'enrollment_year')
    list_filter = ('department', 'current_semester', 'enrollment_year', 'region')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'student_id')
    raw_id_fields = ('user',)


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    """Study session admin"""
    list_display = ('student', 'topic', 'course', 'start_time', 'duration_minutes', 'accuracy_percentage')
    list_filter = ('course', 'start_time')
    search_fields = ('student__email', 'topic')
    raw_id_fields = ('student', 'course')
    readonly_fields = ('accuracy_percentage',)


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    """User progress admin"""
    list_display = ('user', 'course', 'topic', 'accuracy_percentage', 'mastery_level', 'last_activity')
    list_filter = ('course', 'last_activity')
    search_fields = ('user__email', 'topic')
    raw_id_fields = ('user', 'course')
    readonly_fields = ('accuracy_percentage',)
