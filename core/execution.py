# core/execution.py
"""
稽核執行管道
整合風控檢查、解釋生成和稽核記錄
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from .events import (
    SignalGenerated, RiskChecked, ExplainCreated, OrderSubmitted, 
    OrderFilled, OrderRejected, EventType, create_event
)
from .risk import AuditRiskManager, RiskCheckResult
from .explain import ExplanationGenerator
from .audit import AuditLogger


class AuditPipeline:
    """稽核管道"""
    
    def __init__(self, trader, audit_logger: AuditLogger):
        self.trader = trader
        self.audit_logger = audit_logger
        
        # 初始化組件
        self.risk_manager = AuditRiskManager(trader)
        self.explanation_generator = ExplanationGenerator()
        
        logging.info("稽核管道初始化完成")
        
    def process_signal(self, signal_data: Dict[str, Any], symbol: str, df) -> Tuple[bool, str, Dict[str, Any]]:
        """
        處理交易信號
        
        Returns:
            Tuple[bool, str, Dict]: (是否通過, 原因, 結果數據)
        """
        try:
            # 1. 創建信號事件
            signal_event = self._create_signal_event(signal_data, symbol)
            self.audit_logger.log_event(signal_event)
            
            # 2. 並行生成解釋
            explain_task = self._generate_explanation_async(signal_event, symbol, df)
            
            # 3. 現有風控檢查
            existing_risk_result = self._check_existing_risk(symbol, df)
            existing_risk_event = self._create_risk_event(existing_risk_result, symbol, "existing")
            self.audit_logger.log_event(existing_risk_event)
            
            # 4. 稽核風控檢查
            audit_risk_result = self.risk_manager.comprehensive_risk_check(signal_event, symbol, df)
            audit_risk_event = self._create_risk_event(audit_risk_result, symbol, "audit")
            self.audit_logger.log_event(audit_risk_event)
            
            # 5. 綜合決策
            final_decision = self._make_final_decision(existing_risk_result, audit_risk_result)
            
            # 6. 等待解釋生成完成
            explain_event = explain_task
            self.audit_logger.log_event(explain_event)
            
            # 7. 返回結果
            if final_decision.passed:
                return True, "稽核通過", {
                    'signal_event': signal_event,
                    'existing_risk': existing_risk_result,
                    'audit_risk': audit_risk_result,
                    'explanation': explain_event
                }
            else:
                return False, final_decision.details, {
                    'signal_event': signal_event,
                    'existing_risk': existing_risk_result,
                    'audit_risk': audit_risk_result,
                    'explanation': explain_event,
                    'blocked_rules': final_decision.blocked_rules
                }
                
        except Exception as e:
            logging.error(f"稽核管道處理信號失敗: {e}")
            return False, f"稽核系統錯誤: {str(e)}", {}
            
    def _create_signal_event(self, signal_data: Dict[str, Any], symbol: str) -> SignalGenerated:
        """創建信號事件"""
        return SignalGenerated(
            event_type=EventType.SIGNAL_GENERATED,
            account_id=self.trader.get_config('ACCOUNT_ID', default='default'),
            venue=self.trader.get_config('EXCHANGE_NAME', default='BINANCE'),
            symbol=symbol,
            strategy_id=signal_data.get('strategy_name', 'unknown'),
            idempotency_key=f"{symbol}_{int(time.time())}_{uuid.uuid4().hex[:8]}",
            side=signal_data.get('side', 'flat'),
            confidence=signal_data.get('confidence', 0.5),
            indicators=signal_data.get('indicators', {}),
            signal_strength=signal_data.get('signal_strength', 0.5),
            market_conditions=signal_data.get('market_conditions', {})
        )
        
    def _generate_explanation_async(self, signal_event: SignalGenerated, symbol: str, df) -> ExplainCreated:
        """異步生成解釋"""
        try:
            # 創建上下文
            context = {
                'current_price': df['close'].iloc[-1] if not df.empty else 0,
                'leverage': self.trader.leverage,
                'dist_to_liq_pct': self._calculate_dist_to_liquidation(symbol),
                'daily_loss_pct': self._get_daily_loss_percentage(symbol),
                'order_type': 'market',
                'max_slippage_bps': 5
            }
            
            # 創建虛擬風控結果用於解釋生成
            dummy_risk = RiskChecked(
                event_type=EventType.RISK_CHECKED,
                account_id=signal_event.account_id,
                venue=signal_event.venue,
                symbol=signal_event.symbol,
                strategy_id=signal_event.strategy_id,
                idempotency_key=signal_event.idempotency_key,
                risk_result=RiskCheckResult(passed=True),
                leverage=self.trader.leverage,
                daily_loss_used_pct=context['daily_loss_pct'],
                dist_to_liq_pct=context['dist_to_liq_pct']
            )
            
            # 生成解釋
            return self.explanation_generator.generate_explanation(
                signal_event, dummy_risk, context
            )
            
        except Exception as e:
            logging.error(f"生成解釋失敗: {e}")
            # 返回預設解釋
            return ExplainCreated(
                event_type=EventType.EXPLAIN_CREATED,
                account_id=signal_event.account_id,
                venue=signal_event.venue,
                symbol=signal_event.symbol,
                strategy_id=signal_event.strategy_id,
                idempotency_key=signal_event.idempotency_key,
                explanation=["系統無法生成詳細解釋"],
                template_used="default",
                explanation_quality="LOW",
                word_count=10,
                confidence_score=0.1
            )
            
    def _check_existing_risk(self, symbol: str, df) -> RiskCheckResult:
        """檢查現有風控"""
        try:
            blocked_rules = []
            details = []
            
            # 檢查波動率風險調整
            if not self.trader.check_volatility_risk_adjustment(symbol, df):
                blocked_rules.append("volatility_risk")
                details.append("波動率異常，暫停交易")
                
            # 檢查每日虧損熔斷
            if self.trader.should_trigger_circuit_breaker(symbol):
                blocked_rules.append("circuit_breaker")
                details.append("觸發每日虧損熔斷")
                
            # 檢查最大持倉限制
            if not self.trader.check_max_position_limit():
                blocked_rules.append("max_position_limit")
                details.append("達到最大持倉數量限制")
                
            # 綜合結果
            passed = len(blocked_rules) == 0
            details_text = "; ".join(details) if details else "現有風控檢查通過"
            
            return RiskCheckResult(
                passed=passed,
                blocked_rules=blocked_rules,
                details=details_text,
                risk_level="HIGH" if blocked_rules else "NORMAL"
            )
            
        except Exception as e:
            logging.error(f"現有風控檢查失敗: {e}")
            return RiskCheckResult(
                passed=False,
                blocked_rules=["system_error"],
                details=f"現有風控檢查錯誤: {str(e)}",
                risk_level="CRITICAL"
            )
            
    def _create_risk_event(self, risk_result: RiskCheckResult, symbol: str, risk_type: str) -> RiskChecked:
        """創建風控事件"""
        return RiskChecked(
            event_type=EventType.RISK_CHECKED,
            account_id=self.trader.get_config('ACCOUNT_ID', default='default'),
            venue=self.trader.get_config('EXCHANGE_NAME', default='BINANCE'),
            symbol=symbol,
            strategy_id=f"{risk_type}_risk",
            idempotency_key=f"{symbol}_{risk_type}_{int(time.time())}",
            risk_result=risk_result,
            leverage=self.trader.leverage,
            daily_loss_used_pct=self._get_daily_loss_percentage(symbol),
            dist_to_liq_pct=self._calculate_dist_to_liquidation(symbol)
        )
        
    def _make_final_decision(self, existing_risk: RiskCheckResult, audit_risk: RiskCheckResult) -> RiskCheckResult:
        """做出最終決策"""
        # 取最嚴格的結果
        if not existing_risk.passed or not audit_risk.passed:
            # 合併被阻擋的規則
            all_blocked_rules = existing_risk.blocked_rules + audit_risk.blocked_rules
            all_details = [existing_risk.details, audit_risk.details]
            
            # 確定最高風險等級
            risk_levels = [existing_risk.risk_level, audit_risk.risk_level]
            max_risk_level = self._get_max_risk_level(risk_levels)
            
            return RiskCheckResult(
                passed=False,
                blocked_rules=all_blocked_rules,
                details="; ".join(all_details),
                risk_level=max_risk_level
            )
        else:
            return RiskCheckResult(
                passed=True,
                details="所有風控檢查通過",
                risk_level="NORMAL"
            )
            
    def _get_max_risk_level(self, risk_levels: list) -> str:
        """獲取最高風險等級"""
        level_order = {"LOW": 1, "NORMAL": 2, "MEDIUM": 3, "HIGH": 4, "CRITICAL": 5}
        return max(risk_levels, key=lambda x: level_order.get(x, 0))
        
    def _calculate_dist_to_liquidation(self, symbol: str) -> float:
        """計算距爆倉距離"""
        try:
            # 簡化計算
            leverage = self.trader.leverage
            return max(0, (leverage - 1) / leverage * 100)
        except:
            return 50.0
            
    def _get_daily_loss_percentage(self, symbol: str) -> float:
        """獲取當日虧損百分比"""
        try:
            from trading_api.models import DailyStats
            from django.utils import timezone
            
            daily_stats = DailyStats.objects.filter(
                trading_pair__symbol=symbol,
                date=timezone.localdate()
            ).first()
            
            if daily_stats and daily_stats.start_balance > 0:
                return abs(daily_stats.pnl) / daily_stats.start_balance * 100
            return 0.0
        except:
            return 0.0
            
    def log_order_event(self, event_type: EventType, order_data: Dict[str, Any], symbol: str):
        """記錄訂單事件"""
        try:
            if event_type == EventType.ORDER_SUBMITTED:
                event = OrderSubmitted(
                    event_type=event_type,
                    account_id=self.trader.get_config('ACCOUNT_ID', default='default'),
                    venue=self.trader.get_config('EXCHANGE_NAME', default='BINANCE'),
                    symbol=symbol,
                    strategy_id=order_data.get('strategy_id', 'unknown'),
                    idempotency_key=order_data.get('idempotency_key', ''),
                    order_id=order_data.get('order_id', ''),
                    side=order_data.get('side', ''),
                    quantity=order_data.get('quantity', 0.0),
                    price=order_data.get('price', 0.0),
                    order_type=order_data.get('order_type', 'market')
                )
            elif event_type == EventType.ORDER_FILLED:
                event = OrderFilled(
                    event_type=event_type,
                    account_id=self.trader.get_config('ACCOUNT_ID', default='default'),
                    venue=self.trader.get_config('EXCHANGE_NAME', default='BINANCE'),
                    symbol=symbol,
                    strategy_id=order_data.get('strategy_id', 'unknown'),
                    idempotency_key=order_data.get('idempotency_key', ''),
                    order_id=order_data.get('order_id', ''),
                    filled_quantity=order_data.get('filled_quantity', 0.0),
                    filled_price=order_data.get('filled_price', 0.0),
                    commission=order_data.get('commission', 0.0),
                    slippage=order_data.get('slippage', 0.0)
                )
            elif event_type == EventType.ORDER_REJECTED:
                event = OrderRejected(
                    event_type=event_type,
                    account_id=self.trader.get_config('ACCOUNT_ID', default='default'),
                    venue=self.trader.get_config('EXCHANGE_NAME', default='BINANCE'),
                    symbol=symbol,
                    strategy_id=order_data.get('strategy_id', 'unknown'),
                    idempotency_key=order_data.get('idempotency_key', ''),
                    order_id=order_data.get('order_id', ''),
                    rejection_reason=order_data.get('rejection_reason', ''),
                    blocked_rules=order_data.get('blocked_rules', []),
                    risk_level=order_data.get('risk_level', 'NORMAL')
                )
            else:
                return
                
            self.audit_logger.log_event(event)
            
        except Exception as e:
            logging.error(f"記錄訂單事件失敗: {e}")
