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
from backend.users.models import User, CoachProfile, Certification
from django.conf import settings

from .serializers import (
  CoachSerializer,
  ClientSerializer,
  GetCoachesRequestDTO,
)

class GetUserProfileView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def get(self, request):
      user = request.user

      user_serializer = ClientSerializer(user)

      if user.user_type == "Coach":
        user_serializer = CoachSerializer(user)
      elif user.user_type == "Client":
        user_serializer = ClientSerializer(user)

      return Response(
          {
              "message": "Successfully fetched user profile",
              "user": user_serializer.data,
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

        userSerializer = ClientSerializer(user)
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
    certifications_data = data.get("certifications", [])

    print(f"certifications data ----------------------------> {certifications_data}")

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

      # Handle Avatar Image Upload
      if avatar_image_base64:
        format, imgstr = avatar_image_base64.split(';base64,')  
        ext = format.split('/')[-1]
        file_name = f"{user.uuid}_avatar.{ext}"
        file_path = os.path.join(settings.MEDIA_ROOT, 'avatar_images', file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
          f.write(base64.b64decode(imgstr))

        user.avatar_image = f"avatar_images/{file_name}"

      # Handle Banner Image Upload
      if banner_image_base64:
        format, imgstr = banner_image_base64.split(';base64,')  
        ext = format.split('/')[-1]
        file_name = f"{user.uuid}_banner.{ext}"
        file_path = os.path.join(settings.MEDIA_ROOT, 'banner_images', file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
          f.write(base64.b64decode(imgstr))

        coach_profile.banner_image = f"banner_images/{file_name}"

      # Handle Certifications
      existing_certifications = {cert.certification_title: cert for cert in coach_profile.certifications.all()}
      print(f"existing certifications -------------------------> {existing_certifications}")
      updated_certification_titles = set()

      for cert_data in certifications_data:
        title = cert_data.get("certificationTitle", "").strip()
        detail = cert_data.get("certificationDetail", "").strip()

        if title and detail:
          if title in existing_certifications:
            # Update existing certification
            certification = existing_certifications[title]
            certification.certification_detail = detail
            certification.save()
          else:
            # Create new certification
            Certification.objects.create(
              coach=coach_profile,
              certification_title=title,
              certification_detail=detail
            )

          updated_certification_titles.add(title)

      # Delete removed certifications
      for title in existing_certifications:
        if title not in updated_certification_titles:
          existing_certifications[title].delete()

      with transaction.atomic():
        user.save()
        coach_profile.save()

      coach_serializer = CoachSerializer(user)

      return Response(
        {
            "message": "Profile updated successfully",
            "user": coach_serializer.data
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

class GetCoachesView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def get(self, request):
    serializer = GetCoachesRequestDTO(data=request.query_params)

    if not serializer.is_valid():
      return Response(
        {"message": "Invalid request data", "details": serializer.error},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    validated_data = serializer.validated_data

    limit = validated_data.get("limit", 10)
    offset = validated_data.get("offset", 0)
    query = validated_data.get("query")

    users_query = User.objects.all()
    users_query = users_query[offset:offset + limit]
