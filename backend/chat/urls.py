from django.urls import path
from .views import (
  ContactListView,
  UsersListView
)

urlpatterns = [
  path("contact/get/", view=ContactListView.as_view(), name="get_contact_users"),
  path("users/search/", view=UsersListView.as_view(), name="search_users")
]
