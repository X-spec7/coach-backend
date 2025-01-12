from django.urls import path
from .views import CreateInstantMeetingView, CreateSessionView, MeetingAuthorizationView

urlpatterns = [
    path("create/instant/", view=CreateInstantMeetingView.as_view(), name="instant meeting"),
    path("create/session/", view=CreateSessionView.as_view(), name="create session"),
    path("auth/", view=MeetingAuthorizationView.as_view(), name="authorize meeting"),
]
