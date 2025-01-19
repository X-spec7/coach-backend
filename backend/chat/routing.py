from django.urls import re_path
from backend.chat.consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r'chat/(?P<userId>\w+)/$', ChatConsumer.as_asgi())
]
