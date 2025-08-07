# trading/config_manager.py
# 統一的配置管理模組

import os
import logging
from typing import Any, Dict, Optional
from django.conf import settings
from trading_api.models import TraderConfig
from trading.constants import DEFAULT_CONFIG, SUPPORTED_EXCHANGES

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    統一的配置管理類別
    整合 Django 設定、環境變數、資料庫配置
    """
    
    def __init__(self):
        self._cache = {}
        self._load_initial_config()
    
    def _load_initial_config(self):
        """載入初始配置"""
        # 從環境變數載入敏感資訊
        self.api_key = os.getenv('SYRMAX_API_KEY', '')
        self.api_secret = os.getenv('SYRMAX_API_SECRET', '')
        self.exchange = os.getenv('SYRMAX_EXCHANGE', 'BINANCE')
        self.exchange_name = os.getenv('SYRMAX_EXCHANGE_NAME', 'BINANCE')
        
        # 驗證交易所支援
        if self.exchange_name not in SUPPORTED_EXCHANGES:
            logger.warning(f"不支援的交易所: {self.exchange_name}，使用預設: BINANCE")
            self.exchange_name = 'BINANCE'
    
    def get(self, key: str, type=str, default=None) -> Any:
        """
        獲取配置值，優先順序：
        1. 環境變數
        2. 資料庫配置
        3. 預設配置
        4. 傳入的預設值
        """
        # 檢查快取
        if key in self._cache:
            return self._cache[key]
        
        # 1. 檢查環境變數
        env_key = f"SYRMAX_{key}"
        env_value = os.getenv(env_key)
        if env_value is not None:
            try:
                result = self._convert_type(env_value, type)
                self._cache[key] = result
                return result
            except ValueError:
                logger.warning(f"環境變數 {env_key} 格式錯誤: {env_value}")
        
        # 2. 檢查資料庫配置
        try:
            db_config = TraderConfig.objects.filter(key=key).first()
            if db_config:
                result = self._convert_type(db_config.value, type)
                self._cache[key] = result
                return result
        except Exception as e:
            logger.warning(f"讀取資料庫配置失敗 {key}: {e}")
        
        # 3. 檢查預設配置
        if key in DEFAULT_CONFIG:
            result = self._convert_type(DEFAULT_CONFIG[key], type)
            self._cache[key] = result
            return result
        
        # 4. 使用傳入的預設值
        self._cache[key] = default
        return default
    
    def set(self, key: str, value: Any, value_type: str = 'str', description: str = ''):
        """設定配置值到資料庫"""
        try:
            config, created = TraderConfig.objects.get_or_create(
                key=key,
                defaults={
                    'value': str(value),
                    'value_type': value_type,
                    'description': description
                }
            )
            if not created:
                config.value = str(value)
                config.value_type = value_type
                config.description = description
                config.save()
            
            # 更新快取
            self._cache[key] = self._convert_type(str(value), self._get_type_from_string(value_type))
            logger.info(f"配置已更新: {key} = {value}")
            
        except Exception as e:
            logger.error(f"設定配置失敗 {key}: {e}")
            raise
    
    def _convert_type(self, value: str, target_type) -> Any:
        """轉換字串值為指定類型"""
        if target_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif target_type == int:
            return int(float(value))
        elif target_type == float:
            return float(value)
        elif target_type == list:
            import json
            return json.loads(value)
        elif target_type == dict:
            import json
            return json.loads(value)
        else:
            return str(value)
    
    def _get_type_from_string(self, type_str: str):
        """從字串獲取類型"""
        type_map = {
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict
        }
        return type_map.get(type_str, str)
    
    def get_exchange_config(self) -> Dict[str, Any]:
        """獲取交易所配置"""
        return {
            'exchange': self.exchange,
            'exchange_name': self.exchange_name,
            'api_key': self.api_key,
            'api_secret': self.api_secret,
            'use_testnet': self.get('USE_TESTNET', bool, True),
            'test_mode': self.get('TEST_MODE', bool, False)
        }
    
    def get_trading_config(self) -> Dict[str, Any]:
        """獲取交易配置"""
        return {
            'symbols': self.get('SYMBOLS', list, ['BTCUSDT', 'ETHUSDT']),
            'leverage': self.get('LEVERAGE', int, 30),
            'base_position_ratio': self.get('BASE_POSITION_RATIO', float, 0.3),
            'min_position_ratio': self.get('MIN_POSITION_RATIO', float, 0.01),
            'max_position_ratio': self.get('MAX_POSITION_RATIO', float, 0.8),
            'exit_mode': self.get('EXIT_MODE', str, 'AMOUNT'),
            'global_interval_seconds': self.get('GLOBAL_INTERVAL_SECONDS', int, 3),
            'max_trades_per_hour': self.get('MAX_TRADES_PER_HOUR', int, 10),
            'max_trades_per_day': self.get('MAX_TRADES_PER_DAY', int, 50),
            'max_daily_loss_percent': self.get('MAX_DAILY_LOSS_PERCENT', float, 25.0),
        }
    
    def get_risk_config(self) -> Dict[str, Any]:
        """獲取風控配置"""
        return {
            'max_consecutive_stop_loss': self.get('MAX_CONSECUTIVE_STOP_LOSS', int, 3),
            'enable_trade_log': self.get('ENABLE_TRADE_LOG', bool, True),
            'price_take_profit_percent': self.get('PRICE_TAKE_PROFIT_PERCENT', float, 20.0),
            'price_stop_loss_percent': self.get('PRICE_STOP_LOSS_PERCENT', float, 1.0),
            'amount_take_profit_usdt': self.get('AMOUNT_TAKE_PROFIT_USDT', float, 20.0),
            'amount_stop_loss_usdt': self.get('AMOUNT_STOP_LOSS_USDT', float, 10.0),
            'atr_take_profit_multiplier': self.get('ATR_TAKE_PROFIT_MULTIPLIER', float, 2.0),
            'atr_stop_loss_multiplier': self.get('ATR_STOP_LOSS_MULTIPLIER', float, 1.0),
        }
    
    def clear_cache(self):
        """清除配置快取"""
        self._cache.clear()
        logger.info("配置快取已清除")

# 全域配置管理器實例
config_manager = ConfigManager()
