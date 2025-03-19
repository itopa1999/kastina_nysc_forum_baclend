from django.urls import path, include
from .views import *

urlpatterns = [
    path(
        "category/",
        include(
            [
                path("", CategoryListCreateView.as_view()),
                path("update/<int:id>/", CategoryUpdateView.as_view()),
                path("details/<int:id>/", CategoryDetailView.as_view())
            ]
        )
    ),
    
    path(
        "post/",
        include(
            [
                path("", PostCreateView.as_view()),
                path("update/<int:id>/", PostUpdateView.as_view()),
                path("details/<int:id>/", PostDetailView.as_view()),
                path("get/user/<str:username>/posts/", UserRandomPostsView.as_view()),
            ]
        )
    ),
    
    path(
        "home/",
        include(
            [
                path("get/posts/", RandomPostsView.as_view()),
                path("get/trending/posts/", TopCommentedPostsView.as_view()),
                path("get/post/<int:post_id>/comments/", HomePostCommentsView.as_view()),
                path("post/<int:post_id>/like/", HomeLikePostView.as_view()),
                path("create/post/comment/", HomeCommentCreateView.as_view()),
            ]
        )
    ),
    
    path("user/",
         include(
            [
                path("get/user/profile/<str:username>/activities/", UserProfileActivitiesView.as_view()),
                path("get/user/<str:username>/posts/", UserRandomPostsView.as_view()),
                path("search/", SearchView.as_view()),
                
            ]
         ))
    
    
]