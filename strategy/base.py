# base.py
import logging
# 匯入所有策略模組（A/B/C 系列）
# base.py

from strategy.aggressive import (
    strategy_ema3_ema8_crossover,
    strategy_bollinger_breakout,
    strategy_vwap_deviation,
    strategy_volume_spike,
    strategy_cci_reversal
)

from strategy.balanced import (
    strategy_rsi_mean_reversion,
    strategy_atr_breakout,
    strategy_ma_channel,
    strategy_volume_trend,
    strategy_cci_mid_trend
)

from strategy.conservative import (
    strategy_long_ema_crossover,
    strategy_adx_trend,
    strategy_bollinger_mean_reversion,
    strategy_ichimoku_cloud,
    strategy_atr_mean_reversion
)

# 定義策略組合包容器
strategy_bundles = {
    'aggressive': [
        {"name": "A1 + A2", "strategies": [strategy_ema3_ema8_crossover, strategy_bollinger_breakout]},
        {"name": "A2 + A4", "strategies": [strategy_bollinger_breakout, strategy_volume_spike]},
        {"name": "A1 + A5", "strategies": [strategy_ema3_ema8_crossover, strategy_cci_reversal]},
        {"name": "A3 + A4", "strategies": [strategy_vwap_deviation, strategy_volume_spike]},
        {"name": "單獨 A5（量能確認）", "strategies": [strategy_cci_reversal, strategy_volume_spike]},
    ],
    'balanced': [
        {"name": "B1 + B2", "strategies": [strategy_rsi_mean_reversion, strategy_atr_breakout]},
        {"name": "B2 + B3", "strategies": [strategy_atr_breakout, strategy_ma_channel]},
        {"name": "B3 + B4", "strategies": [strategy_ma_channel, strategy_volume_trend]},
        {"name": "B1 + B5", "strategies": [strategy_rsi_mean_reversion, strategy_cci_mid_trend]},
        {"name": "單獨 B2", "strategies": [strategy_atr_breakout]},
    ],
    'conservative': [
        {"name": "C1+C2+C3", "strategies": [strategy_long_ema_crossover, strategy_adx_trend, strategy_bollinger_mean_reversion]},
        {"name": "C2+C4+C5", "strategies": [strategy_adx_trend, strategy_ichimoku_cloud, strategy_atr_mean_reversion]},
        {"name": "C1+C4+C5", "strategies": [strategy_long_ema_crossover, strategy_ichimoku_cloud, strategy_atr_mean_reversion]},
        {"name": "C3+C4+C5", "strategies": [strategy_bollinger_mean_reversion, strategy_ichimoku_cloud, strategy_atr_mean_reversion]},
        {"name": "All Conservative", "strategies": [strategy_long_ema_crossover, strategy_adx_trend, strategy_bollinger_mean_reversion, strategy_ichimoku_cloud, strategy_atr_mean_reversion]},
    ]
}


def evaluate_bundles(df, strategy_style):
    """
    根據指定策略風格執行對應組合，並回傳交易信號
    回傳：1=多單, -1=空單, 0=觀望
    """
    if strategy_style not in strategy_bundles:
        valid = ', '.join(strategy_bundles.keys())
        raise ValueError(f"未知策略風格：{strategy_style}，可選擇：{valid}")

    bundles = strategy_bundles[strategy_style]

    # 定義不同風格的策略確認邏輯
    if strategy_style == 'aggressive':
        def check(results, name):
            if results[0] == 1:
                logging.info(f"符合【{name}】: 多單")
                return 1
            elif results[0] == -1:
                logging.info(f"符合【{name}】: 空單")
                return -1
            return 0
    elif strategy_style == 'balanced':
        def check(results, name):
            if all(r == 1 for r in results):
                logging.info(f"符合【{name}】: 多單（平衡）")
                return 1
            elif all(r == -1 for r in results):
                logging.info(f"符合【{name}】: 空單（平衡）")
                return -1
            return 0
    else:  # conservative
        def check(results, name):
            if all(r == 1 for r in results):
                logging.info(f"符合【{name}】: 多單（保守）")
                return 1
            elif all(r == -1 for r in results):
                logging.info(f"符合【{name}】: 空單（保守）")
                return -1
            return 0

    # 逐個組合測試，只要有一組符合就回傳結果
    for bundle in bundles:
        results = [strategy(df) for strategy in bundle["strategies"]]
        res = check(results, bundle["name"])
        if res != 0:
            return res

    logging.info("策略未達共識，維持觀望 HOLD")
    return 0
