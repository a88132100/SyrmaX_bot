# exchange/okx_client.py
# OKX 合約 API 封裝，需安裝 okx 套件
# pip install okx

import okx.Account as Account
import okx.Trade as Trade
import okx.MarketData as MarketData
import okx.PublicData as PublicData
from exchange.base import ExchangeClient
import logging
from typing import List, Any
import time

class OKXClient(ExchangeClient):
    def __init__(self, api_key: str, api_secret: str, passphrase: str, testnet: bool = False):
        """
        初始化 OKX 合約 API 客戶端
        :param api_key: OKX API KEY
        :param api_secret: OKX API SECRET
        :param passphrase: OKX API 密碼短語
        :param testnet: 是否使用測試網
        """
        # OKX 需要額外的 passphrase 參數
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        
        # 設定測試網或主網
        self.flag = "0" if testnet else "0"  # OKX 使用 flag 參數，0=實盤，1=模擬盤
        
        # 初始化各個 API 模組
        self.account_api = Account.AccountAPI(
            api_key, api_secret, passphrase, 
            flag=self.flag, 
            sandbox=testnet
        )
        self.trade_api = Trade.TradeAPI(
            api_key, api_secret, passphrase, 
            flag=self.flag, 
            sandbox=testnet
        )
        self.market_api = MarketData.MarketAPI(
            api_key, api_secret, passphrase, 
            flag=self.flag, 
            sandbox=testnet
        )
        self.public_api = PublicData.PublicAPI(
            api_key, api_secret, passphrase, 
            flag=self.flag, 
            sandbox=testnet
        )
        
        logging.info(f"✅ OKXClient 已初始化，testnet={testnet}")

    def get_price(self, symbol: str) -> float:
        """取得最新市價"""
        try:
            # OKX 需要將 USDT 轉換為 -USDT 格式
            okx_symbol = self._convert_symbol_format(symbol)
            ticker = self.market_api.get_ticker(instId=okx_symbol)
            
            if ticker['code'] == '0':
                return float(ticker['data'][0]['last'])
            else:
                raise Exception(f"獲取價格失敗: {ticker['msg']}")
                
        except Exception as e:
            logging.error(f"擷取 {symbol} 價格失敗: {e}")
            raise

    def fetch_klines(self, symbol: str, interval: str, limit: int = 500) -> List[Any]:
        """取得 K 線資料 (OHLCV)"""
        try:
            okx_symbol = self._convert_symbol_format(symbol)
            okx_interval = self._convert_interval_format(interval)
            
            klines = self.market_api.get_candlesticks(
                instId=okx_symbol,
                bar=okx_interval,
                limit=str(limit)
            )
            
            if klines['code'] == '0':
                return klines['data']
            else:
                logging.error(f"擷取 K線失敗: {klines['msg']}")
                return []
                
        except Exception as e:
            logging.error(f"擷取 {symbol} K線失敗: {e}")
            return []

    def place_order(self, symbol: str, side: str, quantity: float, type: str = "MARKET", stopPrice: float = None) -> dict:
        """下單，支援市價/限價/止損單"""
        try:
            okx_symbol = self._convert_symbol_format(symbol)
            okx_side = "buy" if side.upper() == "BUY" else "sell"
            okx_type = self._convert_order_type(type)
            
            params = {
                'instId': okx_symbol,
                'tdMode': 'cross',  # 全倉模式
                'side': okx_side,
                'ordType': okx_type,
                'sz': str(quantity)
            }
            
            # 如果是止損單，添加觸發價格
            if type.upper() in ["STOP_MARKET", "STOP"] and stopPrice:
                params['triggerPx'] = str(stopPrice)
            
            result = self.trade_api.place_order(**params)
            
            if result['code'] == '0':
                return result['data'][0]
            else:
                raise Exception(f"下單失敗: {result['msg']}")
                
        except Exception as e:
            logging.error(f"下單失敗: {e}")
            raise

    def cancel_all_orders(self, symbol: str):
        """取消所有未成交訂單"""
        try:
            okx_symbol = self._convert_symbol_format(symbol)
            result = self.trade_api.cancel_multiple_orders([
                {
                    'instId': okx_symbol,
                    'ordId': ''  # 空字串表示取消所有訂單
                }
            ])
            
            if result['code'] == '0':
                return result['data']
            else:
                logging.warning(f"取消訂單失敗: {result['msg']}")
                return []
                
        except Exception as e:
            logging.error(f"取消訂單失敗: {e}")
            raise

    def get_balance(self, asset: str = 'USDT') -> float:
        """查詢合約帳戶餘額"""
        try:
            result = self.account_api.get_account_balance()
            
            if result['code'] == '0':
                for balance in result['data']:
                    if balance['ccy'] == asset:
                        return float(balance['availBal'])
                return 0.0
            else:
                logging.error(f"查詢餘額失敗: {result['msg']}")
                return 0.0
                
        except Exception as e:
            logging.error(f"查詢餘額失敗: {e}")
            return 0.0

    def set_leverage(self, symbol: str, leverage: int):
        """設定槓桿倍數"""
        try:
            okx_symbol = self._convert_symbol_format(symbol)
            result = self.account_api.set_leverage(
                instId=okx_symbol,
                lever=str(leverage),
                mgnMode='cross'  # 全倉模式
            )
            
            if result['code'] == '0':
                logging.info(f"已為 {symbol} 設定槓桿為 {leverage}x")
                return result['data'][0]
            else:
                logging.error(f"設定槓桿失敗: {result['msg']}")
                return None
                
        except Exception as e:
            logging.error(f"設定槓桿失敗: {e}")
            return None

    def close(self):
        """OKX API 無需顯式關閉"""
        pass
    
    def _convert_symbol_format(self, symbol: str) -> str:
        """轉換交易對格式，例如 BTCUSDT -> BTC-USDT"""
        if symbol.endswith('USDT'):
            base = symbol[:-4]
            return f"{base}-USDT"
        return symbol
    
    def _convert_interval_format(self, interval: str) -> str:
        """轉換時間間隔格式"""
        interval_map = {
            '1m': '1m',
            '3m': '3m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1H',
            '2h': '2H',
            '4h': '4H',
            '6h': '6H',
            '12h': '12H',
            '1d': '1D',
            '1w': '1W',
            '1M': '1M'
        }
        return interval_map.get(interval, '1m')
    
    def _convert_order_type(self, order_type: str) -> str:
        """轉換訂單類型"""
        type_map = {
            'MARKET': 'market',
            'LIMIT': 'limit',
            'STOP_MARKET': 'conditional',
            'STOP': 'conditional'
        }
        return type_map.get(order_type.upper(), 'market')
