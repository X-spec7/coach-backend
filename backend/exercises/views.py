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
  GetExerciseRequestDTO,
  UpdateExerciseRequestDTO,
)

class GetExercisesView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def get(self, request):
    serializer = GetExerciseRequestDTO(data=request.query_params)

    if not serializer.is_valid():
      return Response(
        {"message": "Invalid request data", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
      )

    validated_data = serializer.validated_data

    limit = validated_data.get("limit")
    offset = validated_data.get("offset")
    query = validated_data.get("query", None)

    try:
      exercises = Exercise.objects.all()

      if query:
        exercises = exercises.filter(title__icontains=query)
      
      total_exercises_count = exercises.count()

      exercises = exercises[offset:offset + limit]

      serialized_exercises = ExerciseSerializer(exercises, many=True).data

      return Response({
        "message": "Fetched Exercises successfully",
        "exercises": serialized_exercises,
        "totalExercisesCount": total_exercises_count,
      }, status=status.HTTP_200_OK)
    
    except AttributeError as e:
      print("AttributeError:", str(e))
      traceback.print_exc()
      return Response(
        {"error": "Attribute error occurred", "detail": str(e)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )

    except Exception as e:
      return Response(
        {"error": "Failed to fetch session data", "detail": (e)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
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

    max_exercise_id = Exercise.objects.aggregate(Max('id'))['id__max']

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
      format, imgstr = exercise_gif_base64.split(';base64,')
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

class UpdateExerciseView(APIView):
  permission_classes = [IsAuthenticated, IsAdminUserOnly]
  authentication_classes = [JWTAuthentication]

  def post(self, request):
    serializer = UpdateExerciseRequestDTO(data=request.data)

    if not serializer.is_valid():
      return Response(
        {"message": "Invalid request data", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    validated_data = serializer.validated_data

    exercise_id = validated_data.get("exerciseId")

    try:
      exercise = Exercise.objects.get(id=exercise_id)
    except Exercise.DoesNotExist:
      return Response(
        {"message": "Exercise not found"},
        status=status.HTTP_404_NOT_FOUND
      )

    exercise.title = validated_data.get('title', exercise.title)
    exercise.description = validated_data.get('description', exercise.description)
    exercise.calorie_per_round = validated_data.get('caloriePerRound', exercise.calorie_per_round)

    max_exercise_id = Exercise.objects.aggregate(Max('id'))['id__max']

    exercise_icon_base64 = validated_data.get('exerciseIcon')

    if exercise_icon_base64:
      try:
        format, imgstr = exercise_icon_base64.split(';base64,')
        ext = format.split('/')[-1]
        file_name = f"{max_exercise_id + 1}_exercise_icon.{ext}"
        file_path = os.path.join(settings.MEDIA_ROOT, 'exercise_icon_images', file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
          f.write(base64.b64decode(imgstr))
        
        exercise.icon = f"exercise_icon_images/{file_name}"
      except Exception as e:
        return Response({"message": "Failed to save exercise icon", "error": str(e)},
          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Process Exercise GIF
    exercise_gif_base64 = validated_data.get('exerciseGif')
    if exercise_gif_base64:
      try:
        format, imgstr = exercise_gif_base64.split(';base64,')
        ext = format.split('/')[-1]
        file_name = f"{max_exercise_id + 1}_exercise_gif.{ext}"
        file_path = os.path.join(settings.MEDIA_ROOT, 'exercise_gifs', file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
          f.write(base64.b64decode(imgstr))
        
        exercise.gif = f"exercise_gifs/{file_name}"
      except Exception as e:
        return Response({"message": "Failed to save exercise GIF", "error": str(e)},
          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    exercise.save()

    return Response(
      {"message": "Exercise updated successfully"},
      status=status.HTTP_200_OK,
    )
  
class DeleteExerciseView(APIView):
  permission_classes = [IsAuthenticated, IsAdminUserOnly]
  authentication_classes = [JWTAuthentication]

  def delete(self, request, exercise_id):
    try:
      exercise = Exercise.objects.get(id=exercise_id)
      exercise.delete()
      return Response(
        {"message": "Exercise deleted successfully"},
        status=status.HTTP_204_NO_CONTENT
      )
    except Exercise.DoesNotExist:
      return Response(
        {"error": "Exercise not found"},
        status=status.HTTP_404_NOT_FOUND
      )
