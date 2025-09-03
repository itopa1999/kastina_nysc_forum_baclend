import jwt
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.exceptions import TokenError

from django.apps import apps

class JWTAuthMiddleware(BaseMiddleware):
    
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token", [None])[0]

        if not token:
            from django.contrib.auth.models import AnonymousUser
            scope["user"] = AnonymousUser()
            return await super().__call__(scope, receive, send)
        else:
            from django.contrib.auth.models import AnonymousUser
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                decoded_token = AccessToken(token)
                decoded_token.verify()  # Explicit verification
                user = await get_user(decoded_token["user_id"])
                scope["user"] = user or AnonymousUser()
            except TokenError as e:
                # Catches ALL JWT errors (expired, invalid, etc)
                print(f"Token error: {str(e)}")  # Log for debugging
                scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)


@database_sync_to_async
def get_user(user_id):
    User = apps.get_model('administrator', 'User')
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None
