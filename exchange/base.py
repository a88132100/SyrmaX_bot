# exchange/base.py
from abc import ABC, abstractmethod
from typing import List, Any

class ExchangeClient(ABC):
    """
    這是所有交易所 client 必須繼承的基礎類別
    確保一致的操作介面，以便把交易所的實作與策略模型分離
    """

    @abstractmethod
    def get_price(self, symbol: str) -> float:
        """ 獲取定价 """
        pass

    @abstractmethod
    def fetch_klines(self, symbol: str, interval: str, limit: int = 500) -> List[Any]:
        """ 獲取 K 線 (OHLCV) 數據 """
        pass

    @abstractmethod
    def place_order(self, symbol: str, side: str, quantity: float, type: str = "MARKET", stopPrice: float = None) -> dict:
        """ 下單，支援指定訂單類型和止損價 (用於 STOP_MARKET 等) """
        pass

    @abstractmethod
    def cancel_all_orders(self, symbol: str):
        """ 取消所有未成單 """
        pass

    @abstractmethod
    def get_balance(self) -> float:
        """ 獲取用戶餘額 (預設為 USDT) """
        pass

    @abstractmethod
    def set_leverage(self, symbol: str, leverage: int):
        """ 設定交易對的槓桿倍數 """
        pass

    def close(self):
        """ 關閉 API session (非必須) """
        pass
