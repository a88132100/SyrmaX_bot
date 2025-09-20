from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views
from . import api_key_views

# 創建路由器
router = DefaultRouter()

# API金鑰管理相關的URL端點
urlpatterns = [
    # API金鑰管理
    path('api-keys/', api_key_views.ExchangeAPIKeyListCreateView.as_view(), name='api-key-list'),
    path('api-keys/<uuid:pk>/', api_key_views.ExchangeAPIKeyDetailView.as_view(), name='api-key-detail'),
    path('api-keys/<uuid:key_id>/verify/', api_key_views.verify_api_key, name='verify-api-key'),
    path('api-keys/<uuid:key_id>/test/', api_key_views.test_api_connection, name='test-api-connection'),
    
    # 用戶相關
    path('api-key-summary/', api_key_views.api_key_summary, name='api-key-summary'),
    
    # 監控告警儀表板
    path('monitoring/dashboard/', views.monitoring_dashboard, name='monitoring_dashboard'),
    path('monitoring/system-health/', views.system_health, name='system_health'),
    path('monitoring/alerts/', views.alert_summary, name='alert_summary'),
    path('monitoring/performance/', views.performance_metrics, name='performance_metrics'),
    path('monitoring/alerts/acknowledge/', views.acknowledge_alert, name='acknowledge_alert'),
    path('monitoring/alerts/resolve/', views.resolve_alert, name='resolve_alert'),
]

# 添加路由器URL
urlpatterns += router.urls