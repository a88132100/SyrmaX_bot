from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

# 假設你有一個策略邏輯模組，這裡先用簡單範例
from strategy import aggressive, balanced, conservative

class StrategyExecuteAPIView(APIView):
    """
    這個 APIView 讓前端可以傳入策略名稱與參數，
    伺服器會執行對應的策略，並回傳運算結果。
    """
    def post(self, request):
        # 從請求中取得策略名稱與參數
        strategy_name = request.data.get('strategy')
        params = request.data.get('params', {})

        # 根據策略名稱選擇對應的策略邏輯
        if strategy_name == 'aggressive':
            result = aggressive.run(params)
        elif strategy_name == 'balanced':
            result = balanced.run(params)
        elif strategy_name == 'conservative':
            result = conservative.run(params)
        else:
            return Response({'error': '不支援的策略名稱'}, status=status.HTTP_400_BAD_REQUEST)

        # 回傳策略執行結果
        return Response({'result': result}, status=status.HTTP_200_OK)
