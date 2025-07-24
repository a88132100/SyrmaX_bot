# exchange/ccxt_client.py

import ccxt
import logging
from exchange.base import ExchangeClient
from typing import List, Any

class CCXTClient(ExchangeClient):
    def __init__(self, exchange_name: str, api_key: str, api_secret: str, testnet: bool):
        if not api_key or not api_secret:
            raise ValueError("❌ API_KEY 或 API_SECRET 未正確設置，請檢查 config.py 或環境變數！")

        exchange_class = getattr(ccxt, exchange_name.lower(), None)
        if not exchange_class:
            raise ValueError(f"❌ 無效的交易所名稱：{exchange_name}")

        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
            },
        })

        # 讓 CCXT 自行處理測試網的 URL
        if testnet:
            self.exchange.set_sandbox_mode(True)
            logging.info(f"✅ 已為 {exchange_name} 啟用測試網模式")
        else:
            logging.info(f"✅ 已為 {exchange_name} 啟用主網模式")

        # 載入市場，這對於獲取交易對資訊很重要
        try:
            self.exchange.load_markets()
        except ccxt.BaseError as e:
            logging.error(f"❌ 無法從 {exchange_name} 載入市場資訊: {e}")
            raise  # 重新拋出異常，初始化失敗

    def get_price(self, symbol: str) -> float:
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except ccxt.NetworkError as e:
            logging.error(f"擷取 {symbol} 價格時發生網路錯誤: {e}")
            raise
        except ccxt.ExchangeError as e:
            logging.error(f"擷取 {symbol} 價格時發生交易所錯誤: {e}")
            raise
        except Exception as e:
            logging.error(f"擷取 {symbol} 價格時發生未知錯誤: {e}")
            raise

    def fetch_klines(self, symbol: str, interval: str, limit: int = 500) -> List[Any]:
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe=interval, limit=limit)
        except Exception as e:
            logging.error(f"擷取 {symbol} K線時發生錯誤: {e}")
            return []

    def place_order(self, symbol: str, side: str, quantity: float, type: str = "market", params=None) -> dict:
        params = params or {}
        try:
            if type.lower() == "market":
                return self.exchange.create_market_order(symbol, side.lower(), quantity, params=params)
            elif type.lower() == "limit":
                # 假設需要 price 參數
                price = params.get('price')
                if not price:
                    raise ValueError("限價單需要 'price' 參數")
                return self.exchange.create_limit_order(symbol, side.lower(), quantity, price, params=params)
            else:
                raise ValueError(f"不支援的訂單類型: {type}")
        except Exception as e:
            logging.error(f"下單失敗 (symbol={symbol}, side={side}, qty={quantity}): {e}")
            raise

    def cancel_all_orders(self, symbol: str):
        try:
            if self.exchange.has("cancelAllOrders"):
                return self.exchange.cancel_all_orders(symbol)
            else:
                logging.warning(f"交易所 {self.exchange.id} 不支援 cancel_all_orders")
                return None
        except Exception as e:
            logging.error(f"取消 {symbol} 的所有訂單時發生錯誤: {e}")
            raise

    def get_balance(self, asset: str = 'USDT') -> float:
        try:
            # 確保使用合約帳戶
            balance = self.exchange.fetch_balance(params={'type': 'future'})
            return balance.get(asset, {}).get('free', 0.0)
        except Exception as e:
            logging.error(f"擷取 {asset} 餘額時發生錯誤: {e}")
        return 0.0

    def close(self):
        if hasattr(self.exchange, 'close'):
            self.exchange.close()

    def time(self):
        """回傳交易所伺服器時間（毫秒）"""
        try:
            return self.exchange.fetch_time()
        except ccxt.NotSupported:
            logging.warning(f"{self.exchange.id} 不支援 fetch_time(), 將使用本地時間。")
            return None
        except Exception as e:
            logging.error(f"獲取伺服器時間時發生錯誤: {e}")
            return None

    def set_leverage(self, symbol: str, leverage: int):
        """設定指定交易對的槓桿倍數"""
        try:
            # CCXT 的 set_leverage 方法是統一的
            self.exchange.set_leverage(leverage, symbol)
            logging.info(f"✅ 已成功為 {symbol} 設定槓桿為 {leverage}x")
            return True
        except ccxt.ExchangeError as e:
            logging.error(f"❌ 為 {symbol} 設定槓桿 {leverage}x 失敗: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ 為 {symbol} 設定槓桿時發生未知錯誤: {e}")
            return False

    def get_leverage(self, symbol: str) -> int:
        """查詢指定交易對的槓桿倍數。"""
        try:
            # 獲取倉位資訊，槓桿資訊通常包含在內
            # 注意：這只在有倉位時才可能返回槓桿值
            positions = self.exchange.fetch_positions([symbol])
            for position in positions:
                if position['symbol'] == symbol:
                    # 'leverage' 是 ccxt 統一的鍵
                    leverage = position.get('leverage')
                    if leverage:
                        return int(leverage)
            
            # 如果沒有倉位，某些交易所 (如 Binance) 允許直接查詢
            if self.exchange.id == 'binance':
                resp = self.exchange.fapiPrivate_get_leveragebracket({'symbol': symbol})
                # 遍歷返回的列表，找到對應的槓桿設置
                for bracket in resp:
                    if bracket['symbol'] == symbol:
                        return int(bracket['initialLeverage'])

            logging.warning(f"無法直接查詢 {symbol} 的槓桿，且當前無倉位。")
            return 0 # 或者返回一個預設/表示未知的數值

        except ccxt.NotSupported as e:
            logging.warning(f"交易所 {self.exchange.id} 不支援查詢槓桿: {e}")
            return 0
        except Exception as e:
            # 處理像 'binance {"code":-4048,"msg":"Symbol is not valid."}' 這樣的錯誤
            # 這通常發生在槓桿尚未被設定時
            if 'not valid' in str(e) or 'does not exist' in str(e):
                 logging.warning(f"查詢 {symbol} 槓桿失敗，可能是首次設定，將回傳 0。錯誤: {e}")
                 return 0
            logging.error(f"查詢 {symbol} 槓桿時發生錯誤: {e}")
            return 0
