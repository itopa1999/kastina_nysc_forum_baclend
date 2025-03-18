from django.db import models
from administrator.models import User
import re
# Create your models here.

class ChatGroup(models.Model):
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100, null=True)
    description = models.TextField()
    
    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['name'])
        ]
        
    def save(self, *args, **kwargs):
        self.display_name = self.name
        self.name = self.sanitize_name(self.name)
        
        super().save(*args, **kwargs)  # Call the original save method

    def sanitize_name(self, name):
        """Sanitize the name by replacing any character that's not alphanumeric with an underscore."""
        return re.sub(r'[^a-zA-Z0-9]', '_', name)
    
    

    def __str__(self):
        return self.name
    
    def get_members_count(self):
        return self.chatgroupmembership_set.count()

class ChatGroupMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE)

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['group', 'user']),
        ]
        
        
    def __str__(self):
        return f'{self.user.username} in {self.group.name}'

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'group']),
        ]

    def __str__(self):
        return f'Message from {self.user.username} in {self.group.name} at {self.timestamp}'