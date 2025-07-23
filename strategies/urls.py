from django.urls import path
from .views import StrategyExecuteAPIView

urlpatterns = [
    # 這個 endpoint 讓前端可以用 POST 請求執行策略
    path('execute/', StrategyExecuteAPIView.as_view(), name='strategy-execute'),
] 