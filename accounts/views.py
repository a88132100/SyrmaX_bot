from django.shortcuts import render
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django_email_verification import send_email
from social_django.models import UserSocialAuth
from .serializers import (
    UserSerializer, UserCreateSerializer, LoginSerializer,
    PasswordChangeSerializer, EmailVerificationSerializer, PhoneVerificationSerializer
)
from .models import User


class UserProfileView(generics.RetrieveAPIView):
    """
    獲取當前用戶資料
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserProfileUpdateView(generics.UpdateAPIView):
    """
    更新當前用戶資料
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': '用戶資料更新成功',
            'user': serializer.data
        })


class PasswordChangeView(APIView):
    """
    變更密碼
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({
                'message': '密碼變更成功'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    """
    Email 驗證
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            # 發送驗證 Email
            try:
                send_verification_email(user)
                return Response({
                    'message': '驗證 Email 已發送，請檢查您的信箱'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'message': '發送驗證 Email 失敗',
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PhoneVerificationView(APIView):
    """
    手機驗證
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PhoneVerificationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            # 這裡應該驗證驗證碼，暫時模擬驗證成功
            user.is_phone_verified = True
            user.save()
            return Response({
                'message': '手機驗證成功'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    登出
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            logout(request)
            return Response({
                'message': '登出成功'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'message': '登出失敗',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class SocialLoginView(APIView):
    """
    社交登入狀態檢查
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """獲取用戶的社交登入狀態"""
        user = request.user
        social_accounts = UserSocialAuth.objects.filter(user=user)
        
        social_data = []
        for social in social_accounts:
            social_data.append({
                'provider': social.provider,
                'uid': social.uid,
                'extra_data': social.extra_data
            })
        
        return Response({
            'user': UserSerializer(user).data,
            'social_accounts': social_data
        })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def custom_login(request):
    """
    自訂登入端點
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': '登入成功',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_auth(request):
    """
    檢查認證狀態
    """
    return Response({
        'message': '認證有效',
        'user': UserSerializer(request.user).data
    }, status=status.HTTP_200_OK)


def send_verification_email(user):
    """
    發送驗證 Email
    """
    subject = f'驗證您的 {settings.SITE_NAME} 帳號'
    
    # 生成驗證連結
    verification_url = f"http://{settings.DOMAIN}/api/accounts/email/verify/"
    
    # HTML 內容
    html_message = render_to_string('accounts/email_verification.html', {
        'user': user,
        'verification_url': verification_url,
        'site_name': settings.SITE_NAME
    })
    
    # 純文字內容
    text_message = strip_tags(html_message)
    
    # 發送 Email
    send_mail(
        subject=subject,
        message=text_message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
