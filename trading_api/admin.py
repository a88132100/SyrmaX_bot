from django.contrib import admin
from .api_key_models import ExchangeAPIKey
from .models import TradingConfig

# 配置字段類型映射
CONFIG_FIELD_TYPES = {
    'SYMBOLS': list,
    'LEVERAGE': int,
    'BASE_POSITION_RATIO': float,
    'MIN_POSITION_RATIO': float,
    'MAX_POSITION_RATIO': float,
    'GLOBAL_INTERVAL_SECONDS': int,
    'MAX_TRADES_PER_HOUR': int,
    'MAX_TRADES_PER_DAY': int,
    'MAX_DAILY_LOSS_PCT': float,
    'ENABLE_VOLATILITY_RISK_ADJUSTMENT': bool,
    'VOLATILITY_THRESHOLD_MULTIPLIER': float,
    'VOLATILITY_PAUSE_THRESHOLD': float,
    'VOLATILITY_RECOVERY_THRESHOLD': float,
    'VOLATILITY_PAUSE_DURATION_MINUTES': int,
    'ENABLE_MAX_POSITION_LIMIT': bool,
    'MAX_SIMULTANEOUS_POSITIONS': int,
    'EXIT_MODE': str,
    'PRICE_TAKE_PROFIT_PERCENT': float,
    'PRICE_STOP_LOSS_PERCENT': float,
    'AMOUNT_TAKE_PROFIT_USDT': float,
    'AMOUNT_STOP_LOSS_USDT': float,
    'ATR_TAKE_PROFIT_MULTIPLIER': float,
    'ATR_STOP_LOSS_MULTIPLIER': float,
    'HYBRID_MIN_TAKE_PROFIT_USDT': float,
    'HYBRID_MAX_TAKE_PROFIT_USDT': float,
    'HYBRID_MIN_STOP_LOSS_USDT': float,
    'HYBRID_MAX_STOP_LOSS_USDT': float,
    'MAX_CONSECUTIVE_STOP_LOSS': int,
    'ENABLE_TRADE_LOG': bool,
    'AUTO_SYNC_SYMBOLS': bool,
    'AUTO_SET_LEVERAGE': bool,
    'USE_TESTNET': bool,
    'TEST_MODE': bool,
    'EXCHANGE_NAME': str,
    'SYMBOL_INTERVALS': dict,
    'SYMBOL_INTERVAL_SECONDS': dict,
    'RISK_LIMIT_TIERS': list,
}

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

@admin.register(TradingConfig)
class TradingConfigAdmin(admin.ModelAdmin):
    list_display = ('user', 'default_exchange', 'default_network', 'default_leverage', 'max_position_ratio')
    list_filter = ('default_exchange', 'default_network', 'enable_volatility_risk_adjustment', 'enable_max_position_limit')
    search_fields = ('user__username',)
    fieldsets = (
        ('用戶設置', {
            'fields': ('user',)
        }),
        ('默認交易所', {
            'fields': ('default_exchange', 'default_network')
        }),
        ('交易設置', {
            'fields': ('default_leverage', 'max_position_ratio', 'min_position_ratio')
        }),
        ('風控設置', {
            'fields': ('max_trades_per_hour', 'max_trades_per_day', 'max_daily_loss_percent')
        }),
        ('波動率風險調整', {
            'fields': ('enable_volatility_risk_adjustment', 'volatility_threshold_multiplier', 
                      'volatility_pause_threshold', 'volatility_recovery_threshold', 
                      'volatility_pause_duration_minutes'),
            'classes': ('collapse',)
        }),
        ('持倉限制', {
            'fields': ('enable_max_position_limit', 'max_simultaneous_positions'),
            'classes': ('collapse',)
        }),
    )