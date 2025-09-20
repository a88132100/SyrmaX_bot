from django.contrib import admin
from .api_key_models import ExchangeAPIKey

@admin.register(ExchangeAPIKey)
class ExchangeAPIKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'exchange', 'network', 'is_active', 'is_verified', 'can_trade', 'created_at')
    list_filter = ('exchange', 'network', 'is_active', 'is_verified', 'can_trade')
    search_fields = ('user__username', 'exchange', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_verified')
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'exchange', 'network', 'is_active')
        }),
        ('API金鑰', {
            'fields': ('api_key', 'api_secret', 'passphrase'),
            'classes': ('collapse',)
        }),
        ('權限設置', {
            'fields': ('can_trade', 'can_withdraw', 'can_read')
        }),
        ('驗證狀態', {
            'fields': ('is_verified', 'last_verified'),
            'classes': ('collapse',)
        }),
        ('其他信息', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
