from rest_framework import serializers
from django.contrib.auth.models import User
from .api_key_models import ExchangeAPIKey
from .models import TradingConfig

class ExchangeAPIKeySerializer(serializers.ModelSerializer):
    """交易所API金鑰序列化器"""
    
    masked_key = serializers.CharField(read_only=True)
    exchange_display = serializers.CharField(source='get_exchange_display', read_only=True)
    network_display = serializers.CharField(source='get_network_display', read_only=True)
    
    class Meta:
        model = ExchangeAPIKey
        fields = [
            'id', 'exchange', 'network', 'is_active', 'is_verified', 
            'last_verified', 'can_trade', 'can_withdraw', 'can_read',
            'created_at', 'updated_at', 'notes', 'masked_key',
            'exchange_display', 'network_display'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_verified', 'last_verified']

class ExchangeAPIKeyCreateSerializer(serializers.ModelSerializer):
    """創建API金鑰序列化器"""
    
    class Meta:
        model = ExchangeAPIKey
        fields = [
            'exchange', 'network', 'api_key', 'api_secret', 'passphrase',
            'is_active', 'can_trade', 'can_withdraw', 'can_read', 'notes'
        ]
    
    def validate(self, data):
        """驗證API金鑰數據"""
        exchange = data.get('exchange')
        passphrase = data.get('passphrase')
        
        # OKX需要passphrase
        if exchange == 'OKX' and not passphrase:
            raise serializers.ValidationError("OKX交易所需要提供Passphrase")
        
        return data

class TradingConfigSerializer(serializers.ModelSerializer):
    """交易配置序列化器"""
    
    class Meta:
        model = TradingConfig
        fields = [
            'default_exchange', 'default_network', 'default_leverage',
            'max_position_ratio', 'min_position_ratio', 'max_trades_per_hour',
            'max_trades_per_day', 'max_daily_loss_percent',
            'enable_volatility_risk_adjustment', 'volatility_threshold_multiplier',
            'volatility_pause_threshold', 'volatility_recovery_threshold',
            'volatility_pause_duration_minutes', 'enable_max_position_limit',
            'max_simultaneous_positions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    """用戶序列化器"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']