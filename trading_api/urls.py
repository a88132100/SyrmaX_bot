from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views

router = DefaultRouter()
router.register(r'trader-configs', views.TraderConfigViewSet)
router.register(r'trading-pairs', views.TradingPairViewSet)
router.register(r'positions', views.PositionViewSet)
router.register(r'trades', views.TradeViewSet)
router.register(r'daily-stats', views.DailyStatsViewSet)
router.register(r'trader-status', views.TraderStatusViewSet) # 注意這裡的單數形式，因為通常只有一條記錄
router.register(r'strategy-combos', views.StrategyComboViewSet)

# 監控相關的URL端點
urlpatterns = [
    # 監控告警儀表板
    path('monitoring/dashboard/', views.monitoring_dashboard, name='monitoring_dashboard'),
    path('monitoring/system-health/', views.system_health, name='system_health'),
    path('monitoring/alerts/', views.alert_summary, name='alert_summary'),
    path('monitoring/performance/', views.performance_metrics, name='performance_metrics'),
    path('monitoring/alerts/acknowledge/', views.acknowledge_alert, name='acknowledge_alert'),
    path('monitoring/alerts/resolve/', views.resolve_alert, name='resolve_alert'),
]

urlpatterns += router.urls 