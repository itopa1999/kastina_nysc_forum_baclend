import os
from administrator import consumers, middlewares
from chat import consumers as chatConsumer
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kastina_forum.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": middlewares.JWTAuthMiddleware( 
            AuthMiddlewareStack(
            URLRouter([
                path("ws/notifications/", consumers.NotificationConsumer.as_asgi()),
                path("ws/chat/<str:groupName>/", chatConsumer.GroupChatConsumer.as_asgi()),
            ])
        )
    ),
})