# coding: utf-8
"""
平衡策略 (Balanced)
"""
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import pandas as pd
import talib

# ------------------------------ 全域預設參數 -----------------------------

def default_config() -> Dict[str, Any]:
    """集中管理所有可調參數，外部可用 user_cfg 覆寫"""
    return {
        # --- B1 RSI 均值回歸 ---
        "B1_rsi_period": 10,   # RSI 計算週期
        "B1_lower": 40,        # RSI 低檔線
        "B1_upper": 60,        # RSI 高檔線
        # --- B2 ATR 突破 ---
        "B2_atr_mult": 1.0,    # 突破門檻 = ATR × 倍數
        "B2_atr_period": 14,   # ATR 計算週期
        # --- B3 MA 通道 ---
        "B3_short_ma": 5,
        "B3_long_ma": 20,
        "B3_extra_atr": 0.2,   # 額外 ±ATR 作為雜訊濾除
        # --- B4 成交量趨勢 ---
        "B4_volume_window": 3, # 最近幾根量遞增/遞減
        "B4_price_window": 5,  # 搭配價格創高/創低驗證
        # --- B5 CCI 濾網 ---
        "B5_cci_period": 20,
        "B5_threshold": 100,
        # --- 風控設定 ---
        "risk_atr_period": 14,
        "risk_sl_atr_mult": 1.2,
        "risk_tp_atr_mult": 2.5,
    }

# ------------------------------ 基本資料結構 -----------------------------

@dataclass
class Signal:
    """標準化交易訊號物件"""
    side: int                 # 1=Long, -1=Short
    entry: float              # 參考入場價
    stop_loss: float          # 止損價
    take_profit: float        # 止盈價
    source: str               # 來源策略名稱
    meta: Optional[Dict[str, Any]] = None  # 其他補充資料

# ------------------------------ 策略基底類別 -----------------------------

class BaseStrategy:
    """所有子策略繼承此類別，統一 _make() 建立 Signal"""

    filter_only = False  # 若為 True 表示此策略僅作為方向濾網

    def __init__(self, name: str, cfg: Dict[str, Any], atr: float):
        self.name, self.cfg, self.atr = name, cfg, atr

    def generate(self, df: pd.DataFrame) -> List[Signal]:
        raise NotImplementedError  # 交給子類別實作

    def _make(self, df: pd.DataFrame, side: int) -> Signal:
        """依風控設定產出 Signal"""
        price = df["close"].iloc[-1]
        sl = price - side * self.cfg["risk_sl_atr_mult"] * self.atr  # 動態止損
        tp = price + side * self.cfg["risk_tp_atr_mult"] * self.atr  # 動態止盈
        return Signal(side, price, sl, tp, self.name)

# ------------------------------ 子策略實作 -----------------------------

class RSIMeanReversion(BaseStrategy):
    """B1：RSI 40/60 均值回歸策略
    條件：RSI 由下上穿 40 → 做多；RSI 由上跌破 60 → 做空
    屬性：中性偏均值，於盤整或短趨勢反轉時出手。
    """

    def generate(self, df):
        rsi_series = df["rsi"]
        low, high = self.cfg["B1_lower"], self.cfg["B1_upper"]
        # 檢測 RSI 穿越情形
        up_cross = rsi_series.iloc[-2] < low <= rsi_series.iloc[-1]
        dn_cross = rsi_series.iloc[-2] > high >= rsi_series.iloc[-1]
        if up_cross:
            return [self._make(df, 1)]
        if dn_cross:
            return [self._make(df, -1)]
        return []

class ATRBreakout(BaseStrategy):
    """B2：ATR 突破策略
    條件：最新收盤 - 前收 >= ±(ATR × 倍數) 視為動能突破。
    """

    def generate(self, df):
        diff = df["close"].iloc[-1] - df["close"].iloc[-2]
        thr = self.cfg["B2_atr_mult"] * self.atr
        if diff > thr:
            return [self._make(df, 1)]  # 上漲突破
        if diff < -thr:
            return [self._make(df, -1)] # 下跌突破
        return []

class MAChannel(BaseStrategy):
    """B3：移動平均通道策略
    使用 5MA 與 20MA 差值決定通道寬度，並加上 0.2ATR 濾除雜訊。
    當收盤突破上/下通道即進場。
    """

    def generate(self, df):
        diff_ma = abs(df["ma_short"] - df["ma_long"])
        upper = df["ma_long"] + diff_ma + self.cfg["B3_extra_atr"] * self.atr
        lower = df["ma_long"] - diff_ma - self.cfg["B3_extra_atr"] * self.atr
        close = df["close"].iloc[-1]
        if close > upper.iloc[-1]:
            return [self._make(df, 1)]
        if close < lower.iloc[-1]:
            return [self._make(df, -1)]
        return []

class VolumeTrend(BaseStrategy):
    """B4：成交量趨勢 + 價格創高/創低
    條件：
    1. 近 3 根量能遞增且收盤創近 5 根新高 → 做多
    2. 近 3 根量能遞減且收盤創近 5 根新低 → 做空
    """

    def generate(self, df):
        w, p = self.cfg["B4_volume_window"], self.cfg["B4_price_window"]
        vols = df["volume"].iloc[-w:]
        close = df["close"].iloc[-1]
        if vols.is_monotonic_increasing and close >= df["close"].iloc[-p:].max():
            return [self._make(df, 1)]
        if vols.is_monotonic_decreasing and close <= df["close"].iloc[-p:].min():
            return [self._make(df, -1)]
        return []

class CCITrendFilter(BaseStrategy):
    """B5：CCI 趨勢濾網（不單獨開倉，僅限制方向）"""

    filter_only = True  # 標記為濾網

    def generate(self, df):
        latest = df["cci"].iloc[-1]
        thr = self.cfg["B5_threshold"]
        if latest > thr:
            return [Signal(1, df["close"].iloc[-1], 0, 0, self.name)]  # 只允許多單
        if latest < -thr:
            return [Signal(-1, df["close"].iloc[-1], 0, 0, self.name)] # 只允許空單
        return []

# ------------------------------ 指標預計算 -----------------------------

def _precalc(df: pd.DataFrame, cfg: Dict[str, Any]):
    """一次性計算所有子策略共用指標欄位，提升效能"""
    df["rsi"] = talib.RSI(df["close"], timeperiod=cfg["B1_rsi_period"])
    df["atr"] = talib.ATR(df["high"], df["low"], df["close"], timeperiod=cfg["risk_atr_period"])
    df["ma_short"] = df["close"].rolling(cfg["B3_short_ma"]).mean()
    df["ma_long"] = df["close"].rolling(cfg["B3_long_ma"]).mean()
    df["cci"] = talib.CCI(df["high"], df["low"], df["close"], timeperiod=cfg["B5_cci_period"])

# ------------------------------ 核心 run 入口 -----------------------------

def run(df: pd.DataFrame, user_cfg: Dict[str, Any] = None) -> List[Signal]:
    """執行平衡策略組合"""
    cfg = default_config()
    if user_cfg:
        cfg.update(user_cfg)
    
    # 預計算 ATR
    atr = talib.ATR(df["high"], df["low"], df["close"], timeperiod=cfg["risk_atr_period"]).iloc[-1]
    
    strategies = [
        RSIMeanReversion("B1", cfg, atr),
        ATRBreakout("B2", cfg, atr),
        MAChannel("B3", cfg, atr),
        VolumeTrend("B4", cfg, atr),
        CCITrendFilter("B5", cfg, atr),
    ]
    
    all_signals = []
    for strategy in strategies:
        signals = strategy.generate(df)
        all_signals.extend(signals)
    
    return all_signals

# 為了兼容base.py的導入，添加這些函數
def strategy_rsi_mean_reversion(df: pd.DataFrame) -> int:
    """RSI 均值回歸策略"""
    cfg = default_config()
    atr = talib.ATR(df["high"], df["low"], df["close"], timeperiod=cfg["risk_atr_period"]).iloc[-1]
    strategy = RSIMeanReversion("B1", cfg, atr)
    signals = strategy.generate(df)
    if signals:
        return signals[0].side
    return 0

def strategy_atr_breakout(df: pd.DataFrame) -> int:
    """ATR 突破策略"""
    cfg = default_config()
    atr = talib.ATR(df["high"], df["low"], df["close"], timeperiod=cfg["risk_atr_period"]).iloc[-1]
    strategy = ATRBreakout("B2", cfg, atr)
    signals = strategy.generate(df)
    if signals:
        return signals[0].side
    return 0

def strategy_ma_channel(df: pd.DataFrame) -> int:
    """MA 通道策略"""
    cfg = default_config()
    atr = talib.ATR(df["high"], df["low"], df["close"], timeperiod=cfg["risk_atr_period"]).iloc[-1]
    strategy = MAChannel("B3", cfg, atr)
    signals = strategy.generate(df)
    if signals:
        return signals[0].side
    return 0

def strategy_volume_trend(df: pd.DataFrame) -> int:
    """成交量趨勢策略"""
    cfg = default_config()
    atr = talib.ATR(df["high"], df["low"], df["close"], timeperiod=cfg["risk_atr_period"]).iloc[-1]
    strategy = VolumeTrend("B4", cfg, atr)
    signals = strategy.generate(df)
    if signals:
        return signals[0].side
    return 0

def strategy_cci_mid_trend(df: pd.DataFrame) -> int:
    """CCI 中線趨勢策略"""
    cfg = default_config()
    atr = talib.ATR(df["high"], df["low"], df["close"], timeperiod=cfg["risk_atr_period"]).iloc[-1]
    strategy = CCITrendFilter("B5", cfg, atr)
    signals = strategy.generate(df)
    if signals:
        return signals[0].side
    return 0