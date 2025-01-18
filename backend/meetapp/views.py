import os
import requests
import base64
from django.shortcuts import render
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication

from .dto import CreateSessionRequestDTO, CreateInstantMeetingRequestDTO, MeetingAuthorizationRequestDTO
from .util import create_zoom_meeting, create_auth_signature

class CreateInstantMeetingView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            serializer = CreateInstantMeetingRequestDTO(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {"error": "Invalid request data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            validated_data = serializer.validated_data

            recipient_id = validated_data["recipient_id"]

            # TODO: implement actual handler
            data = {
                'type': 1,
                'settings': {
                    'join_before_host': True,
                },
                'user_id': "me"
            }
            response = create_zoom_meeting(data)

            return Response(
                {"message": "Meeting scheduled", 'res': response},
                status.HTTP_201_CREATED
            )
        except Exception as e:
            print(e)
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class CreateSessionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            serializer = CreateSessionRequestDTO(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {"error": "Invalid request data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data

            meeting_type = validated_data["meeting_type"]
            topic = validated_data["topic"]
            agenda = validated_data["agenda"]
            category = validated_data["category"]
            start_time = validated_data["start_time"]
            duration = validated_data["duration"]

        except Exception as e:
            print(e)
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
class MeetingAuthorizationView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, format=None):
        try:
            serializer = CreateSessionRequestDTO(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {"error": "Invalid request data", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            zoom_id = validated_data["meeting_id"]
            role = validated_data["role"]

            response = create_auth_signature(zoom_id, role)
            response["zoom_id"] = zoom_id
            
            return Response(response, status.HTTP_200_OK)
        
        except Exception as e:
            print(e)
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
