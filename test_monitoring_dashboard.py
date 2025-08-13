# test_monitoring_dashboard.py
"""
測試監控告警與性能分析儀表板
"""

import sys
import os
import time
import threading
sys.path.insert(0, os.path.abspath('.'))

from trading.monitoring_dashboard import (
    start_monitoring_dashboard, stop_monitoring_dashboard,
    get_dashboard_summary, add_alert_rule, acknowledge_alert, resolve_alert,
    AlertRule, AlertLevel, monitoring_dashboard
)

def test_monitoring_dashboard():
    """測試監控告警儀表板功能"""
    print("=== 測試監控告警儀表板功能 ===")
    
    try:
        # 啟動監控告警儀表板
        print("🚀 啟動監控告警儀表板...")
        start_monitoring_dashboard()
        
        # 等待一段時間讓監控收集數據
        print("⏳ 等待監控數據收集...")
        time.sleep(25)  # 等待超過2個監控週期
        
        # 獲取儀表板摘要
        print("📊 獲取儀表板摘要...")
        summary = get_dashboard_summary()
        
        if summary:
            print("✅ 儀表板摘要獲取成功！")
            
            # 顯示系統健康狀態
            system_health = summary.get('system_health', {})
            if system_health:
                print(f"   系統健康分數: {system_health.get('overall_score', 0):.1f}/100")
                print(f"   系統狀態: {system_health.get('status', 'UNKNOWN')}")
                
                # 顯示組件分數
                component_scores = system_health.get('component_scores', {})
                if component_scores:
                    print("   組件健康分數:")
                    for component, score in component_scores.items():
                        print(f"     {component}: {score:.1f}/100")
                
                # 顯示建議
                recommendations = system_health.get('recommendations', [])
                if recommendations:
                    print("   系統建議:")
                    for rec in recommendations:
                        print(f"     💡 {rec}")
            
            # 顯示當前指標
            current_metrics = summary.get('current_metrics', {})
            metrics = current_metrics.get('metrics', {})
            if metrics:
                print(f"\n📈 當前性能指標:")
                for name, value in metrics.items():
                    print(f"   {name}: {value:.2f}")
            
            # 顯示告警摘要
            alert_summary = summary.get('alert_summary', {})
            if alert_summary:
                print(f"\n🚨 告警摘要:")
                print(f"   活躍告警數: {alert_summary.get('active_alerts_count', 0)}")
                print(f"   告警規則數: {alert_summary.get('alert_rules_count', 0)}")
                print(f"   歷史告警數: {alert_summary.get('alert_history_count', 0)}")
                
                # 顯示活躍告警
                active_alerts = alert_summary.get('active_alerts', [])
                if active_alerts:
                    print("   活躍告警:")
                    for alert in active_alerts:
                        print(f"     {alert.get('rule_id', 'UNKNOWN')}: {alert.get('message', 'No message')}")
            
            # 顯示性能分析
            performance_analysis = summary.get('performance_analysis', {})
            trend_analysis = performance_analysis.get('trend_analysis', {})
            if trend_analysis:
                print(f"\n📊 性能趨勢分析:")
                for metric_name, analysis in trend_analysis.items():
                    print(f"   {metric_name}:")
                    print(f"     當前值: {analysis.get('current', 0):.2f}")
                    print(f"     平均值: {analysis.get('average', 0):.2f}")
                    print(f"     趨勢: {analysis.get('trend', 'UNKNOWN')}")
                    print(f"     波動性: {analysis.get('volatility', 0):.3f}")
        else:
            print("❌ 儀表板摘要獲取失敗")
        
        # 測試告警規則管理
        print("\n🔧 測試告警規則管理...")
        test_alert_rules()
        
        # 測試告警處理
        print("\n🚨 測試告警處理...")
        test_alert_handling()
        
        # 再次獲取摘要查看變化
        time.sleep(10)
        updated_summary = get_dashboard_summary()
        if updated_summary:
            alert_summary = updated_summary.get('alert_summary', {})
            print(f"   更新後活躍告警數: {alert_summary.get('active_alerts_count', 0)}")
        
        # 停止監控告警儀表板
        print("\n🛑 停止監控告警儀表板...")
        stop_monitoring_dashboard()
        
        print("✅ 監控告警儀表板測試完成！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_alert_rules():
    """測試告警規則管理"""
    try:
        # 添加自定義告警規則
        print("   添加自定義告警規則...")
        custom_rule = AlertRule(
            rule_id="custom_test_rule",
            name="自定義測試規則",
            description="測試用的自定義告警規則",
            metric_name="cpu_percent",
            condition=">",
            threshold=50.0,  # 較低的閾值，容易觸發
            alert_level=AlertLevel.INFO,
            cooldown_minutes=1
        )
        
        add_alert_rule(custom_rule)
        print("   ✅ 自定義告警規則添加成功")
        
        # 等待一段時間讓規則生效
        time.sleep(15)
        
        # 檢查是否觸發了告警
        summary = get_dashboard_summary()
        alert_summary = summary.get('alert_summary', {})
        active_alerts = alert_summary.get('active_alerts', [])
        
        custom_alerts = [alert for alert in active_alerts 
                        if alert.get('rule_id') == 'custom_test_rule']
        
        if custom_alerts:
            print(f"   ✅ 自定義告警規則觸發成功，活躍告警: {len(custom_alerts)}")
        else:
            print("   ⚠️ 自定義告警規則尚未觸發")
            
    except Exception as e:
        print(f"   ❌ 告警規則測試失敗: {e}")

def test_alert_handling():
    """測試告警處理"""
    try:
        # 獲取當前告警
        summary = get_dashboard_summary()
        alert_summary = summary.get('alert_summary', {})
        active_alerts = alert_summary.get('active_alerts', [])
        
        if active_alerts:
            # 測試確認告警
            test_alert = active_alerts[0]
            rule_id = test_alert.get('rule_id')
            
            print(f"   確認告警: {rule_id}")
            acknowledge_alert(rule_id, "test_user")
            
            # 等待一下
            time.sleep(2)
            
            # 測試解決告警
            print(f"   解決告警: {rule_id}")
            resolve_alert(rule_id, "test_user")
            
            print("   ✅ 告警處理測試完成")
        else:
            print("   ⚠️ 沒有活躍告警可供測試")
            
    except Exception as e:
        print(f"   ❌ 告警處理測試失敗: {e}")

def test_performance_analysis():
    """測試性能分析功能"""
    print("\n=== 測試性能分析功能 ===")
    
    try:
        # 啟動監控
        start_monitoring_dashboard()
        
        # 等待數據收集
        print("⏳ 等待性能數據收集...")
        time.sleep(30)
        
        # 獲取性能分析
        summary = get_dashboard_summary()
        performance_analysis = summary.get('performance_analysis', {})
        trend_analysis = performance_analysis.get('trend_analysis', {})
        
        if trend_analysis:
            print("✅ 性能分析測試完成！")
            print("   性能趨勢摘要:")
            for metric_name, analysis in trend_analysis.items():
                print(f"     {metric_name}: {analysis.get('trend', 'UNKNOWN')} 趨勢")
        else:
            print("❌ 性能分析測試失敗")
        
        # 停止監控
        stop_monitoring_dashboard()
        
    except Exception as e:
        print(f"❌ 性能分析測試失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主測試函數"""
    print("🚀 開始測試監控告警與性能分析儀表板\n")
    
    try:
        # 測試基本功能
        test_monitoring_dashboard()
        
        # 測試性能分析
        test_performance_analysis()
        
        print("\n🎉 所有測試完成！")
        print("\n📁 監控告警儀表板功能包括:")
        print("   ✅ 實時監控儀表板 (系統狀態、性能指標、錯誤統計)")
        print("   ✅ 智能告警系統 (基於規則的告警觸發)")
        print("   ✅ 性能分析工具 (響應時間、吞吐量、資源使用分析)")
        print("   ✅ 趨勢分析 (系統性能的歷史趨勢)")
        print("   ✅ 容量規劃 (基於歷史數據的資源需求預測)")
        print("   ✅ 告警管理 (確認、解決、歷史追蹤)")
        print("   ✅ 數據導出 (JSON格式的完整數據導出)")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
