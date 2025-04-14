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
    path('auth/login/', views.EmailAuthToken.as_view(), name='api_token_auth'),
    path('auth/register/client/', views.ClientRegistrationView.as_view(), name='register_client'),
    path('auth/register/therapist/', views.TherapistRegistrationView.as_view(), name='register_therapist'),
    path('auth/user/', views.CurrentUserView.as_view(), name='current-user'),
    path('therapists/', views.TherapistListView.as_view(), name='therapist-list'),
    path('therapists/<int:pk>/', views.TherapistDetailView.as_view(), name='therapist-detail'),
] 