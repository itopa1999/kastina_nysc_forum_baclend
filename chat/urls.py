from django.urls import path, include
from .views import *

urlpatterns = [
    path(
        "chat/",
        include(
            [
                path("", ChatGroupListView.as_view()),
                path("get/messages/<str:groupName>/", MessageReadView.as_view()),
                
            ]
        )
    ),
]