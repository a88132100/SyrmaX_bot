# core/audit_integration.py
"""
稽核層整合模組
將稽核層整合到現有交易流程中
"""

import logging
import time
from typing import Dict, Any, Optional

from .config import AuditConfig
from .audit import AuditLogger
from .execution import AuditPipeline
from .events import EventType


class AuditIntegration:
    """稽核層整合器"""
    
    def __init__(self, trader):
        self.trader = trader
        self.audit_config = AuditConfig(trader)
        
        # 檢查稽核層是否啟用
        if not self.audit_config.is_audit_enabled():
            logging.info("稽核層已禁用")
            self.audit_pipeline = None
            return
            
        # 初始化稽核組件
        try:
            logging_config = self.audit_config.get_logging_config()
            self.audit_logger = AuditLogger(
                audit_dir=logging_config['log_dir'],
                batch_seconds=logging_config['batch_seconds'],
                batch_size=logging_config['batch_size']
            )
            
            self.audit_pipeline = AuditPipeline(trader, self.audit_logger)
            logging.info("稽核層整合完成")
            
        except Exception as e:
            logging.error(f"稽核層初始化失敗: {e}")
            self.audit_pipeline = None
            
    def is_enabled(self) -> bool:
        """檢查稽核層是否啟用"""
        return self.audit_pipeline is not None
        
    def process_trading_signal(self, signal: int, symbol: str, df, strategy_name: str = None) -> Dict[str, Any]:
        """
        處理交易信號（整合稽核層）
        
        Args:
            signal: 交易信號 (1=買入, -1=賣出, 0=觀望)
            symbol: 交易對
            df: K線數據
            strategy_name: 策略名稱
            
        Returns:
            Dict: 處理結果
        """
        if not self.is_enabled():
            # 稽核層未啟用，直接返回原始信號
            return {
                'approved': signal != 0,
                'signal': signal,
                'reason': '稽核層未啟用',
                'audit_data': {}
            }
            
        try:
            # 準備信號數據
            signal_data = self._prepare_signal_data(signal, symbol, df, strategy_name)
            
            # 通過稽核管道處理
            approved, reason, audit_data = self.audit_pipeline.process_signal(
                signal_data, symbol, df
            )
            
            return {
                'approved': approved,
                'signal': signal if approved else 0,
                'reason': reason,
                'audit_data': audit_data
            }
            
        except Exception as e:
            logging.error(f"稽核層處理信號失敗: {e}")
            # 發生錯誤時，為了安全起見，拒絕信號
            return {
                'approved': False,
                'signal': 0,
                'reason': f'稽核層錯誤: {str(e)}',
                'audit_data': {}
            }
            
    def _prepare_signal_data(self, signal: int, symbol: str, df, strategy_name: str = None) -> Dict[str, Any]:
        """準備信號數據"""
        try:
            # 獲取技術指標
            indicators = {}
            if not df.empty and len(df) > 0:
                # 基本價格指標
                indicators['close'] = float(df['close'].iloc[-1])
                indicators['high'] = float(df['high'].iloc[-1])
                indicators['low'] = float(df['low'].iloc[-1])
                indicators['volume'] = float(df['volume'].iloc[-1])
                
                # 技術指標（如果存在）
                if 'ema_5' in df.columns:
                    indicators['ema_5'] = float(df['ema_5'].iloc[-1])
                if 'ema_20' in df.columns:
                    indicators['ema_20'] = float(df['ema_20'].iloc[-1])
                if 'rsi' in df.columns:
                    indicators['rsi'] = float(df['rsi'].iloc[-1])
                if 'atr' in df.columns:
                    indicators['atr'] = float(df['atr'].iloc[-1])
                if 'macd' in df.columns:
                    indicators['macd'] = float(df['macd'].iloc[-1])
                if 'macd_signal' in df.columns:
                    indicators['macd_signal'] = float(df['macd_signal'].iloc[-1])
                    
                # 計算價格變化
                if len(df) > 1:
                    price_change = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100
                    indicators['price_change_pct'] = float(price_change)
                    
                # 計算成交量比率
                if len(df) > 10:
                    avg_volume = df['volume'].iloc[-10:].mean()
                    indicators['avg_volume'] = float(avg_volume)
                    indicators['volume_ratio'] = float(df['volume'].iloc[-1] / avg_volume)
                    
            # 確定交易方向
            if signal == 1:
                side = "long"
            elif signal == -1:
                side = "short"
            else:
                side = "flat"
                
            # 計算信號強度（簡化）
            signal_strength = abs(signal) if signal != 0 else 0
            
            # 計算信心度（基於指標完整性）
            confidence = min(1.0, len(indicators) / 10.0)
            
            return {
                'side': side,
                'confidence': confidence,
                'indicators': indicators,
                'signal_strength': signal_strength,
                'strategy_name': strategy_name or f"combo_{self.trader.active_combo_mode}",
                'market_conditions': {
                    'volatility': indicators.get('atr', 0),
                    'trend': 'up' if indicators.get('ema_5', 0) > indicators.get('ema_20', 0) else 'down',
                    'volume': 'high' if indicators.get('volume_ratio', 1) > 1.2 else 'normal'
                }
            }
            
        except Exception as e:
            logging.error(f"準備信號數據失敗: {e}")
            return {
                'side': 'flat',
                'confidence': 0.1,
                'indicators': {},
                'signal_strength': 0,
                'strategy_name': strategy_name or 'unknown',
                'market_conditions': {}
            }
            
    def log_order_event(self, event_type: str, order_data: Dict[str, Any], symbol: str):
        """記錄訂單事件"""
        if not self.is_enabled():
            return
            
        try:
            # 轉換事件類型
            if event_type == "submitted":
                event_type_enum = EventType.ORDER_SUBMITTED
            elif event_type == "filled":
                event_type_enum = EventType.ORDER_FILLED
            elif event_type == "rejected":
                event_type_enum = EventType.ORDER_REJECTED
            elif event_type == "cancelled":
                event_type_enum = EventType.ORDER_CANCELLED
            else:
                return
                
            self.audit_pipeline.log_order_event(event_type_enum, order_data, symbol)
            
        except Exception as e:
            logging.error(f"記錄訂單事件失敗: {e}")
            
    def get_audit_report(self, date: str = None) -> Dict[str, Any]:
        """獲取稽核報告"""
        if not self.is_enabled():
            return {"error": "稽核層未啟用"}
            
        try:
            if not date:
                from datetime import datetime
                date = datetime.now().strftime("%Y%m%d")
                
            return self.audit_logger.generate_daily_report(date)
            
        except Exception as e:
            logging.error(f"獲取稽核報告失敗: {e}")
            return {"error": str(e)}
            
    def stop(self):
        """停止稽核層"""
        if self.is_enabled() and hasattr(self, 'audit_logger'):
            self.audit_logger.stop()
            logging.info("稽核層已停止")
