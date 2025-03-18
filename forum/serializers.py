from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ParseError

from .models import Category, Like, Post, Comment


 
class CategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id",'name', 'description']
        
        
    def create(self, validated_data):
        cat = Category.objects.create(**validated_data)

        return cat
        
        
    def update(self, instance: Category, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
    
    
    
class PostWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["id",'category','content']
        
        
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        post = Post.objects.create(**validated_data)
        return post
        
        
    def update(self, instance: Post, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
    
    
class PostReadSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    category = serializers.CharField(source="category.name", read_only=True)
    total_comment = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    user_profile_picture = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'content', 'likes', 'views', 'created_at', 'user', 'category','total_comment',
                  'user_profile_picture', 'has_liked']

    def get_total_comment(self, obj):
        """Returns the total number of comments for this post"""
        return obj.get_comments_count()
    
    def get_likes(self, obj):
        """Returns the total number of likes for this post"""
        return obj.get_likes_count()
    
    def get_user_profile_picture(self, obj):
        """Returns the profile picture URL for the user"""
        request = self.context.get('request')
        return request.build_absolute_uri(obj.user.profile_picture.url)
    
    def get_has_liked(self, obj):
        """Checks if the current user has liked this post"""
        request = self.context.get('request')
        user = request.user
        
        has_liked = Like.objects.filter(post=obj, user=user).exists()
        
        return has_liked
    
    
    
class HomePostSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    category = serializers.CharField(source="category.name", read_only=True)
    short_content = serializers.SerializerMethodField()
    total_comment = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    user_profile_picture = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'short_content', 'likes', 'views', 'created_at', 'user', 'category','total_comment',
                  'user_profile_picture', 'has_liked']

    def get_short_content(self, obj):
        """Returns the first 50 characters of content"""
        return obj.content[:200] + "..." if len(obj.content) > 200 else obj.content
    
    def get_total_comment(self, obj):
        """Returns the total number of comments for this post"""
        return obj.get_comments_count()
    
    def get_likes(self, obj):
        """Returns the total number of likes for this post"""
        return obj.get_likes_count()
    
    def get_user_profile_picture(self, obj):
        """Returns the profile picture URL for the user"""
        request = self.context.get('request')
        return request.build_absolute_uri(obj.user.profile_picture.url)
    
    def get_has_liked(self, obj):
        """Checks if the current user has liked this post"""
        request = self.context.get('request')
        user = request.user
        
        has_liked = Like.objects.filter(post=obj, user=user).exists()
        
        return has_liked
    
    
class HomeTrendingPostSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    category = serializers.CharField(source="category.name", read_only=True)
    short_content = serializers.SerializerMethodField()
    total_comment = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'short_content','created_at', 'user', 'category','total_comment']

    def get_short_content(self, obj):
        """Returns the first 50 characters of content"""
        return obj.content[:30] + "..." if len(obj.content) > 30 else obj.content
    
    def get_total_comment(self, obj):
        """Returns the total number of comments for this post"""
        return obj.get_comments_count()
    
    
    
class HomeCommentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    user_profile_picture = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'user', 'user_profile_picture', 'content', 'created_at']

    def get_user_profile_picture(self, obj):
        """Return absolute URL of the user's profile picture."""
        request = self.context.get("request")
        if obj.user.profile_picture:
            return request.build_absolute_uri(obj.user.profile_picture.url)
        return None
    
    
    
class CommentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["post",'content']
        
        
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        comment = Comment.objects.create(**validated_data)
        return comment
        
        
    def update(self, instance: Comment, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance