from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Создаем роутер для ViewSet'ов
router = DefaultRouter()
# Регистрируем ViewSet для управления своими фото
router.register(r'profile/photos', views.MyTherapistPhotoViewSet, basename='my-photos')
# Регистрируем ViewSet для управления своими публикациями
router.register(r'profile/publications', views.MyPublicationViewSet, basename='my-publications')

urlpatterns = [
    # --- Аутентификация и пользователи ---
    path('auth/register/client/', views.ClientRegistrationView.as_view(), name='register-client'),
    path('auth/register/therapist/', views.TherapistRegistrationView.as_view(), name='register-therapist'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/user/', views.CurrentUserView.as_view(), name='current-user'),

    # --- Терапевты ---
    path('therapists/', views.TherapistListView.as_view(), name='therapist-list'),
    path('therapists/<int:id>/', views.TherapistDetailView.as_view(), name='therapist-detail'),

    # --- Справочники ---
    path('skills/', views.SkillListView.as_view(), name='skill-list'),
    path('languages/', views.LanguageListView.as_view(), name='language-list'),

    # --- Управление профилем ---
    path('profile/update/base/', views.MyProfileBaseUpdateView.as_view(), name='profile-update-base'),
    path('profile/update/picture/', views.MyProfilePictureUpdateView.as_view(), name='profile-update-picture'),
    path('profile/update/therapist/', views.MyTherapistProfileUpdateView.as_view(), name='profile-update-therapist'),
    path('profile/update/client/', views.MyClientProfileUpdateView.as_view(), name='profile-update-client'),

    # --- Публичные ресурсы терапевтов ---
    # Список публикаций конкретного терапевта (по ID профиля терапевта)
    path('therapists/<int:therapist_id>/publications/', views.TherapistPublicationsListView.as_view(), name='therapist-publications-list'),
    # Список фотографий конкретного терапевта
    path('therapists/<int:therapist_id>/photos/', views.TherapistPhotosListView.as_view(), name='therapist-photos-list'),

    # Включаем URL из роутера (для управления своими фото и публикациями)
    path('', include(router.urls)),
] 