import os
import traceback
from django.db import ProgrammingError
import requests
import base64
from django.shortcuts import render
from django.db.models import Max
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging

from backend.classes.models import Class
from django.conf import settings

from .serializers import (
  GetClassesRequestDTO,
  ClassSerializer,
)

class CreateClassView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def post(self, request):
    data = request.data
    user = request.user

    if user.user_type != "Coach":
      return Response({"message": "Only coaches can create class",}, status=status.HTTP_403_FORBIDDEN)
    
    title = data["title"]
    category = data["category"]
    description = data["description"]
    intensity = data["intensity"]
    level = data["level"]
    price = data["price"]
    benefits = data["benefits"]
    equipments = data["equipments"]
    
    bannerImageBase64 = data.get('bannerImage')

    try:
      max_class_id = Class.objects.aggregate(Max('id'))['id__max']

      banner_image = None 
      if bannerImageBase64:
        format, imgstr = bannerImageBase64.split(';base64,')
        ext = format.split('/')[-1]
        
        if max_class_id is not None:
          file_name = f"{max_class_id + 1}_class_banner.{ext}"
        else:
          file_name = f"1_class_banner.{ext}"
        file_path = os.path.join(settings.MEDIA_ROOT, 'class_banner_images', file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
          f.write(base64.b64decode(imgstr))
        banner_image = f"class_banner_images/{file_name}"

      new_class = Class.objects.create(
        coach=user,
        title=title,
        category=category,
        description=description,
        intensity=intensity,
        level=level,
        price=price,
        benefits=benefits,
        equipments=equipments,
      )

      if banner_image and banner_image != "":
        new_class.banner_image = banner_image

      new_class.save()

      return Response(
        {"message": "class created successfully"},
        status=status.HTTP_201_CREATED
      )
    except Exception as e:
      return Response(
        {"error": "Failed to create session"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
    
class GetClassesView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def get(self, request):
    serializer = GetClassesRequestDTO(data=request.query_params)

    if not serializer.is_valid():
      return Response(
        {"message": "Invalid request data", "details": serializer.error},
        status=status.HTTP_400_BAD_REQUEST
      )

    validated_data = serializer.validated_data

    limit = validated_data.get("limit", 15)
    offset = validated_data.get("offset", 0)
    query = validated_data.get("query")
    category = validated_data.get("category")
    level = validated_data.get("level")

    try:
      classes_query = Class.objects.all()
      if query and query is not '':
        classes_query = classes_query.filter(title__icontains=query)
      if category and category is not '':
        classes_query = classes_query.filter(cateogry__icontains=category)
      if level and level is not '':
        classes_query = classes_query.filter(level__icontains=level)

      total_count = classes_query.count()
      classes = classes_query[offset:offset + limit]

      serialized_classes = ClassSerializer(classes, many=True)

      # TODO: implement getting my classes, featured class, and recommended classes
      return Response(
        {
          "message": "Got classes successfully",
          "classes": serialized_classes.data,
          "totalClassesCount": total_count,
        },
        status=status.HTTP_200_OK,
      )
    
    except AttributeError as e:
      print("AttributeError:", str(e))
      traceback.print_exc()
      return Response(
        {"message": "Attribute error occurred", "detail": str(e)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )

    except Exception as e:
      return Response(
        {"message": "Attribute error occurred", "detail": str(e)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )