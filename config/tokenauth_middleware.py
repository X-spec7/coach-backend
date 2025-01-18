from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.tokens import AccessToken
from channels.db import database_sync_to_async

@database_sync_to_async
def get_user_from_token(token_key):
    try:
        access_token = AccessToken(token_key)
        return access_token.payload['user_id']
    except Exception:
        return None
    
@database_sync_to_async
def get_user(user_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()
    
class TokenAuthMiddleware(BaseMiddleware):

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope['query_string'].decode()
        token_key = None

        if 'token=' in query_string:
            token_key = query_string.split('token=')[-1]

        user = AnonymousUser()
        if token_key:
            user_id = await get_user_from_token(token_key)
            if user_id:
                user = await get_user(user_id)

        scope['user'] = user
        return await super().__call__(scope, receive, send)