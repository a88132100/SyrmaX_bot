# trading/constants.py
# 統一的常數管理檔案

# 交易方向常數
SIDE_BUY = "BUY"
SIDE_SELL = "SELL"

# 訂單類型常數
ORDER_TYPE_MARKET = "MARKET"
ORDER_TYPE_LIMIT = "LIMIT"
ORDER_TYPE_STOP_MARKET = "STOP_MARKET"
ORDER_TYPE_STOP_LIMIT = "STOP_LIMIT"

# 策略信號常數
SIGNAL_BUY = 1
SIGNAL_SELL = -1
SIGNAL_HOLD = 0

# 交易所名稱常數
EXCHANGE_BINANCE = "BINANCE"
EXCHANGE_BYBIT = "BYBIT"
EXCHANGE_OKX = "OKX"
EXCHANGE_BINGX = "BINGX"
EXCHANGE_BITGET = "BITGET"

# 支援的交易所列表
SUPPORTED_EXCHANGES = [
    EXCHANGE_BINANCE,
    EXCHANGE_BYBIT,
    EXCHANGE_OKX,
    EXCHANGE_BINGX,
    EXCHANGE_BITGET
]

# 交易所 URL 配置
EXCHANGE_URLS = {
    EXCHANGE_BINANCE: {
        "mainnet": "https://fapi.binance.com",
        "testnet": "https://testnet.binancefuture.com"
    },
    EXCHANGE_BYBIT: {
        "mainnet": "https://api.bybit.com",
        "testnet": "https://api-testnet.bybit.com"
    },
    EXCHANGE_OKX: {
        "mainnet": "https://www.okx.com",
        "testnet": "https://testnet.okx.com"
    },
    EXCHANGE_BINGX: {
        "mainnet": "https://bingx.com",
        "testnet": "https://testnet.bingx.com"
    },
    EXCHANGE_BITGET: {
        "mainnet": "https://www.bitget.com",
        "testnet": "https://testnet.bitget.com"
    }
}

# 幣種精度配置（對應舊的 symbol_precision）
SYMBOL_PRECISION = {
    "BTCUSDT": 3,
    "ETHUSDT": 2,
    "BNBUSDT": 2,
    "ADAUSDT": 0,
    "DOTUSDT": 1,
    "LINKUSDT": 1,
    "LTCUSDT": 2,
    "BCHUSDT": 2,
    "XRPUSDT": 0,
    "EOSUSDT": 0
}

# 預設 K 線週期配置
SYMBOL_INTERVALS = {
    "BTCUSDT": "1m",
    "ETHUSDT": "1m",
    "BNBUSDT": "1m",
    "ADAUSDT": "1m",
    "DOTUSDT": "1m",
    "LINKUSDT": "1m",
    "LTCUSDT": "1m",
    "BCHUSDT": "1m",
    "XRPUSDT": "1m",
    "EOSUSDT": "1m"
}

# 交易頻率配置（秒）
SYMBOL_INTERVAL_SECONDS = {
    "BTCUSDT": 3,
    "ETHUSDT": 3,
    "BNBUSDT": 3,
    "ADAUSDT": 5,
    "DOTUSDT": 5,
    "LINKUSDT": 5,
    "LTCUSDT": 5,
    "BCHUSDT": 5,
    "XRPUSDT": 5,
    "EOSUSDT": 5
}

# 策略組合模式
COMBO_MODE_AGGRESSIVE = "aggressive"
COMBO_MODE_BALANCED = "balanced"
COMBO_MODE_CONSERVATIVE = "conservative"
COMBO_MODE_AUTO = "auto"
COMBO_MODE_CUSTOM = "custom"

COMBO_MODE_CHOICES = [
    (COMBO_MODE_AGGRESSIVE, "激進模式"),
    (COMBO_MODE_BALANCED, "平衡模式"),
    (COMBO_MODE_CONSERVATIVE, "保守模式"),
    (COMBO_MODE_AUTO, "自動模式"),
    (COMBO_MODE_CUSTOM, "自定義模式"),
]

# 止盈止損模式
EXIT_MODE_PERCENTAGE = "PERCENTAGE"
EXIT_MODE_AMOUNT = "AMOUNT"
EXIT_MODE_ATR = "ATR"
EXIT_MODE_HYBRID = "HYBRID"

EXIT_MODE_CHOICES = [
    (EXIT_MODE_PERCENTAGE, "百分比模式"),
    (EXIT_MODE_AMOUNT, "固定金額模式"),
    (EXIT_MODE_ATR, "ATR動態模式"),
    (EXIT_MODE_HYBRID, "混合模式"),
]

# 預設配置值（對應舊的 config.py）
DEFAULT_CONFIG = {
    # 交易所配置
    "EXCHANGE": "CCXT",
    "EXCHANGE_NAME": "BINANCE",
    "USE_TESTNET": True,
    "TEST_MODE": False,
    
    # 交易對配置
    "SYMBOLS": ["BTCUSDT", "ETHUSDT"],
    
    # 槓桿配置
    "LEVERAGE": 30,
    
    # 資金管理配置
    "BASE_POSITION_RATIO": 0.3,
    "MIN_POSITION_RATIO": 0.01,
    "MAX_POSITION_RATIO": 0.8,
    
    # 止盈止損配置
    "EXIT_MODE": EXIT_MODE_AMOUNT,
    "PRICE_TAKE_PROFIT_PERCENT": 20.0,
    "PRICE_STOP_LOSS_PERCENT": 1.0,
    "AMOUNT_TAKE_PROFIT_USDT": 20.0,
    "AMOUNT_STOP_LOSS_USDT": 10.0,
    "ATR_TAKE_PROFIT_MULTIPLIER": 2.0,
    "ATR_STOP_LOSS_MULTIPLIER": 1.0,
    "HYBRID_MIN_TAKE_PROFIT_USDT": 5.0,
    "HYBRID_MAX_TAKE_PROFIT_USDT": 20.0,
    "HYBRID_MIN_STOP_LOSS_USDT": 2.0,
    "HYBRID_MAX_STOP_LOSS_USDT": 10.0,
    
    # 風控配置
    "MAX_CONSECUTIVE_STOP_LOSS": 3,
    "ENABLE_TRADE_LOG": True,
    "ENABLE_TRADE_LIMITS": True,
    "MAX_TRADES_PER_HOUR": 10,
    "MAX_TRADES_PER_DAY": 50,
    "MAX_DAILY_LOSS_PERCENT": 25.0,
    
    # 系統配置
    "GLOBAL_INTERVAL_SECONDS": 3,
    
    # 精度配置
    "SYMBOL_PRECISION": SYMBOL_PRECISION,
    "SYMBOL_INTERVALS": SYMBOL_INTERVALS,
    "SYMBOL_INTERVAL_SECONDS": SYMBOL_INTERVAL_SECONDS,
}
