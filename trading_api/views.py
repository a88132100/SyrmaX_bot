from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import status, viewsets
import json

from .models import TraderConfig, TradingPair, Position, Trade, DailyStats, TraderStatus, VolatilityPauseStatus, StrategyCombo
from .serializers import TraderConfigSerializer, TradingPairSerializer, PositionSerializer, TradeSerializer, DailyStatsSerializer, TraderStatusSerializer, VolatilityPauseStatusSerializer, StrategyComboSerializer

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

@api_view(['GET'])
def monitoring_dashboard(request):
    """監控儀表板視圖"""
    try:
        from trading.monitoring_dashboard import get_dashboard_summary
        summary = get_dashboard_summary()
        return Response(summary)
    except Exception as e:
        return Response(
            {'error': f'獲取監控數據失敗: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def system_health(request):
    """系統健康狀態視圖"""
    try:
        from trading.monitoring_dashboard import get_dashboard_summary
        summary = get_dashboard_summary()
        system_health = summary.get('system_health', {})
        return Response(system_health)
    except Exception as e:
        return Response(
            {'error': f'獲取系統健康狀態失敗: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def alert_summary(request):
    """告警摘要視圖"""
    try:
        from trading.monitoring_dashboard import get_dashboard_summary
        summary = get_dashboard_summary()
        alert_summary = summary.get('alert_summary', {})
        return Response(alert_summary)
    except Exception as e:
        return Response(
            {'error': f'獲取告警摘要失敗: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def performance_metrics(request):
    """性能指標視圖"""
    try:
        from trading.monitoring_dashboard import get_dashboard_summary
        summary = get_dashboard_summary()
        current_metrics = summary.get('current_metrics', {})
        performance_analysis = summary.get('performance_analysis', {})
        return Response({
            'current_metrics': current_metrics,
            'performance_analysis': performance_analysis
        })
    except Exception as e:
        return Response(
            {'error': f'獲取性能指標失敗: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def acknowledge_alert(request):
    """確認告警"""
    try:
        from trading.monitoring_dashboard import acknowledge_alert
        data = request.data
        rule_id = data.get('rule_id')
        user = data.get('user', 'admin')
        
        if not rule_id:
            return Response(
                {'error': '缺少 rule_id 參數'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        acknowledge_alert(rule_id, user)
        return Response({'message': f'告警 {rule_id} 已確認'})
    except Exception as e:
        return Response(
            {'error': f'確認告警失敗: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def resolve_alert(request):
    """解決告警"""
    try:
        from trading.monitoring_dashboard import resolve_alert
        data = request.data
        rule_id = data.get('rule_id')
        user = data.get('user', 'admin')
        
        if not rule_id:
            return Response(
                {'error': '缺少 rule_id 參數'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        resolve_alert(rule_id, user)
        return Response({'message': f'告警 {rule_id} 已解決'})
    except Exception as e:
        return Response(
            {'error': f'解決告警失敗: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
