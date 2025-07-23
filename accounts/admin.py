from django.contrib import admin
from .models import User

# 將自訂 User 模型註冊到 Django 管理後台
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'is_email_verified', 'is_phone_verified', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone')
    list_filter = ('is_email_verified', 'is_phone_verified', 'is_staff', 'is_active')
    ordering = ('id',)
    # 你可以根據需求擴充顯示欄位
