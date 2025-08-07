# coding: utf-8
"""Base Strategy Bundler（重構版）

將 Aggressive / Balanced / Conservative 三種風格的『子策略』
重新包裝成五組自訂「策略組合包」，並提供統一的投票邏輯。
兼容：
1. 舊版函式回傳 int（-1/0/1）
2. 新版函式回傳 List[Signal] 物件（含 side 屬性）
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Callable, Iterable
import logging
# ---- 匯入子策略 -----------------------------------------------------------
from aggressive import (
    strategy_ema3_ema8_crossover,
    strategy_bollinger_breakout,
    strategy_vwap_deviation,
    strategy_volume_spike,
    strategy_cci_reversal,
)
from balanced import (
    strategy_rsi_mean_reversion,
    strategy_atr_breakout,
    strategy_ma_channel,
    strategy_volume_trend,
    strategy_cci_mid_trend,
)
from conservative import (
    strategy_long_ema_crossover,
    strategy_adx_trend,
    strategy_bollinger_mean_reversion,
    strategy_ichimoku_cloud,
    strategy_atr_mean_reversion,
)

# ---- Signal 資料類（與各風格模組保持一致） ------------------------------
@dataclass
class Signal:
    side: int
    entry: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    source: str = ""
    meta: Dict[str, Any] | None = None

# ---- 組合包定義 -----------------------------------------------------------
Bundle = Dict[str, Any]  # {'name': str, 'strategies': list[Callable]}

strategy_bundles: Dict[str, List[Bundle]] = {
    "aggressive": [
        {"name": "A1 + A2", "strategies": [strategy_ema3_ema8_crossover, strategy_bollinger_breakout]},
        {"name": "A2 + A4", "strategies": [strategy_bollinger_breakout, strategy_volume_spike]},
        {"name": "A1 + A5", "strategies": [strategy_ema3_ema8_crossover, strategy_cci_reversal]},
        {"name": "A3 + A4", "strategies": [strategy_vwap_deviation, strategy_volume_spike]},
        {"name": "單獨 A5", "strategies": [strategy_cci_reversal]},
    ],
    "balanced": [
        {"name": "B1 + B2", "strategies": [strategy_rsi_mean_reversion, strategy_atr_breakout]},
        {"name": "B2 + B3", "strategies": [strategy_atr_breakout, strategy_ma_channel]},
        {"name": "B3 + B4", "strategies": [strategy_ma_channel, strategy_volume_trend]},
        {"name": "B1 + B5", "strategies": [strategy_rsi_mean_reversion, strategy_cci_mid_trend]},
        {"name": "單獨 B2", "strategies": [strategy_atr_breakout]},
    ],
    "conservative": [
        {"name": "C1+C2+C3", "strategies": [strategy_long_ema_crossover, strategy_adx_trend, strategy_bollinger_mean_reversion]},
        {"name": "C2+C4+C5", "strategies": [strategy_adx_trend, strategy_ichimoku_cloud, strategy_atr_mean_reversion]},
        {"name": "C1+C4+C5", "strategies": [strategy_long_ema_crossover, strategy_ichimoku_cloud, strategy_atr_mean_reversion]},
        {"name": "C3+C4+C5", "strategies": [strategy_bollinger_mean_reversion, strategy_ichimoku_cloud, strategy_atr_mean_reversion]},
        {"name": "All Conservative", "strategies": [strategy_long_ema_crossover, strategy_adx_trend, strategy_bollinger_mean_reversion, strategy_ichimoku_cloud, strategy_atr_mean_reversion]},
    ],
}

# ---- Helper：將各種回傳格式統一為 int(-1/0/1) ---------------------------

def _to_side(result) -> int:
    """接受 int 或 Signal 或 Iterable[Signal] → 回傳最終 side"""
    if isinstance(result, int):
        return result
    if isinstance(result, Signal):
        return result.side
    if isinstance(result, Iterable):
        for r in result:                      # 找第一個非 0 side
            if isinstance(r, Signal) and r.side != 0:
                return r.side
            if isinstance(r, int) and r != 0:
                return r
    return 0

# ---- 投票模型 -------------------------------------------------------------

def _vote(sides: List[int], style: str) -> int:
    """根據風格權重做決策"""
    if style == "aggressive":
        # 只要有一個多/空且無相反訊號即採用
        if 1 in sides and -1 not in sides:
            return 1
        if -1 in sides and 1 not in sides:
            return -1
        return 0
    if style == "balanced":
        pos, neg = sides.count(1), sides.count(-1)
        if max(pos, neg) / len(sides) >= 0.6:
            return 1 if pos > neg else -1
        return 0
    # conservative
    if all(s >= 0 for s in sides) and any(s == 1 for s in sides):
        return 1
    if all(s <= 0 for s in sides) and any(s == -1 for s in sides):
        return -1
    return 0

# ---- 主函式 ---------------------------------------------------------------

def evaluate_bundles(df, style: str) -> int:
    """
    df : pd.DataFrame (包含 open/high/low/close/volume 等欄位)
    style : 'aggressive' | 'balanced' | 'conservative'
    回傳：1=多單, -1=空單, 0=觀望
    """
    if style not in strategy_bundles:
        raise ValueError(f"未知風格 {style}; 應為 {list(strategy_bundles)}")

    for bundle in strategy_bundles[style]:
        # 執行每一子策略並收集 side
        sides: List[int] = []
        for strat in bundle["strategies"]:
            try:
                result = strat(df)
                sides.append(_to_side(result))
            except Exception as e:
                logging.exception(f"策略 {strat.__name__} 失敗: {e}")
                sides.append(0)

        decision = _vote(sides, style)
        if decision != 0:
            logging.info(f"Bundle≪{bundle['name']}≫ 觸發 → {'Long' if decision==1 else 'Short'}")
            return decision

    logging.info("所有組合均無共識 → HOLD")
    return 0

# ---- CLI 測試 -------------------------------------------------------------
if __name__ == "__main__":
    import yfinance as yf

    df_demo = yf.download("BTC-USD", period="60d", interval="1h")
    df_demo.reset_index(inplace=True)
    side = evaluate_bundles(df_demo, "balanced")
    print("最終決策:", side)
