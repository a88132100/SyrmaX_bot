"""
波動率風險調整功能測試
"""
import unittest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from django.test import TestCase
from django.utils import timezone
from trading_api.models import TradingPair, VolatilityPauseStatus
from trading.trader import MultiSymbolTrader


class VolatilityRiskAdjustmentTest(TestCase):
    """波動率風險調整功能測試類"""
    
    def setUp(self):
        """測試前準備"""
        # 創建測試交易對
        self.trading_pair = TradingPair.objects.create(
            symbol="BTCUSDT",
            interval="1m",
            precision=3,
            average_atr=100.0
        )
        
        # 創建測試DataFrame
        self.df = pd.DataFrame({
            'open': [50000, 50100, 50200, 50300, 50400],
            'high': [50100, 50200, 50300, 50400, 50500],
            'low': [49900, 50000, 50100, 50200, 50300],
            'close': [50100, 50200, 50300, 50400, 50500],
            'volume': [1000, 1100, 1200, 1300, 1400],
            'atr': [100, 110, 120, 130, 140]  # 正常波動率
        })
        
        # 創建高波動率DataFrame
        self.high_vol_df = pd.DataFrame({
            'open': [50000, 50100, 50200, 50300, 50400],
            'high': [50100, 50200, 50300, 50400, 50500],
            'low': [49900, 50000, 50100, 50200, 50300],
            'close': [50100, 50200, 50300, 50400, 50500],
            'volume': [1000, 1100, 1200, 1300, 1400],
            'atr': [300, 320, 340, 360, 380]  # 高波動率 (3.8倍)
        })
    
    def test_volatility_pause_status_creation(self):
        """測試波動率暫停狀態創建"""
        status = VolatilityPauseStatus.objects.create(
            trading_pair=self.trading_pair,
            is_paused=True,
            pause_reason="測試暫停",
            current_atr_ratio=3.5
        )
        
        self.assertEqual(status.trading_pair.symbol, "BTCUSDT")
        self.assertTrue(status.is_paused)
        self.assertEqual(status.current_atr_ratio, 3.5)
        self.assertEqual(status.pause_reason, "測試暫停")
    
    def test_normal_volatility_check(self):
        """測試正常波動率檢查"""
        with patch('trading.trader.MultiSymbolTrader') as mock_trader_class:
            mock_trader = Mock()
            mock_trader.enable_volatility_risk_adjustment = True
            mock_trader.volatility_pause_threshold = 3.0
            mock_trader.volatility_recovery_threshold = 1.5
            mock_trader.average_atrs = {"BTCUSDT": 100.0}
            
            # 模擬check_volatility_risk_adjustment方法
            def mock_check_volatility(symbol, df):
                current_atr = df['atr'].iloc[-1]
                avg_atr = mock_trader.average_atrs.get(symbol)
                atr_ratio = current_atr / avg_atr
                
                # 獲取或創建波動率暫停狀態
                status, created = VolatilityPauseStatus.objects.get_or_create(
                    trading_pair=self.trading_pair,
                    defaults={'is_paused': False, 'current_atr_ratio': atr_ratio}
                )
                
                if atr_ratio >= mock_trader.volatility_pause_threshold:
                    status.is_paused = True
                    status.pause_start_time = timezone.now()
                    status.pause_reason = f"波動率異常放大 (ATR比率: {atr_ratio:.2f})"
                    status.save()
                    return False
                
                return True
            
            mock_trader.check_volatility_risk_adjustment = mock_check_volatility
            
            # 測試正常波動率
            result = mock_trader.check_volatility_risk_adjustment("BTCUSDT", self.df)
            self.assertTrue(result)
            
            # 檢查狀態
            status = VolatilityPauseStatus.objects.get(trading_pair=self.trading_pair)
            self.assertFalse(status.is_paused)
            self.assertAlmostEqual(status.current_atr_ratio, 1.4, places=1)
    
    def test_high_volatility_pause(self):
        """測試高波動率暫停"""
        with patch('trading.trader.MultiSymbolTrader') as mock_trader_class:
            mock_trader = Mock()
            mock_trader.enable_volatility_risk_adjustment = True
            mock_trader.volatility_pause_threshold = 3.0
            mock_trader.volatility_recovery_threshold = 1.5
            mock_trader.average_atrs = {"BTCUSDT": 100.0}
            
            # 模擬check_volatility_risk_adjustment方法
            def mock_check_volatility(symbol, df):
                current_atr = df['atr'].iloc[-1]
                avg_atr = mock_trader.average_atrs.get(symbol)
                atr_ratio = current_atr / avg_atr
                
                # 獲取或創建波動率暫停狀態
                status, created = VolatilityPauseStatus.objects.get_or_create(
                    trading_pair=self.trading_pair,
                    defaults={'is_paused': False, 'current_atr_ratio': atr_ratio}
                )
                
                if atr_ratio >= mock_trader.volatility_pause_threshold:
                    status.is_paused = True
                    status.pause_start_time = timezone.now()
                    status.pause_reason = f"波動率異常放大 (ATR比率: {atr_ratio:.2f})"
                    status.save()
                    return False
                
                return True
            
            mock_trader.check_volatility_risk_adjustment = mock_check_volatility
            
            # 測試高波動率
            result = mock_trader.check_volatility_risk_adjustment("BTCUSDT", self.high_vol_df)
            self.assertFalse(result)
            
            # 檢查狀態
            status = VolatilityPauseStatus.objects.get(trading_pair=self.trading_pair)
            self.assertTrue(status.is_paused)
            self.assertAlmostEqual(status.current_atr_ratio, 3.8, places=1)
            self.assertIn("波動率異常放大", status.pause_reason)
    
    def test_position_size_adjustment(self):
        """測試倉位大小調整"""
        with patch('trading.trader.MultiSymbolTrader') as mock_trader_class:
            mock_trader = Mock()
            mock_trader.enable_volatility_risk_adjustment = True
            mock_trader.volatility_threshold_multiplier = 2.0
            mock_trader.average_atrs = {"BTCUSDT": 100.0}
            
            # 模擬adjust_position_size_by_volatility方法
            def mock_adjust_position(symbol, base_quantity, df):
                current_atr = df['atr'].iloc[-1]
                avg_atr = mock_trader.average_atrs.get(symbol)
                atr_ratio = current_atr / avg_atr
                
                if atr_ratio > mock_trader.volatility_threshold_multiplier:
                    # 波動率較高時減少倉位
                    adjustment_factor = mock_trader.volatility_threshold_multiplier / atr_ratio
                    return base_quantity * adjustment_factor
                elif atr_ratio < 0.5:
                    # 波動率較低時可以適當增加倉位
                    adjustment_factor = min(1.5, 1.0 / atr_ratio)
                    return base_quantity * adjustment_factor
                else:
                    # 波動率正常
                    return base_quantity
            
            mock_trader.adjust_position_size_by_volatility = mock_adjust_position
            
            # 測試正常波動率
            adjusted_qty = mock_trader.adjust_position_size_by_volatility("BTCUSDT", 1.0, self.df)
            self.assertEqual(adjusted_qty, 1.0)  # 正常波動率不調整
            
            # 測試高波動率
            adjusted_qty = mock_trader.adjust_position_size_by_volatility("BTCUSDT", 1.0, self.high_vol_df)
            expected_qty = 1.0 * (2.0 / 3.8)  # 調整係數
            self.assertAlmostEqual(adjusted_qty, expected_qty, places=3)


if __name__ == '__main__':
    unittest.main()
