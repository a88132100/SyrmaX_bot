# test_chart_generator.py
"""
測試圖表生成模組
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from trading.chart_generator import generate_equity_curve
from trading.backtest_engine import backtest_engine
import pandas as pd

def test_equity_curve_generation():
    """測試權益曲線圖生成"""
    print("=== 測試權益曲線圖生成 ===")
    
    try:
        # 載入交易數據
        trades_df = backtest_engine.load_trades_data()
        
        if not trades_df.empty:
            print(f"✅ 載入 {len(trades_df)} 筆交易數據")
            
            # 生成權益曲線圖
            chart_path = generate_equity_curve(trades_df)
            
            if chart_path:
                print(f"✅ 權益曲線圖生成成功: {chart_path}")
                
                # 檢查文件是否存在
                if os.path.exists(chart_path):
                    file_size = os.path.getsize(chart_path)
                    print(f"   文件大小: {file_size} bytes")
                else:
                    print("❌ 圖表文件未找到")
            else:
                print("❌ 權益曲線圖生成失敗")
        else:
            print("❌ 沒有找到交易數據")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    print()

def main():
    """主測試函數"""
    print("🚀 開始測試圖表生成模組\n")
    
    try:
        # 測試權益曲線圖生成
        test_equity_curve_generation()
        
        print("🎉 圖表生成測試完成！")
        print(f"\n📁 請檢查以下目錄:")
        print(f"   📄 logs/charts/ - 生成的圖表文件")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
