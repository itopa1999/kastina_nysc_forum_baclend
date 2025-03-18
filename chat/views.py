from django.shortcuts import render

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.pagination import PageNumberPagination

from .models import ChatGroup, Message
from .serializers import ChatGroupListSerializer, MessageReadSerializer


# Create your views here.


class ChatGroupListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatGroupListSerializer

    def get_queryset(self):
        return ChatGroup.objects.only(
            'id', 'name','display_name','description'
        ).order_by('?')

    
    pagination_class = PageNumberPagination
    
    
    
class MessageReadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageReadSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        groupName = self.kwargs['groupName']

        # Query the posts filtered by the provided username
        queryset = Message.objects.only(
            'id', 'content', 'timestamp','user__username'
        ).filter(group__name=groupName)

        # Order the posts randomly
        return queryset