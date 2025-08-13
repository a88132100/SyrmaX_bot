# demo_chart_generation.py
"""
圖表生成功能演示
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from trading.backtest_engine import run_backtest
from trading.chart_generator import generate_equity_curve
import pandas as pd

def demo_chart_generation():
    """演示圖表生成功能"""
    print("🎨 圖表生成功能演示")
    print("=" * 50)
    
    try:
        # 1. 運行回測並自動生成圖表
        print("📊 步驟1: 運行回測分析...")
        report = run_backtest()
        
        if report:
            print("✅ 回測報告生成成功！")
            print(f"   總交易數: {report['summary']['total_trades']}")
            print(f"   總損益: {report['summary']['total_pnl']:.2f}")
            print(f"   勝率: {report['summary']['win_rate']:.2f}%")
            print(f"   夏普比率: {report['summary']['sharpe_ratio']:.2f}")
        else:
            print("❌ 回測報告生成失敗")
            return
        
        # 2. 檢查生成的圖表
        print("\n📈 步驟2: 檢查生成的圖表...")
        charts_dir = "logs/charts"
        if os.path.exists(charts_dir):
            chart_files = os.listdir(charts_dir)
            if chart_files:
                print(f"✅ 找到 {len(chart_files)} 個圖表文件:")
                for i, chart_file in enumerate(chart_files, 1):
                    file_path = os.path.join(charts_dir, chart_file)
                    file_size = os.path.getsize(file_path)
                    print(f"   {i}. {chart_file} ({file_size} bytes)")
            else:
                print("❌ 圖表目錄為空")
        else:
            print("❌ 圖表目錄不存在")
        
        # 3. 檢查回測結果目錄
        print("\n📋 步驟3: 檢查回測結果...")
        results_dir = "logs/backtest_results"
        if os.path.exists(results_dir):
            result_files = os.listdir(results_dir)
            if result_files:
                print(f"✅ 找到 {len(result_files)} 個回測報告:")
                for i, result_file in enumerate(result_files, 1):
                    file_path = os.path.join(results_dir, result_file)
                    file_size = os.path.getsize(file_path)
                    print(f"   {i}. {result_file} ({file_size} bytes)")
            else:
                print("❌ 回測結果目錄為空")
        else:
            print("❌ 回測結果目錄不存在")
        
        # 4. 總結
        print("\n🎉 圖表生成演示完成！")
        print("\n📁 生成的文件:")
        print(f"   📊 圖表文件: {charts_dir}/")
        print(f"   📋 回測報告: {results_dir}/")
        print(f"   📄 交易記錄: logs/trades.csv")
        
        print("\n🚀 功能特點:")
        print("   ✅ 自動生成權益曲線圖")
        print("   ✅ 自動生成回撤分析圖")
        print("   ✅ 高質量PNG格式輸出")
        print("   ✅ 中文字體支持")
        print("   ✅ 專業的圖表樣式")
        
    except Exception as e:
        print(f"❌ 演示過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_chart_generation()
