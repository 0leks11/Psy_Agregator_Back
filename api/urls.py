from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.UserProfileViewSet)
router.register(r'therapist-profiles', views.TherapistProfileViewSet)
router.register(r'client-profiles', views.ClientProfileViewSet)
router.register(r'invite-codes', views.InviteCodeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', obtain_auth_token, name='api_token_auth'),
    path('auth/register/', views.UserViewSet.as_view({'post': 'register_therapist'}), name='register'),
    path('auth/register/client/', views.UserViewSet.as_view({'post': 'register_client'}), name='register_client'),
    path('auth/register/therapist/', views.UserViewSet.as_view({'post': 'register_therapist'}), name='register_therapist'),
    path('auth/user/', views.UserViewSet.as_view({'get': 'retrieve'}), name='user-detail'),
] 