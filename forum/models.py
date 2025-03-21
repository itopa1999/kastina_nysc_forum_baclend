from administrator.models import User
from django.db import models

# Category model for grouping discussions
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),  # Index for the name field
        ]
    
    def __str__(self):
        return self.name

# Post model for forum posts
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at', 'category']),  # Index on created_at and category for optimization
        ]

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}..." if len(self.content) > 30 else f"{self.user.username}: {self.content}"


    def get_comments_count(self):
        return self.comment_set.count()

    def get_likes_count(self):
        return self.like_set.count() 
    
# Comment model for post comments
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['created_at', 'post']),  # Index on created_at and post for optimization
        ]

    def __str__(self):
        content_preview = self.post.content[:30] + "..." if len(self.post.content) > 30 else self.post.content
        return f"Comment by {self.user.username} on {content_preview}"

    @classmethod
    def prefetch_post_comments(cls, queryset):
        """
        Prefetch comments for each post to avoid N+1 queries.
        """
        return queryset.prefetch_related(
            models.Prefetch('comment_set', queryset=Comment.objects.all().select_related('user'), to_attr='comments')
        )


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"liked by {self.user.username} on {self.post}"
    
    
    