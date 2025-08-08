# -*- coding: utf-8 -*-
"""
Aggressive Strategy Module (重構版)
=================================
本檔案為《SyrmaX》系統的「激進 (Aggressive)」交易策略模組重構版。

重構目標
--------
1. **高度參數化**：所有門檻、週期、比例皆可透過 `config` 動態調整。
2. **中文註釋**：程式碼關鍵區段皆含用途、進出邏輯、風控說明。
3. **模組化結構**：採用 OOP 方式管理子策略；Risk Layer 與 Strategy Layer 分離。
4. **統一訊號介面**：策略僅輸出 `Signal` 物件，方便後續倉位管理與多幣種擴充。
5. **效能優化**：避免重複計算，使用向量化 / TA-Lib。

使用方式
--------
```python
>>> import pandas as pd, aggressive_refactored as aggr
>>> df = load_your_klines()
>>> signals = aggr.run(df)
```
`signals` 會是一組 `Signal` 物件 (或空列表)。
"""

from dataclasses import dataclass
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import talib

###############################################################################
# Config 區：所有可調參數集中管理
###############################################################################

def default_config() -> Dict[str, Any]:
    """回傳預設設定，可由外部覆寫"""
    return {
        # === 策略 A1：EMA 交叉 ===
        "A1_fast": 3,
        "A1_slow": 8,
        # === 策略 A2：布林帶突破 ===
        "A2_window": 12,
        "A2_sigma": 1.5,
        # === 策略 A3：VWAP 追價（順勢） ===
        "A3_deviation": 0.01,  # 1%
        # === 策略 A4：量能爆量突破 ===
        "A4_window": 20,
        "A4_volume_mult": 1.5,
        # === 策略 A5：CCI 進出場濾網 ===
        "A5_threshold": 150,
        # === 風控 ===
        "risk_atr_period": 14,
        "risk_sl_atr_mult": 1.5,
        "risk_tp_atr_mult": 3.0,
    }

###############################################################################
# Signal 資料類別
###############################################################################

@dataclass
class Signal:
    """標準化交易訊號"""
    side: int              # 1 = Long, -1 = Short
    entry: float           # 入場價 (參考)
    stop_loss: float       # 止損價
    take_profit: float     # 止盈價
    source: str            # 來源策略名稱

###############################################################################
# 策略基底類別
###############################################################################

class BaseStrategy:
    """所有子策略繼承此類別"""

    def __init__(self, name: str, cfg: Dict[str, Any]):
        self.name = name
        self.cfg = cfg

    def generate_signal(self, df: pd.DataFrame) -> List[Signal]:
        """子類別實作，回傳 0~多筆 Signal"""
        raise NotImplementedError

###############################################################################
# 子策略實作
###############################################################################

class EMACrossover(BaseStrategy):
    """A1: EMA 短週期交叉策略 (突破追價)"""

    def generate_signal(self, df: pd.DataFrame) -> List[Signal]:
        fast = self.cfg["A1_fast"]
        slow = self.cfg["A1_slow"]

        ema_fast = df["close"].ewm(span=fast).mean()
        ema_slow = df["close"].ewm(span=slow).mean()

        # 判斷交叉 (僅最近兩根 K 線)
        cross_up = ema_fast.iloc[-2] <= ema_slow.iloc[-2] and ema_fast.iloc[-1] > ema_slow.iloc[-1]
        cross_dn = ema_fast.iloc[-2] >= ema_slow.iloc[-2] and ema_fast.iloc[-1] < ema_slow.iloc[-1]

        if not (cross_up or cross_dn):
            return []

        side = 1 if cross_up else -1
        return [self._make_signal(df, side)]

    # ---------------------------------------------------------------------
    def _make_signal(self, df: pd.DataFrame, side: int) -> Signal:
        entry = df["close"].iloc[-1]
        sl, tp = calc_atr_sl_tp(df, side, self.cfg)
        return Signal(side, entry, sl, tp, self.name)

class BollingerBreakout(BaseStrategy):
    """A2: 布林帶突破 (提高頻率)"""

    def generate_signal(self, df: pd.DataFrame) -> List[Signal]:
        w = self.cfg["A2_window"]
        sigma = self.cfg["A2_sigma"]

        ma = df["close"].rolling(window=w).mean()
        std = df["close"].rolling(window=w).std()
        upper = ma + sigma * std
        lower = ma - sigma * std

        close = df["close"].iloc[-1]
        signals = []
        if close > upper.iloc[-1]:
            signals.append(self._make_signal(df, 1))
        elif close < lower.iloc[-1]:
            signals.append(self._make_signal(df, -1))
        return signals

    def _make_signal(self, df, side):
        entry = df["close"].iloc[-1]
        sl, tp = calc_atr_sl_tp(df, side, self.cfg)
        return Signal(side, entry, sl, tp, self.name)

class VWAPMomentum(BaseStrategy):
    """A3: VWAP 順勢追價策略 (價格偏離 + 動量)"""

    def generate_signal(self, df: pd.DataFrame) -> List[Signal]:
        dev_th = self.cfg["A3_deviation"]
        cum_vol = df["volume"].cumsum()
        cum_vol_price = (df["close"] * df["volume"]).cumsum()
        vwap = cum_vol_price / cum_vol

        price = df["close"].iloc[-1]
        deviation = (price - vwap.iloc[-1]) / vwap.iloc[-1]

        if abs(deviation) < dev_th:
            return []

        side = 1 if deviation > 0 else -1  # 順勢
        return [self._make_signal(df, side)]

    def _make_signal(self, df, side):
        entry = df["close"].iloc[-1]
        sl, tp = calc_atr_sl_tp(df, side, self.cfg)
        return Signal(side, entry, sl, tp, self.name)

class VolumeSpikeBreakout(BaseStrategy):
    """A4: 量能爆量突破策略"""

    def generate_signal(self, df: pd.DataFrame) -> List[Signal]:
        w = self.cfg["A4_window"]
        mult = self.cfg["A4_volume_mult"]

        avg_vol = df["volume"].rolling(window=w).mean().iloc[-1]
        cur_vol = df["volume"].iloc[-1]

        if cur_vol < avg_vol * mult:
            return []

        side = 1 if df["close"].iloc[-1] > df["open"].iloc[-1] else -1
        return [self._make_signal(df, side)]

    def _make_signal(self, df, side):
        entry = df["close"].iloc[-1]
        sl, tp = calc_atr_sl_tp(df, side, self.cfg)
        return Signal(side, entry, sl, tp, self.name)

class CCITrendFilter(BaseStrategy):
    """A5: CCI 趨勢濾網 (可當輔助，不單獨開倉)"""

    def generate_signal(self, df: pd.DataFrame) -> List[Signal]:
        threshold = self.cfg["A5_threshold"]
        cci = talib.CCI(df["high"], df["low"], df["close"], timeperiod=10)
        latest = cci.iloc[-1]

        # 只回傳趨勢方向作為濾網
        if latest > threshold:
            return [Signal(1, df["close"].iloc[-1], 0, 0, self.name)]  # 1 表示只允許多單
        elif latest < -threshold:
            return [Signal(-1, df["close"].iloc[-1], 0, 0, self.name)]  # -1 只允許空單
        return []

###############################################################################
# Risk / Utility 函式
###############################################################################

def calc_atr_sl_tp(df: pd.DataFrame, side: int, cfg: Dict[str, Any]):
    """依 ATR 計算動態止盈/止損"""
    period = cfg["risk_atr_period"]
    atr = talib.ATR(df["high"], df["low"], df["close"], timeperiod=period).iloc[-1]
    entry = df["close"].iloc[-1]
    sl = entry - side * cfg["risk_sl_atr_mult"] * atr
    tp = entry + side * cfg["risk_tp_atr_mult"] * atr
    return sl, tp

###############################################################################
# 核心 run() 入口
###############################################################################

def run(df: pd.DataFrame, user_config: Dict[str, Any] = None) -> List[Signal]:
    """
    執行激進策略組合
    """
    cfg = default_config()
    if user_config:
        cfg.update(user_config)
    
    strategies = [
        EMACrossover("A1", cfg),
        BollingerBreakout("A2", cfg),
        VWAPMomentum("A3", cfg),
        VolumeSpikeBreakout("A4", cfg),
        CCITrendFilter("A5", cfg),
    ]
    
    all_signals = []
    for strategy in strategies:
        signals = strategy.generate_signal(df)
        all_signals.extend(signals)
    
    return all_signals

# 為了兼容base.py的導入，添加這些函數
def strategy_ema3_ema8_crossover(df: pd.DataFrame) -> int:
    """EMA 3/8 交叉策略"""
    cfg = default_config()
    strategy = EMACrossover("A1", cfg)
    signals = strategy.generate_signal(df)
    if signals:
        return signals[0].side
    return 0

def strategy_bollinger_breakout(df: pd.DataFrame) -> int:
    """布林帶突破策略"""
    cfg = default_config()
    strategy = BollingerBreakout("A2", cfg)
    signals = strategy.generate_signal(df)
    if signals:
        return signals[0].side
    return 0

def strategy_vwap_deviation(df: pd.DataFrame) -> int:
    """VWAP 偏離策略"""
    cfg = default_config()
    strategy = VWAPMomentum("A3", cfg)
    signals = strategy.generate_signal(df)
    if signals:
        return signals[0].side
    return 0

def strategy_volume_spike(df: pd.DataFrame) -> int:
    """量能爆量策略"""
    cfg = default_config()
    strategy = VolumeSpikeBreakout("A4", cfg)
    signals = strategy.generate_signal(df)
    if signals:
        return signals[0].side
    return 0

def strategy_cci_reversal(df: pd.DataFrame) -> int:
    """CCI 反轉策略"""
    cfg = default_config()
    strategy = CCITrendFilter("A5", cfg)
    signals = strategy.generate_signal(df)
    if signals:
        return signals[0].side
    return 0

###############################################################################
# CLI 測試 (開發用，可刪除)
###############################################################################
if __name__ == "__main__":
    # 示範假資料
    import yfinance as yf

    df = yf.download("BTC-USD", period="30d", interval="1h")
    df.reset_index(inplace=True)
    df.rename(columns={"Date": "timestamp"}, inplace=True)

    sigs = run(df)
    for s in sigs:
        print(s)
