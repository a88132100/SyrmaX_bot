# test_strategy_loader.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import pandas as pd
from combos.strategy_loader import load_all_combos, StrategyCombo
from combos.combo_schema import ComboRoot, StrategyComboConfig

# --- 測試 1: 成功載入 combos.json ---
def test_load_valid_combos():
    combos = load_all_combos("combos/combos.generated.json")
    assert isinstance(combos, list)
    assert all(isinstance(c, StrategyCombo) for c in combos)
    assert len(combos) > 0

# --- 測試 2: 欄位缺失時觸發驗證錯誤 ---
def test_invalid_combo_schema():
    broken = {
        "combos": [
            {
                "name": "破損資料",
                # 缺少 description / conditions 等欄位
                "parameters": {}
            }
        ]
    }
    with pytest.raises(Exception):
        ComboRoot.model_validate(broken)

# --- 測試 3: 模擬行情判斷 ---
class DummyCondition:
    type = "strategy_dummy_pass"

def dummy_pass(df):
    return 1

def dummy_fail(df):
    return 0

def test_combo_match_pass(monkeypatch):
    combo = StrategyComboConfig(
        name="Test Combo",
        description="測試條件通過",
        parameters={},
        conditions=[DummyCondition()]
    )
    monkeypatch.setitem(__import__("strategy_loader").strategy_registry, "strategy_dummy_pass", dummy_pass)
    result = StrategyCombo(combo).match(pd.DataFrame({"close": [100]}))
    assert result is True

def test_combo_match_fail(monkeypatch):
    combo = StrategyComboConfig(
        name="Test Combo",
        description="測試條件失敗",
        parameters={},
        conditions=[DummyCondition()]
    )
    monkeypatch.setitem(__import__("strategy_loader").strategy_registry, "strategy_dummy_pass", dummy_fail)
    result = StrategyCombo(combo).match(pd.DataFrame({"close": [100]}))
    assert result is False
