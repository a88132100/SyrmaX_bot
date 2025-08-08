from social_core.pipeline.user import create_user
from social_core.pipeline.social_auth import associate_user
from .models import User


def save_profile(backend, user, response, *args, **kwargs):
    """
    社交登入管道：保存用戶資料
    """
    if backend.name == 'google-oauth2':
        # 處理 Google 登入
        if response.get('email'):
            user.email = response['email']
            user.is_email_verified = True
        
        if response.get('given_name'):
            user.first_name = response['given_name']
        
        if response.get('family_name'):
            user.last_name = response['family_name']
        
        # 設定驗證方式
        user.verification_method = 'email'
        
    elif backend.name == 'facebook':
        # 處理 Facebook 登入
        if response.get('email'):
            user.email = response['email']
            user.is_email_verified = True
        
        if response.get('first_name'):
            user.first_name = response['first_name']
        
        if response.get('last_name'):
            user.last_name = response['last_name']
        
        # 設定驗證方式
        user.verification_method = 'email'
    
    # 保存用戶資料
    user.save()
    return {'user': user}


def get_username(strategy, details, backend, user=None, *args, **kwargs):
    """
    生成唯一的用戶名
    """
    if user:
        return {'username': user.username}
    
    username = details.get('username', '')
    if not username:
        # 如果沒有用戶名，使用 email 的前綴
        email = details.get('email', '')
        if email:
            username = email.split('@')[0]
        else:
            # 使用社交平台 ID
            username = f"{backend.name}_user_{details.get('id', '')}"
    
    # 確保用戶名唯一
    counter = 1
    original_username = username
    while User.objects.filter(username=username).exists():
        username = f"{original_username}_{counter}"
        counter += 1
    
    return {'username': username}


def create_social_user(backend, user, response, *args, **kwargs):
    """
    創建社交登入用戶
    """
    if user:
        return {'user': user}
    
    # 創建新用戶
    user_data = {
        'username': kwargs.get('username', ''),
        'email': response.get('email', ''),
        'first_name': response.get('first_name', ''),
        'last_name': response.get('last_name', ''),
    }
    
    # 移除空值
    user_data = {k: v for k, v in user_data.items() if v}
    
    user = User.objects.create_user(**user_data)
    return {'user': user}
