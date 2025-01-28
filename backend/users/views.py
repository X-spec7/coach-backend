import os
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
import base64
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from backend.users.models import User
from .serializers import UserSerializer
from django.conf import settings

class GetUserProfileView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def get(self, request):
      user = request.user

      return Response(
          {
              "message": "Successfully fetched user profile",
              "user": UserSerializer(user).data,
          },
          status=status.HTTP_200_OK,
      )
  
class UpdateUserProfileView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def post(self, request):
    try:
        data = request.data
        user = request.user

        # Update user profile fields if they are not blank
        if 'phone_number' in data and data['phoneNumebr']:
            user.phone_number = data['phoneNumber']
        if 'address' in data and data['address']:
            user.address = data['address']
        if 'first_name' in data and data['firstName']:
            user.first_name = data['firstName']
        if 'last_name' in data and data['lastName']:
            user.last_name = data['lastName']

        avatar_image_base64 = data.get('avatarImage')
        if avatar_image_base64:
            # Decode the Base64 string
            format, imgstr = avatar_image_base64.split(';base64,')  # Split format and data
            ext = format.split('/')[-1]  # Extract the image file extension (e.g., jpg, png)
            file_name = f"{user.id}_avatar.{ext}"
            file_path = os.path.join(settings.MEDIA_ROOT, 'avatar_images', file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure the directory exists

            # Save the file
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(imgstr))

            # Save the relative path to the user's profile
            user.avatar_image = f"avatar_images/{file_name}"

        user.save()

        userSerializer = UserSerializer(user)
        return Response(
            {
                "message": "Profile Updated successfully.",
                "user": userSerializer.data,
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response({"error": str(e)}, status=400)
