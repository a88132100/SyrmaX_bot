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
from trading.constants import SIDE_BUY, SIDE_SELL, symbol_precision
from strategy.base import evaluate_bundles, strategy_bundles
from trading.utils import get_precision
from django.utils import timezone
from django.db import transaction
from trading_api.models import TradingPair, DailyStats, TraderStatus, Position, StrategyCombo, COMBO_MODE_CHOICES, TraderConfig
from trading_api.admin import CONFIG_FIELD_TYPES

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
    def __init__(self):
        # 新增 get_config 方法來從數據庫讀取配置
        self.configs = {} # 用於緩存已讀取的配置，避免重複查詢

        # 載入所有 TraderConfig 到緩存
        self._load_all_configs()

        # 決定使用哪個交易所客戶端 (從數據庫讀取)
        exchange_name = self.get_config('EXCHANGE_NAME', default='binance_usdm')
        api_key = self.get_config('API_KEY', default='')
        api_secret = self.get_config('API_SECRET', default='')
        use_testnet = self.get_config('USE_TESTNET', type=bool, default=False)

        self.client = load_exchange_client(exchange_name, api_key, api_secret, use_testnet)

        # 初始化 MultiSymbolTrader 的模擬模式狀態 (從數據庫讀取)
        self.test_mode = self.get_config('TEST_MODE', type=bool, default=False)

        # 交易次數限制開關，預設為啟用
        self.enable_trade_limits = self.get_config('ENABLE_TRADE_LIMITS', type=bool, default=True)

        # 從數據庫讀取交易對和槓桿
        self.symbols = self.get_config('SYMBOLS', type=list, default=[])
        self.leverage = self.get_config('LEVERAGE', type=int, default=10)
        
        # 從配置讀取是否自動設置槓桿
        auto_set_leverage = self.get_config('AUTO_SET_LEVERAGE', type=bool, default=True)
        logging.info(f"[DEBUG] AUTO_SET_LEVERAGE 配置值為: {auto_set_leverage} (型別: {type(auto_set_leverage)})")
        if auto_set_leverage is True:
            self.set_leverage()
        else:
            logging.info("已關閉自動設置槓桿，啟動時將跳過 set_leverage() 步驟。")

        # 與交易所伺服器校時
        try:
            server_time = self.client.time()
            local_time = int(time.time() * 1000)
            if server_time is not None:
                self.time_offset = server_time - local_time
                logging.info(f"伺服器時間={server_time}, 本地時間={local_time}, 時間差={self.time_offset} ms")
            else:
                self.time_offset = 0
                logging.warning("無法從交易所獲取伺服器時間，將使用本地時間。")
        except Exception as e:
            self.time_offset = 0
            logging.error(f"與交易所校時失敗: {e}，將使用本地時間。")
       
        # 全局交易判斷頻率
        self.global_interval_seconds = self.get_config('GLOBAL_INTERVAL_SECONDS', type=int, default=3)

        # 每小時與每日允許的最大開倉次數
        self.max_trades_per_hour = self.get_config('MAX_TRADES_PER_HOUR', type=int, default=5)
        self.max_trades_per_day = self.get_config('MAX_TRADES_PER_DAY', type=int, default=100)


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
                # 這裡可以載入其他 TradingPair 的配置，例如 consecutive_stop_loss

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
                    value = value_str.strip().lower() in ['true', '1', 't', 'y', 'yes']
                else:
                    value = bool(value_str)
            elif expected_type_str == 'list':
                # 解析 JSON 格式的列表
                try:
                    value = json.loads(value_str)
                    if not isinstance(value, list):
                        raise ValueError("JSON 解析結果不是一個列表")
                except (json.JSONDecodeError, ValueError) as e:
                    logging.error(f"配置鍵 '{key}' 的值 '{value_str}' 無法解析為列表: {e}")
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
        """
        try:
            # client.fetch_klines 已經有了基本的錯誤處理
            klines = self.client.fetch_klines(symbol, interval, limit)
            
            if not klines: # 如果返回空列表
                logging.warning(f"{symbol}: 從交易所未獲取到 K 線數據。")
                return pd.DataFrame()

            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
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
        if self.test_mode:
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
                    logging.info("已達全局開倉次數上限，跳過開倉。")
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
                    if (trader_status.hourly_trade_count >= self.max_trades_per_hour or
                        trader_status.daily_trade_count >= self.max_trades_per_day):
                        logging.info("已達全局開倉次數上限，跳過開倉。")
                        continue
                    signal = self.generate_signal(df) # 這裡使用 generate_signal，它會根據組合模式來執行
                    if signal == 0:
                        continue

                    price = df['close'].iloc[-1]
                    if price is None:
                        logging.warning(f"{symbol} 無法獲取當前價格，跳過本次下單。")
                        continue

                    final_qty = self.calculate_position_size(symbol, price, df)

                    if final_qty <= 0:
                        logging.info(f"{symbol} 計算出的下單量為零或負數 ({final_qty})，跳過下單。")
                        continue

                    side = SIDE_BUY if signal == 1 else SIDE_SELL
                    self.place_order(symbol, side, final_qty)
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
        balance = self.get_available_usdt_balance()
        max_daily_loss_pct = self.get_config('MAX_DAILY_LOSS_PCT', type=float, default=0.25)
        for trading_pair_obj in TradingPair.objects.all():
            daily_stats, created = DailyStats.objects.get_or_create(
                trading_pair=trading_pair_obj,
                date=timezone.localdate(),
                defaults={'start_balance': balance, 'pnl': 0.0, 'max_daily_loss_pct': max_daily_loss_pct}
            )
            if not created:
                daily_stats.start_balance = balance
                daily_stats.save()
            logging.info(f"{trading_pair_obj.symbol} 當日起始資金已更新為 {balance:.2f} USDT")

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
                self.close_position(symbol, qty)
                
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
