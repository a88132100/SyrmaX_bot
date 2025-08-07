# coding: utf-8
"""
Conservative Strategy Module  ─ 保守型交易策略模組
================================================
本模組針對「保守（低頻 / 風險極低）」操作風格，內建五支子策略：

C1_EMA_Cross     ：50／200 EMA 黃金／死亡交叉（長期趨勢確認）
C2_ADX_Trend     ：ADX +DI／-DI 方向確認（僅在強勢趨勢中順勢）
C3_BB_MeanRev    ：布林通道 ±2σ 均值回歸（震盪盤防守反轉）
C4_Ichimoku_Cloud：一目均衡表雲層突破（需「收盤 + 雲層」雙重確認）
C5_ATR_Extreme   ：±1.5×ATR 過度擴張反轉（極端行情分批進出）

所有參數集中於 `default_config()`；每支策略皆以「generate()」輸出
`Signal` 物件（含入場價、動態 SL/TP 與來源標籤），便於日後回測
與風險統一管理。
"""

# ──────────────────── 1. 依賴與資料結構 ────────────────────
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import pandas as pd
import talib                       # TA-Lib 為技術指標計算函式庫

@dataclass
class Signal:
    """標準化訊號；side: 1=多單, -1=空單"""
    side: int
    entry: float
    stop_loss: float
    take_profit: float
    source: str
    meta: Optional[Dict[str, Any]] = None

# ──────────────────── 2. 全域預設參數 ────────────────────
def default_config() -> Dict[str, Any]:
    return {
        # C1 EMA
        "ema_fast": 50,
        "ema_slow": 200,
        # C2 ADX
        "adx_period": 14,
        "adx_threshold": 30,
        # C3 布林帶
        "bb_window": 20,
        "bb_sigma": 2.0,
        # C4 一目均衡表
        "ichimoku_tenkan": 9,
        "ichimoku_kijun": 26,
        # C5 ATR 反轉
        "atr_period": 14,
        "atr_mult": 1.5,
        # 共用風控
        "risk_sl_atr_mult": 1.0,
        "risk_tp_atr_mult": 2.0,
    }


# ──────────────────── 3. 基底策略類 ────────────────────
class BaseStrategy:
    """所有子策略繼承此類別，統一 `_make()` 產生 Signal"""
    filter_only = False            # 若為濾網專用，設 True

    def __init__(self, name: str, cfg: Dict[str, Any], atr: float):
        self.name, self.cfg, self.atr = name, cfg, atr

    def generate(self, df: pd.DataFrame) -> List[Signal]:
        raise NotImplementedError

    def _make(self, df: pd.DataFrame, side: int, meta: Dict[str, Any] | None = None) -> Signal:
        px = df["close"].iloc[-1]
        sl = px - side * self.cfg["risk_sl_atr_mult"] * self.atr
        tp = px + side * self.cfg["risk_tp_atr_mult"] * self.atr
        return Signal(side, px, sl, tp, self.name, meta)


# ──────────────────── 4. 子策略實作 ────────────────────
class EMA_Cross(BaseStrategy):
    """C1：50/200 EMA 黃金／死亡交叉；附收盤價同向突破過濾"""

    def generate(self, df):
        fast = df["ema_fast"]
        slow = df["ema_slow"]
        cross_up   = fast.iloc[-2] <= slow.iloc[-2] and fast.iloc[-1] > slow.iloc[-1] and df["close"].iloc[-1] > slow.iloc[-1]
        cross_down = fast.iloc[-2] >= slow.iloc[-2] and fast.iloc[-1] < slow.iloc[-1] and df["close"].iloc[-1] < slow.iloc[-1]
        if cross_up:
            return [self._make(df, 1, {"cross": "golden"})]
        if cross_down:
            return [self._make(df, -1, {"cross": "death"})]
        return []


class ADX_Trend(BaseStrategy):
    """C2：ADX 趨勢追蹤；僅在 ADX>threshold 且 +DI/-DI 同向時順勢"""

    def generate(self, df):
        adx = df["adx"].iloc[-1]
        pos, neg = df["+DI"].iloc[-1], df["-DI"].iloc[-1]
        if adx < self.cfg["adx_threshold"]:
            return []
        if pos > neg:                               # 強多趨勢
            return [self._make(df, 1, {"adx": adx})]
        if neg > pos:                               # 強空趨勢
            return [self._make(df, -1, {"adx": adx})]
        return []


class BB_MeanRev(BaseStrategy):
    """C3：布林帶 ±2σ 均值回歸；觸上軌做空、觸下軌做多"""

    def generate(self, df):
        c = df["close"].iloc[-1]
        upper, lower = df["bb_upper"].iloc[-1], df["bb_lower"].iloc[-1]
        if c >= upper:
            return [self._make(df, -1, {"bb": "upper"})]
        if c <= lower:
            return [self._make(df, 1, {"bb": "lower"})]
        return []


class Ichimoku_Cloud(BaseStrategy):
    """C4：一目均衡表雲層突破；收盤站上／跌破雲層 + Tenkan/Kijun 交叉"""

    def generate(self, df):
        tenkan, kijun = df["tenkan"].iloc[-1], df["kijun"].iloc[-1]
        senkou_a, senkou_b = df["senkou_a"].iloc[-1], df["senkou_b"].iloc[-1]
        cloud_top = max(senkou_a, senkou_b)
        cloud_bot = min(senkou_a, senkou_b)
        close = df["close"].iloc[-1]
        cross_up   = tenkan > kijun and tenkan.iloc[-2] <= kijun.iloc[-2]
        cross_down = tenkan < kijun and tenkan.iloc[-2] >= kijun.iloc[-2]
        if cross_up and close > cloud_top:
            return [self._make(df, 1)]
        if cross_down and close < cloud_bot:
            return [self._make(df, -1)]
        return []


class ATR_Extreme(BaseStrategy):
    """C5：±1.5 ATR 過度擴張反轉；適合抄底／逃頂的最後防線"""

    def generate(self, df):
        ref = df["close"].iloc[-2]
        thr = self.cfg["atr_mult"] * self.atr
        diff = df["close"].iloc[-1] - ref
        if diff >= thr:
            return [self._make(df, -1, {"extreme": "up"})]
        if diff <= -thr:
            return [self._make(df, 1, {"extreme": "down"})]
        return []

# ──────────────────── 5. 指標預計算 ────────────────────
def _precalc(df: pd.DataFrame, cfg: Dict[str, Any]):
    """一次性計算共用技術指標，避免重複運算"""
    df["ema_fast"] = talib.EMA(df["close"], timeperiod=cfg["ema_fast"])
    df["ema_slow"] = talib.EMA(df["close"], timeperiod=cfg["ema_slow"])

    df["atr"] = talib.ATR(df["high"], df["low"], df["close"], timeperiod=cfg["atr_period"])
    df["bb_upper"], df["bb_middle"], df["bb_lower"] = talib.BBANDS(
        df["close"], timeperiod=cfg["bb_window"], nbdevup=cfg["bb_sigma"], nbdevdn=cfg["bb_sigma"]
    )

    adx = talib.ADX(df["high"], df["low"], df["close"], timeperiod=cfg["adx_period"])
    plus_di = talib.PLUS_DI(df["high"], df["low"], df["close"], timeperiod=cfg["adx_period"])
    minus_di = talib.MINUS_DI(df["high"], df["low"], df["close"], timeperiod=cfg["adx_period"])
    df["adx"], df["+DI"], df["-DI"] = adx, plus_di, minus_di

    # 一目均衡表：先計算轉換線、基準線，再平移取得先行 Span
    high9, low9 = df["high"].rolling(cfg["ichimoku_tenkan"]).max(), df["low"].rolling(cfg["ichimoku_tenkan"]).min()
    high26, low26 = df["high"].rolling(cfg["ichimoku_kijun"]).max(), df["low"].rolling(cfg["ichimoku_kijun"]).min()
    df["tenkan"] = (high9 + low9) / 2
    df["kijun"] = (high26 + low26) / 2
    df["senkou_a"] = ((df["tenkan"] + df["kijun"]) / 2).shift(cfg["ichimoku_kijun"])
    span_b = (df["high"].rolling(52).max() + df["low"].rolling(52).min()) / 2
    df["senkou_b"] = span_b.shift(cfg["ichimoku_kijun"])


# ──────────────────── 6. 核心執行入口 ────────────────────
def run(df: pd.DataFrame, user_cfg: Dict[str, Any] | None = None) -> List[Signal]:
    """
    入口函式：
    1. 先合併外部設定並計算指標
    2. 逐支策略產生原始 Signal
    3. 以 C5(ATR_Extreme) 為超級濾網，避免追高殺低
    """
    cfg = default_config()
    if user_cfg:
        cfg.update(user_cfg)

    _precalc(df, cfg)
    atr_val = df["atr"].iloc[-1]

    strategies = [
        EMA_Cross("C1_EMA_Cross", cfg, atr_val),
        ADX_Trend("C2_ADX_Trend", cfg, atr_val),
        BB_MeanRev("C3_BB_MeanRev", cfg, atr_val),
        Ichimoku_Cloud("C4_Ichimoku_Cloud", cfg, atr_val),
        ATR_Extreme("C5_ATR_Extreme", cfg, atr_val),   # 濾網 + 末端反轉
    ]

    raw: List[Signal] = []
    for st in strategies:
        raw.extend(st.generate(df))

    # 濾掉 C5 標記為 extreme 的方向（若存在則以它為主）
    extremes = [s for s in raw if s.source == "C5_ATR_Extreme"]
    if extremes:
        # 若出現極端反轉訊號，僅保留其方向
        return extremes[:1]

    # 若沒有 extreme 濾網，就回傳第一支符合的保守訊號（頻率極低）
    tradable = [s for s in raw if s.source != "C5_ATR_Extreme"]
    return tradable[:1]


# ──────────────────── 7. CLI 測試（自行測試用，可刪除） ────────────────────
if __name__ == "__main__":
    import yfinance as yf

    df_demo = yf.download("BTC-USD", period="90d", interval="1d")
    df_demo.reset_index(inplace=True)
    sig = run(df_demo)
    print(sig)
