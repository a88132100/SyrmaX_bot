from django.urls import path
from .views import StrategyExecuteAPIView, RunStrategyAPIView

urlpatterns = [
    # 這個 endpoint 讓前端可以用 POST 請求執行策略
    path('execute/', StrategyExecuteAPIView.as_view(), name='strategy-execute'),
    # 新增策略執行 API
    path('run-strategy/', RunStrategyAPIView.as_view(), name='run-strategy'),
] 