from django.urls import path
from .views import (
  ContactListView
)

urlpatterns = [
  path("contact/get/", view=ContactListView.as_view(), name="get contact users")
]
