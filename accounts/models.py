from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    自訂用戶模型，繼承自 Django 內建 AbstractUser。
    AbstractUser 已經包含 username、password、email、first_name、last_name 等欄位。
    這裡額外擴充手機、驗證狀態與驗證方式。
    """
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name='手機號碼')
    is_email_verified = models.BooleanField(default=False, verbose_name='Email 是否已驗證')
    is_phone_verified = models.BooleanField(default=False, verbose_name='手機是否已驗證')
    VERIFICATION_METHOD_CHOICES = [
        ('email', '信箱驗證'),
        ('phone', '手機驗證'),
    ]
    verification_method = models.CharField(
        max_length=10,
        choices=VERIFICATION_METHOD_CHOICES,
        null=True,
        blank=True,
        verbose_name='用戶選擇的驗證方式'
    )

    def __str__(self):
        return self.username

# 注意：密碼(password) 欄位由 AbstractUser 自動處理，無需自行新增。
