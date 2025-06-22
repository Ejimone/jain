from rest_framework import serializers
from django.db.models import Avg
from .models import (
    Content, Question, StudyMaterial, ContentCategory, Tag,
    ContentRating, ContentView, ContentDownload, UserBookmark
)
from student.serializers import UserProfileSerializer, CourseSerializer


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""
    class Meta:
        model = Tag
        fields = '__all__'


class ContentCategorySerializer(serializers.ModelSerializer):
    """Serializer for ContentCategory model"""
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = ContentCategory
        fields = '__all__'
    
    def get_subcategories(self, obj):
        if obj.subcategories.exists():
            return ContentCategorySerializer(obj.subcategories.filter(is_active=True), many=True).data
        return []


class ContentRatingSerializer(serializers.ModelSerializer):
    """Serializer for ContentRating model"""
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = ContentRating
        fields = '__all__'
        read_only_fields = ('user',)


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for Question model"""
    options_list = serializers.ReadOnlyField()
    success_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = Question
        fields = '__all__'


class StudyMaterialSerializer(serializers.ModelSerializer):
    """Serializer for StudyMaterial model"""
    
    class Meta:
        model = StudyMaterial
        fields = '__all__'


class ContentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for content list views"""
    author = serializers.StringRelatedField()
    course = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    tags = TagSerializer(many=True, read_only=True)
    file_size = serializers.ReadOnlyField()
    file_extension = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    
    class Meta:
        model = Content
        fields = [
            'id', 'title', 'description', 'content_type', 'status',
            'author', 'course', 'category', 'tags', 'difficulty_level',
            'semester', 'topic', 'view_count', 'like_count', 'rating',
            'created_at', 'published_at', 'file_size', 'file_extension',
            'average_rating', 'is_bookmarked'
        ]
    
    def get_average_rating(self, obj):
        avg_rating = obj.ratings.aggregate(avg=Avg('rating'))['avg']
        return round(avg_rating, 2) if avg_rating else 0.0
    
    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserBookmark.objects.filter(user=request.user, content=obj).exists()
        return False


class ContentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for content detail views"""
    author = UserProfileSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    category = ContentCategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    question_detail = QuestionSerializer(read_only=True)
    study_material_detail = StudyMaterialSerializer(read_only=True)
    ratings = ContentRatingSerializer(many=True, read_only=True)
    file_size = serializers.ReadOnlyField()
    file_extension = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    
    class Meta:
        model = Content
        fields = '__all__'
    
    def get_average_rating(self, obj):
        avg_rating = obj.ratings.aggregate(avg=Avg('rating'))['avg']
        return round(avg_rating, 2) if avg_rating else 0.0
    
    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserBookmark.objects.filter(user=request.user, content=obj).exists()
        return False


class ContentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating content"""
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    question_data = QuestionSerializer(required=False, write_only=True)
    study_material_data = StudyMaterialSerializer(required=False, write_only=True)
    
    class Meta:
        model = Content
        fields = [
            'title', 'description', 'content_type', 'course', 'department',
            'region', 'category', 'file', 'difficulty_level', 'semester',
            'topic', 'keywords', 'tag_ids', 'question_data', 'study_material_data'
        ]
    
    def validate(self, attrs):
        content_type = attrs.get('content_type')
        
        if content_type == 'question' and not attrs.get('question_data'):
            raise serializers.ValidationError("Question data is required for question content type")
        
        if content_type in ['note', 'material'] and not attrs.get('study_material_data'):
            raise serializers.ValidationError("Study material data is required for this content type")
        
        return attrs
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        question_data = validated_data.pop('question_data', None)
        study_material_data = validated_data.pop('study_material_data', None)
        
        validated_data['author'] = self.context['request'].user
        content = Content.objects.create(**validated_data)
        
        # Set tags
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids)
            content.tags.set(tags)
        
        # Create related objects
        if question_data and content.content_type == 'question':
            Question.objects.create(content=content, **question_data)
        
        if study_material_data and content.content_type in ['note', 'material']:
            StudyMaterial.objects.create(content=content, **study_material_data)
        
        return content


class UserBookmarkSerializer(serializers.ModelSerializer):
    """Serializer for UserBookmark model"""
    content = ContentListSerializer(read_only=True)
    content_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = UserBookmark
        fields = '__all__'
        read_only_fields = ('user',)
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ContentStatsSerializer(serializers.Serializer):
    """Serializer for content statistics"""
    total_content = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    total_materials = serializers.IntegerField()
    recent_uploads = serializers.IntegerField()
    top_categories = serializers.ListField(child=serializers.DictField())
    popular_content = ContentListSerializer(many=True)


class QuestionAttemptSerializer(serializers.Serializer):
    """Serializer for question attempts"""
    question_id = serializers.UUIDField()
    user_answer = serializers.CharField()
    is_correct = serializers.BooleanField(read_only=True)
    explanation = serializers.CharField(read_only=True)
    time_taken = serializers.IntegerField(required=False)  # in seconds


class ContentSearchSerializer(serializers.Serializer):
    """Serializer for content search parameters"""
    query = serializers.CharField(required=False, allow_blank=True)
    content_type = serializers.ChoiceField(choices=Content.CONTENT_TYPES, required=False)
    course_id = serializers.UUIDField(required=False)
    department_id = serializers.UUIDField(required=False)
    region_id = serializers.UUIDField(required=False)
    category_id = serializers.UUIDField(required=False)
    difficulty_level = serializers.ChoiceField(
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        required=False
    )
    semester = serializers.IntegerField(min_value=1, max_value=10, required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    sort_by = serializers.ChoiceField(
        choices=[
            'created_at', '-created_at', 'rating', '-rating',
            'view_count', '-view_count', 'title', '-title'
        ],
        default='-created_at'
    )
