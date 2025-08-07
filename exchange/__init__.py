# exchange/__init__.py

from trading.config_manager import config_manager

def load_exchange_client():
    """
    載入交易所客戶端
    使用新的配置管理系統替代舊的 config.py
    """
    # 獲取交易所配置
    exchange_config = config_manager.get_exchange_config()
    
    exchange_name = exchange_config['exchange_name']
    api_key = exchange_config['api_key']
    api_secret = exchange_config['api_secret']
    use_testnet = exchange_config['use_testnet']
    
    if exchange_name.upper() == "BINANCE":
        from .binance_client import BinanceClient
        return BinanceClient(api_key, api_secret, use_testnet)
    elif exchange_name.upper() == "BYBIT":
        from .bybit_client import BybitClient
        return BybitClient(api_key, api_secret, use_testnet)
    elif exchange_name.upper() == "OKX":
        from .okx_client import OKXClient
        # OKX 需要額外的 passphrase 參數
        passphrase = config_manager.get('OKX_PASSPHRASE', str, '')
        return OKXClient(api_key, api_secret, passphrase, use_testnet)
    elif exchange_name.upper() in ["BINGX", "BITGET"]:
        from .ccxt_client import CCXTClient
        return CCXTClient(exchange_name, api_key, api_secret, use_testnet)
    else:
        raise ValueError(f"❌ 不支援的交易所名稱: {exchange_name}")
