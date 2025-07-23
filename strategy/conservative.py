# conservative.py

import talib
import pandas as pd


# C1: 長期與中期 EMA 黃金交叉 / 死亡交叉
def strategy_long_ema_crossover(df: pd.DataFrame) -> int:
    ema50 = df['close'].ewm(span=50, adjust=False).mean()
    ema200 = df['close'].ewm(span=200, adjust=False).mean()

    if ema50.iloc[-1] > ema200.iloc[-1] and ema50.iloc[-2] <= ema200.iloc[-2]:
        return 1  # 黃金交叉，多單
    elif ema50.iloc[-1] < ema200.iloc[-1] and ema50.iloc[-2] >= ema200.iloc[-2]:
        return -1  # 死亡交叉，空單
    return 0


# C2: ADX 趨勢強度判斷
def strategy_adx_trend(df: pd.DataFrame) -> int:
    adx = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)

    if adx.iloc[-1] > 25:
        if df['close'].iloc[-1] > df['close'].iloc[-2]:
            return 1  # 趨勢向上
        else:
            return -1  # 趨勢向下
    return 0  # 無明顯趨勢


# C3: 布林帶中軌回歸（類似均值迴歸）
def strategy_bollinger_mean_reversion(df: pd.DataFrame) -> int:
    ma = df['close'].rolling(window=20).mean()
    std = df['close'].rolling(window=20).std()
    upper = ma + std
    lower = ma - std
    price = df['close'].iloc[-1]

    if price < lower.iloc[-1]:
        return 1  # 跌深反彈，多單
    elif price > upper.iloc[-1]:
        return -1  # 漲多回調，空單
    return 0


# C4: Ichimoku 雲圖（短中期趨勢比較）
def strategy_ichimoku_cloud(df: pd.DataFrame) -> int:
    high9 = df['high'].rolling(window=9).max()
    low9 = df['low'].rolling(window=9).min()
    tenkan = (high9 + low9) / 2

    high26 = df['high'].rolling(window=26).max()
    low26 = df['low'].rolling(window=26).min()
    kijun = (high26 + low26) / 2

    if tenkan.iloc[-1] > kijun.iloc[-1]:
        return 1  # 多方掌控
    elif tenkan.iloc[-1] < kijun.iloc[-1]:
        return -1  # 空方主導
    return 0


# C5: ATR 均值回歸策略（價格超出波動範圍）
def strategy_atr_mean_reversion(df: pd.DataFrame) -> int:
    atr = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    mean = df['close'].rolling(window=14).mean()
    price = df['close'].iloc[-1]

    if price < mean.iloc[-1] - atr.iloc[-1]:
        return 1  # 價格跌太深，做多
    elif price > mean.iloc[-1] + atr.iloc[-1]:
        return -1  # 價格漲過頭，做空
    return 0


def run(params):
    """
    執行 Conservative 策略的主入口。
    params: dict，前端傳來的參數（可根據實際需求擴充）
    回傳：策略運算結果（這裡先回傳範例字串）
    """
    # 這裡可以根據 params 做實際運算，這裡先回傳範例
    return {'message': '已執行 Conservative 策略', 'params': params}
