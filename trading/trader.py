# trader.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import logging
import pandas as pd
import talib
import json
import ccxt
from binance.error import ClientError
from datetime import datetime, timedelta
from exchange.load_exchange_client import load_exchange_client
from trading.constants import SIDE_BUY, SIDE_SELL, SYMBOL_PRECISION
from strategy.base import evaluate_bundles, strategy_bundles
from trading.utils import get_precision
from django.utils import timezone
from django.db import transaction
from trading_api.models import (
    TraderConfig, TradingPair, DailyStats, TraderStatus, 
    Position, StrategyCombo, VolatilityPauseStatus
)
from trading_api.admin import CONFIG_FIELD_TYPES

# 導入新開發的功能模組
from trading.trade_logger import TradeLogger
from trading.system_monitor import SystemMonitor
from trading.monitoring_dashboard import MonitoringDashboard
from trading.backtest_engine import BacktestEngine

# 導入可能需要的函數
from trading.system_monitor import start_system_monitoring, stop_system_monitoring, record_system_error
from trading.monitoring_dashboard import start_monitoring_dashboard, stop_monitoring_dashboard, get_dashboard_summary

# 導入所有單一策略函數
from strategy.aggressive import (
    strategy_ema3_ema8_crossover,
    strategy_bollinger_breakout,
    strategy_vwap_deviation,
    strategy_volume_spike,
    strategy_cci_reversal
)
from strategy.balanced import (
    strategy_rsi_mean_reversion,
    strategy_atr_breakout,
    strategy_ma_channel,
    strategy_volume_trend,
    strategy_cci_mid_trend
)
from strategy.conservative import (
    strategy_long_ema_crossover,
    strategy_adx_trend,
    strategy_bollinger_mean_reversion,
    strategy_ichimoku_cloud,
    strategy_atr_mean_reversion
)

# --- 定義所有單一策略的映射 ---
# 這個字典將策略函數名稱（字串）映射到實際的函數物件
ALL_STRATEGIES_MAP = {
    "strategy_ema3_ema8_crossover": strategy_ema3_ema8_crossover,
    "strategy_bollinger_breakout": strategy_bollinger_breakout,
    "strategy_vwap_deviation": strategy_vwap_deviation,
    "strategy_volume_spike": strategy_volume_spike,
    "strategy_cci_reversal": strategy_cci_reversal,
    "strategy_rsi_mean_reversion": strategy_rsi_mean_reversion,
    "strategy_atr_breakout": strategy_atr_breakout,
    "strategy_ma_channel": strategy_ma_channel,
    "strategy_volume_trend": strategy_volume_trend,
    "strategy_cci_mid_trend": strategy_cci_mid_trend,
    "strategy_long_ema_crossover": strategy_long_ema_crossover,
    "strategy_adx_trend": strategy_adx_trend,
    "strategy_bollinger_mean_reversion": strategy_bollinger_mean_reversion,
    "strategy_ichimoku_cloud": strategy_ichimoku_cloud,
    "strategy_atr_mean_reversion": strategy_atr_mean_reversion,
}

# --- 定義預設的策略組合包內容 ---
# 每個組合包包含其預定義的策略函數列表
COMBO_PACKS = {
    "aggressive": [
        strategy_ema3_ema8_crossover,
        strategy_bollinger_breakout,
        strategy_vwap_deviation,
        strategy_volume_spike,
        strategy_cci_reversal
    ],
    "balanced": [
        strategy_rsi_mean_reversion,
        strategy_atr_breakout,
        strategy_ma_channel,
        strategy_volume_trend,
        strategy_cci_mid_trend
    ],
    "conservative": [
        strategy_long_ema_crossover,
        strategy_adx_trend,
        strategy_bollinger_mean_reversion,
        strategy_ichimoku_cloud,
        strategy_atr_mean_reversion
    ]
}

# --- 自動判斷 K 線型態的邏輯 ---
def auto_detect_combo(df: pd.DataFrame, auto_conditions=None) -> str:
    """
    根據 combos.generated.json 的 auto 組合條件，自動判斷要用哪一個策略組合。
    支援 ATR 閾值與 mapping，若無條件則回退原本K線型態判斷。
    """
    if auto_conditions and len(auto_conditions) > 0:
        cond = auto_conditions[0]  # 只取第一個條件
        indicator = cond.get("indicator")
        period = cond.get("period", 14)
        thresholds = cond.get("thresholds", {})
        mapping = cond.get("mapping", {})

        if indicator == "ATR":
            if "atr" not in df.columns:
                import talib
                df["atr"] = talib.ATR(df["high"], df["low"], df["close"], timeperiod=period)
            atr_value = df["atr"].iloc[-1]
            if atr_value > thresholds.get("high", 100):
                return mapping.get("high", "aggressive")
            elif atr_value > thresholds.get("medium", 50):
                return mapping.get("medium", "balanced")
            else:
                return mapping.get("low", "conservative")
    # 若無條件，回退原本K線型態判斷
    if df.empty or len(df) < 20: # 至少需要20根K線來判斷
        logging.warning("K線數據不足或為空，無法進行K線型態自動判斷，預設為『平衡』策略組合。")
        return "balanced" 

    avg_candle_range = (df['high'].iloc[-20:] - df['low'].iloc[-20:]).mean()
    if avg_candle_range == 0: 
        logging.info("近20根K線平均K棒長度為零，判斷為極端平靜，預設為『平衡』策略組合。")
        return "balanced"

    high_20_period = df['high'].iloc[-20:].max()
    low_20_period = df['low'].iloc[-20:].min()
    price_range_20_period = high_20_period - low_20_period

    if price_range_20_period / avg_candle_range > 3.0:
        logging.info("市場處於強趨勢（高波動），自動選擇『激進』策略組合。")
        return "aggressive"
    elif price_range_20_period / avg_candle_range < 1.5:
        logging.info("市場處於盤整（低波動），自動選擇『保守』策略組合。")
        return "conservative"
    else:
        logging.info("市場處於中等波動狀態，自動選擇『平衡』策略組合。")
        return "balanced"

class MultiSymbolTrader:
    """
    支援多幣種的自動交易機器人類別
    """
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        初始化多幣種交易機器人
        """
        # 初始化配置緩存
        self.configs = {}
        
        # 初始化基本屬性
        self.enable_trade_limits = True
        self.max_positions = 5
        self.min_balance = 100
        self.max_daily_loss = 500
        self.max_daily_trades = 50
        self.test_mode = testnet  # 根據傳入的testnet參數設置測試模式
        self.simulation_mode = False  # 模擬交易模式，將從配置中讀取
        
        # 載入配置
        self._load_all_configs()
        
        # 從配置讀取模擬交易模式
        logging.info("正在讀取 TEST_MODE 配置...")
        self.simulation_mode = self.get_config('TEST_MODE', type=bool, default=False)
        logging.info(f"模擬交易模式: {'開啟' if self.simulation_mode else '關閉'}")
        logging.info(f"simulation_mode 變數值: {self.simulation_mode} (類型: {type(self.simulation_mode)})")
        
        # 從配置讀取交易所名稱
        exchange_name = self.get_config('EXCHANGE_NAME', default='BINANCE')
        
        # 初始化交易所客戶端
        self.client = load_exchange_client(exchange_name, api_key, api_secret, testnet)
        
        # 初始化各個模組
        self.trade_logger = TradeLogger()
        self.backtest_engine = BacktestEngine()
        self.system_monitor = SystemMonitor()
        self.monitoring_dashboard = MonitoringDashboard()
        
        # 初始化稽核層
        try:
            from core.audit_integration import AuditIntegration
            self.audit_integration = AuditIntegration(self)
            if self.audit_integration.is_enabled():
                logging.info("稽核層已啟用")
            else:
                logging.info("稽核層已禁用")
        except Exception as e:
            logging.error(f"稽核層初始化失敗: {e}")
            self.audit_integration = None
        
        # 從數據庫讀取交易對和槓桿
        self.symbols = self.get_config('SYMBOLS', type=list, default=[])
        self.leverage = self.get_config('LEVERAGE', type=int, default=10)
        
        # 添加幣種配置檢查日誌
        logging.info(f"=== 幣種配置檢查 ===")
        logging.info(f"從數據庫讀取的SYMBOLS配置: {self.symbols}")
        logging.info(f"配置類型: {type(self.symbols)}")
        logging.info(f"幣種數量: {len(self.symbols) if isinstance(self.symbols, list) else 'N/A'}")
        
        if not self.symbols:
            logging.warning("SYMBOLS配置為空或無效，使用默認幣種")
            self.symbols = ["BTCUSDT", "ETHUSDT"]
            logging.info(f"已設置默認幣種: {self.symbols}")
        elif not isinstance(self.symbols, list):
            logging.error(f"SYMBOLS配置類型錯誤: {type(self.symbols)}，使用默認幣種")
            self.symbols = ["BTCUSDT", "ETHUSDT"]
            logging.info(f"已設置默認幣種: {self.symbols}")
        
        logging.info(f"最終使用的幣種列表: {self.symbols}")
        logging.info(f"=== 幣種配置檢查完成 ===")
        
        # 配置自動同步相關變量
        self.last_config_check = timezone.now()
        self.config_sync_interval = 300  # 5分鐘檢查一次配置變化
        self.auto_sync_symbols = self.get_config('AUTO_SYNC_SYMBOLS', type=bool, default=True)
        
        if self.auto_sync_symbols:
            logging.info("✅ 已啟用幣種配置自動同步，每5分鐘檢查一次配置變化")
        else:
            logging.info("⚠️ 已關閉幣種配置自動同步，需要手動重啟機器人來應用配置變化")
        
        # 從配置讀取是否自動設置槓桿
        auto_set_leverage = self.get_config('AUTO_SET_LEVERAGE', type=bool, default=True)
        logging.info(f"[DEBUG] AUTO_SET_LEVERAGE 配置值為: {auto_set_leverage} (型別: {type(auto_set_leverage)})")
        
        if auto_set_leverage is True:
            logging.info("自動設置槓桿已啟用，將在初始化時設置槓桿")
            # 注意：這裡不直接調用set_leverage()，而是在初始化完成後調用
        else:
            logging.info("已關閉自動設置槓桿，啟動時將跳過自動設置槓桿步驟。")
            logging.info(f"當前配置的槓桿倍數: {self.leverage}x")
            logging.info("如需手動設置槓桿，請使用 set_leverage() 方法")

        # 與交易所校時
        try:
            if hasattr(self.client, '_sync_time'):
                self.client._sync_time()
                logging.info("已與交易所進行時間同步")
            else:
                logging.warning("交易所客戶端不支持時間同步，將使用本地時間。")
        except Exception as e:
            logging.warning(f"與交易所校時失敗: {e}，將使用本地時間。")
       
        # 全局交易判斷頻率
        self.global_interval_seconds = self.get_config('GLOBAL_INTERVAL_SECONDS', type=int, default=3)

        # 每小時與每日允許的最大開倉次數
        self.max_trades_per_hour = self.get_config('MAX_TRADES_PER_HOUR', type=int, default=5)
        self.max_trades_per_day = self.get_config('MAX_TRADES_PER_DAY', type=int, default=100)

        # 波動率風險調整配置
        self.enable_volatility_risk_adjustment = self.get_config('ENABLE_VOLATILITY_RISK_ADJUSTMENT', type=bool, default=True)
        self.volatility_threshold_multiplier = self.get_config('VOLATILITY_THRESHOLD_MULTIPLIER', type=float, default=2.0)
        self.volatility_pause_threshold = self.get_config('VOLATILITY_PAUSE_THRESHOLD', type=float, default=3.0)
        self.volatility_recovery_threshold = self.get_config('VOLATILITY_RECOVERY_THRESHOLD', type=float, default=1.5)
        self.volatility_pause_duration_minutes = self.get_config('VOLATILITY_PAUSE_DURATION_MINUTES', type=int, default=30)
        
        # 波動率暫停狀態
        self.volatility_pause_status = {}
        for symbol in self.symbols:
            self.volatility_pause_status[symbol] = {
                'is_paused': False,
                'pause_start_time': None,
                'pause_reason': None,
                'current_atr_ratio': 1.0
            }
        
        # 最大同時持倉數量限制配置
        self.enable_max_position_limit = self.get_config('ENABLE_MAX_POSITION_LIMIT', type=bool, default=True)
        self.max_simultaneous_positions = self.get_config('MAX_SIMULTANEOUS_POSITIONS', type=int, default=3)

        # 初始化每日風控統計
        self.daily_stats = {
            symbol: {
                'pnl': 0.0,
                'start_balance': 0.0,
                'max_daily_loss_pct': self.get_config('MAX_DAILY_LOSS_PCT', type=float, default=0.25),
                'risk_reward_ratio': 0.4 # 這裡可以根據需要從數據庫獲取
            } for symbol in self.symbols
        }

        # 初始化持倉狀態
        self.positions = {
            symbol: {
                'active': False,
                'side': None,
                'entry_price': None,
                'quantity': 0.0,
            } for symbol in self.symbols
        }

        self.stop_signal = False
        self.trading_enabled = True
        self.cooldown_flags = {symbol: False for symbol in self.symbols}
        self.last_trade_time = {symbol: None for symbol in self.symbols}
        
        # --- 從 StrategyCombo 載入啟用的組合包模式和自定義策略 ---
        self.active_combo_mode = 'balanced' # 預設為平衡
        self.custom_strategies_list = [] # 預設為空列表

        try:
            # 嘗試獲取啟用的 StrategyCombo 實例
            active_combo = StrategyCombo.objects.filter(is_active=True).first()

            if active_combo:
                self.active_combo_mode = active_combo.combo_mode
                self.custom_strategies_list = active_combo.conditions # conditions 字段在自定義模式下包含策略列表
                logging.info(f"從 StrategyCombo 載入啟用組合包模式: {self.active_combo_mode}")
                if self.active_combo_mode == 'custom':
                    logging.info(f"自定義策略清單: {self.custom_strategies_list}")
            else:
                logging.warning("未找到啟用的 StrategyCombo 實例，將使用預設的『平衡』模式。")
                # 如果沒有啟用的 StrategyCombo，也可以在這裡創建一個預設的，或者讓使用者在 Admin 介面創建。
                # 為了避免在啟動時自動創建導致的混亂，這裡只使用預設值並發出警告。

        except Exception as e:
            logging.error(f"從數據庫載入 StrategyCombo 失敗: {e}，將使用預設的『平衡』模式。")
        
        # 初始化當日起始資金
        self.initialize_start_balance()

        # 初始化用於儲存每個幣種歷史平均 ATR 的字典
        self.average_atrs = {}
        # 為每個交易幣種計算歷史平均 ATR 作為波動性參考值
        # 從數據庫獲取 SYMBOL_INTERVALS
        symbol_intervals_config = self.get_config('SYMBOL_INTERVALS', type=dict, default={})

        for symbol in self.symbols:
            # 獲取幣種對應的交易間隔
            interval = symbol_intervals_config.get(symbol, "1m") # 使用從數據庫讀取的配置
            # 呼叫內部方法計算平均 ATR
            avg_atr = self._calculate_average_historical_atr(symbol, interval)
            if avg_atr is not None:
                self.average_atrs[symbol] = avg_atr
                TradingPair.objects.update_or_create(
                    symbol=symbol,
                    defaults={'average_atr': avg_atr}
                )
            else:
                logging.warning(f"無法計算 {symbol} 的歷史平均 ATR。")

        # 從數據庫載入 TradingPair 的配置，包括上次交易時間和連續止損次數
        for symbol in self.symbols:
            trading_pair_instance, created = TradingPair.objects.get_or_create(symbol=symbol)
            if not created: # 如果是已存在的 TradingPair
                self.last_trade_time[symbol] = trading_pair_instance.last_trade_time

        # 初始化新開發的功能模組
        self.trade_logger = TradeLogger()
        self.backtest_engine = BacktestEngine()
        
        # 啟動系統監控和監控告警
        try:
            start_system_monitoring()
            start_monitoring_dashboard()
            logging.info("系統監控和監控告警已啟動")
        except Exception as e:
            logging.error(f"啟動系統監控失敗: {e}")
            from trading.system_monitor import ErrorSeverity
            record_system_error("SYSTEM_STARTUP", str(e), ErrorSeverity.HIGH, "MultiSymbolTrader")
        
        logging.info("MultiSymbolTrader 初始化完成")

        # 根據配置決定是否設置槓桿
        auto_set_leverage = self.get_config('AUTO_SET_LEVERAGE', type=bool, default=True)
        if auto_set_leverage:
            logging.info("開始自動設置槓桿...")
            try:
                # 在測試網環境下，跳過槓桿設置以避免錯誤
                if self.test_mode:
                    logging.info("⚠️ 測試網環境檢測到，跳過槓桿設置以避免權限錯誤")
                    logging.info(f"當前配置槓桿: {self.leverage}x，將在實際交易時使用")
                else:
                    self.set_leverage()
                    logging.info("槓桿設置完成")
            except Exception as e:
                logging.error(f"自動設置槓桿失敗: {e}")
                logging.info("槓桿設置失敗不會影響機器人運行，將在實際交易時使用默認槓桿")
        else:
            logging.info(f"跳過自動設置槓桿，當前配置槓桿: {self.leverage}x")
            logging.info("如需手動設置槓桿，請調用 set_leverage() 方法")

        # 載入 TraderStatus
        try:
            trader_status, created = TraderStatus.objects.get_or_create(pk=1) # 假設只有一個 TraderStatus 實例
            self.trading_enabled = trader_status.is_trading_enabled
            self.stop_signal = trader_status.stop_signal_received
            self.last_daily_reset_date = trader_status.last_daily_reset_date
            self.hourly_trade_count = trader_status.hourly_trade_count
            self.daily_trade_count = trader_status.daily_trade_count
            self.last_hourly_reset = trader_status.last_hourly_reset
        except Exception as e:
            logging.error(f"從數據庫載入 TraderStatus 失敗: {e}，將使用預設狀態。")

    def _load_all_configs(self):
        """
        從 TraderConfig 模型載入所有配置到內存緩存。
        """
        try:
            configs = TraderConfig.objects.all()
            for config_item in configs:
                key = config_item.key
                value_str = config_item.value
                
                # 根據 CONFIG_FIELD_TYPES 進行類型轉換
                field_type = CONFIG_FIELD_TYPES.get(key, str)
                if field_type == bool:
                    self.configs[key] = (value_str == 'True')
                elif field_type == int:
                    try:
                        self.configs[key] = int(value_str) if value_str else None
                    except ValueError:
                        self.configs[key] = None
                elif field_type == float:
                    try:
                        self.configs[key] = float(value_str) if value_str else None
                    except ValueError:
                        self.configs[key] = None
                elif field_type == list:
                    try:
                        self.configs[key] = json.loads(value_str) if value_str else []
                    except json.JSONDecodeError:
                        self.configs[key] = []
                elif field_type == dict:
                    try:
                        self.configs[key] = json.loads(value_str) if value_str else {}
                    except json.JSONDecodeError:
                        self.configs[key] = {}
                else:
                    self.configs[key] = value_str
            logging.info("所有 TraderConfig 配置已從數據庫載入到內存緩存。")
        except Exception as e:
            logging.error(f"載入 TraderConfig 配置失敗: {e}")

    def get_config(self, key: str, type=str, default=None):
        """
        從緩存或數據庫中獲取交易配置。
        支持類型轉換和預設值。
        """
        if key in self.configs:
            return self.configs[key]

        try:
            config_entry = TraderConfig.objects.get(key=key)
            value_str = config_entry.value
            expected_type_str = config_entry.value_type
            
            # 添加調試日誌
            logging.debug(f"獲取配置 '{key}': 值='{value_str}', 類型='{expected_type_str}', 期望類型={type}")

            # --- 類型轉換 ---
            value = None
            if expected_type_str == 'int':
                value = int(value_str)
            elif expected_type_str == 'float':
                value = float(value_str)
            elif expected_type_str == 'bool':
                # 強化布林判斷，無論資料庫存什麼都能正確轉換
                if isinstance(value_str, bool):
                    value = value_str
                elif isinstance(value_str, str):
                    # 修正：只有明確的 true 值才返回 True
                    value = value_str.strip().lower() in ['true', '1', 't', 'y', 'yes']
                    logging.debug(f"布林值轉換: '{value_str}' -> {value}")
                else:
                    value = bool(value_str)
            elif expected_type_str == 'list':
                # 解析 JSON 格式的列表
                try:
                    value = json.loads(value_str)
                    if not isinstance(value, list):
                        raise ValueError("JSON 解析結果不是一個列表")
                    logging.debug(f"成功解析列表配置 '{key}': {value}")
                except (json.JSONDecodeError, ValueError) as e:
                    logging.error(f"配置鍵 '{key}' 的值 '{value_str}' 無法解析為列表: {e}")
                    # 嘗試解析為逗號分隔的字符串
                    if ',' in value_str:
                        value = [s.strip() for s in value_str.split(',') if s.strip()]
                        logging.info(f"將逗號分隔字符串解析為列表: {value}")
                    else:
                        value = default
            elif expected_type_str == 'dict':
                 # 解析 JSON 格式的字典
                try:
                    value = json.loads(value_str)
                    if not isinstance(value, dict):
                        raise ValueError("JSON 解析結果不是一個字典")
                except (json.JSONDecodeError, ValueError) as e:
                    logging.error(f"配置鍵 '{key}' 的值 '{value_str}' 無法解析為字典: {e}")
                    value = default
            else: # 默認為 str
                value = value_str
            
            # 特殊處理SYMBOLS配置
            if key == 'SYMBOLS':
                logging.info(f"SYMBOLS配置解析結果: {value} (類型: {type(value)})")
                if not value or not isinstance(value, list):
                    logging.warning(f"SYMBOLS配置無效，使用默認值: {default}")
                    value = default
            
            self.configs[key] = value
            return value

        except TraderConfig.DoesNotExist:
            logging.warning(f"配置鍵 '{key}' 不存在於數據庫中，使用預設值: {default}")
            self.configs[key] = default
            return default
        except Exception as e:
            logging.error(f"獲取配置 '{key}' 時發生錯誤: {e}")
            self.configs[key] = default
            return default

    def set_leverage(self):
        """為所有在 self.symbols 中的交易對設置目標槓桿為 self.leveragex"""
        logging.info(f"準備為交易對 {self.symbols} 設置目標槓桿為 {self.leverage}x")
        for symbol in self.symbols:
            self._set_leverage_for_symbol(symbol)

    def _set_leverage_for_symbol(self, symbol: str, retries: int = 3, delay: int = 5):
        """為單個交易對設置並驗證槓桿，帶有重試機制。"""
        for attempt in range(retries):
            try:
                # 1. 查詢當前槓桿
                current_leverage = self.client.get_leverage(symbol)
                logging.info(f"({symbol}) 當前槓桿為 {current_leverage}x，目標槓桿為 {self.leverage}x")

                # 2. 如果當前槓桿與目標不符，則設置槓桿
                if current_leverage != self.leverage:
                    logging.info(f"({symbol}) 槓桿不匹配，嘗試設定為 {self.leverage}x")
                    set_success = self.client.set_leverage(symbol, self.leverage)
                    if not set_success:
                        logging.error(f"({symbol}) 第一次設定槓桿失敗。")
                        # 如果設定失敗，短暫等待後進入下一次重試
                        time.sleep(delay)
                        continue
                    
                    # 短暫等待，讓交易所後端更新狀態
                    time.sleep(1)

                    # 3. 再次驗證
                    final_leverage = self.client.get_leverage(symbol)
                    if final_leverage == self.leverage:
                        logging.info(f"✅ ({symbol}) 槓桿已成功驗證為 {final_leverage}x")
                        return  # 成功，退出函數
                    else:
                        logging.error(f"({symbol}) 槓桿驗證失敗！設定後回報的槓桿為 {final_leverage}x")
                else:
                    logging.info(f"✅ ({symbol}) 槓桿已是目標值 {self.leverage}x，無需設定。")
                    return # 成功，退出函數

            except Exception as e:
                logging.error(f"({symbol}) 設定槓桿時發生異常 (嘗試 {attempt + 1}/{retries}): {e}")
            
            logging.warning(f"({symbol}) 第 {attempt + 1} 次設定槓桿失敗，將在 {delay} 秒後重試...")
            time.sleep(delay)
        
        logging.critical(f"❌ ({symbol}) 在 {retries} 次嘗試後，依然無法將槓桿設定為 {self.leverage}x。請檢查 API 權限或交易所狀態。")
        # 在多次失敗後，可以選擇拋出異常或停止機器人
        # raise Exception(f"{symbol} 槓桿設定失敗")

    def manual_set_leverage(self, leverage: int = None):
        """
        手動設置槓桿倍數
        
        參數:
            leverage (int): 要設置的槓桿倍數，如果不提供則使用配置中的值
        """
        if leverage is not None:
            self.leverage = leverage
            logging.info(f"手動設置槓桿為: {leverage}x")
        
        logging.info(f"開始手動設置槓桿為 {self.leverage}x...")
        try:
            self.set_leverage()
            logging.info("✅ 手動設置槓桿完成")
            return True
        except Exception as e:
            logging.error(f"手動設置槓桿失敗: {e}")
            return False

    def _get_timestamp(self) -> int:
        """
        回傳與伺服器時間同步後的當前時間（毫秒）
        """
        return int(time.time() * 1000) + self.time_offset

    def get_available_usdt_balance(self) -> float:
        """安全地獲取可用的 USDT 餘額"""
        try:
            # 假設 get_balance('USDT') 返回的是可用的U本位合約錢包餘額
            balance = self.client.get_balance('USDT')
            if balance is None:
                return 0.0
            return float(balance)
        except Exception as e:
            logging.error(f"擷取 USDT 餘額失敗: {e}")
            return 0.0

    def get_current_price(self, symbol: str) -> float | None:
        """安全地獲取交易對的當前價格"""
        try:
            price = self.client.get_price(symbol)
            return price
        except Exception as e:
            logging.error(f"獲取 {symbol} 當前價格失敗: {e}")
            return None

    def fetch_historical_klines(self, symbol: str, interval: str = '1m', limit: int = 500) -> pd.DataFrame:
        """
        獲取歷史 K 線數據並轉換為 DataFrame
        Binance K線數據格式: [timestamp, open, high, low, close, volume, close_time, quote_asset_volume, number_of_trades, taker_buy_base_asset_volume, taker_buy_quote_asset_volume, ignore]
        """
        try:
            # client.fetch_klines 已經有了基本的錯誤處理
            klines = self.client.fetch_klines(symbol, interval, limit)
            
            if not klines: # 如果返回空列表
                logging.warning(f"{symbol}: 從交易所未獲取到 K 線數據。")
                return pd.DataFrame()

            # Binance K線數據有12列，我們只需要前6列
            # 列定義: [timestamp, open, high, low, close, volume, close_time, quote_asset_volume, number_of_trades, taker_buy_base_asset_volume, taker_buy_quote_asset_volume, ignore]
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades', 
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # 只保留我們需要的列
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # 轉換數據類型
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            # 將 timestamp 轉為 datetime 物件，並設為 index
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
        
        except Exception as e:
            logging.error(f"{symbol} 擷取 K 線失敗: {e}")
            return pd.DataFrame()

    def precompute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        在 DataFrame 上計算常用技術指標
        包含：EMA5、EMA20、RSI、MACD、ATR
        """
        if len(df) < 50:
            return df

        df['ema_5'] = df['close'].ewm(span=5).mean()
        df['ema_20'] = df['close'].ewm(span=20).mean()

        df['rsi'] = talib.RSI(df['close'], timeperiod=14)

        macd, macd_signal, _ = talib.MACD(
            df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
        df['macd'] = macd
        df['macd_signal'] = macd_signal

        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)

        return df

    def calculate_position_size(self, symbol: str, price: float, df: pd.DataFrame) -> float:
        """
        根據帳戶資金、幣種價格、波動性 (ATR) 動態計算下單數量
        並考慮交易所的風險限額 (階梯式槓桿)，確保開倉名義價值不超過設定槓桿允許的上限。
        """
        available_balance = self.get_available_usdt_balance()

        if available_balance <= 0:
            return 0.0

        # 從預先計算好的平均 ATR 中獲取參考值
        atr_reference_value = self.average_atrs.get(symbol)

        # 獲取最新的 ATR 值
        if 'atr' not in df.columns or df['atr'].empty:
             logging.warning(f"{symbol}: 無法取得當前 ATR 數據，使用基礎資金比例。")
             dynamic_ratio = self.get_config('BASE_POSITION_RATIO', type=float, default=0.01)
        elif atr_reference_value is None or atr_reference_value < 1e-9:
             logging.warning(f"{symbol}: 無效的 ATR 參考值，使用基礎資金比例。")
             dynamic_ratio = self.get_config('BASE_POSITION_RATIO', type=float, default=0.01)
        else:
            # 獲取當前最新的 ATR 值
            current_ATR = df['atr'].iloc[-1]

            # 避免除以零或非常小的數
            if current_ATR < 1e-9:
                 # ATR 接近零，波動性極低，使用最大比例 (或者可以設定一個固定較高的比例)
                 dynamic_ratio = self.get_config('MAX_POSITION_RATIO', type=float, default=0.05)
            else:
                 # 根據當前 ATR 相對於平均 ATR 參考值的比例計算動態比例
                 # 比例計算邏輯：ATR 越大，計算出的 dynamic_ratio 越小；ATR 越小，dynamic_ratio 越大
                 base_ratio = self.get_config('BASE_POSITION_RATIO', type=float, default=0.01)
                 min_ratio = self.get_config('MIN_POSITION_RATIO', type=float, default=0.005)
                 max_ratio = self.get_config('MAX_POSITION_RATIO', type=float, default=0.05)

                 scale = atr_reference_value / current_ATR
                 dynamic_ratio = base_ratio * scale

                 # 確保動態比例在合理範圍內
                 dynamic_ratio = max(min_ratio, min(max_ratio, dynamic_ratio))

        logging.info(f"{symbol} 使用動態資金比例: {dynamic_ratio:.4f}")

        # 根據資金比例計算出原始資金量，再計算原始下單數量
        capital = available_balance * dynamic_ratio
        raw_quantity = capital / price

        # === 考慮交易所風險限額 (階梯式槓桿) ===
        # 獲取當前設定的槓桿倍數
        target_leverage = self.leverage # 這裡使用已從數據庫載入的 self.leverage

        # 從數據庫獲取風險限額 tiers
        risk_limit_tiers = self.get_config('RISK_LIMIT_TIERS', type=list, default=[[100000, 20], [200000, 10]])

        # 根據目標槓桿，從風險限額 tiers 中查找對應的最大允許名義價值
        max_notional_value_for_leverage = float('inf') # 初始化為無限大
        # 注意：RISK_LIMIT_TIERS 應該是從低到高排序的
        for max_notional, max_leverage in sorted(risk_limit_tiers):
             if target_leverage <= max_leverage:
                 max_notional_value_for_leverage = max_notional
                 break # 找到匹配的層級，跳出迴圈

        # 計算原始下單數量的名義價值 (數量 * 價格)
        raw_notional_value = raw_quantity * price

        # 比較原始名義價值與設定槓桿允許的最大名義價值
        final_quantity = raw_quantity
        if raw_notional_value > max_notional_value_for_leverage:
             # 如果超出限制，按比例縮減下單數量
             # 縮減後的數量 = (允許的最大名義價值 / 當前價格)
             final_quantity = max_notional_value_for_leverage / price
             logging.warning(f"{symbol}: 計算出的名義價值 ({raw_notional_value:.2f}) 超出 {target_leverage}x 槓桿允許的上限 ({max_notional_value_for_leverage:.2f})，下單數量將縮減。")

        # 確保最終下單數量符合最小交易量要求（這裡簡化處理，實際應查詢交易所的最小交易量）
        # 可以根據需要添加更精確的最小交易量檢查
        min_quantity = 0.001 # 假設一個非常小的最小交易量，實際應從數據庫獲取或交易所信息
        if final_quantity < min_quantity:
            final_quantity = 0.0
            logging.warning(f"{symbol}: 最終計算出的下單數量 ({final_quantity}) 小於最小交易量 ({min_quantity})，將不下單。")

        # 根據幣種精度進行四捨五入
        precision = get_precision(symbol)
        return round(final_quantity, precision)

    def generate_combo_signal(self, df: pd.DataFrame, strategies: list) -> int:
        """
        根據傳入的策略清單生成交易訊號。
        只要策略清單中任何一個策略給出明確信號，就回傳該信號。
        """
        if df.empty:
            logging.info("K線數據為空，無法生成組合信號。")
            return 0

        if not strategies:
            logging.warning("沒有可執行的策略清單，無法生成組合信號。")
            return 0

        for strategy_func in strategies:
            try:
                signal = strategy_func(df)
                if signal != 0:
                    logging.info(f"符合策略：{strategy_func.__name__}，信號: {signal}")
                    return signal
            except Exception as e:
                logging.error(f"執行策略 {strategy_func.__name__} 失敗: {e}")
        
        logging.info("所有策略未達共識，維持觀望 HOLD")
        return 0

    def generate_signal(self, df: pd.DataFrame) -> int:
        """
        根據 StrategyCombo 中設定的組合包模式，獲取並執行對應的策略組合。
        """
        if df.empty:
            logging.info("K線數據為空，無法生成交易信號。")
            return 0

        # 從實例變數獲取當前啟用的策略模式和自定義策略清單
        current_combo_mode = self.active_combo_mode
        current_custom_strategies = self.custom_strategies_list
        
        signal = 0
        selected_mode_log = ""

        if current_combo_mode == 'auto':
            # 自動判斷模式
            determined_style = auto_detect_combo(df)
            selected_mode_log = f"『自動判斷模式』選擇了：【{determined_style.upper()}】組合包。"
            signal = evaluate_bundles(df, determined_style) # 使用 evaluate_bundles 執行自動判斷出的風格
        elif current_combo_mode == 'custom':
            # 自定義模式
            strategies_to_execute = []
            for strategy_item in current_custom_strategies: # custom_strategies_list 包含 {'type': 'strategy_name'} 字典
                strategy_name = strategy_item.get('type')
                if strategy_name:
                    strategy_func = ALL_STRATEGIES_MAP.get(strategy_name)
                    if strategy_func:
                        strategies_to_execute.append(strategy_func)
                    else:
                        logging.warning(f"自定義策略清單中包含未知的策略: {strategy_name}，已跳過。")
                else:
                    logging.warning(f"自定義策略清單中包含格式錯誤的項目: {strategy_item}，已跳過。")

            selected_mode_log = f"『自定義模式』將執行：{[func.__name__ for func in strategies_to_execute]}。"
            if strategies_to_execute:
                signal = self.generate_combo_signal(df, strategies_to_execute) # 使用 generate_combo_signal 執行自定義策略列表
            else:
                logging.warning("自定義模式下沒有可執行的策略，維持觀望 HOLD。")
        elif current_combo_mode in strategy_bundles: # aggressive, balanced, conservative
            # 預定義組合包模式 (aggressive, balanced, conservative)
            # evaluate_bundles 已經處理了這些預設模式的邏輯
            selected_mode_log = f"使用『{current_combo_mode.upper()}模式』策略組合。"
            signal = evaluate_bundles(df, current_combo_mode)
        else:
            logging.warning(f"未定義的組合包模式: {current_combo_mode}，將使用預設的『平衡』策略組合。")
            selected_mode_log = "使用預設『平衡』策略組合。"
            signal = evaluate_bundles(df, 'balanced') # 預設為平衡

        logging.info(selected_mode_log + f" 最終信號: {signal}")

        return signal

    def place_order(self, symbol: str, side: str, quantity: float):
        """下單並更新倉位狀態"""
        if self.simulation_mode:
            logging.info(f"[模擬] 下單: {side} {quantity} {symbol}")
            # 模擬訂單回傳
            mock_order = {
                'symbol': symbol, 'side': side, 'amount': quantity,
                'price': self.get_current_price(symbol), 'id': 'mock_' + str(int(time.time()*1000))
            }
            # 更新模擬倉位
            self.positions[symbol]['active'] = True
            self.positions[symbol]['side'] = side
            self.positions[symbol]['entry_price'] = mock_order['price']
            self.positions[symbol]['quantity'] = quantity
            return mock_order

        try:
            order = self.client.place_order(symbol, side, quantity)
            logging.info(f"下單成功: {order}")
            
            # 獲取準確的進場價和數量
            entry_price = float(order.get('price') or self.get_current_price(symbol))
            filled_quantity = float(order.get('filled') or order.get('amount') or quantity)

            # 立即更新倉位狀態
            self.positions[symbol]['active'] = True
            self.positions[symbol]['side'] = side
            self.positions[symbol]['entry_price'] = entry_price
            self.positions[symbol]['quantity'] = filled_quantity
            
            return order
        except ccxt.InsufficientFunds as e:
            logging.error(f"❌ 資金不足，無法下單 (symbol={symbol}, side={side}, qty={quantity}): {e}")
            # 可以在這裡觸發一個冷卻機制，暫停該幣種的交易
            self.cooldown_flags[symbol] = True
            return None
        except ccxt.ExchangeError as e:
            logging.error(f"下單時交易所返回錯誤 (symbol={symbol}, side={side}, qty={quantity}): {e}")
            return None
        except Exception as e:
            logging.error(f"下單時發生未知錯誤 (symbol={symbol}, side={side}, qty={quantity}): {e}")
            return None

    def close_position(self, symbol: str, quantity: float):
        """平倉"""
        current = self.positions[symbol]
        if not current['active']:
            return

        reverse_side = SIDE_SELL if current['side'] == SIDE_BUY else SIDE_BUY
        self.place_order(symbol, reverse_side, quantity)

    def run_trading_cycle(self):
        """
        主策略運行邏輯：每個幣種檢查 → 產生信號 → 下單或平倉
        """
        # 🔍 檢查並同步配置變化
        if self.auto_sync_symbols:
            self.check_and_sync_configs()
        
        trader_status = TraderStatus.objects.get(pk=1) # 獲取交易器狀態

        # 每小時重置交易計數
        now_dt = timezone.now()
        if now_dt - trader_status.last_hourly_reset >= timedelta(hours=1):
            trader_status.hourly_trade_count = 0
            trader_status.last_hourly_reset = now_dt
            trader_status.save()
            self.hourly_trade_count = 0
            self.last_hourly_reset = now_dt
            logging.info("每小時交易計數已重置")

        # 每日 0 點重新初始化資金與統計
        now = timezone.localdate()
        if trader_status.last_daily_reset_date != now:
            self.reset_daily_state() # 重置每日狀態

        if not trader_status.is_trading_enabled:
            logging.info("交易已暫停，只檢查平倉條件。")
            for trading_pair_obj in TradingPair.objects.all():
                # 僅檢查持倉的平倉條件
                if Position.objects.filter(trading_pair=trading_pair_obj, active=True).exists():
                    self.check_exit_conditions(trading_pair_obj.symbol)
            # 從數據庫獲取全局的 interval_seconds
            global_interval_seconds = self.get_config('GLOBAL_INTERVAL_SECONDS', type=int, default=3)
            time.sleep(global_interval_seconds)
            return

        for trading_pair_obj in TradingPair.objects.all():
            symbol = trading_pair_obj.symbol
            interval = trading_pair_obj.interval # K線週期

            # 若啟用交易次數限制，檢查是否達到每小時或每日開倉上限
            if self.enable_trade_limits:
                if (trader_status.hourly_trade_count >= self.max_trades_per_hour or
                    trader_status.daily_trade_count >= self.max_trades_per_day):
                    logging.info(f"已達全局開倉次數上限 (每小時: {trader_status.hourly_trade_count}/{self.max_trades_per_hour}, 每日: {trader_status.daily_trade_count}/{self.max_trades_per_day})，跳過開倉。")
                    continue
            
            try:
                # ⏱️ 根據設定跳過過快頻率
                now_dt = timezone.now()
                last_trade_time = trading_pair_obj.last_trade_time
                # 從數據庫獲取 SYMBOL_INTERVAL_SECONDS
                symbol_interval_seconds_config = self.get_config('SYMBOL_INTERVAL_SECONDS', type=dict, default={})
                interval_sec = symbol_interval_seconds_config.get(symbol, self.global_interval_seconds) # 使用幣種特定的或全局的

                if last_trade_time and (now_dt - last_trade_time) < timedelta(seconds=interval_sec):
                    continue # 未達間隔秒數 → 跳過

                # 更新最後交易時間
                trading_pair_obj.last_trade_time = now_dt
                trading_pair_obj.save() 

                # cooldown: 若上輪剛止損達上限，跳過一次
                max_consecutive_stop_loss = self.get_config('MAX_CONSECUTIVE_STOP_LOSS', type=int, default=3)
                if trading_pair_obj.consecutive_stop_loss >= max_consecutive_stop_loss:
                    logging.info(f"{symbol} 已達到連續止損上限 ({max_consecutive_stop_loss})，將 cooldown 並重置連續止損次數。")
                    # 重置連續止損次數，但繼續 cooldown
                    trading_pair_obj.consecutive_stop_loss = 0
                    trading_pair_obj.save()
                    continue

                df = self.fetch_historical_klines(symbol, interval=interval)

                if df.empty:
                    continue

                df = self.precompute_indicators(df)

                required = ['ema_5', 'ema_20', 'rsi', 'macd', 'macd_signal', 'atr']
                if not all(col in df.columns and not df[col].isna().all() for col in required):
                    continue

                # 檢查波動率風險調整
                if not self.check_volatility_risk_adjustment(symbol, df):
                    logging.info(f"{symbol}: 因波動率異常暫停交易")
                    continue

                # 檢查是否應該平倉 (包括止盈止損)
                self.check_exit_conditions(symbol)

                # 檢查是否觸發每日虧損熔斷
                if self.should_trigger_circuit_breaker(symbol):
                    logging.warning(f"{symbol} 觸發每日虧損熔斷，停止今日交易。")
                    trader_status.is_trading_enabled = False # 設置全局交易狀態為禁用
                    trader_status.save()
                    return # 熔斷後立即退出主循環

                # 檢查是否有活躍持倉
                active_position = Position.objects.filter(trading_pair=trading_pair_obj, active=True).first()

                if active_position:
                    # 如果有持倉，則等待 check_exit_conditions 處理平倉
                    pass
                else:
                    # 沒有持倉，生成開倉信號
                    # 重複檢查已在上方進行，這裡移除重複檢查
                    # if (trader_status.hourly_trade_count >= self.max_trades_per_hour or
                    #     trader_status.daily_trade_count >= self.max_trades_per_day):
                    #     logging.info("已達全局開倉次數上限，跳過開倉。")
                    #     continue
                    
                    # 檢查最大同時持倉數量限制
                    if not self.check_max_position_limit():
                        logging.info(f"{symbol}: 已達到最大同時持倉數量限制，跳過開倉。")
                        continue
                    
                    signal = self.generate_signal(df) # 這裡使用 generate_signal，它會根據組合模式來執行
                    if signal == 0:
                        continue
                    
                    # 稽核層處理信號
                    if hasattr(self, 'audit_integration') and self.audit_integration:
                        audit_result = self.audit_integration.process_trading_signal(
                            signal, symbol, df, f"combo_{self.active_combo_mode}"
                        )
                        if not audit_result['approved']:
                            logging.info(f"{symbol} 稽核層拒絕信號: {audit_result['reason']}")
                            continue
                        signal = audit_result['signal']  # 使用稽核後的信號

                    price = df['close'].iloc[-1]
                    if price is None:
                        logging.warning(f"{symbol} 無法獲取當前價格，跳過本次下單。")
                        continue

                    # 計算基礎倉位大小
                    base_qty = self.calculate_position_size(symbol, price, df)
                    
                    # 根據波動率調整倉位大小
                    final_qty = self.adjust_position_size_by_volatility(symbol, base_qty, df)

                    if final_qty <= 0:
                        logging.info(f"{symbol} 計算出的下單量為零或負數 ({final_qty})，跳過下單。")
                        continue

                    side = SIDE_BUY if signal == 1 else SIDE_SELL
                    
                    # 記錄訂單提交事件
                    if hasattr(self, 'audit_integration') and self.audit_integration:
                        order_data = {
                            'order_id': f"order_{int(time.time()*1000)}",
                            'side': side,
                            'quantity': final_qty,
                            'price': price,
                            'order_type': 'market',
                            'strategy_id': f"combo_{self.active_combo_mode}",
                            'idempotency_key': f"{symbol}_{side}_{int(time.time())}"
                        }
                        self.audit_integration.log_order_event("submitted", order_data, symbol)
                    
                    order = self.place_order(symbol, side, final_qty)
                    
                    # 記錄交易日誌
                    if order:
                        try:
                            # 獲取當前價格作為成交價
                            current_price = self.get_current_price(symbol)
                            
                            # 記錄稽核層訂單成交事件
                            if hasattr(self, 'audit_integration') and self.audit_integration:
                                filled_data = {
                                    'order_id': order.get('id', f"order_{int(time.time()*1000)}"),
                                    'side': side,
                                    'filled_quantity': final_qty,
                                    'filled_price': current_price,
                                    'commission': 0.0,  # 簡化處理
                                    'slippage': 0.0,    # 簡化處理
                                    'strategy_id': f"combo_{self.active_combo_mode}",
                                    'idempotency_key': f"{symbol}_{side}_{int(time.time())}"
                                }
                                self.audit_integration.log_order_event("filled", filled_data, symbol)
                            
                            # 記錄訂單創建，使用實例變數的組合模式
                            from trading.trade_logger import log_order_created
                            log_order_created(
                                trading_pair=symbol,
                                strategy_name=f"combo_{self.active_combo_mode}",
                                combo_mode=self.active_combo_mode,
                                order_id=order.get('id', f"order_{int(time.time()*1000)}"),
                                side=side,
                                quantity=final_qty,
                                entry_price=current_price
                            )
                            logging.info(f"{symbol} 交易日誌已記錄")
                        except Exception as e:
                            logging.error(f"記錄交易日誌失敗: {e}")
                            from trading.system_monitor import ErrorSeverity
                            record_system_error("TRADE_LOGGING", str(e), ErrorSeverity.MEDIUM, "MultiSymbolTrader")
                    else:
                        # 訂單失敗，記錄拒絕事件
                        if hasattr(self, 'audit_integration') and self.audit_integration:
                            rejected_data = {
                                'order_id': f"order_{int(time.time()*1000)}",
                                'side': side,
                                'rejection_reason': "下單失敗",
                                'blocked_rules': ["order_failed"],
                                'risk_level': "HIGH",
                                'strategy_id': f"combo_{self.active_combo_mode}",
                                'idempotency_key': f"{symbol}_{side}_{int(time.time())}"
                            }
                            self.audit_integration.log_order_event("rejected", rejected_data, symbol)
                    
                    trader_status.hourly_trade_count += 1
                    trader_status.daily_trade_count += 1
                    trader_status.save()
                    self.hourly_trade_count = trader_status.hourly_trade_count
                    self.daily_trade_count = trader_status.daily_trade_count

            except Exception as e:
                logging.error(f"{symbol} 在交易週期中發生錯誤：{e}")

    def initialize_start_balance(self):
        """
        抓取可用餘額，當作當日起始資金（用於每日風控），並更新到 DailyStats 模型
        """
        try:
            balance = self.get_available_usdt_balance()
        except Exception as e:
            logging.warning(f"無法獲取餘額，使用默認值: {e}")
            balance = 1000.0  # 使用默認餘額
        
        max_daily_loss_pct = self.get_config('MAX_DAILY_LOSS_PCT', type=float, default=0.25)
        
        for trading_pair_obj in TradingPair.objects.all():
            try:
                daily_stats, created = DailyStats.objects.get_or_create(
                    trading_pair=trading_pair_obj,
                    date=timezone.localdate(),
                    defaults={
                        'start_balance': balance, 
                        'pnl': 0.0, 
                        'max_daily_loss_pct': max_daily_loss_pct
                    }
                )
                if not created:
                    daily_stats.start_balance = balance
                    daily_stats.max_daily_loss_pct = max_daily_loss_pct  # 確保更新現有記錄
                    daily_stats.save()
                logging.info(f"{trading_pair_obj.symbol} 當日起始資金已更新為 {balance:.2f} USDT")
            except Exception as e:
                logging.error(f"更新 {trading_pair_obj.symbol} 的 DailyStats 失敗: {e}")
                # 嘗試手動創建記錄
                try:
                    DailyStats.objects.create(
                        trading_pair=trading_pair_obj,
                        date=timezone.localdate(),
                        start_balance=balance,
                        pnl=0.0,
                        max_daily_loss_pct=max_daily_loss_pct
                    )
                    logging.info(f"{trading_pair_obj.symbol} DailyStats 手動創建成功")
                except Exception as e2:
                    logging.error(f"手動創建 {trading_pair_obj.symbol} DailyStats 也失敗: {e2}")

    def reset_daily_state(self):
        """
        每日重置交易狀態：止損次數歸零、盈虧歸零、恢復交易開關
        """
        logging.info("[RESET] 每日重置：恢復交易狀態")
        with transaction.atomic():
            # 重置所有 TradingPair 的連續止損次數
            for trading_pair_obj in TradingPair.objects.all():
                trading_pair_obj.consecutive_stop_loss = 0
                trading_pair_obj.save()
                logging.info(f"{trading_pair_obj.symbol} 連續止損次數重置為 0")
            
            # 重置今日的 DailyStats 損益
            self.reset_daily_stats()

            # 恢復交易狀態
            trader_status = TraderStatus.objects.get(pk=1)
            trader_status.is_trading_enabled = True
            trader_status.last_daily_reset_date = timezone.localdate()
            trader_status.daily_trade_count = 0
            trader_status.hourly_trade_count = 0
            trader_status.last_hourly_reset = timezone.now()
            trader_status.save()
            logging.info("交易開關已恢復為 True，每日重置日期已更新。")
            self.daily_trade_count = 0
            self.hourly_trade_count = 0
            self.last_hourly_reset = trader_status.last_hourly_reset


    def reset_daily_stats(self):
        """
        將所有幣種今日的 pnl 歸零，避免前一天統計影響今天的交易
        """
        today = timezone.localdate()
        max_daily_loss_pct = self.get_config('MAX_DAILY_LOSS_PCT', type=float, default=0.25)
        for trading_pair_obj in TradingPair.objects.all():
            daily_stats, created = DailyStats.objects.get_or_create(
                trading_pair=trading_pair_obj,
                date=today,
                defaults={'pnl': 0.0, 'start_balance': self.get_available_usdt_balance(), 'max_daily_loss_pct': max_daily_loss_pct}
            )
            if not created:
                daily_stats.pnl = 0.0
                daily_stats.save()
            logging.info(f"{trading_pair_obj.symbol} 今日損益已清空")

    def should_trigger_circuit_breaker(self, symbol: str) -> bool:
        """
        判斷該幣種是否已達當日虧損上限，若是則觸發熔斷停止交易
        """
        # 從數據庫獲取最新 DailyStats
        daily_stats_obj = DailyStats.objects.filter(trading_pair__symbol=symbol, date=timezone.localdate()).first()
        if not daily_stats_obj:
            logging.warning(f"未找到 {symbol} 今日的 DailyStats，跳過熔斷檢查。")
            return False

        pnl = daily_stats_obj.pnl
        start_balance = daily_stats_obj.start_balance
        max_daily_loss_pct = daily_stats_obj.max_daily_loss_pct # 使用數據庫中的百分比
        
        max_loss = start_balance * max_daily_loss_pct
        return pnl <= -max_loss

    def check_exit_conditions(self, symbol: str):
        """
        檢查是否觸發停利或止損，並執行平倉與記錄
        """
        price = self.get_current_price(symbol)
        if price is None:
            return

        try:
            position_obj = Position.objects.get(trading_pair__symbol=symbol, active=True)
        except Position.DoesNotExist:
            # 沒有活躍持倉，無需檢查平倉條件
            return

        qty = position_obj.quantity
        entry = position_obj.entry_price
        side = position_obj.side
        
        # 計算當前浮動盈虧金額
        pnl = (price - entry) * qty if side == SIDE_BUY else (entry - price) * qty

        # 獲取K線數據用於計算ATR (如果需要)
        trading_pair_obj = TradingPair.objects.get(symbol=symbol) # 從數據庫獲取 TradingPair
        # 從數據庫獲取 SYMBOL_INTERVALS
        symbol_intervals_config = self.get_config('SYMBOL_INTERVALS', type=dict, default={})
        interval = symbol_intervals_config.get(symbol, "1m") # 使用從數據庫讀取的配置
        df = self.fetch_historical_klines(symbol, interval=interval)
        if not df.empty:
            df = self.precompute_indicators(df)

        # 從數據庫獲取止盈止損模式和參數
        exit_mode = self.get_config('EXIT_MODE', default="PERCENTAGE")
        price_take_profit_percent = self.get_config('PRICE_TAKE_PROFIT_PERCENT', type=float, default=0.5)
        price_stop_loss_percent = self.get_config('PRICE_STOP_LOSS_PERCENT', type=float, default=0.25)
        amount_take_profit_usdt = self.get_config('AMOUNT_TAKE_PROFIT_USDT', type=float, default=10.0)
        amount_stop_loss_usdt = self.get_config('AMOUNT_STOP_LOSS_USDT', type=float, default=5.0)
        atr_take_profit_multiplier = self.get_config('ATR_TAKE_PROFIT_MULTIPLIER', type=float, default=1.5)
        atr_stop_loss_multiplier = self.get_config('ATR_STOP_LOSS_MULTIPLIER', type=float, default=1.0)
        hybrid_min_take_profit_usdt = self.get_config('HYBRID_MIN_TAKE_PROFIT_USDT', type=float, default=5.0)
        hybrid_max_take_profit_usdt = self.get_config('HYBRID_MAX_TAKE_PROFIT_USDT', type=float, default=20.0)
        hybrid_min_stop_loss_usdt = self.get_config('HYBRID_MIN_STOP_LOSS_USDT', type=float, default=3.0)
        hybrid_max_stop_loss_usdt = self.get_config('HYBRID_MAX_STOP_LOSS_USDT', type=float, default=10.0)

        exit_triggered = False
        exit_reason = ""

        if exit_mode == "PERCENTAGE":
            if side == SIDE_BUY:
                take_profit_price = entry * (1 + price_take_profit_percent / 100)
                stop_loss_price = entry * (1 - price_stop_loss_percent / 100)
                
                if price >= take_profit_price:
                    exit_triggered = True
                    exit_reason = "take_profit_price_percent"
                elif price <= stop_loss_price:
                    exit_triggered = True
                    exit_reason = "stop_loss_price_percent"
            else:  # SIDE_SELL
                take_profit_price = entry * (1 - price_take_profit_percent / 100)
                stop_loss_price = entry * (1 + price_stop_loss_percent / 100)
                
                if price <= take_profit_price:
                    exit_triggered = True
                    exit_reason = "take_profit_price_percent"
                elif price >= stop_loss_price:
                    exit_triggered = True
                    exit_reason = "stop_loss_price_percent"

        elif exit_mode == "AMOUNT":
            if pnl >= amount_take_profit_usdt:
                exit_triggered = True
                exit_reason = "take_profit_amount"
            elif pnl <= -amount_stop_loss_usdt:
                exit_triggered = True
                exit_reason = "stop_loss_amount"

        elif exit_mode == "ATR":
            if not df.empty and 'atr' in df.columns and df['atr'].iloc[-1] is not None:
                current_atr = df['atr'].iloc[-1]
                if side == SIDE_BUY:
                    take_profit_price = entry + (current_atr * atr_take_profit_multiplier)
                    stop_loss_price = entry - (current_atr * atr_stop_loss_multiplier)
                    
                    if price >= take_profit_price:
                        exit_triggered = True
                        exit_reason = "take_profit_atr"
                    elif price <= stop_loss_price:
                        exit_triggered = True
                        exit_reason = "stop_loss_atr"
                else:  # SIDE_SELL
                    take_profit_price = entry - (current_atr * atr_take_profit_multiplier)
                    stop_loss_price = entry + (current_atr * atr_stop_loss_multiplier)
                    
                    if price <= take_profit_price:
                        exit_triggered = True
                        exit_reason = "take_profit_atr"
                    elif price >= stop_loss_price:
                        exit_triggered = True
                        exit_reason = "stop_loss_atr"
            else:
                logging.warning(f"{symbol}: ATR 數據不可用，無法執行 ATR 止盈止損模式。")

        elif exit_mode == "HYBRID":
            if not df.empty and 'atr' in df.columns and df['atr'].iloc[-1] is not None:
                current_atr = df['atr'].iloc[-1]
                
                # 計算基於 ATR 的止盈止損金額
                atr_tp_amount = current_atr * qty * atr_take_profit_multiplier
                atr_sl_amount = current_atr * qty * atr_stop_loss_multiplier
                
                # 應用混合模式的上下限
                take_profit_amount = max(
                    min(atr_tp_amount, hybrid_max_take_profit_usdt),
                    hybrid_min_take_profit_usdt
                )
                stop_loss_amount = min(
                    max(atr_sl_amount, hybrid_min_stop_loss_usdt),
                    hybrid_max_stop_loss_usdt
                ) # 注意：止損金額應為負值，這裡的 min/max 邏輯可能需要調整以確保止損金額是期望的負值範圍
                # 為了確保 stop_loss_amount 是一個正值用於比較，我們在比較時將 pnl 轉為負數
                # 或是確保 stop_loss_amount 已經是絕對值。
                
                if pnl >= take_profit_amount:
                    exit_triggered = True
                    exit_reason = "take_profit_hybrid"
                elif pnl <= -stop_loss_amount: # pnl 是負數，與 -stop_loss_amount 比較
                    exit_triggered = True
                    exit_reason = "stop_loss_hybrid"
            else:
                logging.warning(f"{symbol}: ATR 數據不可用，無法執行 HYBRID 止盈止損模式。")

        if exit_triggered:
            with transaction.atomic(): # 使用事務確保數據一致性
                # 記錄平倉前的倉位信息
                exit_order = self.close_position(symbol, qty)
                
                # 記錄平倉交易日誌
                if exit_order:
                    try:
                        # 計算實際盈虧
                        realized_pnl = pnl
                        # 記錄平倉
                        from trading.trade_logger import log_order_created
                        log_order_created(
                            trading_pair=symbol,
                            strategy_name=f"exit_{exit_reason}",
                            combo_mode="exit",
                            order_id=exit_order.get('id', f"exit_{int(time.time()*1000)}"),
                            side="CLOSE",
                            quantity=qty,
                            entry_price=price
                        )
                        logging.info(f"{symbol} 平倉交易日誌已記錄，原因: {exit_reason}")
                    except Exception as e:
                        logging.error(f"記錄平倉交易日誌失敗: {e}")
                        from trading.system_monitor import ErrorSeverity
                        record_system_error("EXIT_TRADE_LOGGING", str(e), ErrorSeverity.MEDIUM, "MultiSymbolTrader")
                
                # 更新 DailyStats 的 pnl
                daily_stats_obj = DailyStats.objects.get(trading_pair=trading_pair_obj, date=timezone.localdate())
                daily_stats_obj.pnl += pnl
                daily_stats_obj.save()

                # 更新 TradingPair 的連續止損計數
                if "stop_loss" in exit_reason:
                    trading_pair_obj.consecutive_stop_loss += 1
                    logging.warning(f"{symbol} {exit_reason} 止損平倉 → {pnl:.2f} USDT")
                else:
                    trading_pair_obj.consecutive_stop_loss = 0
                    logging.info(f"{symbol} {exit_reason} 止盈平倉 +{pnl:.2f} USDT")
                trading_pair_obj.save()

                # 記錄交易
                enable_trade_log = self.get_config('ENABLE_TRADE_LOG', type=bool, default=False)
                if enable_trade_log:
                    self.log_trade(symbol, side, entry, price, qty, pnl, exit_reason)

                # 記錄 ATR 相關信息（用於監控和調試）
                if not df.empty and 'atr' in df.columns and df['atr'].iloc[-1] is not None:
                    current_atr = df['atr'].iloc[-1]
                    atr_percent = (current_atr / price) * 100
                    logging.debug(f"{symbol} 當前 ATR: {current_atr:.6f} ({atr_percent:.2f}%) Kishan")

    def log_trade(self, symbol, side, entry_price, exit_price, qty, pnl, reason):
        """
        寫入一筆交易紀錄到 logs/trade_log.csv
        """
        # ENABLE_TRADE_LOG 現在從數據庫獲取，並在調用處檢查，這裡不需要再檢查一次

        import os, csv
        filepath = os.path.join("logs", "trade_log.csv")
        write_header = not os.path.exists(filepath)

        with open(filepath, mode='a', newline='') as file:
            writer = csv.writer(file)
            if write_header:
                writer.writerow(['time', 'symbol', 'side', 'entry_price', 'exit_price', 'quantity', 'pnl', 'reason'])

            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                symbol, side, entry_price, exit_price, qty, pnl, reason
            ])

    def _calculate_average_historical_atr(self, symbol: str, interval: str, limit: int = 200) -> float | None:
        """
        獲取指定幣種在過去一段時間內的歷史 K 線數據，計算並回傳平均 ATR。
        參數：
            symbol (str): 交易對符號 (例如 'BTCUSDT')
            interval (str): K 線週期 (例如 '1m', '5m')
            limit (int): 獲取歷史 K 線的數量 (預設 200 根)
        回傳：
            float | None: 計算出的平均 ATR 值，如果無法獲取數據或計算失敗則回傳 None。
        """
        try:
            # 獲取指定數量歷史 K 線數據
            df = self.fetch_historical_klines(symbol, interval=interval, limit=limit)

            if df.empty:
                logging.warning(f"{symbol}: 無法獲取歷史 K 線數據 (limit={limit})，無法計算平均 ATR。")
                return None

            # 對歷史數據計算技術指標，包括 ATR
            df = self.precompute_indicators(df)

            # 檢查計算結果中 ATR 欄位是否存在且有效
            if 'atr' not in df.columns or df['atr'].empty or df['atr'].isna().all():
                 logging.warning(f"{symbol}: 歷史數據中無法計算 ATR 或 ATR 數據無效，無法計算平均 ATR。")
                 return None

            # 計算 ATR 欄位的平均值
            average_atr = df['atr'].mean()

            # 確保計算出的平均 ATR 是有效的數字
            if pd.isna(average_atr) or average_atr is None:
                 return None

            # 回傳浮點數格式的平均 ATR
            return float(average_atr)

        except Exception as e:
            # 捕獲並記錄計算歷史平均 ATR 過程中的錯誤
            logging.error(f"{symbol}: 計算歷史平均 ATR 時發生錯誤: {e}")
            return None

    def check_volatility_risk_adjustment(self, symbol: str, df: pd.DataFrame) -> bool:
        """
        檢查波動率風險並進行調整
        
        參數：
            symbol (str): 交易對符號
            df (pd.DataFrame): 包含ATR數據的DataFrame
            
        回傳：
            bool: True表示可以正常交易，False表示因波動率異常而暫停交易
        """
        if not self.enable_volatility_risk_adjustment:
            return True
            
        # 獲取歷史平均ATR
        avg_atr = self.average_atrs.get(symbol)
        if avg_atr is None or avg_atr < 1e-9:
            logging.warning(f"{symbol}: 無法獲取有效的歷史平均ATR，跳過波動率檢查")
            return True
            
        # 獲取當前ATR
        if 'atr' not in df.columns or df['atr'].empty:
            logging.warning(f"{symbol}: 無法獲取當前ATR數據，跳過波動率檢查")
            return True
            
        current_atr = df['atr'].iloc[-1]
        if current_atr is None or pd.isna(current_atr):
            logging.warning(f"{symbol}: 當前ATR數據無效，跳過波動率檢查")
            return True
            
        # 計算ATR比率
        atr_ratio = current_atr / avg_atr
        
        # 獲取或創建波動率暫停狀態記錄
        try:
            trading_pair_obj = TradingPair.objects.get(symbol=symbol)
            volatility_status, created = VolatilityPauseStatus.objects.get_or_create(
                trading_pair=trading_pair_obj,
                defaults={
                    'is_paused': False,
                    'current_atr_ratio': atr_ratio
                }
            )
            
            # 更新當前ATR比率
            volatility_status.current_atr_ratio = atr_ratio
            volatility_status.save()
            
        except Exception as e:
            logging.error(f"{symbol}: 無法獲取波動率暫停狀態: {e}")
            return True
        
        # 檢查是否應該暫停交易
        if atr_ratio >= self.volatility_pause_threshold:
            if not volatility_status.is_paused:
                # 開始暫停交易
                volatility_status.is_paused = True
                volatility_status.pause_start_time = timezone.now()
                volatility_status.pause_reason = f"波動率異常放大 (ATR比率: {atr_ratio:.2f})"
                volatility_status.save()
                logging.warning(f"{symbol}: 波動率異常放大，ATR比率為 {atr_ratio:.2f}，暫停交易")
            return False
            
        # 檢查是否可以恢復交易
        elif atr_ratio <= self.volatility_recovery_threshold:
            if volatility_status.is_paused:
                # 檢查是否達到最小暫停時間
                pause_start = volatility_status.pause_start_time
                if pause_start and (timezone.now() - pause_start).total_seconds() >= self.volatility_pause_duration_minutes * 60:
                    # 恢復交易
                    volatility_status.is_paused = False
                    volatility_status.pause_start_time = None
                    volatility_status.pause_reason = None
                    volatility_status.save()
                    logging.info(f"{symbol}: 波動率已恢復正常，ATR比率為 {atr_ratio:.2f}，恢復交易")
                else:
                    # 還在最小暫停時間內
                    remaining_time = self.volatility_pause_duration_minutes * 60 - (timezone.now() - pause_start).total_seconds()
                    logging.info(f"{symbol}: 波動率已降低但仍在冷卻期內，剩餘 {remaining_time/60:.1f} 分鐘")
                    return False
            return True
            
        # 檢查是否在暫停狀態
        if volatility_status.is_paused:
            pause_start = volatility_status.pause_start_time
            if pause_start:
                elapsed_minutes = (timezone.now() - pause_start).total_seconds() / 60
                logging.info(f"{symbol}: 因波動率異常暫停交易中，已暫停 {elapsed_minutes:.1f} 分鐘，ATR比率: {atr_ratio:.2f}")
            return False
            
        return True

    def adjust_position_size_by_volatility(self, symbol: str, base_quantity: float, df: pd.DataFrame) -> float:
        """
        根據波動率調整倉位大小
        
        參數：
            symbol (str): 交易對符號
            base_quantity (float): 基礎倉位大小
            df (pd.DataFrame): 包含ATR數據的DataFrame
            
        回傳：
            float: 調整後的倉位大小
        """
        if not self.enable_volatility_risk_adjustment:
            return base_quantity
            
        # 獲取歷史平均ATR
        avg_atr = self.average_atrs.get(symbol)
        if avg_atr is None or avg_atr < 1e-9:
            return base_quantity
            
        # 獲取當前ATR
        if 'atr' not in df.columns or df['atr'].empty:
            return base_quantity
            
        current_atr = df['atr'].iloc[-1]
        if current_atr is None or pd.isna(current_atr):
            return base_quantity
            
        # 計算ATR比率
        atr_ratio = current_atr / avg_atr
        
        # 根據波動率調整倉位大小
        if atr_ratio > self.volatility_threshold_multiplier:
            # 波動率較高時減少倉位
            adjustment_factor = self.volatility_threshold_multiplier / atr_ratio
            adjusted_quantity = base_quantity * adjustment_factor
            logging.info(f"{symbol}: 波動率較高 (ATR比率: {atr_ratio:.2f})，倉位調整係數: {adjustment_factor:.2f}")
        elif atr_ratio < 0.5:
            # 波動率較低時可以適當增加倉位
            adjustment_factor = min(1.5, 1.0 / atr_ratio)
            adjusted_quantity = base_quantity * adjustment_factor
            logging.info(f"{symbol}: 波動率較低 (ATR比率: {atr_ratio:.2f})，倉位調整係數: {adjustment_factor:.2f}")
        else:
            # 波動率正常
            adjusted_quantity = base_quantity
            logging.debug(f"{symbol}: 波動率正常 (ATR比率: {atr_ratio:.2f})，使用基礎倉位大小")
            
        return adjusted_quantity

    def check_max_position_limit(self) -> bool:
        """
        檢查是否達到最大同時持倉數量限制
        
        回傳：
            bool: True表示可以開新倉，False表示已達到限制
        """
        if not self.enable_max_position_limit:
            return True
            
        try:
            # 統計當前活躍持倉數量
            active_positions_count = Position.objects.filter(active=True).count()
            
            if active_positions_count >= self.max_simultaneous_positions:
                logging.warning(f"已達到最大同時持倉數量限制 ({self.max_simultaneous_positions})，當前活躍持倉: {active_positions_count}")
                return False
            else:
                logging.debug(f"當前活躍持倉數量: {active_positions_count}/{self.max_simultaneous_positions}")
                return True
                
        except Exception as e:
            logging.error(f"檢查最大持倉數量限制時發生錯誤: {e}")
            return True  # 發生錯誤時允許開倉，避免過度限制

    def cleanup(self):
        """
        清理資源，關閉監控服務
        """
        try:
            stop_system_monitoring()
            stop_monitoring_dashboard()
            logging.info("系統監控和監控告警已停止")
        except Exception as e:
            logging.error(f"停止系統監控失敗: {e}")
            
        # 停止稽核層
        try:
            if hasattr(self, 'audit_integration') and self.audit_integration:
                self.audit_integration.stop()
                logging.info("稽核層已停止")
        except Exception as e:
            logging.error(f"停止稽核層失敗: {e}")

    def __del__(self):
        """
        析構函數，確保資源被正確清理
        """
        self.cleanup()

    def check_and_sync_configs(self):
        """
        檢查並同步配置變化，特別是SYMBOLS配置
        """
        try:
            current_time = timezone.now()
            time_since_last_check = (current_time - self.last_config_check).total_seconds()
            
            # 每5分鐘檢查一次配置
            if time_since_last_check < self.config_sync_interval:
                return
            
            logging.info("🔍 開始檢查配置變化...")
            
            # 檢查SYMBOLS配置是否有變化
            new_symbols = self.get_config('SYMBOLS', type=list, default=[])
            
            if new_symbols != self.symbols:
                logging.info(f"📝 檢測到SYMBOLS配置變化:")
                logging.info(f"   舊配置: {self.symbols}")
                logging.info(f"   新配置: {new_symbols}")
                
                # 找出新增和刪除的幣種
                added_symbols = [s for s in new_symbols if s not in self.symbols]
                removed_symbols = [s for s in self.symbols if s not in new_symbols]
                
                if added_symbols:
                    logging.info(f"➕ 新增幣種: {added_symbols}")
                    # 為新增幣種初始化相關數據結構
                    for symbol in added_symbols:
                        self._initialize_symbol_data(symbol)
                
                if removed_symbols:
                    logging.info(f"➖ 移除幣種: {removed_symbols}")
                    # 清理移除幣種的相關數據
                    for symbol in removed_symbols:
                        self._cleanup_symbol_data(symbol)
                
                # 更新幣種列表
                self.symbols = new_symbols
                logging.info(f"✅ 幣種配置已同步更新: {self.symbols}")
                
                # 更新相關配置
                self._update_symbol_related_configs()
                
            else:
                logging.debug("✅ SYMBOLS配置無變化")
            
            # 檢查其他重要配置
            new_leverage = self.get_config('LEVERAGE', type=int, default=10)
            if new_leverage != self.leverage:
                logging.info(f"📝 檢測到槓桿配置變化: {self.leverage}x -> {new_leverage}x")
                self.leverage = new_leverage
                # 可以選擇是否自動重新設置槓桿
                if self.get_config('AUTO_SET_LEVERAGE', type=bool, default=True):
                    logging.info("🔄 自動重新設置槓桿...")
                    self.set_leverage()
            
            self.last_config_check = current_time
            logging.info("✅ 配置檢查完成")
            
        except Exception as e:
            logging.error(f"❌ 配置同步檢查失敗: {e}")
    
    def _initialize_symbol_data(self, symbol: str):
        """
        為新增的幣種初始化相關數據結構
        """
        try:
            # 初始化波動率暫停狀態
            self.volatility_pause_status[symbol] = {
                'is_paused': False,
                'pause_start_time': None,
                'pause_reason': None,
                'current_atr_ratio': 1.0
            }
            
            # 初始化每日風控統計
            self.daily_stats[symbol] = {
                'pnl': 0.0,
                'start_balance': 0.0,
                'max_daily_loss_pct': self.get_config('MAX_DAILY_LOSS_PCT', type=float, default=0.25),
                'risk_reward_ratio': 0.4
            }
            
            # 初始化持倉狀態
            self.positions[symbol] = {
                'active': False,
                'side': None,
                'entry_price': None,
                'quantity': 0.0,
            }
            
            # 初始化其他狀態
            self.cooldown_flags[symbol] = False
            self.last_trade_time[symbol] = None
            
            logging.info(f"✅ 已為 {symbol} 初始化相關數據結構")
            
        except Exception as e:
            logging.error(f"❌ 初始化 {symbol} 數據結構失敗: {e}")
    
    def _cleanup_symbol_data(self, symbol: str):
        """
        清理移除幣種的相關數據結構
        """
        try:
            # 清理波動率暫停狀態
            if symbol in self.volatility_pause_status:
                del self.volatility_pause_status[symbol]
            
            # 清理每日風控統計
            if symbol in self.daily_stats:
                del self.daily_stats[symbol]
            
            # 清理持倉狀態
            if symbol in self.positions:
                del self.positions[symbol]
            
            # 清理其他狀態
            if symbol in self.cooldown_flags:
                del self.cooldown_flags[symbol]
            
            if symbol in self.last_trade_time:
                del self.last_trade_time[symbol]
            
            logging.info(f"✅ 已清理 {symbol} 的相關數據結構")
            
        except Exception as e:
            logging.error(f"❌ 清理 {symbol} 數據結構失敗: {e}")
    
    def _update_symbol_related_configs(self):
        """
        更新與幣種相關的配置
        """
        try:
            # 更新SYMBOL_INTERVALS配置
            intervals_config = self.get_config('SYMBOL_INTERVALS', type=dict, default={})
            updated_intervals = {}
            
            for symbol in self.symbols:
                updated_intervals[symbol] = intervals_config.get(symbol, '1m')
            
            # 如果配置有變化，更新到數據庫
            if updated_intervals != intervals_config:
                from trading_api.models import TraderConfig
                try:
                    config_obj = TraderConfig.objects.get(key='SYMBOL_INTERVALS')
                    config_obj.value = json.dumps(updated_intervals, ensure_ascii=False)
                    config_obj.save()
                    logging.info(f"✅ 已更新SYMBOL_INTERVALS配置: {updated_intervals}")
                except TraderConfig.DoesNotExist:
                    logging.warning("⚠️ SYMBOL_INTERVALS配置不存在，跳過更新")
            
        except Exception as e:
            logging.error(f"❌ 更新幣種相關配置失敗: {e}")
