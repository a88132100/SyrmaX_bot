import logging
from .ccxt_client import CCXTClient

def load_exchange_client(exchange_name: str, api_key: str, api_secret: str, testnet: bool = False):
    """
    統一的交易所客戶端加載器。
    現在只使用 CCXTClient，它能同時處理主網和測試網。
    """
    logging.info(f"正在為交易所 '{exchange_name}' 加載客戶端 (測試網模式: {testnet})")
    
    try:
        # 無論何種情況，都使用通用的 CCXTClient
        return CCXTClient(
            exchange_name=exchange_name,
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet
        )
    except Exception as e:
        logging.error(f"為 {exchange_name} 加載客戶端時出錯: {e}")
        raise # 重新拋出異常，讓上層調用者知道失敗了 