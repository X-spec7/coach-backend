from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from backend.users.api.views import UserViewSet
from django.urls import path, include

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)

sub_urls = [
    path('authentication/', include('users.api.urls')),
    path('users/', include('users.urls')),
    path("chat/", include('chat.urls')),
    path("session/", include('session.urls')),
    path("classes/", include('classes.urls')),
]

app_name = "api"
urlpatterns = router.urls + sub_urls
