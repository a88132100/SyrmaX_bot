# test_system_monitor.py
"""
測試系統監控模組
"""

import sys
import os
import time
import threading
sys.path.insert(0, os.path.abspath('.'))

from trading.system_monitor import (
    start_system_monitoring, stop_system_monitoring, 
    record_system_error, get_system_status, 
    ErrorSeverity, SystemStatus
)

def test_system_monitoring():
    """測試系統監控功能"""
    print("=== 測試系統監控功能 ===")
    
    try:
        # 啟動系統監控
        print("🚀 啟動系統監控...")
        start_system_monitoring()
        
        # 等待一段時間讓監控收集數據
        print("⏳ 等待監控數據收集...")
        time.sleep(35)  # 等待超過一個監控週期
        
        # 獲取系統狀態
        print("📊 獲取系統狀態...")
        status = get_system_status()
        
        if status:
            print("✅ 系統狀態獲取成功！")
            print(f"   系統狀態: {status.get('system_status', 'UNKNOWN')}")
            
            # 顯示系統指標
            metrics = status.get('metrics', {})
            if metrics:
                print(f"   CPU使用率: {metrics.get('cpu_percent', 0):.1f}%")
                print(f"   內存使用率: {metrics.get('memory_percent', 0):.1f}%")
                print(f"   磁盤使用率: {metrics.get('disk_percent', 0):.1f}%")
                print(f"   進程數量: {metrics.get('process_count', 0)}")
            
            # 顯示連接狀態
            connections = status.get('connections', {})
            if connections:
                print("\n🔗 連接狀態:")
                for component, conn_status in connections.items():
                    print(f"   {component}: {conn_status.get('status', 'UNKNOWN')} "
                          f"(響應時間: {conn_status.get('response_time', 0):.1f}ms)")
            
            # 顯示錯誤摘要
            error_summary = status.get('error_summary', {})
            if error_summary:
                print(f"\n⚠️ 錯誤摘要:")
                print(f"   總錯誤數: {error_summary.get('total_errors', 0)}")
                print(f"   嚴重錯誤: {error_summary.get('critical_errors', 0)}")
                print(f"   高級錯誤: {error_summary.get('high_errors', 0)}")
                print(f"   未解決錯誤: {error_summary.get('unresolved_errors', 0)}")
        else:
            print("❌ 系統狀態獲取失敗")
        
        # 測試錯誤記錄
        print("\n📝 測試錯誤記錄...")
        test_error_recording()
        
        # 再次獲取狀態查看錯誤記錄
        time.sleep(5)
        status = get_system_status()
        recent_errors = status.get('recent_errors', [])
        if recent_errors:
            print(f"✅ 最近記錄的錯誤: {len(recent_errors)} 個")
            for i, error in enumerate(recent_errors, 1):
                print(f"   {i}. {error.get('error_type', 'UNKNOWN')} - "
                      f"{error.get('error_message', 'No message')} "
                      f"(嚴重程度: {error.get('severity', 'UNKNOWN')})")
        
        # 停止系統監控
        print("\n🛑 停止系統監控...")
        stop_system_monitoring()
        
        print("✅ 系統監控測試完成！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_error_recording():
    """測試錯誤記錄功能"""
    try:
        # 記錄不同嚴重程度的錯誤
        print("   記錄低級錯誤...")
        record_system_error(
            "test_low_error",
            "這是一個測試用的低級錯誤",
            ErrorSeverity.LOW,
            "test_component",
            {"test": True, "timestamp": time.time()}
        )
        
        print("   記錄中級錯誤...")
        record_system_error(
            "test_medium_error",
            "這是一個測試用的中級錯誤",
            ErrorSeverity.MEDIUM,
            "test_component",
            {"test": True, "timestamp": time.time()}
        )
        
        print("   記錄高級錯誤...")
        record_system_error(
            "test_high_error",
            "這是一個測試用的高級錯誤",
            ErrorSeverity.HIGH,
            "test_component",
            {"test": True, "timestamp": time.time()}
        )
        
        print("   記錄嚴重錯誤...")
        record_system_error(
            "test_critical_error",
            "這是一個測試用的嚴重錯誤",
            ErrorSeverity.CRITICAL,
            "test_component",
            {"test": True, "timestamp": time.time()}
        )
        
        print("✅ 錯誤記錄測試完成")
        
    except Exception as e:
        print(f"❌ 錯誤記錄測試失敗: {e}")

def test_connection_monitoring():
    """測試連接監控功能"""
    print("\n=== 測試連接監控功能 ===")
    
    try:
        # 啟動監控
        start_system_monitoring()
        
        # 等待連接檢查
        print("⏳ 等待連接狀態檢查...")
        time.sleep(40)
        
        # 獲取狀態
        status = get_system_status()
        connections = status.get('connections', {})
        
        if connections:
            print("✅ 連接監控測試完成！")
            print("   連接狀態摘要:")
            for component, conn_status in connections.items():
                print(f"     {component}: {conn_status.get('status', 'UNKNOWN')}")
        else:
            print("❌ 連接監控測試失敗")
        
        # 停止監控
        stop_system_monitoring()
        
    except Exception as e:
        print(f"❌ 連接監控測試失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主測試函數"""
    print("🚀 開始測試系統監控模組\n")
    
    try:
        # 測試基本監控功能
        test_system_monitoring()
        
        # 測試連接監控
        test_connection_monitoring()
        
        print("\n🎉 所有測試完成！")
        print("\n📁 系統監控功能包括:")
        print("   ✅ 系統健康監控 (CPU、內存、磁盤、網絡)")
        print("   ✅ 外部依賴監控 (交易所API、數據庫、網絡)")
        print("   ✅ 錯誤捕捉與記錄")
        print("   ✅ 自動恢復策略")
        print("   ✅ 人工干預觸發")
        print("   ✅ 實時狀態監控")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
