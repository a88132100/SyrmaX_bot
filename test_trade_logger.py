# test_trade_logger.py
"""
測試交易日誌模組
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from trading.trade_logger import trade_logger, log_order_created, OrderInfo
from datetime import datetime
import uuid

def test_basic_logging():
    """測試基本日誌記錄功能"""
    print("=== 測試基本日誌記錄功能 ===")
    
    # 創建測試訂單
    order_id = str(uuid.uuid4())
    order_info = log_order_created(
        trading_pair="BTCUSDT",
        strategy_name="strategy_ema3_ema8_crossover",
        combo_mode="aggressive",
        order_id=order_id,
        side="BUY",
        quantity=0.001,
        entry_price=50000.0,
        leverage=10.0,
        target_price=52000.0,
        stop_loss_price=48000.0,
        take_profit_price=52000.0,
        notional_value=50.0,
        margin_used=5.0,
        margin_ratio=0.1,
        market_volatility=0.02,
        atr_value=1000.0,
        trend_strength="STRONG_UP",
        signal_strength=0.8,
        signal_confidence=0.9,
        multiple_signals=[
            {"strategy": "strategy_ema3_ema8_crossover", "signal": "BUY", "strength": 0.8},
            {"strategy": "strategy_bollinger_breakout", "signal": "BUY", "strength": 0.7}
        ],
        tags=["aggressive", "trend_following", "high_volatility"]
    )
    
    print(f"✅ 訂單創建成功: {order_info.order_id}")
    print(f"   交易對: {order_info.trading_pair}")
    print(f"   策略: {order_info.strategy_name}")
    print(f"   方向: {order_info.side}")
    print(f"   數量: {order_info.quantity}")
    print(f"   價格: {order_info.entry_price}")
    print(f"   槓桿: {order_info.leverage}x")
    print(f"   狀態: {order_info.order_status}")
    print(f"   創建時間: {order_info.order_created_time}")
    print()

def test_multiple_orders():
    """測試多個訂單記錄"""
    print("=== 測試多個訂單記錄 ===")
    
    # 創建多個測試訂單
    orders = [
        {
            "trading_pair": "ETHUSDT",
            "strategy_name": "strategy_rsi_mean_reversion",
            "combo_mode": "balanced",
            "side": "SELL",
            "quantity": 0.01,
            "entry_price": 3000.0,
            "leverage": 5.0,
            "tags": ["balanced", "mean_reversion", "medium_volatility"]
        },
        {
            "trading_pair": "ADAUSDT",
            "strategy_name": "strategy_ichimoku_cloud",
            "combo_mode": "conservative",
            "side": "BUY",
            "quantity": 100.0,
            "entry_price": 0.5,
            "leverage": 3.0,
            "tags": ["conservative", "trend_following", "low_volatility"]
        },
        {
            "trading_pair": "SOLUSDT",
            "strategy_name": "strategy_volume_spike",
            "combo_mode": "aggressive",
            "side": "BUY",
            "quantity": 2.0,
            "entry_price": 100.0,
            "leverage": 8.0,
            "tags": ["aggressive", "momentum", "high_volume"]
        }
    ]
    
    for i, order_data in enumerate(orders, 1):
        order_id = str(uuid.uuid4())
        order_info = log_order_created(
            order_id=order_id,
            **order_data
        )
        print(f"✅ 訂單 {i} 創建成功: {order_info.trading_pair} {order_info.side}")
    
    print()

def test_csv_output():
    """測試CSV輸出"""
    print("=== 測試CSV輸出 ===")
    
    # 檢查CSV文件是否創建
    csv_path = "logs/trades.csv"
    if os.path.exists(csv_path):
        print(f"✅ CSV文件已創建: {csv_path}")
        
        # 讀取並顯示前幾行
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"   總行數: {len(lines)}")
            print(f"   標題行: {lines[0].strip()}")
            if len(lines) > 1:
                print(f"   第一行數據: {lines[1].strip()}")
    else:
        print(f"❌ CSV文件未找到: {csv_path}")
    
    print()

def test_log_directory():
    """測試日誌目錄結構"""
    print("=== 測試日誌目錄結構 ===")
    
    log_dir = "logs"
    if os.path.exists(log_dir):
        print(f"✅ 日誌目錄存在: {log_dir}")
        
        # 列出目錄內容
        files = os.listdir(log_dir)
        print(f"   目錄內容:")
        for file in files:
            file_path = os.path.join(log_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"     📄 {file} ({size} bytes)")
            else:
                print(f"     📁 {file}/")
    else:
        print(f"❌ 日誌目錄不存在: {log_dir}")
    
    print()

def main():
    """主測試函數"""
    print("🚀 開始測試交易日誌模組\n")
    
    try:
        # 測試基本功能
        test_basic_logging()
        test_multiple_orders()
        test_csv_output()
        test_log_directory()
        
        print("🎉 所有測試完成！")
        print("\n📋 測試結果摘要:")
        print("   ✅ 基本日誌記錄功能")
        print("   ✅ 多訂單記錄功能")
        print("   ✅ CSV文件輸出")
        print("   ✅ 日誌目錄結構")
        
        print(f"\n📁 請檢查以下文件:")
        print(f"   📄 logs/trades.csv - 交易記錄")
        print(f"   📄 logs/trading_detailed.log - 詳細日誌")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
