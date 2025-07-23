from rest_framework import serializers
from .models import TraderConfig, TradingPair, Position, Trade, DailyStats, TraderStatus, StrategyCombo

class TraderConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = TraderConfig
        fields = '__all__'

class TradingPairSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradingPair
        fields = '__all__'

class PositionSerializer(serializers.ModelSerializer):
    trading_pair_symbol = serializers.CharField(source='trading_pair.symbol', read_only=True) # 顯示交易對符號

    class Meta:
        model = Position
        fields = '__all__' # 或者指定需要顯示的字段，例如 ['trading_pair_symbol', 'active', 'side', 'entry_price', 'quantity', 'open_time']

class TradeSerializer(serializers.ModelSerializer):
    trading_pair_symbol = serializers.CharField(source='trading_pair.symbol', read_only=True) # 顯示交易對符號

    class Meta:
        model = Trade
        fields = '__all__' # 或者指定需要顯示的字段，例如 ['trading_pair_symbol', 'trade_time', 'side', 'entry_price', 'exit_price', 'quantity', 'pnl', 'reason']

class DailyStatsSerializer(serializers.ModelSerializer):
    trading_pair_symbol = serializers.CharField(source='trading_pair.symbol', read_only=True) # 顯示交易對符號

    class Meta:
        model = DailyStats
        fields = '__all__' # 或者指定需要顯示的字段

class TraderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TraderStatus
        fields = '__all__'

class StrategyComboSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyCombo
        fields = '__all__'  # 包含所有欄位
        # 你也可以只列出需要的欄位，例如：['id', 'name', 'description', 'conditions', 'combo_mode', 'is_active', 'created_at', 'updated_at'] 