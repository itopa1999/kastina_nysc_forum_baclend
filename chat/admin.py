from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(ChatGroup)
admin.site.register(ChatGroupMembership)
admin.site.register(Message)