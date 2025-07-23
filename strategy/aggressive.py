# aggressive.py

import talib
import pandas as pd

# A1: EMA(3) / EMA(8) 短期均線交叉
def strategy_ema3_ema8_crossover(df: pd.DataFrame) -> int:
    ema3 = df['close'].ewm(span=3).mean()
    ema8 = df['close'].ewm(span=8).mean()

    if ema3.iloc[-1] > ema8.iloc[-1] and ema3.iloc[-2] <= ema8.iloc[-2]:
        return 1  # 多單進場
    elif ema3.iloc[-1] < ema8.iloc[-1] and ema3.iloc[-2] >= ema8.iloc[-2]:
        return -1  # 空單進場
    return 0  # 無訊號


# A2: 布林帶突破策略
def strategy_bollinger_breakout(df: pd.DataFrame) -> int:
    ma = df['close'].rolling(window=20).mean()
    std = df['close'].rolling(window=20).std()
    upper = ma + 2 * std
    lower = ma - 2 * std
    close = df['close'].iloc[-1]

    if close > upper.iloc[-1]:
        return 1  # 多單進場
    elif close < lower.iloc[-1]:
        return -1  # 空單進場
    return 0


# A3: VWAP 偏離策略（反向均值回歸）
def strategy_vwap_deviation(df: pd.DataFrame) -> int:
    cum_vol = df['volume'].cumsum()
    cum_vol_price = (df['close'] * df['volume']).cumsum()
    vwap = cum_vol_price / cum_vol
    current_price = df['close'].iloc[-1]
    deviation = (current_price - vwap.iloc[-1]) / vwap.iloc[-1]

    if deviation > 0.015:
        return -1  # 做空（價格過高）
    elif deviation < -0.015:
        return 1   # 做多（價格過低）
    return 0


# A4: 成交量爆量策略
def strategy_volume_spike(df: pd.DataFrame) -> int:
    avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
    current_volume = df['volume'].iloc[-1]

    if current_volume > avg_volume * 2:
        if df['close'].iloc[-1] > df['open'].iloc[-1]:
            return 1  # 陽線爆量，多單
        else:
            return -1  # 陰線爆量，空單
    return 0


# A5: CCI 反轉策略（震盪區間反轉）
def strategy_cci_reversal(df: pd.DataFrame) -> int:
    cci = talib.CCI(df['high'], df['low'], df['close'], timeperiod=10)
    latest = cci.iloc[-1]

    if latest > 100:
        return -1  # 超買做空
    elif latest < -100:
        return 1   # 超賣做多
    return 0

def run(params):
    """
    執行 Aggressive 策略的主入口。
    params: dict，前端傳來的參數（可根據實際需求擴充）
    回傳：策略運算結果（這裡先回傳範例字串）
    """
    # 這裡可以根據 params 做實際運算，這裡先回傳範例
    return {'message': '已執行 Aggressive 策略', 'params': params}
