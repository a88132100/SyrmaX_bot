from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

# 假設你有一個策略邏輯模組，這裡先用簡單範例
from strategy import aggressive, balanced, conservative
from combos.models import Combo
from trading.trader import ALL_STRATEGIES_MAP
import pandas as pd
from trading.trader import MultiSymbolTrader

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

class RunStrategyAPIView(APIView):
    """
    提供 /api/run-strategy/ API，讓前端傳入 symbol + combo_id，
    自動查詢組合、抓取K線、執行所有策略並回傳結果。
    """
    def post(self, request):
        symbol = request.data.get('symbol')
        combo_id = request.data.get('combo_id')
        if not symbol or not combo_id:
            return Response({'error': '請提供 symbol 和 combo_id'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            combo = Combo.objects.get(id=combo_id)
        except Combo.DoesNotExist:
            return Response({'error': '找不到對應的策略組合'}, status=status.HTTP_404_NOT_FOUND)
        # 取得策略清單
        strategies = []
        for item in combo.conditions:
            strategy_name = item.get('strategy') or item.get('type')
            if strategy_name and strategy_name in ALL_STRATEGIES_MAP:
                strategies.append(ALL_STRATEGIES_MAP[strategy_name])
        if not strategies:
            return Response({'error': '該組合沒有可執行的策略'}, status=status.HTTP_400_BAD_REQUEST)
        # 抓取K線資料
        trader = MultiSymbolTrader()
        interval = '1m'  # 你可以根據需求調整或從DB查詢
        df = trader.fetch_historical_klines(symbol, interval=interval, limit=100)
        if df.empty:
            return Response({'error': f'{symbol} 無法取得K線資料'}, status=status.HTTP_400_BAD_REQUEST)
        # 執行所有策略，收集結果
        results = {}
        for func in strategies:
            try:
                results[func.__name__] = func(df)
            except Exception as e:
                results[func.__name__] = f'執行失敗: {e}'
        return Response({'symbol': symbol, 'combo': combo.name, 'results': results}, status=status.HTTP_200_OK)
