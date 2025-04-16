from django.shortcuts import render
from rest_framework import viewsets, status, permissions, generics, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import get_user_model, authenticate
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import UserProfile, TherapistProfile, ClientProfile, InviteCode, Skill, Language, Role
from .serializers import (
    UserSerializer, UserProfileSerializer, TherapistProfileSerializer,
    ClientProfileSerializer, InviteCodeSerializer, ClientRegistrationSerializer,
    TherapistRegistrationSerializer, EmailAuthTokenSerializer,
    CurrentUserSerializer, TherapistProfileReadSerializer, SkillSerializer, LanguageSerializer,
    UserUpdateSerializer, UserProfileUpdateSerializer,
    TherapistProfileUpdateSerializer, ClientProfileUpdateSerializer
)
from rest_framework.views import APIView

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def register_client(self, request):
        serializer = ClientRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def register_therapist(self, request):
        serializer = TherapistRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientRegistrationView(generics.CreateAPIView):
    serializer_class = ClientRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': CurrentUserSerializer(user, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)

class TherapistRegistrationView(generics.CreateAPIView):
    serializer_class = TherapistRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': CurrentUserSerializer(user, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

class TherapistProfileViewSet(viewsets.ModelViewSet):
    queryset = TherapistProfile.objects.all()
    serializer_class = TherapistProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

class ClientProfileViewSet(viewsets.ModelViewSet):
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

class InviteCodeViewSet(viewsets.ModelViewSet):
    queryset = InviteCode.objects.all()
    serializer_class = InviteCodeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = CurrentUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class EmailAuthToken(ObtainAuthToken):
    serializer_class = EmailAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'is_therapist': user.is_therapist,
            'is_client': user.is_client
        })

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = EmailAuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, username=email, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            user_data = CurrentUserSerializer(user, context={'request': request}).data
            return Response({
                'token': token.key,
                'user': user_data
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, *args, **kwargs):
        try:
            request.user.auth_token.delete()
        except: pass
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)

class SkillListView(generics.ListAPIView):
    queryset = Skill.objects.all().order_by('name')
    serializer_class = SkillSerializer
    permission_classes = [permissions.AllowAny]

class LanguageListView(generics.ListAPIView):
    queryset = Language.objects.all().order_by('name')
    serializer_class = LanguageSerializer
    permission_classes = [permissions.AllowAny]

class TherapistListView(generics.ListAPIView):
    serializer_class = TherapistProfileReadSerializer
    permission_classes = [permissions.AllowAny]
    queryset = TherapistProfile.objects.filter(
        is_verified=True, is_subscribed=True
    ).select_related('user', 'user__profile').prefetch_related('skills', 'languages')

class TherapistDetailView(generics.RetrieveAPIView):
    serializer_class = TherapistProfileReadSerializer
    permission_classes = [permissions.AllowAny]
    queryset = TherapistProfile.objects.filter(
        is_verified=True, is_subscribed=True
    ).select_related('user', 'user__profile').prefetch_related('skills', 'languages')
    lookup_field = 'id'

class MyProfileBaseUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        user_profile = user.profile

        user_serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        profile_serializer = UserProfileUpdateSerializer(user_profile, data=request.data, partial=True)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        return Response(CurrentUserSerializer(user, context={'request': request}).data)

class MyProfilePictureUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request, *args, **kwargs):
        user = request.user
        profile = user.profile
        file = request.FILES.get('profile_picture')

        if file:
            profile.profile_picture = file
            profile.save(update_fields=['profile_picture'])
            return Response(CurrentUserSerializer(user, context={'request': request}).data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No profile picture provided'}, status=status.HTTP_400_BAD_REQUEST)

class MyTherapistProfileUpdateView(generics.UpdateAPIView):
    serializer_class = TherapistProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(TherapistProfile, user=self.request.user)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(CurrentUserSerializer(self.request.user, context={'request': request}).data)

class MyClientProfileUpdateView(generics.UpdateAPIView):
    serializer_class = ClientProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(ClientProfile, user=self.request.user)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(CurrentUserSerializer(self.request.user, context={'request': request}).data)
