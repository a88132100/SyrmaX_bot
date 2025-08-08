from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    用戶資訊序列化器，用於顯示用戶資料
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'phone', 'is_email_verified', 'is_phone_verified', 
                 'verification_method', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login', 
                           'is_email_verified', 'is_phone_verified')


class UserCreateSerializer(serializers.ModelSerializer):
    """
    用戶註冊序列化器
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 
                 'first_name', 'last_name', 'phone', 'verification_method')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone': {'required': False},
            'verification_method': {'required': False},
        }
    
    def validate(self, attrs):
        """
        驗證密碼確認和用戶名唯一性
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("密碼確認不匹配")
        
        # 檢查用戶名是否已存在
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError("用戶名已存在")
        
        # 檢查 Email 是否已存在
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Email 已存在")
        
        return attrs
    
    def create(self, validated_data):
        """
        創建新用戶
        """
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """
    登入序列化器
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """
        驗證用戶憑證
        """
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("用戶名或密碼錯誤")
            if not user.is_active:
                raise serializers.ValidationError("用戶帳號已被停用")
            attrs['user'] = user
        else:
            raise serializers.ValidationError("請提供用戶名和密碼")
        
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    密碼變更序列化器
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """
        驗證舊密碼和新密碼確認
        """
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError("舊密碼錯誤")
        
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("新密碼確認不匹配")
        
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """
    Email 驗證序列化器
    """
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """
        驗證 Email 是否屬於當前用戶
        """
        user = self.context['request'].user
        if user.email != value:
            raise serializers.ValidationError("此 Email 不屬於當前用戶")
        return value


class PhoneVerificationSerializer(serializers.Serializer):
    """
    手機驗證序列化器
    """
    phone = serializers.CharField(max_length=20)
    verification_code = serializers.CharField(max_length=6)
    
    def validate_phone(self, value):
        """
        驗證手機號碼是否屬於當前用戶
        """
        user = self.context['request'].user
        if user.phone != value:
            raise serializers.ValidationError("此手機號碼不屬於當前用戶")
        return value
