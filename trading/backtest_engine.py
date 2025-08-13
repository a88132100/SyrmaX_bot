# backtest_engine.py
"""
完整的回測引擎模組
包含策略性能分析、風險指標計算、市場環境分析等功能
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json
import os
from trading.trade_logger import OrderInfo
from trading.chart_generator import generate_equity_curve

# 配置日誌
logger = logging.getLogger(__name__)

@dataclass
class StrategyPerformance:
    """策略性能指標"""
    # 基本統計
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    break_even_trades: int = 0
    
    # 勝率指標
    win_rate: float = 0.0
    loss_rate: float = 0.0
    
    # 盈虧指標
    total_pnl: float = 0.0
    total_profit: float = 0.0
    total_loss: float = 0.0
    average_profit: float = 0.0
    average_loss: float = 0.0
    profit_factor: float = 0.0  # 總盈利/總虧損
    
    # 風險指標
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    max_single_loss: float = 0.0
    max_single_profit: float = 0.0
    consecutive_losses: int = 0
    max_consecutive_losses: int = 0
    
    # 高級指標
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    var_95: float = 0.0  # 95%置信度的VaR
    var_99: float = 0.0  # 99%置信度的VaR
    
    # 時間指標
    avg_trade_duration: float = 0.0
    total_trading_days: int = 0
    annualized_return: float = 0.0
    
    # 策略特定指標
    strategy_efficiency: float = 0.0  # 策略效率
    signal_accuracy: float = 0.0      # 信號準確率

@dataclass
class MarketEnvironment:
    """市場環境分析"""
    trading_pair: str
    period_start: datetime
    period_end: datetime
    
    # 波動率指標
    volatility_daily: float = 0.0
    volatility_annualized: float = 0.0
    atr_average: float = 0.0
    atr_volatility: float = 0.0
    
    # 趨勢指標
    trend_strength: str = "NEUTRAL"  # STRONG_UP, UP, NEUTRAL, DOWN, STRONG_DOWN
    trend_direction: str = "NEUTRAL"
    trend_consistency: float = 0.0
    
    # 市場情緒
    market_sentiment: str = "NEUTRAL"  # BULLISH, NEUTRAL, BEARISH
    fear_greed_index: float = 50.0
    volume_trend: str = "NEUTRAL"
    
    # 市場狀態
    market_regime: str = "NORMAL"  # NORMAL, VOLATILE, TRENDING, SIDEWAYS
    regime_volatility: float = 0.0
    regime_trend: float = 0.0

@dataclass
class ParameterSensitivity:
    """參數敏感性分析"""
    parameter_name: str
    parameter_values: List[Any]
    performance_metrics: List[Dict[str, float]]
    
    # 敏感性指標
    sensitivity_score: float = 0.0
    optimal_value: Any = None
    optimal_performance: float = 0.0
    stability_score: float = 0.0

class BacktestEngine:
    """回測引擎"""
    
    def __init__(self, log_dir: str = 'logs'):
        self.log_dir = log_dir
        self.trades_csv_path = os.path.join(log_dir, 'trades.csv')
        self.results_dir = os.path.join(log_dir, 'backtest_results')
        self.ensure_directories()
        
        logger.info("回測引擎初始化完成")
    
    def ensure_directories(self):
        """確保必要的目錄存在"""
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            logger.info(f"創建回測結果目錄: {self.results_dir}")
    
    def load_trades_data(self, trading_pair: str = None, 
                        start_date: datetime = None, 
                        end_date: datetime = None) -> pd.DataFrame:
        """
        載入交易數據
        
        Args:
            trading_pair: 交易對過濾
            start_date: 開始日期
            end_date: 結束日期
        
        Returns:
            交易數據DataFrame
        """
        try:
            if not os.path.exists(self.trades_csv_path):
                logger.error(f"交易記錄文件不存在: {self.trades_csv_path}")
                return pd.DataFrame()
            
            # 讀取CSV
            df = pd.read_csv(self.trades_csv_path)
            
            # 轉換時間列
            time_columns = ['timestamp', 'order_created_time', 'order_submitted_time', 
                           'first_fill_time', 'last_fill_time', 'order_completed_time', 
                           'order_cancelled_time']
            
            for col in time_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            
            # 過濾條件
            if trading_pair:
                df = df[df['trading_pair'] == trading_pair]
            
            if start_date:
                df = df[df['timestamp'] >= start_date]
            
            if end_date:
                df = df[df['timestamp'] <= end_date]
            
            # 只保留已完成的交易
            df = df[df['order_status'] == 'FILLED'].copy()
            
            logger.info(f"載入 {len(df)} 筆交易記錄")
            return df
            
        except Exception as e:
            logger.error(f"載入交易數據失敗: {e}")
            return pd.DataFrame()
    
    def calculate_strategy_performance(self, trades_df: pd.DataFrame) -> StrategyPerformance:
        """
        計算策略性能指標
        
        Args:
            trades_df: 交易數據DataFrame
        
        Returns:
            策略性能指標
        """
        if trades_df.empty:
            return StrategyPerformance()
        
        try:
            # 基本統計
            total_trades = len(trades_df)
            winning_trades = len(trades_df[trades_df['realized_pnl'] > 0])
            losing_trades = len(trades_df[trades_df['realized_pnl'] < 0])
            break_even_trades = len(trades_df[trades_df['realized_pnl'] == 0])
            
            # 勝率指標
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            loss_rate = (losing_trades / total_trades) * 100 if total_trades > 0 else 0
            
            # 盈虧指標
            total_pnl = trades_df['realized_pnl'].sum()
            total_profit = trades_df[trades_df['realized_pnl'] > 0]['realized_pnl'].sum()
            total_loss = abs(trades_df[trades_df['realized_pnl'] < 0]['realized_pnl'].sum())
            
            average_profit = total_profit / winning_trades if winning_trades > 0 else 0
            average_loss = total_loss / losing_trades if losing_trades > 0 else 0
            
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
            
            # 風險指標
            max_single_loss = trades_df['realized_pnl'].min()
            max_single_profit = trades_df['realized_pnl'].max()
            
            # 計算最大回撤
            cumulative_pnl = trades_df['realized_pnl'].cumsum()
            running_max = cumulative_pnl.expanding().max()
            drawdown = cumulative_pnl - running_max
            max_drawdown = drawdown.min()
            max_drawdown_pct = (max_drawdown / running_max.max()) * 100 if running_max.max() > 0 else 0
            
            # 計算連續虧損
            consecutive_losses = self._calculate_consecutive_losses(trades_df)
            max_consecutive_losses = max(consecutive_losses) if consecutive_losses else 0
            
            # 計算高級指標
            returns = trades_df['realized_pnl'] / trades_df['notional_value']
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            sortino_ratio = self._calculate_sortino_ratio(returns)
            calmar_ratio = self._calculate_calmar_ratio(returns, max_drawdown)
            var_95, var_99 = self._calculate_var(returns)
            
            # 時間指標
            if 'order_created_time' in trades_df.columns and 'order_completed_time' in trades_df.columns:
                trade_durations = (trades_df['order_completed_time'] - trades_df['order_created_time']).dt.total_seconds()
                avg_trade_duration = trade_durations.mean() if not trade_durations.empty else 0
            else:
                avg_trade_duration = 0
            
            # 計算年化收益率
            if 'timestamp' in trades_df.columns:
                total_days = (trades_df['timestamp'].max() - trades_df['timestamp'].min()).days
                total_days = max(total_days, 1)  # 避免除零
                annualized_return = (total_pnl / total_days) * 365
            else:
                annualized_return = 0
            
            # 策略效率（盈利交易的平均盈利 / 虧損交易的平均虧損）
            strategy_efficiency = average_profit / abs(average_loss) if average_loss != 0 else 0
            
            # 信號準確率（基於策略信號強度）
            if 'signal_strength' in trades_df.columns:
                signal_accuracy = trades_df['signal_strength'].mean() if not trades_df['signal_strength'].isna().all() else 0
            else:
                signal_accuracy = 0
            
            return StrategyPerformance(
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                break_even_trades=break_even_trades,
                win_rate=win_rate,
                loss_rate=loss_rate,
                total_pnl=total_pnl,
                total_profit=total_profit,
                total_loss=total_loss,
                average_profit=average_profit,
                average_loss=average_loss,
                profit_factor=profit_factor,
                max_drawdown=max_drawdown,
                max_drawdown_pct=max_drawdown_pct,
                max_single_loss=max_single_loss,
                max_single_profit=max_single_profit,
                consecutive_losses=len(consecutive_losses),
                max_consecutive_losses=max_consecutive_losses,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                var_95=var_95,
                var_99=var_99,
                avg_trade_duration=avg_trade_duration,
                total_trading_days=total_days if 'timestamp' in trades_df.columns else 0,
                annualized_return=annualized_return,
                strategy_efficiency=strategy_efficiency,
                signal_accuracy=signal_accuracy
            )
            
        except Exception as e:
            logger.error(f"計算策略性能指標失敗: {e}")
            return StrategyPerformance()
    
    def analyze_market_environment(self, trades_df: pd.DataFrame) -> MarketEnvironment:
        """
        分析市場環境
        
        Args:
            trades_df: 交易數據DataFrame
        
        Returns:
            市場環境分析
        """
        if trades_df.empty:
            return MarketEnvironment("", datetime.now(), datetime.now())
        
        try:
            trading_pair = trades_df['trading_pair'].iloc[0]
            period_start = trades_df['timestamp'].min()
            period_end = trades_df['timestamp'].max()
            
            # 波動率分析
            if 'market_volatility' in trades_df.columns:
                volatility_daily = trades_df['market_volatility'].mean()
                volatility_annualized = volatility_daily * np.sqrt(365)
            else:
                volatility_daily = volatility_annualized = 0
            
            if 'atr_value' in trades_df.columns:
                atr_average = trades_df['atr_value'].mean()
                atr_volatility = trades_df['atr_value'].std()
            else:
                atr_average = atr_volatility = 0
            
            # 趨勢分析
            trend_strength = self._analyze_trend_strength(trades_df)
            trend_direction = self._analyze_trend_direction(trades_df)
            trend_consistency = self._analyze_trend_consistency(trades_df)
            
            # 市場情緒分析
            market_sentiment = self._analyze_market_sentiment(trades_df)
            fear_greed_index = self._calculate_fear_greed_index(trades_df)
            volume_trend = self._analyze_volume_trend(trades_df)
            
            # 市場狀態分析
            market_regime = self._classify_market_regime(trades_df)
            regime_volatility = self._calculate_regime_volatility(trades_df)
            regime_trend = self._calculate_regime_trend(trades_df)
            
            return MarketEnvironment(
                trading_pair=trading_pair,
                period_start=period_start,
                period_end=period_end,
                volatility_daily=volatility_daily,
                volatility_annualized=volatility_annualized,
                atr_average=atr_average,
                atr_volatility=atr_volatility,
                trend_strength=trend_strength,
                trend_direction=trend_direction,
                trend_consistency=trend_consistency,
                market_sentiment=market_sentiment,
                fear_greed_index=fear_greed_index,
                volume_trend=volume_trend,
                market_regime=market_regime,
                regime_volatility=regime_volatility,
                regime_trend=regime_trend
            )
            
        except Exception as e:
            logger.error(f"分析市場環境失敗: {e}")
            return MarketEnvironment("", datetime.now(), datetime.now())
    
    def analyze_parameter_sensitivity(self, trades_df: pd.DataFrame, 
                                    parameter_name: str) -> ParameterSensitivity:
        """
        分析參數敏感性
        
        Args:
            trades_df: 交易數據DataFrame
            parameter_name: 參數名稱
        
        Returns:
            參數敏感性分析
        """
        if trades_df.empty or parameter_name not in trades_df.columns:
            return ParameterSensitivity(parameter_name, [], [])
        
        try:
            # 獲取參數的唯一值
            parameter_values = sorted(trades_df[parameter_name].unique())
            performance_metrics = []
            
            # 對每個參數值計算性能
            for value in parameter_values:
                subset_df = trades_df[trades_df[parameter_name] == value]
                if len(subset_df) > 0:
                    performance = self.calculate_strategy_performance(subset_df)
                    metrics = {
                        'win_rate': performance.win_rate,
                        'profit_factor': performance.profit_factor,
                        'sharpe_ratio': performance.sharpe_ratio,
                        'max_drawdown_pct': performance.max_drawdown_pct,
                        'total_pnl': performance.total_pnl
                    }
                    performance_metrics.append(metrics)
                else:
                    performance_metrics.append({})
            
            # 計算敏感性分數
            sensitivity_score = self._calculate_sensitivity_score(performance_metrics, parameter_values)
            
            # 找到最優值
            optimal_idx = np.argmax([m.get('total_pnl', 0) for m in performance_metrics])
            optimal_value = parameter_values[optimal_idx] if optimal_idx < len(parameter_values) else None
            optimal_performance = performance_metrics[optimal_idx].get('total_pnl', 0) if optimal_idx < len(performance_metrics) else 0
            
            # 計算穩定性分數
            stability_score = self._calculate_stability_score(performance_metrics)
            
            return ParameterSensitivity(
                parameter_name=parameter_name,
                parameter_values=parameter_values,
                performance_metrics=performance_metrics,
                sensitivity_score=sensitivity_score,
                optimal_value=optimal_value,
                optimal_performance=optimal_performance,
                stability_score=stability_score
            )
            
        except Exception as e:
            logger.error(f"分析參數敏感性失敗: {e}")
            return ParameterSensitivity(parameter_name, [], [])
    
    def analyze_strategy_combination(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析策略組合的協同效應
        
        Args:
            trades_df: 交易數據DataFrame
        
        Returns:
            策略組合分析結果
        """
        if trades_df.empty:
            return {}
        
        try:
            # 按策略分組分析
            strategy_groups = trades_df.groupby('strategy_name')
            strategy_performances = {}
            
            for strategy_name, group_df in strategy_groups:
                performance = self.calculate_strategy_performance(group_df)
                strategy_performances[strategy_name] = performance
            
            # 分析策略組合效果
            combo_analysis = self._analyze_combo_effectiveness(trades_df)
            
            # 計算策略相關性
            strategy_correlation = self._calculate_strategy_correlation(trades_df)
            
            return {
                'individual_performances': strategy_performances,
                'combo_effectiveness': combo_analysis,
                'strategy_correlation': strategy_correlation
            }
            
        except Exception as e:
            logger.error(f"分析策略組合失敗: {e}")
            return {}
    
    def generate_backtest_report(self, trading_pair: str = None,
                                start_date: datetime = None,
                                end_date: datetime = None) -> Dict[str, Any]:
        """
        生成完整的回測報告
        
        Args:
            trading_pair: 交易對
            start_date: 開始日期
            end_date: 結束日期
        
        Returns:
            回測報告
        """
        try:
            # 載入數據
            trades_df = self.load_trades_data(trading_pair, start_date, end_date)
            
            if trades_df.empty:
                logger.warning("沒有找到交易數據，無法生成回測報告")
                return {}
            
            # 計算各項指標
            strategy_performance = self.calculate_strategy_performance(trades_df)
            market_environment = self.analyze_market_environment(trades_df)
            strategy_combination = self.analyze_strategy_combination(trades_df)
            
            # 參數敏感性分析（針對關鍵參數）
            key_parameters = ['leverage', 'signal_strength', 'market_volatility']
            parameter_analysis = {}
            
            for param in key_parameters:
                if param in trades_df.columns:
                    parameter_analysis[param] = self.analyze_parameter_sensitivity(trades_df, param)
            
            # 生成報告
            report = {
                'summary': {
                    'trading_pair': trading_pair or 'ALL',
                    'period_start': start_date.isoformat() if start_date else trades_df['timestamp'].min().isoformat(),
                    'period_end': end_date.isoformat() if end_date else trades_df['timestamp'].max().isoformat(),
                    'total_trades': strategy_performance.total_trades,
                    'total_pnl': strategy_performance.total_pnl,
                    'win_rate': strategy_performance.win_rate,
                    'sharpe_ratio': strategy_performance.sharpe_ratio
                },
                'strategy_performance': strategy_performance.__dict__,
                'market_environment': market_environment.__dict__,
                'strategy_combination': strategy_combination,
                'parameter_analysis': {k: v.__dict__ for k, v in parameter_analysis.items()},
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # 保存報告
            self._save_backtest_report(report, trading_pair, start_date, end_date)
            
            # 生成圖表
            self._generate_backtest_charts(trades_df, strategy_performance, 
                                        strategy_combination, parameter_analysis, market_environment)
            
            logger.info("回測報告生成完成")
            return report
            
        except Exception as e:
            logger.error(f"生成回測報告失敗: {e}")
            return {}
    
    def _calculate_consecutive_losses(self, trades_df: pd.DataFrame) -> List[int]:
        """計算連續虧損次數"""
        try:
            consecutive_losses = []
            current_streak = 0
            
            for pnl in trades_df['realized_pnl']:
                if pnl < 0:
                    current_streak += 1
                else:
                    if current_streak > 0:
                        consecutive_losses.append(current_streak)
                        current_streak = 0
            
            # 處理最後一個連續虧損
            if current_streak > 0:
                consecutive_losses.append(current_streak)
            
            return consecutive_losses
        except Exception as e:
            logger.error(f"計算連續虧損失敗: {e}")
            return []
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """計算夏普比率"""
        try:
            if returns.empty or returns.std() == 0:
                return 0.0
            return (returns.mean() - risk_free_rate/365) / returns.std() * np.sqrt(365)
        except Exception as e:
            logger.error(f"計算夏普比率失敗: {e}")
            return 0.0
    
    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """計算索提諾比率"""
        try:
            if returns.empty:
                return 0.0
            negative_returns = returns[returns < 0]
            if negative_returns.empty:
                return float('inf')
            downside_deviation = negative_returns.std()
            if downside_deviation == 0:
                return 0.0
            return (returns.mean() - risk_free_rate/365) / downside_deviation * np.sqrt(365)
        except Exception as e:
            logger.error(f"計算索提諾比率失敗: {e}")
            return 0.0
    
    def _calculate_calmar_ratio(self, returns: pd.Series, max_drawdown: float) -> float:
        """計算卡爾馬比率"""
        try:
            if returns.empty or max_drawdown == 0:
                return 0.0
            annualized_return = returns.mean() * 365
            return annualized_return / abs(max_drawdown)
        except Exception as e:
            logger.error(f"計算卡爾馬比率失敗: {e}")
            return 0.0
    
    def _calculate_var(self, returns: pd.Series, confidence_levels: List[float] = [0.95, 0.99]) -> Tuple[float, float]:
        """計算風險價值(VaR)"""
        try:
            if returns.empty:
                return 0.0, 0.0
            var_95 = np.percentile(returns, (1 - confidence_levels[0]) * 100)
            var_99 = np.percentile(returns, (1 - confidence_levels[1]) * 100)
            return var_95, var_99
        except Exception as e:
            logger.error(f"計算VaR失敗: {e}")
            return 0.0, 0.0
    
    def _analyze_trend_strength(self, trades_df: pd.DataFrame) -> str:
        """分析趨勢強度"""
        try:
            if 'trend_strength' in trades_df.columns:
                trend_values = trades_df['trend_strength'].value_counts()
                if 'STRONG_UP' in trend_values and trend_values['STRONG_UP'] > len(trades_df) * 0.3:
                    return "STRONG_UP"
                elif 'STRONG_DOWN' in trend_values and trend_values['STRONG_DOWN'] > len(trades_df) * 0.3:
                    return "STRONG_DOWN"
                elif 'UP' in trend_values and trend_values['UP'] > len(trades_df) * 0.4:
                    return "UP"
                elif 'DOWN' in trend_values and trend_values['DOWN'] > len(trades_df) * 0.4:
                    return "DOWN"
            return "NEUTRAL"
        except Exception as e:
            logger.error(f"分析趨勢強度失敗: {e}")
            return "NEUTRAL"
    
    def _analyze_trend_direction(self, trades_df: pd.DataFrame) -> str:
        """分析趨勢方向"""
        try:
            if 'trend_strength' in trades_df.columns:
                up_count = len(trades_df[trades_df['trend_strength'].str.contains('UP', na=False)])
                down_count = len(trades_df[trades_df['trend_strength'].str.contains('DOWN', na=False)])
                
                if up_count > down_count * 1.5:
                    return "UP"
                elif down_count > up_count * 1.5:
                    return "DOWN"
            return "NEUTRAL"
        except Exception as e:
            logger.error(f"分析趨勢方向失敗: {e}")
            return "NEUTRAL"
    
    def _analyze_trend_consistency(self, trades_df: pd.DataFrame) -> float:
        """分析趨勢一致性"""
        try:
            if 'trend_strength' in trades_df.columns:
                # 計算趨勢變化的頻率
                trend_changes = (trades_df['trend_strength'] != trades_df['trend_strength'].shift()).sum()
                consistency = 1 - (trend_changes / len(trades_df))
                return max(0, consistency)
            return 0.5
        except Exception as e:
            logger.error(f"分析趨勢一致性失敗: {e}")
            return 0.5
    
    def _analyze_market_sentiment(self, trades_df: pd.DataFrame) -> str:
        """分析市場情緒"""
        try:
            # 基於盈利交易的比例和信號強度
            if 'realized_pnl' in trades_df.columns and 'signal_strength' in trades_df.columns:
                winning_ratio = len(trades_df[trades_df['realized_pnl'] > 0]) / len(trades_df)
                avg_signal_strength = trades_df['signal_strength'].mean()
                
                if winning_ratio > 0.6 and avg_signal_strength > 0.7:
                    return "BULLISH"
                elif winning_ratio < 0.4 and avg_signal_strength < 0.3:
                    return "BEARISH"
            return "NEUTRAL"
        except Exception as e:
            logger.error(f"分析市場情緒失敗: {e}")
            return "NEUTRAL"
    
    def _calculate_fear_greed_index(self, trades_df: pd.DataFrame) -> float:
        """計算恐懼貪婪指數"""
        try:
            if 'realized_pnl' in trades_df.columns and 'market_volatility' in trades_df.columns:
                # 基於盈利比例和波動率計算
                winning_ratio = len(trades_df[trades_df['realized_pnl'] > 0]) / len(trades_df)
                avg_volatility = trades_df['market_volatility'].mean()
                
                # 恐懼貪婪指數：0-100，50為中性
                fear_greed = 50 + (winning_ratio - 0.5) * 40 - (avg_volatility - 0.02) * 1000
                return max(0, min(100, fear_greed))
            return 50.0
        except Exception as e:
            logger.error(f"計算恐懼貪婪指數失敗: {e}")
            return 50.0
    
    def _analyze_volume_trend(self, trades_df: pd.DataFrame) -> str:
        """分析成交量趨勢"""
        try:
            # 這裡可以基於實際的成交量數據進行分析
            # 目前返回中性
            return "NEUTRAL"
        except Exception as e:
            logger.error(f"分析成交量趨勢失敗: {e}")
            return "NEUTRAL"
    
    def _classify_market_regime(self, trades_df: pd.DataFrame) -> str:
        """分類市場狀態"""
        try:
            if 'market_volatility' in trades_df.columns:
                avg_volatility = trades_df['market_volatility'].mean()
                
                if avg_volatility > 0.05:
                    return "VOLATILE"
                elif avg_volatility < 0.01:
                    return "SIDEWAYS"
                else:
                    return "NORMAL"
            return "NORMAL"
        except Exception as e:
            logger.error(f"分類市場狀態失敗: {e}")
            return "NORMAL"
    
    def _calculate_regime_volatility(self, trades_df: pd.DataFrame) -> float:
        """計算市場狀態的波動率"""
        try:
            if 'market_volatility' in trades_df.columns:
                return trades_df['market_volatility'].mean()
            return 0.0
        except Exception as e:
            logger.error(f"計算市場狀態波動率失敗: {e}")
            return 0.0
    
    def _calculate_regime_trend(self, trades_df: pd.DataFrame) -> float:
        """計算市場狀態的趨勢強度"""
        try:
            if 'trend_strength' in trades_df.columns:
                # 將趨勢強度轉換為數值
                trend_mapping = {
                    'STRONG_UP': 1.0, 'UP': 0.5, 'NEUTRAL': 0.0,
                    'DOWN': -0.5, 'STRONG_DOWN': -1.0
                }
                trend_values = trades_df['trend_strength'].map(trend_mapping).fillna(0)
                return trend_values.mean()
            return 0.0
        except Exception as e:
            logger.error(f"計算市場狀態趨勢強度失敗: {e}")
            return 0.0
    
    def _analyze_combo_effectiveness(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """分析策略組合效果"""
        try:
            if 'combo_mode' in trades_df.columns:
                combo_performances = {}
                for combo_mode in trades_df['combo_mode'].unique():
                    combo_df = trades_df[trades_df['combo_mode'] == combo_mode]
                    if len(combo_df) > 0:
                        performance = self.calculate_strategy_performance(combo_df)
                        combo_performances[combo_mode] = {
                            'total_trades': performance.total_trades,
                            'win_rate': performance.win_rate,
                            'total_pnl': performance.total_pnl,
                            'sharpe_ratio': performance.sharpe_ratio
                        }
                return combo_performances
            return {}
        except Exception as e:
            logger.error(f"分析策略組合效果失敗: {e}")
            return {}
    
    def _calculate_strategy_correlation(self, trades_df: pd.DataFrame) -> Dict[str, float]:
        """計算策略相關性"""
        try:
            if 'strategy_name' in trades_df.columns and 'realized_pnl' in trades_df.columns:
                # 按策略分組計算累積收益
                strategy_returns = {}
                for strategy_name in trades_df['strategy_name'].unique():
                    strategy_df = trades_df[trades_df['strategy_name'] == strategy_name]
                    if len(strategy_df) > 1:
                        strategy_returns[strategy_name] = strategy_df['realized_pnl'].cumsum()
                
                # 計算相關性矩陣
                if len(strategy_returns) > 1:
                    returns_df = pd.DataFrame(strategy_returns)
                    correlation_matrix = returns_df.corr()
                    return correlation_matrix.to_dict()
            return {}
        except Exception as e:
            logger.error(f"計算策略相關性失敗: {e}")
            return {}
    
    def _calculate_sensitivity_score(self, performance_metrics: List[Dict], 
                                   parameter_values: List) -> float:
        """計算參數敏感性分數"""
        try:
            if len(performance_metrics) < 2:
                return 0.0
            
            # 基於性能指標的變化計算敏感性
            pnl_values = [m.get('total_pnl', 0) for m in performance_metrics]
            if len(set(pnl_values)) > 1:
                pnl_std = np.std(pnl_values)
                pnl_mean = np.mean(pnl_values)
                if pnl_mean != 0:
                    return pnl_std / abs(pnl_mean)
            return 0.0
        except Exception as e:
            logger.error(f"計算敏感性分數失敗: {e}")
            return 0.0
    
    def _calculate_stability_score(self, performance_metrics: List[Dict]) -> float:
        """計算穩定性分數"""
        try:
            if len(performance_metrics) < 2:
                return 0.0
            
            # 基於性能指標的一致性計算穩定性
            win_rates = [m.get('win_rate', 0) for m in performance_metrics]
            win_rate_std = np.std(win_rates)
            max_win_rate = max(win_rates)
            
            if max_win_rate > 0:
                stability = 1 - (win_rate_std / max_win_rate)
                return max(0, stability)
            return 0.0
        except Exception as e:
            logger.error(f"計算穩定性分數失敗: {e}")
            return 0.0
    
    def _save_backtest_report(self, report: Dict[str, Any], 
                             trading_pair: str, 
                             start_date: datetime, 
                             end_date: datetime):
        """保存回測報告"""
        try:
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pair_name = trading_pair or 'ALL'
            start_str = start_date.strftime('%Y%m%d') if start_date else 'ALL'
            end_str = end_date.strftime('%Y%m%d') if end_date else 'ALL'
            
            filename = f"backtest_report_{pair_name}_{start_str}_{end_str}_{timestamp}.json"
            filepath = os.path.join(self.results_dir, filename)
            
            # 保存JSON報告
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"回測報告已保存: {filepath}")
            
        except Exception as e:
            logger.error(f"保存回測報告失敗: {e}")
    
    def _generate_backtest_charts(self, trades_df: pd.DataFrame, 
                                 strategy_performance: StrategyPerformance,
                                 strategy_combination: Dict[str, Any],
                                 parameter_analysis: Dict[str, Any],
                                 market_environment: MarketEnvironment):
        """生成回測圖表"""
        try:
            logger.info("開始生成回測圖表...")
            
            # 生成權益曲線圖
            equity_chart_path = generate_equity_curve(trades_df)
            if equity_chart_path:
                logger.info(f"權益曲線圖已生成: {equity_chart_path}")
            
            # 這裡可以添加更多圖表生成邏輯
            # 例如：性能指標圖、策略對比圖、參數敏感性圖等
            
            logger.info("回測圖表生成完成")
            
        except Exception as e:
            logger.error(f"生成回測圖表失敗: {e}")

# 創建全局實例
backtest_engine = BacktestEngine()

# 便捷函數
def run_backtest(trading_pair: str = None, 
                 start_date: datetime = None, 
                 end_date: datetime = None) -> Dict[str, Any]:
    """便捷函數：運行回測"""
    return backtest_engine.generate_backtest_report(trading_pair, start_date, end_date)

def analyze_strategy_performance(trades_df: pd.DataFrame) -> StrategyPerformance:
    """便捷函數：分析策略性能"""
    return backtest_engine.calculate_strategy_performance(trades_df)

def analyze_market_environment(trades_df: pd.DataFrame) -> MarketEnvironment:
    """便捷函數：分析市場環境"""
    return backtest_engine.analyze_market_environment(trades_df)
