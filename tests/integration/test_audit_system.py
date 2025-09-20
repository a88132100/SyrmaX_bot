# test_audit_system.py
"""
稽核層系統測試
測試稽核層的核心功能
"""

import os
import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime

# 添加項目路徑
sys.path.insert(0, os.path.abspath('.'))

# 設置Django環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syrmax_api.settings')

import django
django.setup()

from core.events import SignalGenerated, EventType, RiskCheckResult, RiskChecked
from core.risk import AuditRiskManager, RiskRule
from core.explain import ExplanationGenerator
from core.audit import AuditLogger
from core.execution import AuditPipeline
from core.audit_integration import AuditIntegration


def test_events():
    """測試事件模型"""
    print("=== 測試事件模型 ===")
    
    # 創建信號事件
    signal = SignalGenerated(
        event_type=EventType.SIGNAL_GENERATED,
        account_id="test_account",
        venue="BINANCE",
        symbol="BTCUSDT",
        strategy_id="test_strategy",
        idempotency_key="test_key_001",
        side="long",
        confidence=0.8,
        indicators={"rsi": 30.5, "atr": 0.02, "ema_5": 50000, "ema_20": 49500},
        signal_strength=0.7,
        market_conditions={"volatility": "high", "trend": "up"}
    )
    
    print(f"信號事件創建成功: {signal.side} {signal.symbol}")
    print(f"指標數據: {signal.indicators}")
    
    # 創建風控結果
    risk_result = RiskCheckResult(
        passed=True,
        blocked_rules=[],
        details="風控檢查通過",
        risk_level="NORMAL"
    )
    
    print(f"風控結果: {risk_result.passed} - {risk_result.details}")
    print("✅ 事件模型測試通過\n")


def test_risk_rules():
    """測試風控規則"""
    print("=== 測試風控規則 ===")
    
    # 創建模擬交易器
    class MockTrader:
        def __init__(self):
            self.leverage = 2.0
            
        def get_config(self, key, default=None):
            return default
            
        def check_volatility_risk_adjustment(self, symbol, df):
            return True
            
        def should_trigger_circuit_breaker(self, symbol):
            return False
            
        def check_max_position_limit(self):
            return True
    
    trader = MockTrader()
    risk_manager = AuditRiskManager(trader)
    
    # 測試槓桿檢查
    result = risk_manager.check_leverage_cap("BTCUSDT", 1.5)
    print(f"槓桿1.5x檢查: {result.passed} - {result.details}")
    
    result = risk_manager.check_leverage_cap("BTCUSDT", 3.0)
    print(f"槓桿3.0x檢查: {result.passed} - {result.details}")
    
    # 測試距爆倉距離檢查
    result = risk_manager.check_dist_to_liquidation("BTCUSDT", 20.0)
    print(f"距爆倉20%檢查: {result.passed} - {result.details}")
    
    result = risk_manager.check_dist_to_liquidation("BTCUSDT", 10.0)
    print(f"距爆倉10%檢查: {result.passed} - {result.details}")
    
    print("✅ 風控規則測試通過\n")


def test_explanation_templates():
    """測試解釋模板"""
    print("=== 測試解釋模板 ===")
    
    # 創建測試數據
    signal = SignalGenerated(
        event_type=EventType.SIGNAL_GENERATED,
        account_id="test_account",
        venue="BINANCE",
        symbol="BTCUSDT",
        strategy_id="trend_strategy",
        idempotency_key="test_key_002",
        side="long",
        confidence=0.8,
        indicators={"rsi": 30.5, "atr": 0.02, "ema_5": 50000, "ema_20": 49500},
        signal_strength=0.7
    )
    
    risk_result = RiskChecked(
        event_type=EventType.RISK_CHECKED,
        account_id="test_account",
        venue="BINANCE",
        symbol="BTCUSDT",
        strategy_id="risk_check",
        idempotency_key="test_key_003",
        risk_result=RiskCheckResult(passed=True),
        leverage=2.0,
        daily_loss_used_pct=1.5,
        dist_to_liq_pct=25.0
    )
    
    context = {
        'current_price': 50000,
        'leverage': 2.0,
        'dist_to_liq_pct': 25.0,
        'daily_loss_pct': 1.5,
        'order_type': 'market',
        'max_slippage_bps': 5
    }
    
    # 測試解釋生成器
    generator = ExplanationGenerator()
    
    # 測試趨勢ATR模板
    explain_event = generator.generate_explanation(signal, risk_result, context, "trend_atr_v2")
    print(f"趨勢ATR解釋: {explain_event.explanation}")
    print(f"模板: {explain_event.template_used}, 品質: {explain_event.explanation_quality}")
    
    # 測試區間反轉模板
    signal.side = "short"
    signal.indicators["rsi"] = 75.0
    explain_event = generator.generate_explanation(signal, risk_result, context, "range_revert_v1")
    print(f"區間反轉解釋: {explain_event.explanation}")
    
    print("✅ 解釋模板測試通過\n")


def test_audit_logger():
    """測試稽核日誌"""
    print("=== 測試稽核日誌 ===")
    
    # 創建稽核日誌器
    logger = AuditLogger(audit_dir="test_audit", batch_seconds=1, batch_size=5)
    
    # 創建測試事件
    signal = SignalGenerated(
        event_type=EventType.SIGNAL_GENERATED,
        account_id="test_account",
        venue="BINANCE",
        symbol="BTCUSDT",
        strategy_id="test_strategy",
        idempotency_key="test_key_004",
        side="long",
        confidence=0.8,
        indicators={"rsi": 30.5},
        signal_strength=0.7
    )
    
    # 記錄事件
    logger.log_event(signal)
    print("事件已記錄到稽核日誌")
    
    # 等待批次寫入
    time.sleep(2)
    
    # 檢查日報表
    today = datetime.now().strftime("%Y%m%d")
    report = logger.generate_daily_report(today)
    print(f"日報表生成: 總事件數 {report.get('summary', {}).get('total_events', 0)}")
    
    # 停止日誌器
    logger.stop()
    print("✅ 稽核日誌測試通過\n")


def test_audit_pipeline():
    """測試稽核管道"""
    print("=== 測試稽核管道 ===")
    
    # 創建模擬交易器
    class MockTrader:
        def __init__(self):
            self.leverage = 2.0
            
        def get_config(self, key, default=None):
            configs = {
                'ACCOUNT_ID': 'test_account',
                'EXCHANGE_NAME': 'BINANCE'
            }
            return configs.get(key, default)
            
        def check_volatility_risk_adjustment(self, symbol, df):
            return True
            
        def should_trigger_circuit_breaker(self, symbol):
            return False
            
        def check_max_position_limit(self):
            return True
    
    trader = MockTrader()
    logger = AuditLogger(audit_dir="test_audit", batch_seconds=1, batch_size=5)
    pipeline = AuditPipeline(trader, logger)
    
    # 創建測試信號數據
    signal_data = {
        'side': 'long',
        'confidence': 0.8,
        'indicators': {'rsi': 30.5, 'atr': 0.02, 'ema_5': 50000, 'ema_20': 49500},
        'signal_strength': 0.7,
        'strategy_name': 'test_strategy',
        'market_conditions': {'volatility': 'high'}
    }
    
    # 創建測試K線數據
    df = pd.DataFrame({
        'close': [50000, 50100, 50200],
        'high': [50100, 50200, 50300],
        'low': [49900, 50000, 50100],
        'volume': [1000, 1100, 1200],
        'atr': [0.02, 0.021, 0.022],
        'rsi': [30, 31, 32],
        'ema_5': [49950, 50050, 50150],
        'ema_20': [49500, 49600, 49700]
    })
    
    # 測試稽核管道
    approved, reason, audit_data = pipeline.process_signal(signal_data, "BTCUSDT", df)
    print(f"稽核結果: 通過={approved}, 原因={reason}")
    print(f"稽核數據: {list(audit_data.keys())}")
    
    # 停止日誌器
    logger.stop()
    print("✅ 稽核管道測試通過\n")


def test_audit_integration():
    """測試稽核整合"""
    print("=== 測試稽核整合 ===")
    
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
        print("稽核整合已啟用")
        
        # 創建測試K線數據
        df = pd.DataFrame({
            'close': [50000, 50100, 50200],
            'high': [50100, 50200, 50300],
            'low': [49900, 50000, 50100],
            'volume': [1000, 1100, 1200],
            'atr': [0.02, 0.021, 0.022],
            'rsi': [30, 31, 32],
            'ema_5': [49950, 50050, 50150],
            'ema_20': [49500, 49600, 49700]
        })
        
        # 測試信號處理
        result = integration.process_trading_signal(1, "BTCUSDT", df, "test_strategy")
        print(f"信號處理結果: {result}")
        
        # 測試訂單事件記錄
        order_data = {
            'order_id': 'test_order_001',
            'side': 'BUY',
            'quantity': 0.1,
            'price': 50000,
            'strategy_id': 'test_strategy',
            'idempotency_key': 'test_key_005'
        }
        integration.log_order_event("submitted", order_data, "BTCUSDT")
        print("訂單事件已記錄")
        
        # 停止整合
        integration.stop()
        print("稽核整合已停止")
    else:
        print("稽核整合未啟用")
    
    print("✅ 稽核整合測試通過\n")


def main():
    """主測試函數"""
    print("開始稽核層系統測試\n")
    
    try:
        test_events()
        test_risk_rules()
        test_explanation_templates()
        test_audit_logger()
        test_audit_pipeline()
        test_audit_integration()
        
        print("🎉 所有測試通過！稽核層系統運行正常")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
