from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ParseError

from .models import ChatGroup, Message


 
class ChatGroupListSerializer(serializers.ModelSerializer):
    total_member = serializers.SerializerMethodField()
    class Meta:
        model = ChatGroup
        fields = ['id', 'name', 'display_name', 'description', 'total_member']

    def get_total_member(self, obj):
        return obj.get_members_count()
    
   

  
class MessageReadSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    user_profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'content', 'timestamp','user',
                  'user_profile_picture']
    
    def get_user_profile_picture(self, obj):
        """Returns the profile picture URL for the user"""
        request = self.context.get('request')
        return request.build_absolute_uri(obj.user.profile_picture.url)
    