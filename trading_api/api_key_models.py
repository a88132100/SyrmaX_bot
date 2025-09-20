from django.db import models
from django.conf import settings
import uuid

class ExchangeAPIKey(models.Model):
    """交易所API金鑰模型"""
    
    EXCHANGE_CHOICES = [
        ('BINANCE', 'Binance'),
        ('BYBIT', 'Bybit'),
        ('OKX', 'OKX'),
        ('BINGX', 'BingX'),
        ('BITGET', 'Bitget'),
    ]
    
    NETWORK_CHOICES = [
        ('MAINNET', '主網'),
        ('TESTNET', '測試網'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_keys')
    exchange = models.CharField(max_length=20, choices=EXCHANGE_CHOICES)
    network = models.CharField(max_length=10, choices=NETWORK_CHOICES, default='TESTNET')
    
    # 存儲敏感信息（在生產環境中應該加密）
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255)
    passphrase = models.CharField(max_length=255, blank=True, null=True)  # OKX需要
    
    # 狀態和配置
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_verified = models.DateTimeField(null=True, blank=True)
    
    # 權限設置
    can_trade = models.BooleanField(default=True)
    can_withdraw = models.BooleanField(default=False)
    can_read = models.BooleanField(default=True)
    
    # 元數據
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['user', 'exchange', 'network']
        verbose_name = '交易所API金鑰'
        verbose_name_plural = '交易所API金鑰'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_exchange_display()} ({self.get_network_display()})"
    
    def get_masked_key(self):
        """返回遮罩的API金鑰用於顯示"""
        if self.api_key:
            return f"{self.api_key[:8]}...{self.api_key[-4:]}"
        return "未設置"
    
    def verify_connection(self):
        """驗證API連接"""
        # 這裡可以添加實際的API連接測試邏輯
        # 暫時返回True，實際實現時會調用相應交易所的API
        return True
