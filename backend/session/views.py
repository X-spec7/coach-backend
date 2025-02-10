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

from backend.session.models import Session, Meeting
from django.conf import settings
from .dto import (
  GetSessionsRequestDTO,
  GetTotalSessionCountRequestDTO,
  GetMySessionsRequestDTO,
  GetMySessionTotalCountRequestDTO,
)
from .util import create_zoom_meeting

from .serializers import SessionSerializer

logger = logging.getLogger(__name__)

class GetSessionsView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def get(self, request):
    # Deserialize the request data using the provided DTO
    serializer = GetSessionsRequestDTO(data=request.query_params)

    if not serializer.is_valid():
      return Response(
        {"message": "Invalid request data", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    validated_data = serializer.validated_data

    limit = validated_data.get("limit", 10)
    offset = validated_data.get("offset", 0)
    goal = validated_data.get("goal", None)
    booked = validated_data.get("booked", None)
    query = validated_data.get("query", None)

    try:
      sessions_query = Session.objects.all()

      if goal:
        sessions_query = sessions_query.filter(goal__icontains=goal)

      if query:
        sessions_query = sessions_query.filter(title__icontains=query)

      if booked is True:
        user = request.user
        sessions_query = sessions_query.filter(booked_users=user)

      total_sessions = sessions_query.count()
      
      # Apply pagination (limit and offset)
      sessions_query = sessions_query[offset:offset + limit]

      session_data = SessionSerializer(sessions_query, many=True).data

      for session in session_data:
        session_obj = Session.objects.get(id=session["id"])
        booked_users = session_obj.booked_users.all()
        is_booked = booked_users.filter(id=request.user.id).exists()

        session["booked"] = is_booked

      return Response(
        {
          "message": "Sessions fetched successfully.",
          "sessions": session_data,
          "totalSessionCount": total_sessions
        },
        status=status.HTTP_200_OK
      )
    
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
    
class GetSessionTotalCountView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def get(self, request):
    serializer = GetTotalSessionCountRequestDTO(data=request.query_params)

    if not serializer.is_valid():
      return Response(
        {"error": "Invalid request data", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    validated_data = serializer.validated_data

    goal = validated_data.get("goal", None)
    booked = validated_data.get("booked", None)
    query = validated_data.get("query", None)

    try:
      sessions_query = Session.objects.all()

      if goal:
        sessions_query = sessions_query.filter(goal__icontains=goal)
      
      if query:
        sessions_query = sessions_query.filter(title__icontains=query)

      if booked:
        user = request.user
        sessions_query = sessions_query.filter(booked_users = user)

      total_sessions = sessions_query.count()

      return Response(
        {"message": "Fetched session count successfully", "totalSessionCount": total_sessions},
        status=status.HTTP_200_OK
      )
    
    except Exception as e:
      return Response(
        {"error": "Failed to fetch session count", "detail": (e)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
    
class BookSessionView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def post(self, request):
    data = request.data
    user = request.user

    sessionId = data.get("sessionId")
    if sessionId == "":
      return Response(
        {"error": "Invalid request data"},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    try:
      session = Session.objects.get(id=sessionId)

      if session.booked_users.count() >= session.total_participant_number:
        return Response(
          {"error": "Session is fully booked."},
          status=status.HTTP_400_BAD_REQUEST,
        )

      if session.booked_users.filter(id=user.id).exists():
        return Response(
          {"error": "You are already booked for this session."},
          status=status.HTTP_400_BAD_REQUEST,
        )

      session.booked_users.add(user)

      return Response(
        {"message": "Successfully booked the session."},
        status=status.HTTP_200_OK,
      )
    
    except Session.DoesNotExist:
      return Response(
          {"error": "Session not found."},
          status=status.HTTP_404_NOT_FOUND,
      )
    except Exception as e:
      logger.error(f"Error booking session: {e}")
      return Response(
        {"error": "Failed to book session"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
  
class JoinSessionView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def post(self, request):
    data = request.data
    user = request.user

    sessionId = data.get("sessionId", "")
    if sessionId == "":
      return Response(
        {"error": "Invalid request data"},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    session = Session.objects.get(id=sessionId)

    if session.coach.id == user.id:
      return Response(
        {"zoom_url": session.meeting.start_url},
        status=status.HTTP_200_OK
      )
    
    try:
      if not session.booked_users.filter(id=user.id).exists():
        return Response(
          {"error": "You haven't booked in this session yet"},
          status=status.HTTP_400_BAD_REQUEST
        )

      return Response(
        {"zoom_url": session.meeting.join_url},
        status=status.HTTP_200_OK
      )
      
    except Session.DoesNotExist:
      return Response(
        {"error": "Session not found."},
        status=status.HTTP_404_NOT_FOUND,
      )
    except Exception as e:
      logger.error(f"Error joining session: {e}")
      return Response(
        {"error": "Failed to join session"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
    
class CreateSessionView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def post(self, request):
    data = request.data
    user = request.user

    title = data['title']
    startDate = data['startDate']
    duration = data['duration']
    description = data['description']
    goal = data['goal']
    level = data['level']
    totalParticipantNumber = data['totalParticipantNumber']
    price = data['price']
    equipments = data.get('equipments', [])

    max_session_id = Session.objects.aggregate(Max('id'))['id__max']

    bannerImageBase64 = data.get('bannerImage')

    banner_image = None 
    if bannerImageBase64:
      format, imgstr = bannerImageBase64.split(';base64,')
      ext = format.split('/')[-1]
      if max_session_id is not None:
        file_name = f"{max_session_id + 1}_session_banner.{ext}"
      else:
        file_name = f"1_session_banner.{ext}"
      file_path = os.path.join(settings.MEDIA_ROOT, 'session_banner_images', file_name)
      os.makedirs(os.path.dirname(file_path), exist_ok=True)

      with open(file_path, "wb") as f:
        f.write(base64.b64decode(imgstr))
      banner_image = f"session_banner_images/{file_name}"

    try:
      createMeetingPayload = {
        'topic': title,
        'agenda': description,
        'start_time': startDate,
        'duration': duration,
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

      session = Session.objects.create(
        title=title,
        start_date=startDate,
        duration=duration,
        coach=user,
        goal=goal,
        level=level,
        total_participant_number=totalParticipantNumber,
        equipments=equipments,
        price=price,
        meeting=meeting,
      )

      if banner_image and banner_image != "":
        session.banner_image = banner_image

      session.save()

      return Response(
        {
          "message": "session created successfully",
          "sessionId": session.id,
          "meetingId": meeting.id
        },
        status=status.HTTP_201_CREATED
      )

    except Exception as e:
      return Response(
        {"error": "Failed to create session"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
    
class GetMySessionsView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def get(self, request):
    serializer = GetMySessionsRequestDTO(data=request.query_params)

    if not serializer.is_valid():
        return Response(
            {"error": "Invalid request data", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    validated_data = serializer.validated_data

    limit = validated_data.get("limit")
    offset = validated_data.get("offset")
    query = validated_data.get("query", "")

    try:
      sessions_query = Session.objects.all()

      if query:
        sessions_query = sessions_query.filter(title__icontains=query)
      
      session_query = sessions_query.filter(coach=request.user)

      total_sessions = session_query.count()

      sessions_query = sessions_query[offset:offset + limit]

      session_data = []

      for session in sessions_query:
        # Serialize each session object using the SessionSerializer
        serializer = SessionSerializer(session)
        
        # Append the serialized data to the session_data list
        session_data.append(serializer.data)

      # Now you can use `session_data` to return a response
      return Response(
        {
          "message": "Sessions fetched successfully.",
          "sessions": session_data,
          "totalSessionCount": total_sessions
        },
        status=status.HTTP_200_OK
      )
    
    except ProgrammingError as e:
      # Log the error for debugging purposes
      print(f"Database error: {str(e)}")
      return Response(
        {"error": "Database error occurred", "detail": str(e)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
    
    except AssertionError as e:
      # Log the full traceback for debugging
      print("AssertionError:", str(e))
      traceback.print_exc()
      return Response(
        {"error": "Assertion error occurred", "detail": str(e)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
    
    except AttributeError as e:
      # Log the full traceback for debugging
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
    
class GetMySessionTotalCountView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def get(self, request):
    serializer = GetMySessionTotalCountRequestDTO(data=request.query_params)

    if not serializer.is_valid():
      return Response(
        {"error": "Invalid request data", "details": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
      )
    
    validated_data = serializer.validated_data
    query = validated_data.get("query")

    try:
      sessions_query = Session.objects.all()

      if query:
        sessions_query = sessions_query.filter(title__icontains=query)

      total_sessions = sessions_query.count()

      return Response(
        {"message": "Fetched my session count successfully", "totalSessionCount": total_sessions},
        status=status.HTTP_200_OK
      )
    except Exception as e:
      return Response(
        {"error": "Failed to fetch session count", "detail": (e)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )

class CreateMeetingView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def post(self, request):
    try:
      createMeetingPayload = {
        'type': 1,
        'settings': {
          'join_before_host': True,
        },
        'user_id': "me"
      }
      zoomRes = create_zoom_meeting(createMeetingPayload)

      return Response(
        {
          "message": "Created Meeting",
          "joinUrl": zoomRes.get("join_url"),
          "startUrl": zoomRes.get("start_url")
        },
        status=status.HTTP_201_CREATED,
      )
    except Exception as e:
      print(e)
      return Response(
        {"error": "Something went wrong"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
      )
