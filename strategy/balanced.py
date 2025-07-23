# balanced.py

import talib
import pandas as pd


# B1: RSI 均值回歸策略
def strategy_rsi_mean_reversion(df: pd.DataFrame) -> int:
    delta = df['close'].diff()
    gain = delta.clip(lower=0).rolling(window=10).mean()
    loss = -delta.clip(upper=0).rolling(window=10).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # RSI 從低檔穿越 40，做多；從高檔跌破 60，做空
    if rsi.iloc[-2] < 40 and rsi.iloc[-1] >= 40:
        return 1
    elif rsi.iloc[-2] > 60 and rsi.iloc[-1] <= 60:
        return -1
    return 0


# B2: ATR 突破策略（波動區突破）
def strategy_atr_breakout(df: pd.DataFrame) -> int:
    atr = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    prev_close = df['close'].iloc[-2]
    curr_close = df['close'].iloc[-1]
    prev_atr = atr.iloc[-2]

    # 若價格突破上一期 ATR 範圍則進場
    if curr_close > prev_close + prev_atr:
        return 1
    elif curr_close < prev_close - prev_atr:
        return -1
    return 0


# B3: 均線通道突破策略
def strategy_ma_channel(df: pd.DataFrame) -> int:
    ma_short = df['close'].rolling(window=5).mean()
    ma_long = df['close'].rolling(window=20).mean()
    upper = ma_long + (ma_long - ma_short)
    lower = ma_long - (ma_long - ma_short)
    price = df['close'].iloc[-1]

    if price > upper.iloc[-1]:
        return 1  # 多單
    elif price < lower.iloc[-1]:
        return -1  # 空單
    return 0


# B4: 成交量持續放大策略（三期內遞增）
def strategy_volume_trend(df: pd.DataFrame) -> int:
    vol = df['volume']
    last3 = vol.iloc[-3:]

    if last3.is_monotonic_increasing:
        return 1
    elif last3.is_monotonic_decreasing:
        return -1
    return 0


# B5: CCI 中期趨勢延續策略
def strategy_cci_mid_trend(df: pd.DataFrame) -> int:
    cci = talib.CCI(df['high'], df['low'], df['close'], timeperiod=20)
    prev = cci.iloc[-2]
    curr = cci.iloc[-1]

    if prev > 100 and curr > prev:
        return 1  # 趨勢增強，多單
    elif prev < -100 and curr < prev:
        return -1  # 趨勢減弱，空單
    return 0


def run(params):
    """
    執行 Balanced 策略的主入口。
    params: dict，前端傳來的參數（可根據實際需求擴充）
    回傳：策略運算結果（這裡先回傳範例字串）
    """
    # 這裡可以根據 params 做實際運算，這裡先回傳範例
    return {'message': '已執行 Balanced 策略', 'params': params}
