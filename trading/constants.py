# constants.py

# 交易方向常數，避免硬編碼字串錯誤
SIDE_BUY = "BUY"
SIDE_SELL = "SELL"

# 幣種精度對照表（例如 BTCUSDT 需要小數點後 3 位）
# 用來計算下單數量時的 round() 精度
symbol_precision = {
    "BTCUSDT": 3,
    "ETHUSDT": 2
}
