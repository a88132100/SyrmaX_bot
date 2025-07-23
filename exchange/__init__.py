# exchange/__init__.py

from config import EXCHANGE, EXCHANGE_NAME, API_KEY, API_SECRET, TEST_MODE

def load_exchange_client():
    if EXCHANGE.upper() == "CCXT":
        from .ccxt_client import CCXTClient
        return CCXTClient(EXCHANGE_NAME, API_KEY, API_SECRET, TEST_MODE)  # <-- 多一層指定 exchange_name
    elif EXCHANGE.upper() == "BINANCE":
        from .binance_client import BinanceClient
        return BinanceClient(API_KEY, API_SECRET)
    elif EXCHANGE.upper() == "OKX":
        from .okx_client import OKXClient
        return OKXClient(API_KEY, API_SECRET)
    elif EXCHANGE.upper() == "BYBIT":
        from .bybit_client import BybitClient
        return BybitClient(API_KEY, API_SECRET)
    elif EXCHANGE.upper() == "BINGX":
        from .bingx_client import BingXClient
        return BingXClient(API_KEY, API_SECRET)
    elif EXCHANGE.upper() == "BITGET":
        from .bitget_client import BitgetClient
        return BitgetClient(API_KEY, API_SECRET)
    else:
        raise ValueError(f"❌ 不支援的交易所名稱: {EXCHANGE}")
