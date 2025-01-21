from django.urls import path
from .views import (
  ContactListView,
  UsersListView,
  MessageListView,
)

urlpatterns = [
  path("contact/get/", view=ContactListView.as_view(), name="get_contact_users"),
  path("messages/<int:otherPersonId>/", MessageListView.as_view(), name="message-list"),
  path("users/search/", view=UsersListView.as_view(), name="search_users"),
]
