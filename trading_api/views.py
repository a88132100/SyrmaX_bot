from django.shortcuts import render
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import TraderConfig, TradingPair, Position, Trade, DailyStats, TraderStatus, StrategyCombo
from .serializers import TraderConfigSerializer, TradingPairSerializer, PositionSerializer, TradeSerializer, DailyStatsSerializer, TraderStatusSerializer, StrategyComboSerializer

# Create your views here.

# 交易員配置視圖集
class TraderConfigViewSet(viewsets.ModelViewSet):
    queryset = TraderConfig.objects.all()
    serializer_class = TraderConfigSerializer
    lookup_field = 'key' # 使用 key 作為查詢字段

# 交易對視圖集
class TradingPairViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TradingPair.objects.all()
    serializer_class = TradingPairSerializer

# 持倉視圖集
class PositionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer

# 交易記錄視圖集
class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Trade.objects.all().order_by('-trade_time') # 預設按時間倒序排列
    serializer_class = TradeSerializer

# 每日統計視圖集
class DailyStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DailyStats.objects.all().order_by('-date', 'trading_pair__symbol') # 按日期倒序、交易對符號排序
    serializer_class = DailyStatsSerializer

# 交易員狀態視圖集
class TraderStatusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TraderStatus.objects.all()
    serializer_class = TraderStatusSerializer

    # 由於 TraderStatus 只有一條記錄，我們可以提供一個單獨的 endpoint 來獲取它
    @action(detail=False, methods=['get', 'put'], name='get_or_update_status')
    def status(self, request):
        # 確保只有一條記錄存在
        if not TraderStatus.objects.exists():
            TraderStatus.objects.create()
        status_obj = TraderStatus.objects.first()

        if request.method == 'GET':
            serializer = self.get_serializer(status_obj)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = self.get_serializer(status_obj, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

# 策略組合（Combo）API 視圖集，提供查詢、新增、修改、刪除功能
class StrategyComboViewSet(viewsets.ModelViewSet):
    """
    這個 ViewSet 讓前端或其他程式可以透過 API 來管理策略組合（Combo），
    包含查詢全部、新增、修改、刪除等功能。
    """
    queryset = StrategyCombo.objects.all()
    serializer_class = StrategyComboSerializer
