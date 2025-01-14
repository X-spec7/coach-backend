import os
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
  GetTotalSessionCountRequestDTO
)
from .util import create_zoom_meeting

logger = logging.getLogger(__name__)

class GetSessionsView(APIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]

  def get(self, request):
    # Deserialize the request data using the provided DTO
    serializer = GetSessionsRequestDTO(data=request.query_params)

    if not serializer.is_valid():
      return Response(
        {"error": "Invalid request data", "details": serializer.errors},
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

      if booked is True:  # If booked is True, filter sessions where the user is in booked_users
        user = request.user  # Get the authenticated user
        sessions_query = sessions_query.filter(booked_users=user)

      total_sessions = sessions_query.count()
      
      # Apply pagination (limit and offset)
      sessions_query = sessions_query[offset:offset + limit]

      session_data = [
        {
          "id": session.id,
          "title": session.title,
          "startDate": session.start_date.isoformat(),
          "duration": session.duration,
          "coachId": session.coach.id,
          "coachFullname": f"{session.coach.first_name} {session.coach.last_name}",
          "goal": session.goal,
          "level": session.level,
          "description": session.description,
          "bannerImageUrl": session.banner_image_url or "",
          "totalParticipantNumber": session.total_participant_number,
          "currentParticipantNumber": session.booked_users.count(),
          "price": session.price,
          "equipments": session.equipments or [],
          "meetingId": session.meeting.id,
          "booked": request.user in session.booked_users.all()
        }
        for session in sessions_query
      ]

      return Response(
        {
          "message": "Sessions fetched successfully.",
          "sessions": session_data,
          "totalSessionCount": total_sessions
        },
        status=status.HTTP_200_OK
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
        {"error": "Failed to fetch session data", "detail": (e)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )
    
class BookSessionView(APIView):
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

    banner_image_url = None 
    if bannerImageBase64:
      format, imgstr = bannerImageBase64.split(';base64,')
      ext = format.split('/')[-1]
      if max_session_id is not None:
        file_name = f"{max_session_id}_session_banner.{ext}"
      else:
        file_name = f"1_session_banner.{ext}"
      file_path = os.path.join(settings.MEDIA_ROOT, 'session_banner_images', file_name)
      os.makedirs(os.path.dirname(file_path), exist_ok=True)

      with open(file_path, "wb") as f:
        f.write(base64.b64decode(imgstr))
      banner_image_url = f"session_banner_images/{file_name}"
    try:
      createMeetingPayload = {
        'topic': title,
        'agenda': description,
        'start_time': startDate,
        'duration': duration,
        'type': 2,
        'settings': {
            'join_before_host': True,
        },
        'user_id': 'me'
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
      meeting.save()

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

      if banner_image_url and banner_image_url != "":
        session.banner_image_url = banner_image_url

      session.save()

      return Response(
        {
          "message": "session created successfully",
          "session": session.id,
          "meeting": meeting.id
        },
        status=status.HTTP_201_CREATED
      )

    except Exception as e:
      logger.error(f"Error creating session: {e}")
      return Response(
        {"error": "Failed to create session"},
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
        {"message": "Created Meeting", "data": zoomRes},
        status=status.HTTP_201_CREATED,
      )
    except Exception as e:
      print(e)
      return Response(
        {"error": "Something went wrong"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
      )