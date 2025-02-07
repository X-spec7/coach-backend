import os
import traceback
from django.conf import settings
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

from backend.exercises.models import Exercise
from backend.permissions import IsAdminUserOnly
from .serializers import (
  ExerciseSerializer,
  CreateExerciseRequestDTO,
)

class CreateExerciseView(APIView):
  permission_classes = [IsAuthenticated, IsAdminUserOnly]
  authentication_classes = [JWTAuthentication]

  def post(self, request):
    serializer = CreateExerciseRequestDTO(data=request.data)

    if not serializer.is_valid():
      return Response(
        {"message": "Invalid request data", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    validated_data = serializer.validated_data

    title = validated_data.get('title')
    description = validated_data.get('description')
    calorie_per_round = validated_data.get('caloriePerRound')

    max_exercise_id = Exercise.objects.aggregate(Max('id'))['id_max']

    exercise_icon_base64 = validated_data.get('exerciseIcon')

    icon = None
    if exercise_icon_base64:
      format, imgstr = exercise_icon_base64.split(';base64,')
      ext = format.split('/')[-1]
      if max_exercise_id is not None:
        file_name = f"{max_exercise_id + 1}_exercise_icon.{ext}"
      else:
        file_name = f"1_exercise_icon.{ext}"
      file_path = os.path.join(settings.MEDIA_ROOT, 'exercise_icon_images', file_name)
      os.makedirs(os.path.dirname(file_path), exist_ok=True)

      with open(file_path, "wb") as f:
        f.write(base64.b64decode(imgstr))
      icon = f"exercise_icon_images/{file_name}"
    
    exercise_gif_base64 = validated_data.get('exerciseGif')

    gif = None
    if exercise_gif_base64:
      format, imgstr = exercise_icon_base64.split(';base64,')
      ext = format.split('/')[-1]
      if max_exercise_id is not None:
        file_name = f"{max_exercise_id + 1}_exercise_gif.{ext}"
      else:
        file_name = f"1_exercise_gif.{ext}"
      file_path = os.path.join(settings.MEDIA_ROOT, 'exercise_gifs', file_name)
      os.makedirs(os.path.dirname(file_path), exist_ok=True)

      with open(file_path, "wb") as f:
        f.write(base64.b64decode(imgstr))
      gif = f"exercise_gifs/{file_name}"
    
    try:
      exercise = Exercise.objects.create(
        title=title,
        description=description,
        calorie_per_round=calorie_per_round,
      )

      if icon and icon != "":
        exercise.icon = icon
      if gif and gif != "":
        exercise.gif = gif

      exercise.save()

      serialized_exercise = ExerciseSerializer(exercise)

      return Response(
        {
          "message": "Exercise created successfully",
          "exercise": serialized_exercise.data,
        },
        status=status.HTTP_201_CREATED,
      )

    except Exception as e:
      return Response(
        {"error": "Failed to create session"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
