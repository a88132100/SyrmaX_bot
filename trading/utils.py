# utils.py

from trading.constants import SYMBOL_PRECISION


def round_to_precision(symbol: str, value: float) -> float:
    """
    根據幣種精度將數值四捨五入，避免下單精度錯誤
    """
    precision = SYMBOL_PRECISION.get(symbol, 3)
    return round(value, precision)


def format_float(val: float, digits: int = 2) -> str:
    """
    格式化浮點數顯示用
    """
    return f"{val:.{digits}f}"

def get_precision(symbol: str) -> int:
    from trading.constants import SYMBOL_PRECISION
    return SYMBOL_PRECISION.get(symbol, 3)
