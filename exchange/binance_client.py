# exchange/binance_client.py
# 幣安合約 API 封裝，需安裝 python-binance 套件
# pip install python-binance

from binance.um_futures import UMFutures
from binance.error import ClientError
from exchange.base import ExchangeClient
import logging
import time
from typing import List, Any

class BinanceClient(ExchangeClient):
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        初始化 Binance 合約 API 客戶端
        :param api_key: 幣安 API KEY
        :param api_secret: 幣安 API SECRET
        :param testnet: 是否使用測試網
        """
        base_url = "https://testnet.binancefuture.com" if testnet else "https://fapi.binance.com"
        self.client = UMFutures(key=api_key, secret=api_secret, base_url=base_url)
        self.testnet = testnet
        self.exchange_name = "BINANCE"
        
        # 初始化時進行時間同步
        self._sync_time()
        
        logging.info(f"✅ BinanceClient 已初始化，testnet={testnet}")

    def _sync_time(self):
        """同步本地時間與Binance服務器時間"""
        try:
            server_time = self.client.time()
            local_time = int(time.time() * 1000)
            time_diff = abs(server_time['serverTime'] - local_time)
            
            if time_diff > 1000:  # 如果時間差超過1秒
                logging.warning(f"本地時間與Binance服務器時間相差 {time_diff}ms")
                logging.info("建議檢查系統時間設置")
            
            logging.info(f"Binance服務器時間同步成功，時間差: {time_diff}ms")
            
        except Exception as e:
            logging.warning(f"無法同步Binance服務器時間: {e}")

    def get_price(self, symbol: str) -> float:
        """取得最新市價"""
        try:
            ticker = self.client.ticker_price(symbol=symbol)
            return float(ticker['price'])
        except ClientError as e:
            logging.error(f"擷取 {symbol} 價格失敗: {e}")
            raise

    def fetch_klines(self, symbol: str, interval: str, limit: int = 500) -> List[Any]:
        """取得 K 線資料 (OHLCV)"""
        try:
            return self.client.klines(symbol=symbol, interval=interval, limit=limit)
        except ClientError as e:
            logging.error(f"擷取 {symbol} K線失敗: {e}")
            return []

    def place_order(self, symbol: str, side: str, quantity: float, type: str = "MARKET", stopPrice: float = None) -> dict:
        """下單，支援市價/限價/止損單"""
        try:
            params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': type.upper(),
                'quantity': quantity
            }
            if type.upper() in ["STOP_MARKET", "STOP"] and stopPrice:
                params['stopPrice'] = stopPrice
            return self.client.new_order(**params)
        except ClientError as e:
            logging.error(f"下單失敗: {e}")
            raise

    def cancel_all_orders(self, symbol: str):
        """取消所有未成交訂單"""
        try:
            return self.client.cancel_open_orders(symbol=symbol)
        except ClientError as e:
            logging.error(f"取消訂單失敗: {e}")
            raise

    def get_balance(self, asset: str = 'USDT') -> float:
        """查詢合約帳戶餘額"""
        try:
            balances = self.client.balance()
            for b in balances:
                if b['asset'] == asset:
                    return float(b['balance'])
            return 0.0
        except ClientError as e:
            if "Timestamp for this request was" in str(e):
                logging.error(f"時間同步問題，嘗試重新同步: {e}")
                self._sync_time()
                # 重試一次
                try:
                    balances = self.client.balance()
                    for b in balances:
                        if b['asset'] == asset:
                            return float(b['balance'])
                    return 0.0
                except Exception as e2:
                    logging.error(f"重試查詢餘額仍然失敗: {e2}")
                    return 0.0
            else:
                logging.error(f"查詢餘額失敗: {e}")
                return 0.0

    def get_leverage(self, symbol: str) -> int:
        """查詢當前槓桿倍數"""
        try:
            # 獲取賬戶信息，包含槓桿設置
            account_info = self.client.account()
            
            # 查找指定交易對的槓桿信息
            for position in account_info.get('positions', []):
                if position['symbol'] == symbol:
                    leverage = int(position.get('leverage', 1))
                    logging.info(f"{symbol} 當前槓桿: {leverage}x")
                    return leverage
            
            # 如果沒有找到，返回默認槓桿
            logging.warning(f"未找到 {symbol} 的槓桿信息，使用默認值")
            return 1
            
        except Exception as e:
            logging.error(f"查詢 {symbol} 槓桿失敗: {e}")
            return 1

    def set_leverage(self, symbol: str, leverage: int):
        """設定槓桿倍數"""
        try:
            resp = self.client.change_leverage(symbol=symbol, leverage=leverage)
            logging.info(f"已為 {symbol} 設定槓桿為 {leverage}x")
            return resp
        except ClientError as e:
            logging.error(f"設定槓桿失敗: {e}")
            return None

    def close(self):
        """Binance API 無需顯式關閉"""
        pass 