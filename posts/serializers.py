# blog/serializers.py
from rest_framework import serializers
from .models import Comment, PageView, BlogPost


# Existing serializers ...
# CommentSerializer, BlogViewSerializer, PageViewSerializer, BlogReadTimeSerializer, RecursiveCommentSerializer
from rest_framework import serializers
from .models import BlogPost, Category

from rest_framework import serializers
from .models import Comment
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email','name','profile']

    def get_name(self, obj):
        return obj.get_full_name() or f"{obj.first_name} {obj.last_name}".strip()  # Adjust based on what you want exposed
        
    def get_profile(self, obj):
        # Assuming featured_image is in User model
        if hasattr(obj, 'profile_image') and obj.profile_image:
            return obj.profile_image.url
        # Or if it's in a related Profile model: return obj.profile.featured_image.url
        return None

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'created_at', 'parent', 'replies']

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class BlogPostListSerializer(serializers.ModelSerializer):
    read_time = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    featured_image = serializers.ImageField(read_only=True)
    tags = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )
    user = UserSerializer(source='author', read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            "id", "title", "excerpt", "category", "content",
            "comments_count", "slug", "status",
            "featured_image", "tags", "allow_comments", "published",
            "read_time", "created_at", "updated_at",
            "meta_title", "meta_description", 'user',
        ]

    def get_read_time(self, obj):
        page =  PageView.objects.filter(path__icontains=obj.slug).first()
        if page:
            read_time  = page.total_read_time
            if read_time:
                return read_time
        return 0

    def get_comments_count(self, obj):
        return obj.comments.filter(parent=None).count()

# For creating comments AND replies
class CreateCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content', 'parent']  # parent field handles the reply functionality
        
    def validate_parent(self, value):
        """Ensure parent comment belongs to the same blog and exists"""
        if value:
            # Ensure parent comment exists
            if not Comment.objects.filter(id=value.id).exists():
                raise serializers.ValidationError("Parent comment does not exist")
            
            # Ensure parent comment belongs to the same blog (if you have blog context)
            if hasattr(self, 'context'):
                blog = self.context.get('blog')
                if blog and value.blog != blog:
                    raise serializers.ValidationError("Parent comment must be from the same blog")
        return value

 
class PageViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageView
        fields = ['id', 'path', 'ip_address', 'user', 'viewed_at']
        read_only_fields = ['viewed_at']

class BlogReadTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = ['id', 'read_time']

 