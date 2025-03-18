import jwt
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async


from django.apps import apps

class JWTAuthMiddleware(BaseMiddleware):
    
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token", [None])[0]

        if not token:
            from django.contrib.auth.models import AnonymousUser
            scope["user"] = AnonymousUser()
        else:
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                decoded_data = AccessToken(token)
                user = await get_user(decoded_data["user_id"])
                scope["user"] = user if user else AnonymousUser()
            except jwt.ExpiredSignatureError:
                scope["user"] = AnonymousUser()
            except jwt.InvalidTokenError:
                scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

@database_sync_to_async
def get_user(user_id):
    User = apps.get_model('administrator', 'User')
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None
