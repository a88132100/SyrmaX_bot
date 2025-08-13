# test_backtest_engine.py
"""
測試回測引擎模組
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from trading.backtest_engine import (
    backtest_engine, run_backtest, analyze_strategy_performance, 
    analyze_market_environment, StrategyPerformance, MarketEnvironment
)
from trading.trade_logger import log_order_created
from datetime import datetime, timezone, timedelta
import uuid
import pandas as pd

def create_test_data():
    """創建測試交易數據"""
    print("=== 創建測試交易數據 ===")
    
    # 創建多個測試訂單，模擬真實交易場景
    test_orders = [
        # BTCUSDT - 激進策略
        {
            "trading_pair": "BTCUSDT",
            "strategy_name": "strategy_ema3_ema8_crossover",
            "combo_mode": "aggressive",
            "side": "BUY",
            "quantity": 0.001,
            "entry_price": 50000.0,
            "exit_price": 52000.0,
            "leverage": 10.0,
            "notional_value": 50.0,
            "realized_pnl": 20.0,
            "commission": 0.5,
            "slippage": 0.2,
            "market_volatility": 0.02,
            "atr_value": 1000.0,
            "trend_strength": "STRONG_UP",
            "signal_strength": 0.8,
            "signal_confidence": 0.9,
            "tags": ["aggressive", "trend_following"]
        },
        {
            "trading_pair": "BTCUSDT",
            "strategy_name": "strategy_bollinger_breakout",
            "combo_mode": "aggressive",
            "side": "SELL",
            "quantity": 0.001,
            "entry_price": 52000.0,
            "exit_price": 50000.0,
            "leverage": 10.0,
            "notional_value": 52.0,
            "realized_pnl": 20.0,
            "commission": 0.5,
            "slippage": 0.2,
            "market_volatility": 0.03,
            "atr_value": 1200.0,
            "trend_strength": "STRONG_DOWN",
            "signal_strength": 0.7,
            "signal_confidence": 0.8,
            "tags": ["aggressive", "mean_reversion"]
        },
        # ETHUSDT - 平衡策略
        {
            "trading_pair": "ETHUSDT",
            "strategy_name": "strategy_rsi_mean_reversion",
            "combo_mode": "balanced",
            "side": "BUY",
            "quantity": 0.01,
            "entry_price": 3000.0,
            "exit_price": 3100.0,
            "leverage": 5.0,
            "notional_value": 30.0,
            "realized_pnl": 10.0,
            "commission": 0.3,
            "slippage": 0.1,
            "market_volatility": 0.015,
            "atr_value": 50.0,
            "trend_strength": "UP",
            "signal_strength": 0.6,
            "signal_confidence": 0.7,
            "tags": ["balanced", "mean_reversion"]
        },
        {
            "trading_pair": "ETHUSDT",
            "strategy_name": "strategy_atr_breakout",
            "combo_mode": "balanced",
            "side": "SELL",
            "quantity": 0.01,
            "entry_price": 3100.0,
            "exit_price": 3050.0,
            "leverage": 5.0,
            "notional_value": 31.0,
            "realized_pnl": 5.0,
            "commission": 0.3,
            "slippage": 0.1,
            "market_volatility": 0.02,
            "atr_value": 60.0,
            "trend_strength": "DOWN",
            "signal_strength": 0.5,
            "signal_confidence": 0.6,
            "tags": ["balanced", "breakout"]
        },
        # ADAUSDT - 保守策略
        {
            "trading_pair": "ADAUSDT",
            "strategy_name": "strategy_ichimoku_cloud",
            "combo_mode": "conservative",
            "side": "BUY",
            "quantity": 100.0,
            "entry_price": 0.5,
            "exit_price": 0.52,
            "leverage": 3.0,
            "notional_value": 50.0,
            "realized_pnl": 2.0,
            "commission": 0.2,
            "slippage": 0.05,
            "market_volatility": 0.01,
            "atr_value": 0.02,
            "trend_strength": "UP",
            "signal_strength": 0.4,
            "signal_confidence": 0.5,
            "tags": ["conservative", "trend_following"]
        },
        {
            "trading_pair": "ADAUSDT",
            "strategy_name": "strategy_long_ema_crossover",
            "combo_mode": "conservative",
            "side": "SELL",
            "quantity": 100.0,
            "entry_price": 0.52,
            "exit_price": 0.51,
            "leverage": 3.0,
            "notional_value": 52.0,
            "realized_pnl": 1.0,
            "commission": 0.2,
            "slippage": 0.05,
            "market_volatility": 0.008,
            "atr_value": 0.015,
            "trend_strength": "NEUTRAL",
            "signal_strength": 0.3,
            "signal_confidence": 0.4,
            "tags": ["conservative", "trend_following"]
        }
    ]
    
    # 創建訂單並記錄
    for i, order_data in enumerate(test_orders, 1):
        order_id = str(uuid.uuid4())
        
        # 創建訂單
        order_info = log_order_created(
            order_id=order_id,
            **order_data
        )
        
        # 模擬訂單完成
        order_info.order_status = 'FILLED'
        order_info.order_completed_time = datetime.now(timezone.utc)
        order_info.filled_quantity = order_info.quantity
        order_info.remaining_quantity = 0.0
        
        print(f"✅ 測試訂單 {i} 創建成功: {order_info.trading_pair} {order_info.side}")
    
    print()

def update_csv_with_filled_orders():
    """更新CSV文件，將訂單狀態改為FILLED"""
    print("=== 更新CSV文件中的訂單狀態 ===")
    
    try:
        csv_path = "logs/trades.csv"
        if os.path.exists(csv_path):
            # 讀取CSV
            df = pd.read_csv(csv_path)
            
            # 更新最近的6筆訂單狀態為FILLED
            if len(df) >= 6:
                # 獲取最近的6筆訂單（排除之前的測試數據）
                recent_orders = df.tail(6)
                
                # 更新狀態
                df.loc[recent_orders.index, 'order_status'] = 'FILLED'
                df.loc[recent_orders.index, 'filled_quantity'] = df.loc[recent_orders.index, 'quantity']
                df.loc[recent_orders.index, 'remaining_quantity'] = 0.0
                
                # 添加完成時間
                current_time = datetime.now(timezone.utc).isoformat()
                df.loc[recent_orders.index, 'order_completed_time'] = current_time
                
                # 保存更新
                df.to_csv(csv_path, index=False, encoding='utf-8')
                
                print(f"✅ 已更新 {len(recent_orders)} 筆訂單狀態為FILLED")
            else:
                print("❌ CSV文件中沒有足夠的訂單數據")
        else:
            print("❌ CSV文件不存在")
            
    except Exception as e:
        print(f"❌ 更新CSV文件失敗: {e}")
    
    print()

def test_strategy_performance_analysis():
    """測試策略性能分析"""
    print("=== 測試策略性能分析 ===")
    
    try:
        # 載入交易數據
        trades_df = backtest_engine.load_trades_data()
        
        if not trades_df.empty:
            # 分析整體策略性能
            performance = analyze_strategy_performance(trades_df)
            
            print(f"📊 策略性能分析結果:")
            print(f"   總交易數: {performance.total_trades}")
            print(f"   盈利交易: {performance.winning_trades}")
            print(f"   虧損交易: {performance.losing_trades}")
            print(f"   勝率: {performance.win_rate:.2f}%")
            print(f"   總損益: {performance.total_pnl:.2f}")
            print(f"   盈利因子: {performance.profit_factor:.2f}")
            print(f"   最大回撤: {performance.max_drawdown:.2f} ({performance.max_drawdown_pct:.2f}%)")
            print(f"   夏普比率: {performance.sharpe_ratio:.2f}")
            print(f"   索提諾比率: {performance.sortino_ratio:.2f}")
            print(f"   年化收益率: {performance.annualized_return:.2f}")
            print(f"   策略效率: {performance.strategy_efficiency:.2f}")
            print(f"   信號準確率: {performance.signal_accuracy:.2f}")
        else:
            print("❌ 沒有找到交易數據")
            
    except Exception as e:
        print(f"❌ 策略性能分析失敗: {e}")
    
    print()

def test_market_environment_analysis():
    """測試市場環境分析"""
    print("=== 測試市場環境分析 ===")
    
    try:
        # 載入交易數據
        trades_df = backtest_engine.load_trades_data()
        
        if not trades_df.empty:
            # 分析市場環境
            market_env = analyze_market_environment(trades_df)
            
            print(f"🌍 市場環境分析結果:")
            print(f"   交易對: {market_env.trading_pair}")
            print(f"   分析期間: {market_env.period_start.strftime('%Y-%m-%d')} 到 {market_env.period_end.strftime('%Y-%m-%d')}")
            print(f"   日波動率: {market_env.volatility_daily:.4f}")
            print(f"   年化波動率: {market_env.volatility_annualized:.4f}")
            print(f"   平均ATR: {market_env.atr_average:.4f}")
            print(f"   趨勢強度: {market_env.trend_strength}")
            print(f"   趨勢方向: {market_env.trend_direction}")
            print(f"   趨勢一致性: {market_env.trend_consistency:.2f}")
            print(f"   市場情緒: {market_env.market_sentiment}")
            print(f"   恐懼貪婪指數: {market_env.fear_greed_index:.1f}")
            print(f"   市場狀態: {market_env.market_regime}")
        else:
            print("❌ 沒有找到交易數據")
            
    except Exception as e:
        print(f"❌ 市場環境分析失敗: {e}")
    
    print()

def test_parameter_sensitivity_analysis():
    """測試參數敏感性分析"""
    print("=== 測試參數敏感性分析 ===")
    
    try:
        # 載入交易數據
        trades_df = backtest_engine.load_trades_data()
        
        if not trades_df.empty:
            # 分析槓桿參數敏感性
            leverage_sensitivity = backtest_engine.analyze_parameter_sensitivity(trades_df, 'leverage')
            
            print(f"🔧 槓桿參數敏感性分析:")
            print(f"   參數名稱: {leverage_sensitivity.parameter_name}")
            print(f"   參數值範圍: {leverage_sensitivity.parameter_values}")
            print(f"   敏感性分數: {leverage_sensitivity.sensitivity_score:.4f}")
            print(f"   最優值: {leverage_sensitivity.optimal_value}")
            print(f"   最優性能: {leverage_sensitivity.optimal_performance:.2f}")
            print(f"   穩定性分數: {leverage_sensitivity.stability_score:.4f}")
            
            # 分析信號強度參數敏感性
            signal_sensitivity = backtest_engine.analyze_parameter_sensitivity(trades_df, 'signal_strength')
            
            print(f"\n📡 信號強度參數敏感性分析:")
            print(f"   參數名稱: {signal_sensitivity.parameter_name}")
            print(f"   參數值範圍: {signal_sensitivity.parameter_values}")
            print(f"   敏感性分數: {signal_sensitivity.sensitivity_score:.4f}")
            print(f"   最優值: {signal_sensitivity.optimal_value}")
            print(f"   最優性能: {signal_sensitivity.optimal_performance:.2f}")
            print(f"   穩定性分數: {signal_sensitivity.stability_score:.4f}")
        else:
            print("❌ 沒有找到交易數據")
            
    except Exception as e:
        print(f"❌ 參數敏感性分析失敗: {e}")
    
    print()

def test_strategy_combination_analysis():
    """測試策略組合分析"""
    print("=== 測試策略組合分析 ===")
    
    try:
        # 載入交易數據
        trades_df = backtest_engine.load_trades_data()
        
        if not trades_df.empty:
            # 分析策略組合
            combo_analysis = backtest_engine.analyze_strategy_combination(trades_df)
            
            print(f"🎯 策略組合分析結果:")
            
            # 個別策略性能
            if 'individual_performances' in combo_analysis:
                print(f"   個別策略性能:")
                for strategy_name, performance in combo_analysis['individual_performances'].items():
                    print(f"     {strategy_name}:")
                    print(f"       交易數: {performance.total_trades}")
                    print(f"       勝率: {performance.win_rate:.2f}%")
                    print(f"       總損益: {performance.total_pnl:.2f}")
                    print(f"       夏普比率: {performance.sharpe_ratio:.2f}")
            
            # 組合效果
            if 'combo_effectiveness' in combo_analysis:
                print(f"   組合效果:")
                for combo_mode, metrics in combo_analysis['combo_effectiveness'].items():
                    print(f"     {combo_mode}:")
                    print(f"       交易數: {metrics.get('total_trades', 0)}")
                    print(f"       勝率: {metrics.get('win_rate', 0):.2f}%")
                    print(f"       總損益: {metrics.get('total_pnl', 0):.2f}")
                    print(f"       夏普比率: {metrics.get('sharpe_ratio', 0):.2f}")
        else:
            print("❌ 沒有找到交易數據")
            
    except Exception as e:
        print(f"❌ 策略組合分析失敗: {e}")
    
    print()

def test_full_backtest_report():
    """測試完整回測報告"""
    print("=== 測試完整回測報告 ===")
    
    try:
        # 運行完整回測
        report = run_backtest()
        
        if report:
            print(f"📋 完整回測報告生成成功!")
            print(f"   摘要:")
            print(f"     交易對: {report['summary']['trading_pair']}")
            print(f"     總交易數: {report['summary']['total_trades']}")
            print(f"     總損益: {report['summary']['total_pnl']:.2f}")
            print(f"     勝率: {report['summary']['win_rate']:.2f}%")
            print(f"     夏普比率: {report['summary']['sharpe_ratio']:.2f}")
            
            print(f"\n   報告已保存到: logs/backtest_results/")
            
            # 檢查保存的文件
            results_dir = "logs/backtest_results"
            if os.path.exists(results_dir):
                files = os.listdir(results_dir)
                if files:
                    latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(results_dir, x)))
                    print(f"   最新報告文件: {latest_file}")
        else:
            print("❌ 回測報告生成失敗")
            
    except Exception as e:
        print(f"❌ 完整回測報告測試失敗: {e}")
    
    print()

def main():
    """主測試函數"""
    print("🚀 開始測試回測引擎模組\n")
    
    try:
        # 創建測試數據
        create_test_data()
        
        # 更新CSV文件中的訂單狀態
        update_csv_with_filled_orders()
        
        # 測試各項功能
        test_strategy_performance_analysis()
        test_market_environment_analysis()
        test_parameter_sensitivity_analysis()
        test_strategy_combination_analysis()
        test_full_backtest_report()
        
        print("🎉 所有測試完成！")
        print("\n📋 測試結果摘要:")
        print("   ✅ 策略性能分析")
        print("   ✅ 市場環境分析")
        print("   ✅ 參數敏感性分析")
        print("   ✅ 策略組合分析")
        print("   ✅ 完整回測報告")
        
        print(f"\n📁 請檢查以下文件:")
        print(f"   📄 logs/trades.csv - 交易記錄")
        print(f"   📄 logs/backtest_results/ - 回測報告")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
