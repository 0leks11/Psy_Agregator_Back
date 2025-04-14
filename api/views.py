from django.shortcuts import render
from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import get_user_model
from .models import UserProfile, TherapistProfile, ClientProfile, InviteCode
from .serializers import (
    UserSerializer, UserProfileSerializer, TherapistProfileSerializer,
    ClientProfileSerializer, InviteCodeSerializer, ClientRegistrationSerializer,
    TherapistRegistrationSerializer, EmailAuthTokenSerializer
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
            'user': UserSerializer(user).data
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
            'user': UserSerializer(user).data
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
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        user_data = UserSerializer(user).data
        
        try:
            # Получаем базовый профиль пользователя
            user_profile = UserProfile.objects.filter(user=user).first()
            if user_profile:
                user_data['profile'] = UserProfileSerializer(user_profile).data
            
            # Если пользователь - терапевт, получаем его профиль терапевта
            if user.is_therapist:
                try:
                    therapist_profile = TherapistProfile.objects.filter(user=user).first()
                    if therapist_profile:
                        user_data['therapist_profile'] = TherapistProfileSerializer(therapist_profile).data
                    else:
                        user_data['therapist_profile'] = None
                except Exception as e:
                    print(f"Ошибка при получении профиля терапевта: {e}")
                    user_data['therapist_profile'] = None
            
            # Если пользователь - клиент, получаем его профиль клиента
            if user.is_client:
                try:
                    client_profile = ClientProfile.objects.filter(user=user).first()
                    if client_profile:
                        user_data['client_profile'] = ClientProfileSerializer(client_profile).data
                    else:
                        user_data['client_profile'] = None
                except Exception as e:
                    print(f"Ошибка при получении профиля клиента: {e}")
                    user_data['client_profile'] = None
                    
        except Exception as e:
            print(f"Ошибка при получении данных пользователя: {e}")
        
        return Response(user_data)

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

class TherapistListView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, *args, **kwargs):
        try:
            # Получаем всех терапевтов
            therapist_profiles = TherapistProfile.objects.all()
            
            # Если есть фильтрация по специализации
            specialization = request.query_params.get('specialization', None)
            if specialization:
                therapist_profiles = therapist_profiles.filter(specialization__icontains=specialization)
            
            # Сериализуем данные
            serializer = TherapistProfileSerializer(therapist_profiles, many=True)
            therapist_data = serializer.data
            
            # Дополняем данные профилей пользователей
            for i, profile in enumerate(therapist_data):
                therapist = therapist_profiles[i]
                user_profile = UserProfile.objects.filter(user=therapist.user).first()
                if user_profile:
                    profile['name'] = user_profile.name
                    
                # Добавляем временные поля для совместимости с фронтендом
                profile['experience'] = profile.get('experience_years', 0)
                profile['rating'] = 5  # Временное значение
                profile['price'] = 1500  # Временное значение
                profile['specialization'] = "Психотерапия"  # Временное значение
                profile['image'] = "/default-profile.jpg"  # Временное значение
                if 'profile_picture' in profile and profile['profile_picture']:
                    profile['image'] = profile['profile_picture']
            
            return Response(therapist_data)
        except Exception as e:
            print(f"Ошибка при получении списка терапевтов: {e}")
            return Response(
                {"error": "Произошла ошибка при получении списка терапевтов"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TherapistDetailView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, pk=None, *args, **kwargs):
        try:
            # Получаем профиль терапевта по ID
            try:
                therapist_profile = TherapistProfile.objects.get(id=pk)
            except TherapistProfile.DoesNotExist:
                return Response(
                    {"error": "Профиль терапевта не найден"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Сериализуем данные
            serializer = TherapistProfileSerializer(therapist_profile)
            therapist_data = serializer.data
            
            # Добавляем данные из профиля пользователя
            user_profile = UserProfile.objects.filter(user=therapist_profile.user).first()
            if user_profile:
                therapist_data['name'] = user_profile.name
                
            # Добавляем временные поля для совместимости с фронтендом
            therapist_data['experience'] = therapist_data.get('experience_years', 0)
            therapist_data['rating'] = 5  # Временное значение
            therapist_data['price'] = 1500  # Временное значение
            therapist_data['specialization'] = "Психотерапия"  # Временное значение
            therapist_data['image'] = "/default-profile.jpg"  # Временное значение
            if 'profile_picture' in therapist_data and therapist_data['profile_picture']:
                therapist_data['image'] = therapist_data['profile_picture']
            
            return Response(therapist_data)
        except Exception as e:
            print(f"Ошибка при получении данных терапевта: {e}")
            return Response(
                {"error": "Произошла ошибка при получении данных терапевта"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
