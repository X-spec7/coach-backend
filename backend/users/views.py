import os
import traceback
from django.db import transaction
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
import base64
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from backend.users.models import User, CoachProfile
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
  
class UpdateClientProfileView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def post(self, request):
    try:
        data = request.data
        user = request.user

        phone_number = data.get("phoneNumber", "")
        address = data.get("address", "")
        first_name = data.get("firstName", "")
        last_name = data.get("lastName", "")

        user.phone_number = phone_number
        user.address = address
        user.first_name = first_name
        user.last_name = last_name

        avatar_image_base64 = data.get('avatar')
        if avatar_image_base64:
            # Decode the Base64 string
            format, imgstr = avatar_image_base64.split(';base64,')  # Split format and data
            ext = format.split('/')[-1]  # Extract the image file extension (e.g., jpg, png)
            file_name = f"{user.uuid}_avatar.{ext}"
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
        return Response(
          {"message": str(e)},
          status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class UpdateCoachProfileView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def post(self, request):
    data = request.data
    user = request.user

    first_name = data.get("firstName", "")
    last_name = data.get("lastName", "")
    address = data.get("address", "")
    phone_number = data.get("phoneNumber", "")
    years_of_experience = data.get("yearsOfExperience", 0)
    specialization = data.get("specialization", "")

    avatar_image_base64 = data.get("avatar")
    banner_image_base64 = data.get("banner")

    try:
      coach_profile, created = CoachProfile.objects.get_or_create(user=user)

      user.phone_number = phone_number
      user.address = address
      user.first_name = first_name
      user.last_name = last_name
      
      coach_profile.years_of_experience = years_of_experience
      coach_profile.specialization = specialization

      if avatar_image_base64:
        format, imgstr = avatar_image_base64.split(';base64,')  # Split format and data
        ext = format.split('/')[-1]
        file_name = f"{user.uuid}_avatar.{ext}"
        file_path = os.path.join(settings.MEDIA_ROOT, 'avatar_images', file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure the directory exists

        # Save the file
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(imgstr))

        user.avatar_image = f"avatar_images/{file_name}"

      if banner_image_base64:
        format, imgstr = banner_image_base64.split(';base64,')  # Split format and data
        ext = format.split('/')[-1]
        file_name = f"{user.uuid}_banner.{ext}"
        file_path = os.path.join(settings.MEDIA_ROOT, 'banner_images', file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure the directory exists

        # Save the file
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(imgstr))

        coach_profile.banner_image = f"banner_images/{file_name}"
      
      with transaction.atomic():
        user.save()
        coach_profile.save()
      
      user_serializer = UserSerializer(user)
      
      return Response(
        {
          "message": "Profile updated successfully",
          "user": user_serializer.data
        },
        status=status.HTTP_200_OK
      )

    except AssertionError as e:
      traceback.print_exc()
      return Response(
          {"message": "Assertion error occurred", "detail": str(e)},
          status=status.HTTP_500_INTERNAL_SERVER_ERROR,
      )

    except Exception as e:
      traceback.print_exc()
      return Response(
          {"message": "An error occurred", "detail": str(e)},
          status=status.HTTP_500_INTERNAL_SERVER_ERROR,
      )
