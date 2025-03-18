from django.db.models import Count

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.pagination import PageNumberPagination


from administrator.permissions import CanCommentPermission, CanPostPermission, IsSuperAdminPermission
from .serializers import CategoryWriteSerializer, CommentWriteSerializer, HomeCommentSerializer, HomePostSerializer, HomeTrendingPostSerializer, PostReadSerializer, PostWriteSerializer
from .models import Category, Like, Post, Comment
# Create your views here.




class CategoryListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = CategoryWriteSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.is_cds_leader:
            return Response({"error":"Your account doesn't have enough access. Please contact support."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"detail": "Category created successfully"}, status=status.HTTP_201_CREATED)
    
    
class CategoryUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdminPermission]
    serializer_class = CategoryWriteSerializer
    queryset = Category.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "id"
    
    
    
class CategoryDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CategoryWriteSerializer
    queryset = Category.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "id"
    
    
    


class PostCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CanPostPermission]
    queryset = Post.objects.all()
    serializer_class = PostWriteSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"detail": "Posted"}, status=status.HTTP_201_CREATED)
    
    
class PostUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdminPermission]
    serializer_class = PostWriteSerializer
    queryset = Post.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "id"
    
    
    
class PostDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostReadSerializer
    queryset = Post.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "id"
    
    
    

class RandomPostsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HomePostSerializer

    def get_queryset(self):
        return Post.objects.select_related('user', 'category').only(
            'id', 'content', 'views', 'created_at',
            'user__username', 'category__name'
        ).order_by('?')

    
    pagination_class = PageNumberPagination
    
    

class UserRandomPostsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HomePostSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        username = self.kwargs['username']

        # Query the posts filtered by the provided username
        queryset = Post.objects.select_related('user', 'category').only(
            'id', 'content', 'views', 'created_at',
            'user__username', 'category__name'
        ).filter(user__username=username)

        # Order the posts randomly
        return queryset.order_by('?')

    
    
class TopCommentedPostsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HomeTrendingPostSerializer  

    def get_queryset(self):
        return Post.objects.annotate(comment_count=Count('comment')).select_related('user', 'category').only(
            'id', 'user__username', 'category__name'
        ).order_by('-comment_count')[:4]
        
        
class HomePostCommentsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    """
    Fetch paginated comments for a given post.
    """
    serializer_class = HomeCommentSerializer

    def get_queryset(self):
        post_id = self.kwargs.get("post_id")
        return Comment.objects.filter(post_id=post_id).select_related('user')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return Response({"comments": serializer.data})
    
    

class HomeLikePostView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, post_id, *args, **kwargs):
        user = request.user
        
        # Check if the post exists
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the user has already liked the post
        existing_like = Like.objects.filter(post=post, user=user).first()
        
        if existing_like:
            existing_like.delete()
            return Response({"message": "Post unliked successfully"}, status=status.HTTP_200_OK)
        else:
            try:
                Like.objects.create(post=post, user=user)
                return Response({"message": "Post liked successfully"}, status=status.HTTP_201_CREATED)
            except:
                return Response({"error": "Failed to like/unlike the post"}, status=status.HTTP_400_BAD_REQUEST)
            
            
            

class HomeCommentCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CanCommentPermission]
    queryset = Comment.objects.all()
    serializer_class = CommentWriteSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "notifications_group",
            {
                "type": "notification_message",
                "message": "A new post has been made!"
            }
        )
        return Response({"detail": "commented"}, status=status.HTTP_201_CREATED)