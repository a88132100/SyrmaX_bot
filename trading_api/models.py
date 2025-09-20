from django.db import models
from django.conf import settings
import uuid

# TraderConfig 模型 - 用於存儲鍵值對配置
class TraderConfig(models.Model):
    """交易器配置模型 - 鍵值對存儲"""
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    value_type = models.CharField(max_length=20, default='str')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '交易器配置'
        verbose_name_plural = '交易器配置'
    
    def __str__(self):
        return f"{self.key} = {self.value}"

# 交易對模型
class TradingPair(models.Model):
    """交易對模型"""
    symbol = models.CharField(max_length=20, unique=True)
    interval = models.CharField(max_length=10, default='1m')
    average_atr = models.FloatField(null=True, blank=True)
    last_trade_time = models.DateTimeField(null=True, blank=True)
    consecutive_stop_loss = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '交易對'
        verbose_name_plural = '交易對'
    
    def __str__(self):
        return self.symbol

# 每日統計模型
class DailyStats(models.Model):
    """每日統計模型"""
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE)
    date = models.DateField()
    start_balance = models.FloatField(default=0.0)
    pnl = models.FloatField(default=0.0)
    max_daily_loss_pct = models.FloatField(default=0.25)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['trading_pair', 'date']
        verbose_name = '每日統計'
        verbose_name_plural = '每日統計'
    
    def __str__(self):
        return f"{self.trading_pair.symbol} - {self.date}"

# 交易器狀態模型
class TraderStatus(models.Model):
    """交易器狀態模型"""
    is_trading_enabled = models.BooleanField(default=True)
    stop_signal_received = models.BooleanField(default=False)
    last_daily_reset_date = models.DateField(null=True, blank=True)
    hourly_trade_count = models.IntegerField(default=0)
    daily_trade_count = models.IntegerField(default=0)
    last_hourly_reset = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '交易器狀態'
        verbose_name_plural = '交易器狀態'
    
    def __str__(self):
        return f"交易器狀態 - {'啟用' if self.is_trading_enabled else '禁用'}"

# 持倉模型
class Position(models.Model):
    """持倉模型"""
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE)
    side = models.CharField(max_length=10)  # BUY/SELL
    quantity = models.FloatField()
    entry_price = models.FloatField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '持倉'
        verbose_name_plural = '持倉'
    
    def __str__(self):
        return f"{self.trading_pair.symbol} - {self.side} - {self.quantity}"

# 策略組合模型
class StrategyCombo(models.Model):
    """策略組合模型"""
    COMBO_MODE_CHOICES = [
        ('aggressive', '激進'),
        ('balanced', '平衡'),
        ('conservative', '保守'),
        ('auto', '自動'),
        ('custom', '自定義'),
    ]
    
    combo_mode = models.CharField(max_length=20, choices=COMBO_MODE_CHOICES, default='balanced')
    is_active = models.BooleanField(default=True)
    conditions = models.JSONField(default=list, blank=True)  # 自定義策略列表
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '策略組合'
        verbose_name_plural = '策略組合'
    
    def __str__(self):
        return f"{self.get_combo_mode_display()} - {'啟用' if self.is_active else '禁用'}"

# 波動率暫停狀態模型
class VolatilityPauseStatus(models.Model):
    """波動率暫停狀態模型"""
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE)
    is_paused = models.BooleanField(default=False)
    pause_start_time = models.DateTimeField(null=True, blank=True)
    pause_reason = models.TextField(blank=True, null=True)
    current_atr_ratio = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['trading_pair']
        verbose_name = '波動率暫停狀態'
        verbose_name_plural = '波動率暫停狀態'
    
    def __str__(self):
        return f"{self.trading_pair.symbol} - {'暫停' if self.is_paused else '正常'}"

# TradingConfig 模型 - 用於用戶交易配置
class TradingConfig(models.Model):
    """交易配置模型"""
    
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
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trading_config')
    
    # 默認交易所設置
    default_exchange = models.CharField(max_length=20, choices=EXCHANGE_CHOICES, default='BINANCE')
    default_network = models.CharField(max_length=10, choices=NETWORK_CHOICES, default='TESTNET')
    
    # 交易設置
    default_leverage = models.FloatField(default=1.0)
    max_position_ratio = models.FloatField(default=0.3)
    min_position_ratio = models.FloatField(default=0.01)
    
    # 風控設置
    max_trades_per_hour = models.IntegerField(default=10)
    max_trades_per_day = models.IntegerField(default=50)
    max_daily_loss_percent = models.FloatField(default=25.0)
    
    # 波動率風險調整
    enable_volatility_risk_adjustment = models.BooleanField(default=True)
    volatility_threshold_multiplier = models.FloatField(default=2.0)
    volatility_pause_threshold = models.FloatField(default=3.0)
    volatility_recovery_threshold = models.FloatField(default=1.5)
    volatility_pause_duration_minutes = models.IntegerField(default=30)
    
    # 最大持倉限制
    enable_max_position_limit = models.BooleanField(default=True)
    max_simultaneous_positions = models.IntegerField(default=3)
    
    # 元數據
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '交易配置'
        verbose_name_plural = '交易配置'
    
    def __str__(self):
        return f"{self.user.username} - 交易配置"