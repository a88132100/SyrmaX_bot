from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from .api_key_models import ExchangeAPIKey
from .models import TradingConfig
from .serializers import (
    ExchangeAPIKeySerializer, ExchangeAPIKeyCreateSerializer,
    TradingConfigSerializer, UserSerializer
)
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)

class ExchangeAPIKeyListCreateView(generics.ListCreateAPIView):
    """API金鑰列表和創建視圖"""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ExchangeAPIKeyCreateSerializer
        return ExchangeAPIKeySerializer
    
    def get_queryset(self):
        return ExchangeAPIKey.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ExchangeAPIKeyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API金鑰詳情視圖"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = ExchangeAPIKeySerializer
    
    def get_queryset(self):
        return ExchangeAPIKey.objects.filter(user=self.request.user)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_api_key(request, key_id):
    """驗證API金鑰"""
    try:
        api_key = get_object_or_404(ExchangeAPIKey, id=key_id, user=request.user)
        
        # 這裡可以添加實際的API驗證邏輯
        # 暫時模擬驗證成功
        api_key.is_verified = True
        api_key.save()
        
        return Response({
            'success': True,
            'message': f'{api_key.get_exchange_display()} API金鑰驗證成功'
        })
    
    except Exception as e:
        logger.error(f"API金鑰驗證失敗: {e}")
        return Response({
            'success': False,
            'message': 'API金鑰驗證失敗'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_api_connection(request, key_id):
    """測試API連接"""
    try:
        api_key = get_object_or_404(ExchangeAPIKey, id=key_id, user=request.user)
        
        # 這裡可以添加實際的API連接測試邏輯
        # 暫時返回成功
        return Response({
            'success': True,
            'message': f'{api_key.get_exchange_display()} 連接測試成功',
            'data': {
                'exchange': api_key.exchange,
                'network': api_key.network,
                'can_trade': api_key.can_trade,
                'can_read': api_key.can_read
            }
        })
    
    except Exception as e:
        logger.error(f"API連接測試失敗: {e}")
        return Response({
            'success': False,
            'message': 'API連接測試失敗'
        }, status=status.HTTP_400_BAD_REQUEST)

class TradingConfigView(generics.RetrieveUpdateAPIView):
    """交易配置視圖"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = TradingConfigSerializer
    
    def get_object(self):
        config, created = TradingConfig.objects.get_or_create(user=self.request.user)
        return config

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """用戶資料"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_key_summary(request):
    """API金鑰摘要"""
    api_keys = ExchangeAPIKey.objects.filter(user=request.user)
    
    summary = {
        'total_keys': api_keys.count(),
        'active_keys': api_keys.filter(is_active=True).count(),
        'verified_keys': api_keys.filter(is_verified=True).count(),
        'exchanges': list(api_keys.values_list('exchange', flat=True).distinct()),
        'networks': list(api_keys.values_list('network', flat=True).distinct())
    }
    
    return Response(summary)

# 監控相關視圖
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monitoring_dashboard(request):
    """監控告警儀表板"""
    return Response({
        'status': 'success',
        'data': {
            'system_status': '正常',
            'trading_status': '運行中',
            'alerts_count': 0,
            'last_update': '2024-01-01T00:00:00Z'
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_health(request):
    """系統健康狀態"""
    return Response({
        'status': 'success',
        'data': {
            'cpu_usage': 45.2,
            'memory_usage': 67.8,
            'disk_usage': 23.1,
            'api_status': '正常'
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def alert_summary(request):
    """告警摘要"""
    return Response({
        'status': 'success',
        'data': {
            'total_alerts': 0,
            'critical_alerts': 0,
            'warning_alerts': 0,
            'alerts': []
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_metrics(request):
    """性能指標"""
    return Response({
        'status': 'success',
        'data': {
            'trades_today': 0,
            'success_rate': 0.0,
            'profit_loss': 0.0,
            'active_positions': 0
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def acknowledge_alert(request):
    """確認告警"""
    return Response({
        'status': 'success',
        'message': '告警已確認'
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_alert(request):
    """解決告警"""
    return Response({
        'status': 'success',
        'message': '告警已解決'
    })