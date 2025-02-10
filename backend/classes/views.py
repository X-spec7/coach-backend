import os
import traceback
import base64
from django.db import transaction
from django.db.models import Max
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from django.shortcuts import get_object_or_404

from backend.classes.models import Class
from backend.exercises.models import ClassExercise, Exercise
from backend.session.models import ClassSession, Meeting
from backend.permissions import IsCoachUserOnly, IsClientUserOnly
from backend.util.zoom_meeting import create_zoom_meeting

from .serializers import (
  GetClassesRequestDTO,
  ClassSerializer,
  CreateClassRequestSerializer,
)

class CreateClassView(APIView):
  permission_classes = [IsAuthenticated, IsCoachUserOnly]
  authentication_classes = [JWTAuthentication]

  def post(self, request):
    user = request.user

    serializer = CreateClassRequestSerializer(data=request.data)

    if not serializer.is_valid():
      return Response(
        {"message": "Invalid request data", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
      )
    
    validated_data = serializer.validated_data
    
    bannerImageBase64 = validated_data.pop("banner_image")
    exercises = validated_data.pop("exercises")
    sessions = validated_data.pop("sessions")

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

      with transaction.atomic():
        new_class = Class.objects.create(
          coach=user,
          **validated_data
        )

        if banner_image and banner_image != "":
          new_class.banner_image = banner_image

        new_class.save()

        allowed_exercise_fields = {"set_count", "reps_count", "rest_duration", "calorie_per_set"}

        for exercise in exercises:
          exercise_id = exercise.pop("id")
          exercise_ref = None
          try:
            exercise_ref = Exercise.objects.get(id=exercise_id)
          except Exercise.DoesNotExist:
            return Response(
              {"error": f"Exercise with ID {exercise_id} does not exist"},
              status=status.HTTP_400_BAD_REQUEST
            )

          filtered_exercise_data = {k: v for k, v in exercise.items() if k in allowed_exercise_fields}

          print(f"filtered exercise -----------------------------> {filtered_exercise_data}")

          try:
            ClassExercise.objects.create(
              class_ref=new_class,
              exercise_ref=exercise_ref,
              **filtered_exercise_data,
            )

          except Exception as e:
            return Response(
              {"error": "Failed to create ClassExercise", "details": str(e)},
              status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        allowed_session_fields = {
          "title",
          "start_date",
          "duration",
          "description",
          "total_participant_number",
          "calorie",
          "equipments",
        }
        
        for session in sessions:
          print(f"session ----------------------------> {session}")
          createMeetingPayload = {
            'topic': session["title"],
            'agenda': session["description"],
            'duration': session["duration"],
            'type': 2,
            'settings': {
              'join_before_host': False,
              'waiting_room': True,
            },
            'user_id': 'me',
          }

          zoomRes = create_zoom_meeting(createMeetingPayload)

          meeting = Meeting.objects.create(
            start_time=zoomRes.get('start_time'),
            duration=zoomRes.get('duration'),
            meeting_number=zoomRes.get('id'),
            encrypted_password=zoomRes.get('encrypted_password'),
            join_url=zoomRes.get('join_url'),
            start_url=zoomRes.get('start_url'),
            creator=user,
          )

          filtered_session_data = {k: v for k, v in session.items() if k in allowed_session_fields}

          try:
            class_session = ClassSession.objects.create(
              class_ref=new_class,
              meeting=meeting,
              **filtered_session_data
            )
          except Exception as e:
            return Response(
              {"error": "Failed to create ClassExercise", "details": str(e)},
              status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

          print(f"class session created ----------------------------> {class_session}")

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
        {"message": "Invalid request data", "details": serializer.errors},
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
      if query and query != '':
        classes_query = classes_query.filter(title__icontains=query)
      if category and category != '':
        classes_query = classes_query.filter(cateogry__icontains=category)
      if level and level != '':
        classes_query = classes_query.filter(level__icontains=level)

      total_count = classes_query.count()
      classes = classes_query[offset:offset + limit]

      serialized_classes = ClassSerializer(classes, many=True, context={"request": request})

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

class GetClassByIdView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def get(self, request, class_id):
    try:
      spec_class = get_object_or_404(Class, id=class_id)

      serialized_class = ClassSerializer(spec_class, context={"request": request})

      return Response(
        {
          "message": "Got class successfully",
          "class": serialized_class.data,
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

class BookClassView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def post(self, request, class_id):
    try:
      target_class = get_object_or_404(Class, id=class_id)

      if request.user in target_class.booked_users.all():
        return Response(
          {"message": "You have already booked this class."},
          status=status.HTTP_400_BAD_REQUEST,
        )

      target_class.booked_users.add(request.user)

      serialized_class = ClassSerializer(target_class, context={"request": request})

      return Response(
        {
          "message": "Class booked successfully.",
          "class": serialized_class.data,
        },
        status=status.HTTP_200_OK,
      )

    except Exception as e:
      return Response(
        {"message": "An error occurred while booking the class", "detail": str(e)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
      )
    
class JoinClassSessionView(APIView):
  permission_classes = [IsAuthenticated, IsClientUserOnly]
  authentication_classes = [JWTAuthentication]

  def get(self, request, class_session_id):
    class_session = get_object_or_404(ClassSession, id=class_session_id)
    class_ref = class_session.class_ref

    user = request.user

    if user not in class_ref.booked_users.all():
      return Response(
        {"message": "You must book this class before joining."},
        status=status.HTTP_403_FORBIDDEN
      )

    return Response(
      {
        "message": "Successfully fetched class session join URL",
        "joinUrl": class_session.meeting.join_url,
      },
      status=status.HTTP_200_OK,
    )

class StartClassSessionView(APIView):
  permission_classes = [IsAuthenticated, IsCoachUserOnly]
  authentication_classes = [JWTAuthentication]

  def get(self, request, class_session_id):
    class_session = get_object_or_404(ClassSession, id=class_session_id)
    class_ref = class_session.class_ref

    user = request.user
  
    if class_ref.coach.id == user.id:
      return Response(
        {
          "message": "Successfully fetched class session start url",
          "startUrl": class_session.meeting.start_url,
        },
        status=status.HTTP_200_OK,
      )
    else:
      return Response(
        {"message": "You are not the creator of this class session"},
        status=status.HTTP_403_FORBIDDEN,
      )
