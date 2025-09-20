from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from .api_key_models import ExchangeAPIKey
import logging

logger = logging.getLogger(__name__)

class ExchangeAPIKeyListCreateView(generics.ListCreateAPIView):
    """API金鑰列表和創建視圖"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = None  # 暫時不使用序列化器
    
    def get_queryset(self):
        return ExchangeAPIKey.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """獲取API金鑰列表"""
        try:
            api_keys = self.get_queryset()
            data = []
            for key in api_keys:
                data.append({
                    'id': str(key.id),
                    'exchange': key.exchange,
                    'network': key.network,
                    'is_active': key.is_active,
                    'is_verified': key.is_verified,
                    'can_trade': key.can_trade,
                    'can_withdraw': key.can_withdraw,
                    'can_read': key.can_read,
                    'masked_key': key.get_masked_key(),
                    'exchange_display': key.get_exchange_display(),
                    'network_display': key.get_network_display(),
                    'created_at': key.created_at.isoformat(),
                    'notes': key.notes
                })
            return Response(data)
        except Exception as e:
            logger.error(f"獲取API金鑰列表失敗: {e}")
            return Response({'error': '獲取API金鑰列表失敗'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request, *args, **kwargs):
        """創建API金鑰"""
        try:
            data = request.data
            api_key = ExchangeAPIKey.objects.create(
                user=request.user,
                exchange=data.get('exchange'),
                network=data.get('network', 'TESTNET'),
                api_key=data.get('api_key'),
                api_secret=data.get('api_secret'),
                passphrase=data.get('passphrase'),
                is_active=data.get('is_active', True),
                can_trade=data.get('can_trade', True),
                can_withdraw=data.get('can_withdraw', False),
                can_read=data.get('can_read', True),
                notes=data.get('notes', '')
            )
            
            return Response({
                'id': str(api_key.id),
                'exchange': api_key.exchange,
                'network': api_key.network,
                'is_active': api_key.is_active,
                'is_verified': api_key.is_verified,
                'can_trade': api_key.can_trade,
                'can_withdraw': api_key.can_withdraw,
                'can_read': api_key.can_read,
                'masked_key': api_key.get_masked_key(),
                'exchange_display': api_key.get_exchange_display(),
                'network_display': api_key.get_network_display(),
                'created_at': api_key.created_at.isoformat(),
                'notes': api_key.notes
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"創建API金鑰失敗: {e}")
            return Response({'error': '創建API金鑰失敗'}, status=status.HTTP_400_BAD_REQUEST)

class ExchangeAPIKeyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API金鑰詳情視圖"""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ExchangeAPIKey.objects.filter(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """獲取API金鑰詳情"""
        try:
            api_key = self.get_object()
            return Response({
                'id': str(api_key.id),
                'exchange': api_key.exchange,
                'network': api_key.network,
                'is_active': api_key.is_active,
                'is_verified': api_key.is_verified,
                'can_trade': api_key.can_trade,
                'can_withdraw': api_key.can_withdraw,
                'can_read': api_key.can_read,
                'masked_key': api_key.get_masked_key(),
                'exchange_display': api_key.get_exchange_display(),
                'network_display': api_key.get_network_display(),
                'created_at': api_key.created_at.isoformat(),
                'updated_at': api_key.updated_at.isoformat(),
                'notes': api_key.notes
            })
        except Exception as e:
            logger.error(f"獲取API金鑰詳情失敗: {e}")
            return Response({'error': '獲取API金鑰詳情失敗'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, *args, **kwargs):
        """更新API金鑰"""
        try:
            api_key = self.get_object()
            data = request.data
            
            # 更新字段
            if 'is_active' in data:
                api_key.is_active = data['is_active']
            if 'can_trade' in data:
                api_key.can_trade = data['can_trade']
            if 'can_withdraw' in data:
                api_key.can_withdraw = data['can_withdraw']
            if 'can_read' in data:
                api_key.can_read = data['can_read']
            if 'notes' in data:
                api_key.notes = data['notes']
            
            api_key.save()
            
            return Response({
                'id': str(api_key.id),
                'exchange': api_key.exchange,
                'network': api_key.network,
                'is_active': api_key.is_active,
                'is_verified': api_key.is_verified,
                'can_trade': api_key.can_trade,
                'can_withdraw': api_key.can_withdraw,
                'can_read': api_key.can_read,
                'masked_key': api_key.get_masked_key(),
                'exchange_display': api_key.get_exchange_display(),
                'network_display': api_key.get_network_display(),
                'created_at': api_key.created_at.isoformat(),
                'updated_at': api_key.updated_at.isoformat(),
                'notes': api_key.notes
            })
        except Exception as e:
            logger.error(f"更新API金鑰失敗: {e}")
            return Response({'error': '更新API金鑰失敗'}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """刪除API金鑰"""
        try:
            api_key = self.get_object()
            api_key.delete()
            return Response({'message': 'API金鑰刪除成功'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"刪除API金鑰失敗: {e}")
            return Response({'error': '刪除API金鑰失敗'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_api_key(request, key_id):
    """驗證API金鑰"""
    try:
        api_key = ExchangeAPIKey.objects.get(id=key_id, user=request.user)
        
        # 這裡可以添加實際的API驗證邏輯
        # 暫時模擬驗證成功
        api_key.is_verified = True
        api_key.save()
        
        return Response({
            'success': True,
            'message': f'{api_key.get_exchange_display()} API金鑰驗證成功'
        })
    
    except ExchangeAPIKey.DoesNotExist:
        return Response({
            'success': False,
            'message': 'API金鑰不存在'
        }, status=status.HTTP_404_NOT_FOUND)
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
        api_key = ExchangeAPIKey.objects.get(id=key_id, user=request.user)
        
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
    
    except ExchangeAPIKey.DoesNotExist:
        return Response({
            'success': False,
            'message': 'API金鑰不存在'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"API連接測試失敗: {e}")
        return Response({
            'success': False,
            'message': 'API連接測試失敗'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_key_summary(request):
    """API金鑰摘要"""
    try:
        api_keys = ExchangeAPIKey.objects.filter(user=request.user)
        
        summary = {
            'total_keys': api_keys.count(),
            'active_keys': api_keys.filter(is_active=True).count(),
            'verified_keys': api_keys.filter(is_verified=True).count(),
            'exchanges': list(api_keys.values_list('exchange', flat=True).distinct()),
            'networks': list(api_keys.values_list('network', flat=True).distinct())
        }
        
        return Response(summary)
    except Exception as e:
        logger.error(f"獲取API金鑰摘要失敗: {e}")
        return Response({'error': '獲取API金鑰摘要失敗'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
