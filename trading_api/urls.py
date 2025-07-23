from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'trader-configs', views.TraderConfigViewSet)
router.register(r'trading-pairs', views.TradingPairViewSet)
router.register(r'positions', views.PositionViewSet)
router.register(r'trades', views.TradeViewSet)
router.register(r'daily-stats', views.DailyStatsViewSet)
router.register(r'trader-status', views.TraderStatusViewSet) # 注意這裡的單數形式，因為通常只有一條記錄
router.register(r'strategy-combos', views.StrategyComboViewSet)

urlpatterns = router.urls 