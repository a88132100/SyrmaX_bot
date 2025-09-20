# test_trading_system.py
"""
SyrmaX 交易機器人系統完整測試
測試所有核心模組和功能
"""

import os
import sys
import time
import logging
from datetime import datetime

# 設置Django環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syrmax_api.settings')

import django
django.setup()

from trading.trader import MultiSymbolTrader
from trading_api.models import TraderConfig, TradingPair, Position, Trade
from exchange.binance_client import BinanceClient
from strategy.aggressive import EMACrossover, BollingerBreakout
from core.audit_integration import AuditIntegration


def test_database_connection():
    """測試數據庫連接"""
    print("=== 測試數據庫連接 ===")
    try:
        # 測試基本查詢
        config_count = TraderConfig.objects.count()
        pair_count = TradingPair.objects.count()
        position_count = Position.objects.count()
        trade_count = Trade.objects.count()
        
        print(f"✅ 數據庫連接成功")
        print(f"   配置項目: {config_count}")
        print(f"   交易對: {pair_count}")
        print(f"   倉位: {position_count}")
        print(f"   交易記錄: {trade_count}")
        return True
    except Exception as e:
        print(f"❌ 數據庫連接失敗: {e}")
        return False


def test_exchange_client():
    """測試交易所客戶端"""
    print("\n=== 測試交易所客戶端 ===")
    try:
        # 創建Binance客戶端（測試模式）
        client = BinanceClient(
            api_key="test_key",
            api_secret="test_secret",
            testnet=True
        )
        
        print(f"✅ Binance客戶端創建成功")
        print(f"   測試網: {client.testnet}")
        print(f"   交易所: {client.exchange_name}")
        return True
    except Exception as e:
        print(f"❌ 交易所客戶端創建失敗: {e}")
        return False


def test_strategy_modules():
    """測試策略模組"""
    print("\n=== 測試策略模組 ===")
    try:
        import pandas as pd
        import numpy as np
        
        # 創建測試數據
        dates = pd.date_range('2024-01-01', periods=100, freq='1min')
        test_data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.uniform(50000, 51000, 100),
            'high': np.random.uniform(51000, 52000, 100),
            'low': np.random.uniform(49000, 50000, 100),
            'close': np.random.uniform(50000, 51000, 100),
            'volume': np.random.uniform(1000, 2000, 100)
        })
        
        # 測試EMA交叉策略
        from strategy.aggressive import default_config
        config = default_config()
        ema_strategy = EMACrossover("EMA交叉", config)
        ema_signals = ema_strategy.generate_signal(test_data)
        print(f"✅ EMA交叉策略: 生成 {len(ema_signals)} 個信號")
        
        # 測試布林帶突破策略
        bb_strategy = BollingerBreakout("布林帶突破", config)
        bb_signals = bb_strategy.generate_signal(test_data)
        print(f"✅ 布林帶突破策略: 生成 {len(bb_signals)} 個信號")
        
        return True
    except Exception as e:
        print(f"❌ 策略模組測試失敗: {e}")
        return False


def test_trader_initialization():
    """測試交易器初始化"""
    print("\n=== 測試交易器初始化 ===")
    try:
        # 創建交易器實例（使用測試參數）
        trader = MultiSymbolTrader(
            api_key="test_key",
            api_secret="test_secret"
        )
        
        print(f"✅ 交易器初始化成功")
        print(f"   槓桿: {trader.leverage}")
        print(f"   交易對: {trader.symbols}")
        print(f"   活躍組合: {trader.active_combo_mode}")
        print(f"   測試模式: {trader.test_mode}")
        
        return True
    except Exception as e:
        print(f"❌ 交易器初始化失敗: {e}")
        return False


def test_audit_integration():
    """測試稽核層整合"""
    print("\n=== 測試稽核層整合 ===")
    try:
        # 創建模擬交易器
        class MockTrader:
            def __init__(self):
                self.leverage = 2.0
                self.active_combo_mode = "balanced"
                
            def get_config(self, key, default=None):
                configs = {
                    'ACCOUNT_ID': 'test_account',
                    'EXCHANGE_NAME': 'BINANCE',
                    'AUDIT_ENABLED': True
                }
                return configs.get(key, default)
                
            def check_volatility_risk_adjustment(self, symbol, df):
                return True
                
            def should_trigger_circuit_breaker(self, symbol):
                return False
                
            def check_max_position_limit(self):
                return True
        
        trader = MockTrader()
        integration = AuditIntegration(trader)
        
        if integration.is_enabled():
            print(f"✅ 稽核層整合成功")
            print(f"   稽核層狀態: 已啟用")
        else:
            print(f"⚠️ 稽核層未啟用")
            
        return True
    except Exception as e:
        print(f"❌ 稽核層整合測試失敗: {e}")
        return False


def test_configuration_system():
    """測試配置系統"""
    print("\n=== 測試配置系統 ===")
    try:
        # 測試關鍵配置
        key_configs = [
            'EXCHANGE_NAME',
            'LEVERAGE',
            'SYMBOLS',
            'TEST_MODE',
            'USE_TESTNET'
        ]
        
        for key in key_configs:
            try:
                config = TraderConfig.objects.get(key=key)
                print(f"   {key}: {config.value} ({config.value_type})")
            except TraderConfig.DoesNotExist:
                print(f"   {key}: 未找到")
        
        print(f"✅ 配置系統正常")
        return True
    except Exception as e:
        print(f"❌ 配置系統測試失敗: {e}")
        return False


def test_trading_pair_management():
    """測試交易對管理"""
    print("\n=== 測試交易對管理 ===")
    try:
        # 檢查交易對
        pairs = TradingPair.objects.all()
        print(f"   交易對數量: {pairs.count()}")
        
        for pair in pairs[:3]:  # 只顯示前3個
            print(f"   {pair.symbol}: 精度={pair.precision}, 連續止損={pair.consecutive_stop_loss}")
        
        print(f"✅ 交易對管理正常")
        return True
    except Exception as e:
        print(f"❌ 交易對管理測試失敗: {e}")
        return False


def test_system_monitoring():
    """測試系統監控"""
    print("\n=== 測試系統監控 ===")
    try:
        from trading.system_monitor import SystemMonitor
        
        monitor = SystemMonitor()
        status = monitor.get_system_status()
        
        print(f"✅ 系統監控正常")
        print(f"   系統狀態: {status.get('status', 'N/A')}")
        print(f"   CPU使用率: {status.get('cpu_percent', 'N/A')}%")
        print(f"   內存使用率: {status.get('memory_percent', 'N/A')}%")
        print(f"   磁盤使用率: {status.get('disk_percent', 'N/A')}%")
        
        return True
    except Exception as e:
        print(f"❌ 系統監控測試失敗: {e}")
        return False


def test_logging_system():
    """測試日誌系統"""
    print("\n=== 測試日誌系統 ===")
    try:
        from trading.trade_logger import TradeLogger
        
        logger = TradeLogger()
        
        # 測試日誌記錄
        from trading.trade_logger import OrderInfo
        
        test_order = OrderInfo(
            trading_pair='BTCUSDT',
            strategy_name='test_strategy',
            combo_mode='test',
            order_id='test_001',
            side='BUY',
            order_type='MARKET',
            entry_price=50000.0,
            quantity=0.001
        )
        
        logger.log_order_created(test_order)
        print(f"✅ 日誌系統正常")
        
        return True
    except Exception as e:
        print(f"❌ 日誌系統測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("🚀 開始 SyrmaX 交易機器人系統測試")
    print("=" * 50)
    
    test_results = []
    
    # 執行所有測試
    tests = [
        ("數據庫連接", test_database_connection),
        ("交易所客戶端", test_exchange_client),
        ("策略模組", test_strategy_modules),
        ("交易器初始化", test_trader_initialization),
        ("稽核層整合", test_audit_integration),
        ("配置系統", test_configuration_system),
        ("交易對管理", test_trading_pair_management),
        ("系統監控", test_system_monitoring),
        ("日誌系統", test_logging_system),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 測試異常: {e}")
            test_results.append((test_name, False))
    
    # 統計結果
    print("\n" + "=" * 50)
    print("📊 測試結果統計")
    print("=" * 50)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    print(f"\n總體結果: {passed}/{total} 通過 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有測試通過！系統運行正常")
    else:
        print("⚠️ 部分測試失敗，請檢查相關模組")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
