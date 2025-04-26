from django.shortcuts import render
from rest_framework import viewsets, status, permissions, generics, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import get_user_model, authenticate
from django.shortcuts import get_object_or_404
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from .models import UserProfile, TherapistProfile, ClientProfile, InviteCode, Skill, Language, Role, TherapistPhoto, Publication
from .serializers import (
    UserSerializer, UserProfileSerializer, TherapistProfileSerializer,
    ClientProfileSerializer, InviteCodeSerializer, ClientRegistrationSerializer,
    TherapistRegistrationSerializer, EmailAuthTokenSerializer,
    CurrentUserSerializer, TherapistProfileReadSerializer, SkillSerializer, LanguageSerializer,
    UserUpdateSerializer, UserProfileUpdateSerializer,
    TherapistProfileUpdateSerializer, ClientProfileUpdateSerializer,
    TherapistPhotoSerializer, PublicationSerializer, PublicationWriteSerializer,
    PublicUserProfileSerializer, TherapistCardSerializer
)
from rest_framework.views import APIView
from .permissions import IsOwnerOrReadOnly, IsTherapistOwner
from django.db.models import Prefetch, Count, Avg, Q
from django.utils import timezone
from django.conf import settings
from django.http import Http404
from rest_framework.pagination import PageNumberPagination

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
    """
    Возвращает список верифицированных терапевтов.
    Доступно всем пользователям.
    """
    serializer_class = TherapistCardSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = PageNumberPagination
    pagination_class.page_size = 12

    def get_queryset(self):
        return User.objects.select_related(
            'profile', 'therapist_profile'
        ).prefetch_related(
            'therapist_profile__skills',
            'therapist_profile__languages'
        ).filter(
            profile__role=Role.THERAPIST,
            therapist_profile__is_verified=True,
            therapist_profile__is_subscribed=True
        ).order_by('-therapist_profile__created_at')

class TherapistDetailView(generics.RetrieveAPIView):
    """
    Представление для детальной информации о терапевте.
    Возвращает только подтвержденных терапевтов с активной подпиской.
    """
    serializer_class = TherapistProfileReadSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
    
    def get_queryset(self):
        return TherapistProfile.objects.filter(
            is_verified=True,
            is_subscribed=True
        ).prefetch_related(
            'skills',
            'languages',
            'photos'
        ).select_related('user')

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

class MyTherapistPhotoViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления фотографиями терапевта.
    Терапист может создавать, просматривать, обновлять и удалять свои фотографии.
    """
    serializer_class = TherapistPhotoSerializer
    permission_classes = [permissions.IsAuthenticated, IsTherapistOwner]
    
    def get_queryset(self):
        """
        Получить фотографии, связанные с профилем терапевта текущего пользователя.
        """
        if not hasattr(self.request.user, 'therapist_profile'):
            return TherapistPhoto.objects.none()
            
        return TherapistPhoto.objects.filter(
            therapist_profile=self.request.user.therapist_profile
        )
    
    def perform_create(self, serializer):
        """
        При создании фотографии связать её с профилем терапевта текущего пользователя.
        """
        if not hasattr(self.request.user, 'therapist_profile'):
            raise ValidationError("У вас нет профиля терапевта")
            
        serializer.save(therapist_profile=self.request.user.therapist_profile)
    
    def get_object(self):
        """
        Получить объект фотографии и проверить, принадлежит ли она текущему пользователю.
        """
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

class MyPublicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления публикациями терапевта.
    Терапист может создавать, просматривать, обновлять и удалять свои публикации.
    Другие пользователи могут только просматривать опубликованные статьи.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_serializer_class(self):
        """
        Использовать разные сериализаторы для чтения и записи.
        """
        if self.request.method in permissions.SAFE_METHODS:
            return PublicationSerializer
        return PublicationWriteSerializer
    
    def get_queryset(self):
        """
        Получить публикации текущего пользователя-терапевта.
        Для небезопасных методов и просмотра черновиков нужно быть автором.
        """
        user = self.request.user
        
        # Проверяем, что у пользователя есть профиль терапевта
        if not hasattr(user, 'therapist_profile'):
            return Publication.objects.none()
            
        # Для методов чтения (GET, HEAD, OPTIONS)
        if self.request.method in permissions.SAFE_METHODS:
            # Проверяем, запрашивается ли конкретная статья или список
            if 'pk' in self.kwargs:
                # Возвращаем любую статью (включая черновики), если пользователь её автор
                return Publication.objects.filter(
                    author=user
                ).select_related('author')
            else:
                # Для списка возвращаем все статьи (включая черновики) текущего пользователя
                return Publication.objects.filter(
                    author=user
                ).select_related('author')
        
        # Для методов записи (POST, PUT, PATCH, DELETE)
        # Возвращаем только статьи текущего пользователя
        return Publication.objects.filter(
            author=user
        ).select_related('author')
    
    def perform_create(self, serializer):
        """
        При создании публикации установить автора - текущего пользователя.
        """
        serializer.save(author=self.request.user)
    
    def get_object(self):
        """
        Получить объект публикации и проверить разрешения.
        """
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

class TherapistPublicationsListView(generics.ListAPIView):
    """
    Представление для просмотра опубликованных статей конкретного терапевта.
    Доступно всем пользователям.
    """
    serializer_class = PublicationSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """
        Получить опубликованные статьи конкретного терапевта.
        """
        therapist_id = self.kwargs.get('therapist_id')
        
        # Находим профиль терапевта
        therapist = get_object_or_404(
            TherapistProfile, 
            id=therapist_id,
            is_verified=True,
            is_subscribed=True
        )
        
        # Возвращаем только опубликованные статьи
        return Publication.objects.filter(
            author=therapist.user,
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author').order_by('-published_at')
    
    # Здесь можно добавить пагинацию, если это необходимо

# Добавим класс для просмотра фотографий конкретного терапевта
class TherapistPhotosListView(generics.ListAPIView):
    """
    Представление для просмотра фотографий конкретного терапевта.
    Доступно всем пользователям.
    """
    serializer_class = TherapistPhotoSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """
        Получить фотографии конкретного терапевта.
        """
        therapist_id = self.kwargs.get('therapist_id')
        
        # Находим профиль терапевта
        therapist = get_object_or_404(
            TherapistProfile, 
            id=therapist_id,
            is_verified=True,
            is_subscribed=True
        )
        
        # Возвращаем все фотографии терапевта, отсортированные по порядку
        return TherapistPhoto.objects.filter(
            therapist_profile=therapist
        ).order_by('order')

class PublicationListCreateView(generics.ListCreateAPIView):
    serializer_class = PublicationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['author']

    def get_queryset(self):
        return Publication.objects.select_related('author').all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class PublicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticatedOrReadOnly()]

class PublicUserProfileView(generics.RetrieveAPIView):
    """
    Возвращает публичный профиль пользователя (предназначен для терапевтов).
    Доступно только аутентифицированным пользователям.
    Показывает профиль только если это верифицированный терапевт.
    """
    serializer_class = PublicUserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.select_related(
        'profile', 'therapist_profile'
    ).prefetch_related(
        'publications',
        'therapist_profile__skills',
        'therapist_profile__languages'
    ).filter(
        profile__role=Role.THERAPIST
    )
    lookup_field = 'public_id'
    lookup_url_kwarg = 'public_user_id'

    def get_object(self):
        # Получаем объект стандартным способом
        user = super().get_object()

        # Проверяем наличие и статус профиля терапевта
        try:
            if not hasattr(user, 'therapist_profile'):
                raise Http404("Профиль терапевта не найден.")

            is_allowed_to_view = user.therapist_profile.is_verified

            if not is_allowed_to_view:
                raise Http404("Профиль недоступен.")

        except AttributeError:
            raise Http404("Профиль терапевта не найден.")

        return user
