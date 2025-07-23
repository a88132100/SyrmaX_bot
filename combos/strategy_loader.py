# strategy_loader.py
import logging
from typing import List
from combos.combo_schema import load_combos_from_file, StrategyComboConfig

class StrategyCombo:
    def __init__(self, config: StrategyComboConfig):
        self.name = config.name
        self.description = config.description
        self.parameters = config.parameters
        self.conditions = config.conditions

    def match(self, market_data) -> bool:
        for cond in self.conditions:
            # 假設所有條件函式已註冊於 registry，根據 type 取得執行結果
            if hasattr(cond, 'type'):
                func = strategy_registry.get(cond.type)
                if func is None:
                    logging.warning(f"未註冊策略函式: {cond.type}")
                    return False
                result = func(market_data)
                if result == 0:
                    return False  # 有一個條件不滿足就略過
        return True

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "conditions": [cond.dict() for cond in self.conditions]
        }

    @classmethod
    def from_dict(cls, data):
        parsed = StrategyComboConfig(**data)
        return cls(parsed)

# --- 策略函式註冊區 ---
from strategy import *

strategy_registry = {
    fn.__name__: fn
    for fn in globals().values()
    if callable(fn) and fn.__name__.startswith("strategy_")
}

# --- 載入主函式 ---
def load_all_combos(path: str) -> List[StrategyCombo]:
    try:
        config_root = load_combos_from_file(path)
        return [StrategyCombo(c) for c in config_root.combos]
    except Exception as e:
        logging.error(f"載入策略組合失敗: {e}")
        raise
