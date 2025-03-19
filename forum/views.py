from django.db.models import Count, Sum, Q, F

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView


from administrator.models import User
from administrator.permissions import CanCommentPermission, CanPostPermission, IsSuperAdminPermission
from .serializers import CategoryWriteSerializer, CommentWriteSerializer, HomeCommentSerializer, HomePostSerializer, HomeTrendingPostSerializer, PostReadSerializer, PostWriteSerializer, SearchPostSerializer, SearchUserSerializer
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
    
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views = F("views") + 1  # Increment views using F() for atomic update
        instance.save(update_fields=["views"])  # Save only the views field
        instance.refresh_from_db()  # Refresh the instance to get updated views count
        return super().retrieve(request, *args, **kwargs)
    
    
    

class RandomPostsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HomePostSerializer

    def get_queryset(self):
        return Post.objects.select_related('user', 'category').only(
            'id', 'content', 'views', 'created_at',
            'user__username', 'category__name'
        )

    
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
        return queryset
    
    
    
    
class UserProfileActivitiesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, username):
        # Get user object
        user = User.objects.filter(username=username).first()

        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        posts_count = Post.objects.filter(user=user).count()

        comments_count = Comment.objects.filter(post__user=user).count()

        likes_count = Like.objects.filter(post__user=user).count()

        total_views = Post.objects.filter(user=user).aggregate(Sum('views'))['views__sum'] or 0

        # Prepare data to return
        data = {
            "total_posts": posts_count,
            "total_comments": comments_count,
            "total_likes": likes_count,
            "total_views": total_views
        }

        return Response(data, status=status.HTTP_200_OK)

    
    
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
    
    

class HomeLikePostView(APIView):
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
        
        # channel_layer = get_channel_layer()
        # async_to_sync(channel_layer.group_send)(
        #     "notifications_group",
        #     {
        #         "type": "notification_message",
        #         "message": "A new post has been made!"
        #     }
        # )
        return Response({"detail": "commented"}, status=status.HTTP_201_CREATED)

        
        
   
class SearchView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        query = request.query_params.get("query", "").strip()
        
        if not query:
            return Response({"error": "Query parameter 'query' is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Search for users matching the query
        users = User.objects.filter(Q(username__icontains=query) | Q(email__icontains=query))
        user_data = SearchUserSerializer(users, many=True, context={"request": request}).data

        # Search for posts matching the query
        posts = Post.objects.filter(Q(content__icontains=query) | Q(category__name__icontains=query))
        post_data = SearchPostSerializer(posts, many=True).data

        return Response({"users": user_data, "posts": post_data}, status=status.HTTP_200_OK)