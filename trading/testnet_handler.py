# trading/testnet_handler.py
# 測試網功能處理模組

import logging
from typing import Dict, Any, Optional
from trading.constants import EXCHANGE_URLS

logger = logging.getLogger(__name__)

class TestnetHandler:
    """
    測試網功能處理類別
    解決測試網環境下的特殊問題，如止盈止損功能限制
    """
    
    def __init__(self, exchange_name: str, testnet: bool = False):
        self.exchange_name = exchange_name.upper()
        self.testnet = testnet
        self._load_testnet_config()
    
    def _load_testnet_config(self):
        """載入測試網配置"""
        self.testnet_config = {
            'BINANCE': {
                'supports_stop_orders': True,
                'supports_take_profit': True,
                'supports_stop_loss': True,
                'order_types': ['MARKET', 'LIMIT', 'STOP_MARKET', 'STOP_LIMIT'],
                'max_leverage': 125,
                'min_order_size': 0.001,
                'price_precision': 2,
                'quantity_precision': 3
            },
            'BYBIT': {
                'supports_stop_orders': True,
                'supports_take_profit': True,
                'supports_stop_loss': True,
                'order_types': ['MARKET', 'LIMIT', 'STOP_MARKET', 'STOP_LIMIT'],
                'max_leverage': 100,
                'min_order_size': 0.001,
                'price_precision': 2,
                'quantity_precision': 3
            },
            'OKX': {
                'supports_stop_orders': True,
                'supports_take_profit': True,
                'supports_stop_loss': True,
                'order_types': ['MARKET', 'LIMIT', 'CONDITIONAL'],
                'max_leverage': 125,
                'min_order_size': 0.001,
                'price_precision': 2,
                'quantity_precision': 3
            },
            'BINGX': {
                'supports_stop_orders': False,  # 測試網可能不支援
                'supports_take_profit': False,
                'supports_stop_loss': False,
                'order_types': ['MARKET', 'LIMIT'],
                'max_leverage': 100,
                'min_order_size': 0.001,
                'price_precision': 2,
                'quantity_precision': 3
            },
            'BITGET': {
                'supports_stop_orders': False,  # 測試網可能不支援
                'supports_take_profit': False,
                'supports_stop_loss': False,
                'order_types': ['MARKET', 'LIMIT'],
                'max_leverage': 100,
                'min_order_size': 0.001,
                'price_precision': 2,
                'quantity_precision': 3
            }
        }
    
    def get_supported_features(self) -> Dict[str, Any]:
        """獲取測試網支援的功能"""
        if not self.testnet:
            return self.testnet_config.get(self.exchange_name, {})
        
        config = self.testnet_config.get(self.exchange_name, {})
        
        # 測試網環境下的特殊處理
        if self.testnet:
            # 某些交易所的測試網可能功能受限
            if self.exchange_name in ['BINGX', 'BITGET']:
                config['supports_stop_orders'] = False
                config['supports_take_profit'] = False
                config['supports_stop_loss'] = False
                config['order_types'] = ['MARKET', 'LIMIT']
        
        return config
    
    def can_use_stop_orders(self) -> bool:
        """檢查是否可以使用止損單"""
        features = self.get_supported_features()
        return features.get('supports_stop_orders', False)
    
    def can_use_take_profit(self) -> bool:
        """檢查是否可以使用止盈單"""
        features = self.get_supported_features()
        return features.get('supports_take_profit', False)
    
    def get_supported_order_types(self) -> list:
        """獲取支援的訂單類型"""
        features = self.get_supported_features()
        return features.get('order_types', ['MARKET', 'LIMIT'])
    
    def validate_order_params(self, order_type: str, side: str, quantity: float, 
                            price: Optional[float] = None, stop_price: Optional[float] = None) -> Dict[str, Any]:
        """
        驗證訂單參數，根據測試網限制調整
        
        :return: 調整後的訂單參數
        """
        features = self.get_supported_features()
        supported_types = features.get('order_types', ['MARKET', 'LIMIT'])
        
        # 檢查訂單類型是否支援
        if order_type not in supported_types:
            logger.warning(f"測試網不支援 {order_type} 訂單類型，改用 MARKET")
            order_type = 'MARKET'
        
        # 檢查止損單支援
        if order_type in ['STOP_MARKET', 'STOP_LIMIT'] and not features.get('supports_stop_orders', False):
            logger.warning(f"測試網不支援止損單，改用 MARKET 單")
            order_type = 'MARKET'
            stop_price = None
        
        # 檢查數量精度
        min_size = features.get('min_order_size', 0.001)
        if quantity < min_size:
            logger.warning(f"訂單數量 {quantity} 小於最小數量 {min_size}")
            quantity = min_size
        
        return {
            'order_type': order_type,
            'side': side,
            'quantity': quantity,
            'price': price,
            'stop_price': stop_price
        }
    
    def create_testnet_order_strategy(self, original_strategy: str) -> str:
        """
        根據測試網限制調整訂單策略
        
        :param original_strategy: 原始策略
        :return: 調整後的策略
        """
        if not self.testnet:
            return original_strategy
        
        # 測試網環境下的策略調整
        if original_strategy in ['STOP_MARKET', 'STOP_LIMIT']:
            if not self.can_use_stop_orders():
                logger.info("測試網不支援止損單，改用市價單策略")
                return 'MARKET'
        
        return original_strategy
    
    def get_testnet_warning_message(self) -> str:
        """獲取測試網警告訊息"""
        if not self.testnet:
            return ""
        
        warnings = []
        features = self.get_supported_features()
        
        if not features.get('supports_stop_orders', False):
            warnings.append("止損單功能受限")
        
        if not features.get('supports_take_profit', False):
            warnings.append("止盈單功能受限")
        
        if warnings:
            return f"測試網限制: {', '.join(warnings)}"
        
        return ""
    
    def log_testnet_status(self):
        """記錄測試網狀態"""
        if self.testnet:
            features = self.get_supported_features()
            logger.info(f"測試網模式 - 交易所: {self.exchange_name}")
            logger.info(f"支援的訂單類型: {features.get('order_types', [])}")
            logger.info(f"止損單支援: {features.get('supports_stop_orders', False)}")
            logger.info(f"止盈單支援: {features.get('supports_take_profit', False)}")
            
            warning_msg = self.get_testnet_warning_message()
            if warning_msg:
                logger.warning(warning_msg)
