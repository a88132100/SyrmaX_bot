from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import User

User = get_user_model()


class UserModelTest(TestCase):
    """
    用戶模型測試
    """
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '0912345678',
            'verification_method': 'email'
        }
    
    def test_create_user(self):
        """測試創建用戶"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_email_verified)
        self.assertFalse(user.is_phone_verified)
    
    def test_user_str_representation(self):
        """測試用戶字串表示"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'testuser')


class UserAPITest(APITestCase):
    """
    用戶 API 測試
    """
    def setUp(self):
        self.register_url = reverse('accounts:user-list')
        self.login_url = reverse('accounts:token_obtain_pair')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_user_registration(self):
        """測試用戶註冊"""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')
    
    def test_user_registration_duplicate_username(self):
        """測試重複用戶名註冊"""
        User.objects.create_user(username='testuser', email='existing@example.com', password='pass123')
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_login(self):
        """測試用戶登入"""
        # 先創建用戶
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        
        # 登入
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_user_login_invalid_credentials(self):
        """測試無效憑證登入"""
        login_data = {
            'username': 'nonexistent',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileTest(APITestCase):
    """
    用戶資料測試
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.profile_url = reverse('accounts:user_profile')
    
    def test_get_user_profile(self):
        """測試獲取用戶資料"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_update_user_profile(self):
        """測試更新用戶資料"""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.patch(self.profile_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')


class PasswordChangeTest(APITestCase):
    """
    密碼變更測試
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.password_change_url = reverse('accounts:password_change')
    
    def test_password_change(self):
        """測試密碼變更"""
        change_data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        response = self.client.post(self.password_change_url, change_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 驗證新密碼
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))
    
    def test_password_change_wrong_old_password(self):
        """測試錯誤舊密碼"""
        change_data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        response = self.client.post(self.password_change_url, change_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
