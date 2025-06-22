from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, StudentProfile, Region, Department, Course, StudySession, UserProgress


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'phone_number', 'password', 'password_confirm')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Password fields didn't match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Must include "email" and "password".'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class RegionSerializer(serializers.ModelSerializer):
    """Serializer for Region model"""
    class Meta:
        model = Region
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model"""
    class Meta:
        model = Department
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model"""
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Course
        fields = '__all__'


class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializer for StudentProfile model"""
    user = serializers.StringRelatedField(read_only=True)
    region = RegionSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    courses = CourseSerializer(many=True, read_only=True)
    region_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    department_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    course_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = StudentProfile
        fields = '__all__'
        read_only_fields = ('student_id',)

    def update(self, instance, validated_data):
        course_ids = validated_data.pop('course_ids', None)
        instance = super().update(instance, validated_data)
        
        if course_ids is not None:
            instance.courses.set(Course.objects.filter(id__in=course_ids))
        
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for User profile with student data"""
    student_profile = StudentProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'profile_picture', 'is_verified', 'created_at', 'student_profile')
        read_only_fields = ('id', 'is_verified', 'created_at')


class StudySessionSerializer(serializers.ModelSerializer):
    """Serializer for StudySession model"""
    student = serializers.StringRelatedField(read_only=True)
    course = CourseSerializer(read_only=True)
    course_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    accuracy_percentage = serializers.ReadOnlyField()

    class Meta:
        model = StudySession
        fields = '__all__'
        read_only_fields = ('student', 'duration_minutes')

    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)


class UserProgressSerializer(serializers.ModelSerializer):
    """Serializer for UserProgress model"""
    user = serializers.StringRelatedField(read_only=True)
    course = CourseSerializer(read_only=True)
    course_id = serializers.UUIDField(write_only=True)
    accuracy_percentage = serializers.ReadOnlyField()

    class Meta:
        model = UserProgress
        fields = '__all__'
        read_only_fields = ('user', 'last_activity')


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics"""
    total_study_time = serializers.IntegerField()
    total_questions_attempted = serializers.IntegerField()
    total_questions_correct = serializers.IntegerField()
    overall_accuracy = serializers.FloatField()
    current_streak = serializers.IntegerField()
    favorite_subjects = serializers.ListField(child=serializers.CharField())
    recent_progress = UserProgressSerializer(many=True)
    weekly_activity = serializers.DictField()


class ProfileSetupSerializer(serializers.Serializer):
    """Serializer for initial profile setup"""
    region_id = serializers.UUIDField()
    department_id = serializers.UUIDField()
    current_semester = serializers.IntegerField(min_value=1, max_value=10)
    course_ids = serializers.ListField(child=serializers.UUIDField())
    bio = serializers.CharField(max_length=500, required=False, allow_blank=True)
    study_preferences = serializers.DictField(required=False)

    def validate_course_ids(self, value):
        """Validate that all course IDs exist"""
        existing_courses = Course.objects.filter(id__in=value).count()
        if existing_courses != len(value):
            raise serializers.ValidationError("One or more course IDs are invalid.")
        return value
