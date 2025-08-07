# exchange/load_exchange_client.py
# 交易所客戶端載入器

from exchange.binance_client import BinanceClient
from exchange.bybit_client import BybitClient
from exchange.okx_client import OKXClient
from exchange.ccxt_client import CCXTClient
from exchange.base import ExchangeClient
import logging

def load_exchange_client(exchange_name: str, api_key: str, api_secret: str, 
                        testnet: bool = False, **kwargs) -> ExchangeClient:
    """
    根據交易所名稱載入對應的客戶端
    
    :param exchange_name: 交易所名稱 (BINANCE, BYBIT, OKX, BINGX, BITGET)
    :param api_key: API 金鑰
    :param api_secret: API 密鑰
    :param testnet: 是否使用測試網
    :param kwargs: 額外參數 (如 OKX 的 passphrase)
    :return: 交易所客戶端實例
    """
    
    exchange_name = exchange_name.upper()
    
    try:
        if exchange_name == "BINANCE":
            return BinanceClient(api_key, api_secret, testnet)
            
        elif exchange_name == "BYBIT":
            return BybitClient(api_key, api_secret, testnet)
            
        elif exchange_name == "OKX":
            # OKX 需要額外的 passphrase 參數
            passphrase = kwargs.get('passphrase', '')
            if not passphrase:
                raise ValueError("OKX 交易所需要 passphrase 參數")
            return OKXClient(api_key, api_secret, passphrase, testnet)
            
        elif exchange_name in ["BINGX", "BITGET"]:
            # 使用 CCXT 通用客戶端
            return CCXTClient(exchange_name, api_key, api_secret, testnet)
            
        else:
            # 預設使用 CCXT 通用客戶端
            logging.warning(f"未知交易所 {exchange_name}，使用 CCXT 通用客戶端")
            return CCXTClient(exchange_name, api_key, api_secret, testnet)
            
    except Exception as e:
        logging.error(f"載入交易所客戶端失敗 {exchange_name}: {e}")
        raise 