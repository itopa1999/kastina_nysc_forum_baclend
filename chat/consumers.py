import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from django.apps import apps

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get the group name from the URL
        self.group_name = self.scope['url_route']['kwargs']['groupName']
        
        self.user = self.scope.get('user', None)

        if self.user is None or self.user.is_anonymous:
            await self.close() 
            return

        # Check if the user is a member of the group, or create a new membership if they aren't
        is_member = await self.user_is_member(self.user, self.group_name)
        if not is_member:
            # Add user to the group if they are not already a member
            group = await self.get_group(self.group_name)
            await self.add_user_to_group(self.user, group)

        # Add the user to the group channel
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Notify the group that a new user has joined
        await self.notify_group('join')

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Notify the group that the user has left
        await self.notify_group('leave')

        # Remove the user from the group
        group = await self.get_group(self.group_name)
        await self.remove_user_from_group(self.user, group)

        # Remove the user from the group channel
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message  = text_data_json.get("message")
        is_typing = text_data_json.get('is_typing', False)
        
        profile_picture = await self.get_profile_picture(self.user)

        # Send the message to the group if it's not just typing status
        if message:
            await self.save_message(message)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'user': self.user.username,
                    'profile_picture': profile_picture,
                    'is_typing': False
                }
            )
        elif is_typing:
            # Notify the group that a user is typing
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'user_typing',
                    'user': self.user.username,
                    'is_typing': True
                }
            )

    async def chat_message(self, event):
        
        from django.utils import timezone
        # Send the message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event.get("message", ""),
            'user': event['user'],
            'profile_picture': event['profile_picture'],
            'is_typing': event['is_typing'],
            "timestamp": f"{timezone.now()}"
        }))

    async def user_typing(self, event):
        # Show who is typing in the group
        await self.send(text_data=json.dumps({
            'user': event.get("user", ""),
            'is_typing': True,
        }))

    async def notify_group(self, action):
        # Notify the group when a user joins or leaves
        group_members = await self.get_group_members(self.group_name)
        total_members = len(group_members)

        if action == 'join':
            message = f'{self.user.username} has joined the group.'
        else:
            message = f'{self.user.username} has left the group.'

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'user_join_leave',
                'message': message,
                'total_members': total_members
            }
        )
        
        
    async def user_join_leave(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'total_members': event['total_members']
        }))

    @database_sync_to_async
    def user_is_member(self, user, group_name):
        ChatGroup = apps.get_model('chat', 'ChatGroup')
        ChatGroupMembership = apps.get_model('chat', 'ChatGroupMembership')
        try:
            group = ChatGroup.objects.get(name=group_name)
            return ChatGroupMembership.objects.filter(user__id=user.id, group=group).exists()
        except ChatGroup.DoesNotExist:
            return False

    @database_sync_to_async
    def add_user_to_group(self, user, group):
        ChatGroupMembership = apps.get_model('chat', 'ChatGroupMembership')
        group_membership = ChatGroupMembership(user=user, group=group)
        group_membership.save()

    @database_sync_to_async
    def remove_user_from_group(self, user, group):
        ChatGroupMembership = apps.get_model('chat', 'ChatGroupMembership')
        group_membership = ChatGroupMembership.objects.get(user=user, group=group)
        group_membership.delete()

    @database_sync_to_async
    def get_group(self, group_name):
        ChatGroup = apps.get_model('chat', 'ChatGroup')
        return ChatGroup.objects.get(name=group_name)

    @database_sync_to_async
    def save_message(self, message):
        ChatGroup = apps.get_model('chat', 'ChatGroup')
        Message = apps.get_model('chat', 'Message')
        group = ChatGroup.objects.get(name=self.group_name)
        msg = Message(user=self.user, group=group, content=message)
        msg.save()

    @database_sync_to_async
    def get_group_members(self, group_name):
        ChatGroup = apps.get_model('chat', 'ChatGroup')
        ChatGroupMembership = apps.get_model('chat', 'ChatGroupMembership')
        group = ChatGroup.objects.get(name=group_name)
        members = ChatGroupMembership.objects.filter(group=group)
        return [member.user.username for member in members]
    
    @database_sync_to_async
    def get_profile_picture(self, user):
    
        return f"http://127.0.0.1:8000{user.profile_picture.url}"
