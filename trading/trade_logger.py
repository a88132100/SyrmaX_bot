# trade_logger.py
"""
完整的交易日誌模組
記錄每筆交易的完整信息
"""

import logging
import json
import csv
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_detailed.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class OrderInfo:
    """訂單信息數據類"""
    # 基本信息
    trading_pair: str
    strategy_name: str
    combo_mode: str
    order_id: str
    exchange_order_id: Optional[str] = None
    
    # 訂單狀態
    order_status: str = 'PENDING'
    
    # 交易方向
    side: str = 'BUY'
    order_type: str = 'MARKET'
    
    # 價格信息
    entry_price: float = 0.0
    exit_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    
    # 數量信息
    quantity: float = 0.0
    filled_quantity: float = 0.0
    remaining_quantity: float = 0.0
    
    # 時間戳記錄
    order_created_time: datetime = None
    order_submitted_time: Optional[datetime] = None
    first_fill_time: Optional[datetime] = None
    last_fill_time: Optional[datetime] = None
    order_completed_time: Optional[datetime] = None
    order_cancelled_time: Optional[datetime] = None
    
    # 財務信息
    commission: float = 0.0
    slippage: float = 0.0
    notional_value: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    
    # 風險指標
    leverage: float = 1.0
    margin_used: float = 0.0
    margin_ratio: float = 0.0
    risk_reward_ratio: Optional[float] = None
    
    # 市場環境
    market_volatility: Optional[float] = None
    atr_value: Optional[float] = None
    trend_strength: Optional[str] = None
    
    # 策略信號
    signal_strength: Optional[float] = None
    signal_confidence: Optional[float] = None
    multiple_signals: List[Dict] = None
    
    # 執行質量
    execution_quality: str = 'NORMAL'
    execution_delay: Optional[float] = None
    price_improvement: float = 0.0
    
    # 錯誤和異常
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    # 備註和標籤
    notes: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        """初始化後處理"""
        if self.order_created_time is None:
            self.order_created_time = datetime.now(timezone.utc)
        if self.multiple_signals is None:
            self.multiple_signals = []
        if self.tags is None:
            self.tags = []
        if self.remaining_quantity == 0.0:
            self.remaining_quantity = self.quantity

class TradeLogger:
    """交易日誌記錄器"""
    
    def __init__(self, log_dir: str = 'logs'):
        self.log_dir = log_dir
        self.ensure_log_dir()
        
        # 初始化CSV文件
        self.trade_csv_path = os.path.join(log_dir, 'trades.csv')
        self.init_csv_files()
        
        logger.info("交易日誌記錄器初始化完成")
    
    def ensure_log_dir(self):
        """確保日誌目錄存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            logger.info(f"創建日誌目錄: {self.log_dir}")
    
    def init_csv_files(self):
        """初始化CSV文件"""
        if not os.path.exists(self.trade_csv_path):
            trade_headers = [
                'timestamp', 'trading_pair', 'strategy_name', 'combo_mode', 'order_id',
                'exchange_order_id', 'order_status', 'side', 'order_type',
                'entry_price', 'exit_price', 'target_price', 'stop_loss_price', 'take_profit_price',
                'quantity', 'filled_quantity', 'remaining_quantity',
                'order_created_time', 'order_submitted_time', 'first_fill_time', 'last_fill_time',
                'order_completed_time', 'order_cancelled_time',
                'commission', 'slippage', 'notional_value', 'realized_pnl', 'unrealized_pnl',
                'leverage', 'margin_used', 'margin_ratio', 'risk_reward_ratio',
                'market_volatility', 'atr_value', 'trend_strength',
                'signal_strength', 'signal_confidence', 'multiple_signals',
                'execution_quality', 'execution_delay', 'price_improvement',
                'error_code', 'error_message', 'retry_count',
                'notes', 'tags'
            ]
            self.write_csv_headers(self.trade_csv_path, trade_headers)
            logger.info("創建交易記錄CSV文件")
    
    def write_csv_headers(self, file_path: str, headers: List[str]):
        """寫入CSV標題行"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def log_order_created(self, order_info: OrderInfo):
        """記錄訂單創建"""
        try:
            order_info.order_status = 'PENDING'
            order_info.order_created_time = datetime.now(timezone.utc)
            
            logger.info(f"訂單創建: {order_info.trading_pair} {order_info.side} "
                       f"{order_info.quantity} @ {order_info.entry_price} "
                       f"策略: {order_info.strategy_name}")
            
            self.write_trade_to_csv(order_info)
            
        except Exception as e:
            logger.error(f"記錄訂單創建失敗: {e}")
    
    def write_trade_to_csv(self, order_info: OrderInfo):
        """將交易記錄寫入CSV"""
        try:
            row_data = [
                datetime.now(timezone.utc).isoformat(),
                order_info.trading_pair,
                order_info.strategy_name,
                order_info.combo_mode,
                order_info.order_id,
                order_info.exchange_order_id or '',
                order_info.order_status,
                order_info.side,
                order_info.order_type,
                order_info.entry_price,
                order_info.exit_price or '',
                order_info.target_price or '',
                order_info.stop_loss_price or '',
                order_info.take_profit_price or '',
                order_info.quantity,
                order_info.filled_quantity,
                order_info.remaining_quantity,
                order_info.order_created_time.isoformat() if order_info.order_created_time else '',
                order_info.order_submitted_time.isoformat() if order_info.order_submitted_time else '',
                order_info.first_fill_time.isoformat() if order_info.first_fill_time else '',
                order_info.last_fill_time.isoformat() if order_info.last_fill_time else '',
                order_info.order_completed_time.isoformat() if order_info.order_completed_time else '',
                order_info.order_cancelled_time.isoformat() if order_info.order_cancelled_time else '',
                order_info.commission,
                order_info.slippage,
                order_info.notional_value,
                order_info.realized_pnl,
                order_info.unrealized_pnl,
                order_info.leverage,
                order_info.margin_used,
                order_info.margin_ratio,
                order_info.risk_reward_ratio or '',
                order_info.market_volatility or '',
                order_info.atr_value or '',
                order_info.trend_strength or '',
                order_info.signal_strength or '',
                order_info.signal_confidence or '',
                json.dumps(order_info.multiple_signals),
                order_info.execution_quality,
                order_info.execution_delay or '',
                order_info.price_improvement,
                order_info.error_code or '',
                order_info.error_message or '',
                order_info.retry_count,
                order_info.notes or '',
                json.dumps(order_info.tags)
            ]
            
            with open(self.trade_csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
                
        except Exception as e:
            logger.error(f"寫入交易CSV失敗: {e}")

# 創建全局實例
trade_logger = TradeLogger()

# 便捷函數
def log_order_created(trading_pair: str, strategy_name: str, combo_mode: str,
                      order_id: str, side: str, quantity: float, entry_price: float,
                      **kwargs) -> OrderInfo:
    """便捷函數：記錄訂單創建"""
    order_info = OrderInfo(
        trading_pair=trading_pair,
        strategy_name=strategy_name,
        combo_mode=combo_mode,
        order_id=order_id,
        side=side,
        quantity=quantity,
        entry_price=entry_price,
        **kwargs
    )
    trade_logger.log_order_created(order_info)
    return order_info
