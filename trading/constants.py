# trading/constants.py
# 統一的常數管理檔案

# 交易方向常數
SIDE_BUY = "BUY"
SIDE_SELL = "SELL"

# 訂單類型常數
ORDER_TYPE_MARKET = "MARKET" # 市價單
ORDER_TYPE_LIMIT = "LIMIT"   # 限價單
ORDER_TYPE_STOP_MARKET = "STOP_MARKET" # 市價止損單
ORDER_TYPE_STOP_LIMIT = "STOP_LIMIT"   # 限價止損單

# 策略信號常數
SIGNAL_BUY = 1 # 買入信號
SIGNAL_SELL = -1 # 賣出信號
SIGNAL_HOLD = 0 # 持有信號

# 交易所名稱常數
EXCHANGE_BINANCE = "BINANCE" # 幣安
EXCHANGE_BYBIT = "BYBIT"     # BYBIT
EXCHANGE_OKX = "OKX"         # OKX
EXCHANGE_BINGX = "BINGX"     # BINGX
EXCHANGE_BITGET = "BITGET"   # BITGET

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
COMBO_MODE_AGGRESSIVE = "aggressive" # 激進模式
COMBO_MODE_BALANCED = "balanced"     # 平衡模式
COMBO_MODE_CONSERVATIVE = "conservative" # 保守模式
COMBO_MODE_AUTO = "auto"            # 自動模式
COMBO_MODE_CUSTOM = "custom"        # 自定義模式

COMBO_MODE_CHOICES = [
    (COMBO_MODE_AGGRESSIVE, "激進模式"),
    (COMBO_MODE_BALANCED, "平衡模式"),
    (COMBO_MODE_CONSERVATIVE, "保守模式"),
    (COMBO_MODE_AUTO, "自動模式"),
    (COMBO_MODE_CUSTOM, "自定義模式"),
]

# 止盈止損模式
EXIT_MODE_PERCENTAGE = "PERCENTAGE" # 百分比模式
EXIT_MODE_AMOUNT = "AMOUNT"         # 固定金額模式
EXIT_MODE_ATR = "ATR"               # ATR動態模式
EXIT_MODE_HYBRID = "HYBRID"         # 混合模式

EXIT_MODE_CHOICES = [
    (EXIT_MODE_PERCENTAGE, "百分比模式"),
    (EXIT_MODE_AMOUNT, "固定金額模式"),
    (EXIT_MODE_ATR, "ATR動態模式"),
    (EXIT_MODE_HYBRID, "混合模式"),
]

# 預設配置值（對應舊的 config.py）
DEFAULT_CONFIG = {
    # 交易所配置
    "EXCHANGE": "CCXT",     # 交易所
    "EXCHANGE_NAME": "BINANCE", # 交易所名稱
    "USE_TESTNET": True,    # 使用測試網
    "TEST_MODE": False,     # 測試模式
    
    # 交易對配置
    "SYMBOLS": ["BTCUSDT", "ETHUSDT"],
    
    # 槓桿配置
    "LEVERAGE": 30,
    
    # 資金管理配置
    "BASE_POSITION_RATIO": 0.3, # 基礎部位比例
    "MIN_POSITION_RATIO": 0.01, # 最小部位比例
    "MAX_POSITION_RATIO": 0.8,  # 最大部位比例
    
    # 止盈止損配置
    "EXIT_MODE": EXIT_MODE_AMOUNT,    # 止盈止損模式
    "PRICE_TAKE_PROFIT_PERCENT": 20.0, # 價格止盈百分比
    "PRICE_STOP_LOSS_PERCENT": 1.0,    # 價格止損百分比
    "AMOUNT_TAKE_PROFIT_USDT": 20.0,   # 金額止盈USDT
    "AMOUNT_STOP_LOSS_USDT": 10.0,    # 金額止損USDT
    "ATR_TAKE_PROFIT_MULTIPLIER": 2.0, # ATR止盈倍數
    "ATR_STOP_LOSS_MULTIPLIER": 1.0,   # ATR止損倍數
    "HYBRID_MIN_TAKE_PROFIT_USDT": 5.0, # 混合止盈最小USDT
    "HYBRID_MAX_TAKE_PROFIT_USDT": 20.0, # 混合止盈最大USDT
    "HYBRID_MIN_STOP_LOSS_USDT": 2.0,    # 混合止損最小USDT
    "HYBRID_MAX_STOP_LOSS_USDT": 10.0,   # 混合止損最大USDT
    
    # 風控配置
    "MAX_CONSECUTIVE_STOP_LOSS": 3, # 最大連續止損次數
    "ENABLE_TRADE_LOG": True,       # 是否啟用交易日誌
    "ENABLE_TRADE_LIMITS": True,    # 是否啟用每日/每小時開倉次數限制
    "MAX_TRADES_PER_HOUR": 10,      # 每小時最大開倉次數
    "MAX_TRADES_PER_DAY": 50,       # 每日最大開倉次數
    "MAX_DAILY_LOSS_PERCENT": 25.0, # 每日最大虧損百分比
    
    # 波動率風險調整配置
    "ENABLE_VOLATILITY_RISK_ADJUSTMENT": True, # 是否啟用基於波動率的風險調整
    "VOLATILITY_THRESHOLD_MULTIPLIER": 2.0,    # 波動率閾值倍數（用於倉位調整）
    "VOLATILITY_PAUSE_THRESHOLD": 3.0,         # 波動率暫停閾值（ATR比率超過此值時暫停交易）
    "VOLATILITY_RECOVERY_THRESHOLD": 1.5,      # 波動率恢復閾值（ATR比率低於此值時恢復交易）
    "VOLATILITY_PAUSE_DURATION_MINUTES": 30,   # 波動率暫停持續時間（分鐘）
    
    # 最大同時持倉數量限制配置
    "ENABLE_MAX_POSITION_LIMIT": True,
    "MAX_SIMULTANEOUS_POSITIONS": 3,
    
    # 系統配置
    "GLOBAL_INTERVAL_SECONDS": 3,   # 全局間隔秒數
    
    # 精度配置
    "SYMBOL_PRECISION": SYMBOL_PRECISION, # 幣種精度
    "SYMBOL_INTERVALS": SYMBOL_INTERVALS, # 幣種間隔
    "SYMBOL_INTERVAL_SECONDS": SYMBOL_INTERVAL_SECONDS, # 幣種間隔秒數
}
