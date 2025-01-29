from django.db import transaction
import os
import requests

from django.contrib.auth import authenticate, login
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django_ratelimit.decorators import ratelimit

from backend.users.models import CoachProfile, User

from ..serializers import ClientSerializer, LoginSerializer

def send_mail(email, content):
    apiKey = os.getenv("ELASTIC_API_KEY")
    registeredEmail = os.getenv("ElASTIC_REGISTERED_EMAIL")

    print("api key: ", apiKey)
    print("registered email: ", registeredEmail)

    email_params = {
        "apikey": os.getenv("ELASTIC_API_KEY"),
        "from": os.getenv("ElASTIC_REGISTERED_EMAIL"),
        "to": email,
        "subject": "Email Verify - Coach Account",
        "bodyHtml": f"{content}",
        # "isTransactional": True,
    }

    response = requests.post(
        "https://api.elasticemail.com/v2/email/send",
        data=email_params,
    )
    return response

def send_mailgun_mail(to_mail, content):
    try:
        MAILGUN_API_URL = "https://api.mailgun.net/v3/sandbox5023f2da06d8495cbcb235139417e7bf.mailgun.org/messages"
        api_key = os.getenv("MAILGUN_API_KEY")

        print('api key', api_key)
        
        FROM_EMAIL_ADDRESS = "John Doe <mercury.spec77@gmail.com>"

        resp = requests.post(MAILGUN_API_URL, auth=("api", api_key),
            data={"from": FROM_EMAIL_ADDRESS,
            "to": to_mail, "subject": "Email verification", "text": f"{content}"})
        return resp

    except Exception as ex:
        print(f"Mailgun error: {ex}")

class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = ClientSerializer
    queryset = User.objects.all()
    lookup_field = "pk"

    def get_queryset(self, *args, **kwargs):
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False)
    def me(self, request):
        serializer = ClientSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny,]
    authentication_classes = ()

    # TODO: increase rate limit 
    # @ratelimit(key='ip', rate='5/min')
    def post(self, request):
        try:
            data = request.data
            firstName = data["firstName"]
            lastName = data["lastName"]
            role = data["userType"]
            email = data["email"]
            password = data["password"]

            if password:
                if len(password) >= 6:
                    if not User.objects.filter(email=email).exists():
                        with transaction.atomic():
                            user = User.objects.create_user(
                                email=email,
                                full_name=f"{firstName} {lastName}",
                                first_name=firstName,
                                last_name=lastName,
                                user_type=role,
                                password=password,
                                email_verified=True,
                            )

                            # If the user type is "Coach", create the CoachProfile
                            if role == "Coach":
                                CoachProfile.objects.create(user=user)
                        if User.objects.filter(email=email).exists():

                            return Response(
                                {"message": "User created successfully"},
                                status=status.HTTP_201_CREATED
                            )

                            # TODO: implement email verification logic
                        else:
                            return Response(
                                {"message": "Something went wrong creating user"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            )
                    else:
                        return Response(
                            {"message": "Username already exists"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                else:
                    return Response(
                        {"message": "Password must be at least 6 characters long"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {"message": "Passwords do not match"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            print(e)
            return Response(
                {"message": "Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MailVerifyView(APIView):
    def post(self, request):
        user = request.user
        user.email_verified = True
        user.save()
        return Response({"success": "Email verified"}, status=status.HTTP_200_OK)

class LoginView(APIView):
    permission_classes = [AllowAny,]
    authentication_classes = ()

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]
            user = authenticate(request, email=email, password=password)
            userSerializer = ClientSerializer(user)
            if user is not None:
                if user.email_verified:
                    login(request, user)
                    refresh = RefreshToken.for_user(user)
                    return Response(
                        {
                            "message": "Successfully Logged in",
                            "token": str(refresh.access_token),
                            "user": userSerializer.data,
                        },
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {
                            "message": "Email not verified",
                        },
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            else:
                return Response(
                    {
                        "message": "Invalid email or password",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(serializer.error_messages)

