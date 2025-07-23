# exchange/bybit_client.py
# Bybit 合約 API 封裝，需安裝 pybit 套件
# pip install pybit

from pybit.unified_trading import HTTP
from exchange.base import ExchangeClient
import logging
from typing import List, Any

class BybitClient(ExchangeClient):
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        初始化 Bybit 合約 API 客戶端
        :param api_key: Bybit API KEY
        :param api_secret: Bybit API SECRET
        :param testnet: 是否使用測試網
        """
        endpoint = "https://api-testnet.bybit.com" if testnet else "https://api.bybit.com"
        self.client = HTTP(api_key=api_key, api_secret=api_secret, endpoint=endpoint)
        logging.info(f"✅ BybitClient 已初始化，testnet={testnet}")

    def get_price(self, symbol: str) -> float:
        """取得最新市價"""
        try:
            resp = self.client.get_tickers(category="linear", symbol=symbol)
            return float(resp['result']['list'][0]['lastPrice'])
        except Exception as e:
            logging.error(f"擷取 {symbol} 價格失敗: {e}")
            raise

    def fetch_klines(self, symbol: str, interval: str, limit: int = 500) -> List[Any]:
        """取得 K 線資料 (OHLCV)"""
        try:
            resp = self.client.get_kline(category="linear", symbol=symbol, interval=interval, limit=limit)
            return resp['result']['list']
        except Exception as e:
            logging.error(f"擷取 {symbol} K線失敗: {e}")
            return []

    def place_order(self, symbol: str, side: str, quantity: float, type: str = "MARKET", stopPrice: float = None) -> dict:
        """下單，支援市價/限價/止損單"""
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'side': side.upper(),
                'orderType': type.upper(),
                'qty': quantity
            }
            if type.upper() in ["STOP_MARKET", "STOP"] and stopPrice:
                params['triggerPrice'] = stopPrice
            return self.client.place_order(**params)
        except Exception as e:
            logging.error(f"下單失敗: {e}")
            raise

    def cancel_all_orders(self, symbol: str):
        """取消所有未成交訂單"""
        try:
            return self.client.cancel_all_orders(category="linear", symbol=symbol)
        except Exception as e:
            logging.error(f"取消訂單失敗: {e}")
            raise

    def get_balance(self, asset: str = 'USDT') -> float:
        """查詢合約帳戶餘額"""
        try:
            resp = self.client.get_wallet_balance(accountType="UNIFIED")
            return float(resp['result']['list'][0]['totalEquity'])
        except Exception as e:
            logging.error(f"查詢餘額失敗: {e}")
            return 0.0

    def set_leverage(self, symbol: str, leverage: int):
        """設定槓桿倍數"""
        try:
            resp = self.client.set_leverage(category="linear", symbol=symbol, buyLeverage=leverage, sellLeverage=leverage)
            logging.info(f"已為 {symbol} 設定槓桿為 {leverage}x")
            return resp
        except Exception as e:
            logging.error(f"設定槓桿失敗: {e}")
            return None

    def close(self):
        """Bybit API 無需顯式關閉"""
        pass 