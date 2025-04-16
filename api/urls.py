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
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/user/', views.CurrentUserView.as_view(), name='current-user'),
    path('therapists/', views.TherapistListView.as_view(), name='therapist-list'),
    path('therapists/<int:id>/', views.TherapistDetailView.as_view(), name='therapist-detail'),
    path('skills/', views.SkillListView.as_view(), name='skill-list'),
    path('languages/', views.LanguageListView.as_view(), name='language-list'),
    path('profile/update/base/', views.MyProfileBaseUpdateView.as_view(), name='profile-update-base'),
    path('profile/update/picture/', views.MyProfilePictureUpdateView.as_view(), name='profile-update-picture'),
    path('profile/update/therapist/', views.MyTherapistProfileUpdateView.as_view(), name='profile-update-therapist'),
    path('profile/update/client/', views.MyClientProfileUpdateView.as_view(), name='profile-update-client'),
] 