# demo_system_monitor.py
"""
系統監控功能演示
"""

import sys
import os
import time
import threading
sys.path.insert(0, os.path.abspath('.'))

from trading.system_monitor import (
    start_system_monitoring, stop_system_monitoring, 
    record_system_error, get_system_status, 
    ErrorSeverity, SystemStatus, system_monitor
)

def health_callback(metrics):
    """健康監控回調函數"""
    print(f"💚 系統健康檢查: {metrics.system_status.value}")
    print(f"   CPU: {metrics.cpu_percent:.1f}% | "
          f"內存: {metrics.memory_percent:.1f}% | "
          f"磁盤: {metrics.disk_percent:.1f}%")

def error_callback(error_record):
    """錯誤處理回調函數"""
    print(f"🚨 錯誤檢測: {error_record.error_type}")
    print(f"   組件: {error_record.component}")
    print(f"   嚴重程度: {error_record.severity.value}")
    print(f"   消息: {error_record.error_message}")

def simulate_trading_errors():
    """模擬交易過程中的錯誤"""
    print("\n🎭 模擬交易錯誤場景...")
    
    # 模擬API連接超時
    print("   模擬Binance API連接超時...")
    record_system_error(
        "connection_timeout",
        "Binance API連接超時，無法獲取市場數據",
        ErrorSeverity.HIGH,
        "binance_api",
        {"retry_count": 0, "last_success": time.time() - 300}
    )
    
    # 模擬數據庫連接失敗
    print("   模擬數據庫連接失敗...")
    record_system_error(
        "database_connection_failed",
        "無法連接到SQLite數據庫",
        ErrorSeverity.CRITICAL,
        "database",
        {"db_path": "db.sqlite3", "error_code": "SQLITE_CANTOPEN"}
    )
    
    # 模擬策略執行錯誤
    print("   模擬策略執行錯誤...")
    record_system_error(
        "strategy_execution_error",
        "EMA策略計算失敗，指標數據不完整",
        ErrorSeverity.MEDIUM,
        "strategy_engine",
        {"strategy_name": "EMA_Crossover", "missing_data": ["ema_fast", "ema_slow"]}
    )
    
    # 模擬網絡問題
    print("   模擬網絡連接問題...")
    record_system_error(
        "network_instability",
        "網絡連接不穩定，延遲過高",
        ErrorSeverity.MEDIUM,
        "network",
        {"latency": 5000, "packet_loss": 0.15}
    )

def monitor_system_health():
    """監控系統健康狀態"""
    print("\n📊 實時系統健康監控...")
    
    try:
        # 啟動監控
        start_system_monitoring()
        
        # 添加回調函數
        system_monitor.add_health_callback(health_callback)
        system_monitor.add_error_callback(error_callback)
        
        # 監控一段時間
        for i in range(6):  # 監控6個週期
            time.sleep(30)  # 每30秒檢查一次
            
            status = get_system_status()
            print(f"\n🔄 監控週期 {i+1}/6:")
            print(f"   系統狀態: {status.get('system_status', 'UNKNOWN')}")
            
            # 檢查連接狀態
            connections = status.get('connections', {})
            offline_components = [k for k, v in connections.items() 
                                if v.get('status') == 'SystemStatus.OFFLINE']
            if offline_components:
                print(f"   ⚠️ 離線組件: {', '.join(offline_components)}")
            else:
                print("   ✅ 所有組件在線")
            
            # 檢查錯誤數量
            error_summary = status.get('error_summary', {})
            total_errors = error_summary.get('total_errors', 0)
            unresolved_errors = error_summary.get('unresolved_errors', 0)
            print(f"   錯誤統計: 總計 {total_errors}, 未解決 {unresolved_errors}")
        
        # 停止監控
        stop_system_monitoring()
        
    except Exception as e:
        print(f"❌ 系統健康監控失敗: {e}")
        import traceback
        traceback.print_exc()

def export_monitoring_data():
    """導出監控數據"""
    print("\n📤 導出監控數據...")
    
    try:
        # 創建logs目錄
        os.makedirs('logs', exist_ok=True)
        
        # 導出監控指標
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        export_path = f"logs/system_monitor_export_{timestamp}.json"
        
        system_monitor.export_metrics(export_path)
        
        if os.path.exists(export_path):
            file_size = os.path.getsize(export_path)
            print(f"✅ 監控數據已導出: {export_path}")
            print(f"   文件大小: {file_size} bytes")
        else:
            print("❌ 監控數據導出失敗")
            
    except Exception as e:
        print(f"❌ 導出監控數據失敗: {e}")

def main():
    """主演示函數"""
    print("🚀 系統監控功能完整演示")
    print("=" * 60)
    
    try:
        # 1. 基本系統監控
        print("📊 步驟1: 啟動系統監控...")
        start_system_monitoring()
        time.sleep(35)  # 等待初始數據收集
        
        # 2. 獲取初始系統狀態
        print("\n📈 步驟2: 獲取初始系統狀態...")
        initial_status = get_system_status()
        if initial_status:
            print("✅ 初始系統狀態:")
            print(f"   系統狀態: {initial_status.get('system_status', 'UNKNOWN')}")
            print(f"   監控組件: {len(initial_status.get('connections', {}))} 個")
        
        # 3. 模擬錯誤場景
        simulate_trading_errors()
        
        # 4. 實時健康監控
        monitor_system_health()
        
        # 5. 導出監控數據
        export_monitoring_data()
        
        # 6. 最終狀態報告
        print("\n📋 最終系統狀態報告:")
        final_status = get_system_status()
        if final_status:
            print(f"   系統狀態: {final_status.get('system_status', 'UNKNOWN')}")
            
            # 錯誤統計
            error_summary = final_status.get('error_summary', {})
            print(f"   總錯誤數: {error_summary.get('total_errors', 0)}")
            print(f"   嚴重錯誤: {error_summary.get('critical_errors', 0)}")
            print(f"   高級錯誤: {error_summary.get('high_errors', 0)}")
            print(f"   未解決錯誤: {error_summary.get('unresolved_errors', 0)}")
            
            # 連接狀態
            connections = final_status.get('connections', {})
            healthy_connections = sum(1 for v in connections.values() 
                                    if v.get('status') == 'SystemStatus.HEALTHY')
            print(f"   健康連接: {healthy_connections}/{len(connections)}")
        
        print("\n🎉 系統監控演示完成！")
        print("\n🚀 已實現的功能:")
        print("   ✅ 系統健康監控 (CPU、內存、磁盤、網絡)")
        print("   ✅ 外部依賴監控 (交易所API、數據庫、網絡)")
        print("   ✅ 業務邏輯監控 (策略執行狀態)")
        print("   ✅ 錯誤捕捉與記錄 (4個嚴重程度等級)")
        print("   ✅ 自動恢復策略 (API重連、錯誤分類)")
        print("   ✅ 人工干預觸發 (嚴重錯誤自動觸發)")
        print("   ✅ 實時狀態監控 (30秒週期)")
        print("   ✅ 監控數據導出 (JSON格式)")
        print("   ✅ 回調機制 (健康監控、錯誤處理)")
        
        print(f"\n📁 生成的文件:")
        print(f"   📄 logs/system_monitor_export_*.json - 監控數據導出")
        print(f"   📄 logs/trading.log - 系統日誌")
        
    except Exception as e:
        print(f"❌ 演示過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
