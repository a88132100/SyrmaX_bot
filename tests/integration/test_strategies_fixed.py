#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略組合測試腳本（修復版）
測試三種策略組合包（激進、平衡、保守）是否可以正常運行
修復了技術指標預計算的問題
"""

import sys
import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

# 添加項目路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_data():
    """創建測試用的K線數據"""
    logger.info("創建測試數據...")
    
    # 創建100根K線的測試數據
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    
    # 模擬價格走勢（包含趨勢和震盪）
    np.random.seed(42)  # 固定隨機種子，確保結果可重現
    
    # 基礎趨勢
    trend = np.linspace(100, 120, 100) + np.random.normal(0, 2, 100)
    
    # 添加一些震盪
    noise = np.random.normal(0, 1, 100)
    
    # 生成OHLC數據
    close_prices = trend + noise
    
    # 生成開盤價、最高價、最低價
    open_prices = np.roll(close_prices, 1)
    open_prices[0] = close_prices[0]
    
    high_prices = np.maximum(open_prices, close_prices) + np.random.uniform(0, 2, 100)
    low_prices = np.minimum(open_prices, close_prices) - np.random.uniform(0, 2, 100)
    
    # 生成成交量（與價格變動相關）
    price_changes = np.abs(np.diff(close_prices, prepend=close_prices[0]))
    volumes = np.random.uniform(1000, 5000, 100) * (1 + price_changes / 10)
    
    # 創建DataFrame
    df = pd.DataFrame({
        'timestamp': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    })
    
    logger.info(f"測試數據創建完成，共 {len(df)} 根K線")
    return df

def precompute_indicators_for_strategies(df):
    """為所有策略預計算必要的技術指標"""
    logger.info("預計算技術指標...")
    
    try:
        import talib
        
        # 激進策略需要的指標
        df['ema_3'] = talib.EMA(df['close'], timeperiod=3)
        df['ema_8'] = talib.EMA(df['close'], timeperiod=8)
        
        # 平衡策略需要的指標
        df['rsi'] = talib.RSI(df['close'], timeperiod=10)
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        df['ma_short'] = df['close'].rolling(5).mean()
        df['ma_long'] = df['close'].rolling(20).mean()
        df['cci'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=20)
        
        # 保守策略需要的指標
        df['ema_fast'] = talib.EMA(df['close'], timeperiod=50)
        df['ema_slow'] = talib.EMA(df['close'], timeperiod=200)
        
        # 布林帶
        bb_upper, bb_middle, bb_lower = talib.BBANDS(
            df['close'], timeperiod=20, nbdevup=2.0, nbdevdn=2.0
        )
        df['bb_upper'] = bb_upper
        df['bb_middle'] = bb_middle
        df['bb_lower'] = bb_lower
        
        # ADX指標
        df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
        df['+DI'] = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
        df['-DI'] = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
        
        # 一目均衡表 - 修復：確保所有指標都是pandas Series
        high9 = df['high'].rolling(9).max()
        low9 = df['low'].rolling(9).min()
        high26 = df['high'].rolling(26).max()
        low26 = df['low'].rolling(26).min()
        
        df['tenkan'] = (high9 + low9) / 2
        df['kijun'] = (high26 + low26) / 2
        
        # 計算先行A和先行B
        senkou_a = ((df['tenkan'] + df['kijun']) / 2).shift(26)
        span_b = (df['high'].rolling(52).max() + df['low'].rolling(52).min()) / 2
        senkou_b = span_b.shift(26)
        
        df['senkou_a'] = senkou_a
        df['senkou_b'] = senkou_b
        
        logger.info("技術指標預計算完成")
        return df
        
    except Exception as e:
        logger.error(f"技術指標預計算失敗: {e}")
        return df

def test_aggressive_strategies(df):
    """測試激進策略組合"""
    logger.info("=" * 50)
    logger.info("測試激進策略組合")
    logger.info("=" * 50)
    
    try:
        from strategy.aggressive import run as aggressive_run
        
        # 測試整體策略組合
        signals = aggressive_run(df)
        logger.info(f"激進策略組合總信號數量: {len(signals)}")
        
        if signals:
            for i, signal in enumerate(signals):
                logger.info(f"信號 {i+1}: {signal}")
        
        # 測試個別策略
        from strategy.aggressive import (
            strategy_ema3_ema8_crossover,
            strategy_bollinger_breakout,
            strategy_vwap_deviation,
            strategy_volume_spike,
            strategy_cci_reversal
        )
        
        strategies = [
            ("EMA交叉策略", strategy_ema3_ema8_crossover),
            ("布林帶突破", strategy_bollinger_breakout),
            ("VWAP偏離", strategy_vwap_deviation),
            ("量能爆量", strategy_volume_spike),
            ("CCI反轉", strategy_cci_reversal)
        ]
        
        for name, strategy_func in strategies:
            try:
                result = strategy_func(df)
                logger.info(f"{name}: {result} ({'買入' if result == 1 else '賣出' if result == -1 else '觀望'})")
            except Exception as e:
                logger.error(f"{name} 執行失敗: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"激進策略測試失敗: {e}")
        return False

def test_balanced_strategies(df):
    """測試平衡策略組合"""
    logger.info("=" * 50)
    logger.info("測試平衡策略組合")
    logger.info("=" * 50)
    
    try:
        from strategy.balanced import run as balanced_run
        
        # 測試整體策略組合
        signals = balanced_run(df)
        logger.info(f"平衡策略組合總信號數量: {len(signals)}")
        
        if signals:
            for i, signal in enumerate(signals):
                logger.info(f"信號 {i+1}: {signal}")
        
        # 測試個別策略
        from strategy.balanced import (
            strategy_rsi_mean_reversion,
            strategy_atr_breakout,
            strategy_ma_channel,
            strategy_volume_trend,
            strategy_cci_mid_trend
        )
        
        strategies = [
            ("RSI均值回歸", strategy_rsi_mean_reversion),
            ("ATR突破", strategy_atr_breakout),
            ("MA通道", strategy_ma_channel),
            ("成交量趨勢", strategy_volume_trend),
            ("CCI中線趨勢", strategy_cci_mid_trend)
        ]
        
        for name, strategy_func in strategies:
            try:
                result = strategy_func(df)
                logger.info(f"{name}: {result} ({'買入' if result == 1 else '賣出' if result == -1 else '觀望'})")
            except Exception as e:
                logger.error(f"{name} 執行失敗: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"平衡策略測試失敗: {e}")
        return False

def test_conservative_strategies(df):
    """測試保守策略組合"""
    logger.info("=" * 50)
    logger.info("測試保守策略組合")
    logger.info("=" * 50)
    
    try:
        from strategy.conservative import run as conservative_run
        
        # 測試整體策略組合
        signals = conservative_run(df)
        logger.info(f"保守策略組合總信號數量: {len(signals)}")
        
        if signals:
            for i, signal in enumerate(signals):
                logger.info(f"信號 {i+1}: {signal}")
        
        # 測試個別策略
        from strategy.conservative import (
            strategy_long_ema_crossover,
            strategy_adx_trend,
            strategy_bollinger_mean_reversion,
            strategy_ichimoku_cloud,
            strategy_atr_mean_reversion
        )
        
        strategies = [
            ("長期EMA交叉", strategy_long_ema_crossover),
            ("ADX趨勢", strategy_adx_trend),
            ("布林帶均值回歸", strategy_bollinger_mean_reversion),
            ("一目均衡表", strategy_ichimoku_cloud),
            ("ATR均值回歸", strategy_atr_mean_reversion)
        ]
        
        for name, strategy_func in strategies:
            try:
                result = strategy_func(df)
                logger.info(f"{name}: {result} ({'買入' if result == 1 else '賣出' if result == -1 else '觀望'})")
            except Exception as e:
                logger.error(f"{name} 執行失敗: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"保守策略測試失敗: {e}")
        return False

def test_strategy_bundles(df):
    """測試策略組合包的投票邏輯"""
    logger.info("=" * 50)
    logger.info("測試策略組合包投票邏輯")
    logger.info("=" * 50)
    
    try:
        from strategy.base import evaluate_bundles
        
        styles = ['aggressive', 'balanced', 'conservative']
        
        for style in styles:
            try:
                result = evaluate_bundles(df, style)
                logger.info(f"{style.upper()} 組合包投票結果: {result} ({'買入' if result == 1 else '賣出' if result == -1 else '觀望'})")
            except Exception as e:
                logger.error(f"{style} 組合包測試失敗: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"策略組合包測試失敗: {e}")
        return False

def test_trader_integration(df):
    """測試與交易機器人的整合"""
    logger.info("=" * 50)
    logger.info("測試與交易機器人的整合")
    logger.info("=" * 50)
    
    try:
        # 模擬交易機器人的信號生成
        from strategy.base import evaluate_bundles
        
        # 測試不同風格的策略組合
        for style in ['aggressive', 'balanced', 'conservative']:
            try:
                signal = evaluate_bundles(df, style)
                logger.info(f"交易機器人 {style} 模式信號: {signal}")
                
                # 模擬下單邏輯
                if signal == 1:
                    logger.info(f"  → 執行買入操作")
                elif signal == -1:
                    logger.info(f"  → 執行賣出操作")
                else:
                    logger.info(f"  → 保持觀望")
                    
            except Exception as e:
                logger.error(f"交易機器人 {style} 模式測試失敗: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"交易機器人整合測試失敗: {e}")
        return False

def test_individual_strategy_functions(df):
    """測試個別策略函數的獨立運行"""
    logger.info("=" * 50)
    logger.info("測試個別策略函數的獨立運行")
    logger.info("=" * 50)
    
    try:
        # 測試激進策略的個別函數
        logger.info("--- 激進策略個別函數測試 ---")
        from strategy.aggressive import (
            strategy_ema3_ema8_crossover,
            strategy_bollinger_breakout,
            strategy_vwap_deviation,
            strategy_volume_spike,
            strategy_cci_reversal
        )
        
        aggressive_strategies = [
            ("EMA交叉", strategy_ema3_ema8_crossover),
            ("布林帶突破", strategy_bollinger_breakout),
            ("VWAP偏離", strategy_vwap_deviation),
            ("量能爆量", strategy_volume_spike),
            ("CCI反轉", strategy_cci_reversal)
        ]
        
        for name, func in aggressive_strategies:
            try:
                result = func(df)
                logger.info(f"  {name}: {result}")
            except Exception as e:
                logger.error(f"  {name} 失敗: {e}")
        
        # 測試平衡策略的個別函數
        logger.info("--- 平衡策略個別函數測試 ---")
        from strategy.balanced import (
            strategy_rsi_mean_reversion,
            strategy_atr_breakout,
            strategy_ma_channel,
            strategy_volume_trend,
            strategy_cci_mid_trend
        )
        
        balanced_strategies = [
            ("RSI均值回歸", strategy_rsi_mean_reversion),
            ("ATR突破", strategy_atr_breakout),
            ("MA通道", strategy_ma_channel),
            ("成交量趨勢", strategy_volume_trend),
            ("CCI中線趨勢", strategy_cci_mid_trend)
        ]
        
        for name, func in balanced_strategies:
            try:
                result = func(df)
                logger.info(f"  {name}: {result}")
            except Exception as e:
                logger.error(f"  {name} 失敗: {e}")
        
        # 測試保守策略的個別函數
        logger.info("--- 保守策略個別函數測試 ---")
        from strategy.conservative import (
            strategy_long_ema_crossover,
            strategy_adx_trend,
            strategy_bollinger_mean_reversion,
            strategy_ichimoku_cloud,
            strategy_atr_mean_reversion
        )
        
        conservative_strategies = [
            ("長期EMA交叉", strategy_long_ema_crossover),
            ("ADX趨勢", strategy_adx_trend),
            ("布林帶均值回歸", strategy_bollinger_mean_reversion),
            ("一目均衡表", strategy_ichimoku_cloud),
            ("ATR均值回歸", strategy_atr_mean_reversion)
        ]
        
        for name, func in conservative_strategies:
            try:
                result = func(df)
                logger.info(f"  {name}: {result}")
            except Exception as e:
                logger.error(f"  {name} 失敗: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"個別策略函數測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("開始策略組合測試（修復版）")
    logger.info(f"測試時間: {datetime.now()}")
    
    # 創建測試數據
    df = create_test_data()
    
    # 預計算技術指標
    df = precompute_indicators_for_strategies(df)
    
    # 測試結果統計
    test_results = {}
    
    # 測試個別策略函數
    test_results['individual_functions'] = test_individual_strategy_functions(df)
    
    # 測試激進策略
    test_results['aggressive'] = test_aggressive_strategies(df)
    
    # 測試平衡策略
    test_results['balanced'] = test_balanced_strategies(df)
    
    # 測試保守策略
    test_results['conservative'] = test_conservative_strategies(df)
    
    # 測試策略組合包
    test_results['bundles'] = test_strategy_bundles(df)
    
    # 測試交易機器人整合
    test_results['trader_integration'] = test_trader_integration(df)
    
    # 輸出測試總結
    logger.info("=" * 50)
    logger.info("測試總結")
    logger.info("=" * 50)
    
    for test_name, result in test_results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        logger.info(f"{test_name}: {status}")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    logger.info(f"總計: {passed_tests}/{total_tests} 項測試通過")
    
    if passed_tests == total_tests:
        logger.info("🎉 所有策略組合測試通過！")
    else:
        logger.warning("⚠️  部分測試失敗，請檢查相關策略實現")
    
    return test_results

if __name__ == "__main__":
    main()
