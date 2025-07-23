# combo_schema.py
from typing import List, Literal, Union, Optional, Dict
from pydantic import BaseModel, Field, validator

# --- Condition Schema ---

class MACDCrossCondition(BaseModel):
    type: Literal["macd_cross"]
    direction: Literal["bullish", "bearish"]

class RSICondition(BaseModel):
    type: Literal["rsi"]
    operator: Literal[">=", "<=", ">", "<"]
    value: float

class BollingerCondition(BaseModel):
    type: Literal["bollinger"]
    position: Literal["above", "below"]

class ADXCondition(BaseModel):
    type: Literal["adx"]
    operator: Literal[">", "<", ">=", "<="]
    value: float

class GenericCondition(BaseModel):
    type: str  # e.g. strategy_cci_reversal 等

Condition = Union[
    MACDCrossCondition,
    RSICondition,
    BollingerCondition,
    ADXCondition,
    GenericCondition
]

# --- Combo Config Schema ---

class StrategyComboConfig(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Dict[str, Union[int, float, str]]]
    conditions: List[Condition]

class ComboRoot(BaseModel):
    combos: List[StrategyComboConfig]

# --- File Loader ---

import json

def load_combos_from_file(path: str) -> ComboRoot:
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    return ComboRoot.parse_obj(raw)
