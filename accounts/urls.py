from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

app_name = 'accounts'

urlpatterns = [
    # Djoser 提供的認證端點
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    
    # 社交登入端點
    path('social/', include('social_django.urls', namespace='social')),
    
    # JWT Token 端點
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # 自訂端點
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/update/', views.UserProfileUpdateView.as_view(), name='user_profile_update'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('email/verify/', views.EmailVerificationView.as_view(), name='email_verification'),
    path('phone/verify/', views.PhoneVerificationView.as_view(), name='phone_verification'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('social/status/', views.SocialLoginView.as_view(), name='social_status'),
]
