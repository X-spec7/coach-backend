from rest_framework.permissions import BasePermission

class IsAdminUserOnly(BasePermission):
  """
  Custom permission to allow only admin users to access the view.
  """

  def has_permission(self, request, view):
    return request.user and request.user.is_staff
  