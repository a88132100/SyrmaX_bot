# config.py
# 選擇交易所
EXCHANGE = "CCXT"  # 直接填 "BINANCE" / "BYBIT" / ... 或 "CCXT"
EXCHANGE_NAME = "BINANCE"  # 僅在 CCXT 模式下指定具體交易所

# ✅ 控制是否使用測試網
USE_TESTNET = True
# API 金鑰設定（請填入你自己的）
API_KEY ="b68f1727f53dc69e6ba79b087292fd092b9a95e8b6f11f59a2e9f35462d0c396"
API_SECRET ="521158d85eefd7641b8f6fd94ab424ed404dbd047a9e1f4e5c22dc13047cc788"

# 要交易的幣種
SYMBOLS = ["BTCUSDT", "ETHUSDT"]

# 是否為測試模式（True = 測試，不會下真單）
TEST_MODE = False

# 交易槓桿倍數
LEVERAGE = 30

# 動態資金比例設置
BASE_POSITION_RATIO = 0.3  # 基礎資金比例
MIN_POSITION_RATIO = 0.01   # 最小資金比例
MAX_POSITION_RATIO = 0.8   # 最大資金比例

# 止盈止損模式設定
EXIT_MODE = "AMOUNT"  # 可選值: "PERCENTAGE"（百分比）, "AMOUNT"（固定金額）, "ATR"（ATR動態）, "HYBRID"（混合模式）

# 止盈止損 觸發判斷方式 (定義「如何判斷是否達到目標並觸發平倉」)


# 模式一：基於百分比的價格點觸發
PRICE_TAKE_PROFIT_PERCENT = 20.0  # 止盈百分比（例如：20.0 表示 20%）
PRICE_STOP_LOSS_PERCENT = 1.0     # 止損百分比（例如：1.0 表示 1%）

# 模式二：基於固定金額的浮動盈虧觸發
AMOUNT_TAKE_PROFIT_USDT = 20.0    # 止盈金額（USDT）
AMOUNT_STOP_LOSS_USDT = 10.0       # 止損金額（USDT）

# 模式三：基於 ATR 的動態止盈止損
ATR_TAKE_PROFIT_MULTIPLIER = 2.0  # ATR 止盈倍數
ATR_STOP_LOSS_MULTIPLIER = 1.0    # ATR 止損倍數

# 模式四：混合模式參數
HYBRID_MIN_TAKE_PROFIT_USDT = 5.0   # 最小止盈金額
HYBRID_MAX_TAKE_PROFIT_USDT = 20.0  # 最大止盈金額
HYBRID_MIN_STOP_LOSS_USDT = 2.0     # 最小止損金額
HYBRID_MAX_STOP_LOSS_USDT = 10.0    # 最大止損金額

# 每日風險控制參數
MAX_CONSECUTIVE_STOP_LOSS = 3
ENABLE_TRADE_LOG = True

# 幣種的小數位精度
symbol_precision = {
    "BTCUSDT": 3,
    "ETHUSDT": 2
}

# 每個幣種使用的策略 K 線週期（依 Binance 支援）
SYMBOL_INTERVALS = {
    "BTCUSDT": "1m",
    "ETHUSDT": "1m",
    
}

# ✅ 每家交易所的正式網與測試網 URL
EXCHANGE_URLS = {
    "BINANCE": {
        "mainnet": "https://fapi.binance.com",
        "testnet": "https://testnet.binancefuture.com"
    },
    "OKX": {"mainnet": "https://www.okx.com/trade-futures"},
    "BYBIT": {
        "mainnet": "https://api.bybit.com",
        "testnet": "https://api-testnet.bybit.com"
    },
    "BINGX": { "mainnet": "	https://bingx.com/en/market/futures/"},
    "BITGET": {"mainnet": "	https://www.bitget.com/futures"},
}

# 每個幣種的交易判斷頻率（單位：秒）
SYMBOL_INTERVAL_SECONDS = {
    "BTCUSDT": 3,     # 每 1 秒檢查一次
    "ETHUSDT": 3   
    # 可根據需求增加更多幣種與頻率
}
