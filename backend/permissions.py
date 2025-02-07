from rest_framework.permissions import BasePermission

class IsAdminUserOnly(BasePermission):
  """
  Custom permission to allow only admin users to access the view.
  """

  def has_permission(self, request, view):
    return request.user and request.user.is_staff
  
class IsCoachUserOnly(BasePermission):
  """
  Custom permission to allow only coach users to access the view.
  """

  def has_permission(self, request, view):
    return request.user and request.user.user_type == "Coach"
  
class IsClientUserOnly(BasePermission):
  """
  Custom permission to allow only client users to access the view.
  """

  def has_permission(self, request, view):
    return request.user and request.user.user_type == "Client"
