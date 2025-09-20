# core/risk.py
"""
稽核層風控規則系統
實現強制風控檢查和規則管理
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .events import RiskCheckResult, RiskChecked, EventType
from trading.trader import MultiSymbolTrader


@dataclass
class RiskRule:
    """風控規則定義"""
    rule_id: str
    name: str
    description: str
    enabled: bool = True
    severity: str = "HIGH"  # LOW, MEDIUM, HIGH, CRITICAL
    threshold: float = 0.0
    operator: str = ">"  # >, <, >=, <=, ==, !=
    
    def check(self, value: float) -> bool:
        """檢查規則是否觸發"""
        if not self.enabled:
            return True
            
        if self.operator == ">":
            return value <= self.threshold
        elif self.operator == "<":
            return value >= self.threshold
        elif self.operator == ">=":
            return value < self.threshold
        elif self.operator == "<=":
            return value > self.threshold
        elif self.operator == "==":
            return value != self.threshold
        elif self.operator == "!=":
            return value == self.threshold
        else:
            return True


class AuditRiskManager:
    """稽核風控管理器"""
    
    def __init__(self, trader: MultiSymbolTrader):
        self.trader = trader
        self.rules: Dict[str, RiskRule] = {}
        self._setup_default_rules()
        
    def _setup_default_rules(self):
        """設置預設風控規則"""
        # 槓桿上限規則
        self.add_rule(RiskRule(
            rule_id="leverage_cap",
            name="槓桿上限",
            description="槓桿倍數不能超過設定上限",
            threshold=2.0,
            operator=">"
        ))
        
        # 距爆倉距離規則
        self.add_rule(RiskRule(
            rule_id="dist_to_liq_min",
            name="距爆倉最小距離",
            description="距爆倉距離不能低於最小閾值",
            threshold=15.0,
            operator="<"
        ))
        
        # 單日最大虧損規則
        self.add_rule(RiskRule(
            rule_id="daily_max_loss",
            name="單日最大虧損",
            description="單日虧損不能超過最大百分比",
            threshold=3.0,
            operator=">"
        ))
        
        # 連續虧損冷卻規則
        self.add_rule(RiskRule(
            rule_id="consecutive_loss_cooldown",
            name="連續虧損冷卻",
            description="連續虧損達到上限後需要冷卻",
            threshold=3,
            operator=">="
        ))
        
        # 滑點上限規則
        self.add_rule(RiskRule(
            rule_id="max_slippage",
            name="滑點上限",
            description="預估滑點不能超過上限",
            threshold=5.0,  # 5 bps
            operator=">"
        ))
        
    def add_rule(self, rule: RiskRule):
        """添加風控規則"""
        self.rules[rule.rule_id] = rule
        logging.info(f"添加風控規則: {rule.name}")
        
    def remove_rule(self, rule_id: str):
        """移除風控規則"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logging.info(f"移除風控規則: {rule_id}")
            
    def enable_rule(self, rule_id: str):
        """啟用風控規則"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            logging.info(f"啟用風控規則: {rule_id}")
            
    def disable_rule(self, rule_id: str):
        """禁用風控規則"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            logging.info(f"禁用風控規則: {rule_id}")
            
    def check_leverage_cap(self, symbol: str, leverage: float) -> RiskCheckResult:
        """檢查槓桿上限"""
        rule = self.rules.get("leverage_cap")
        if not rule or not rule.enabled:
            return RiskCheckResult(passed=True, details="槓桿上限檢查已禁用")
            
        if rule.check(leverage):
            return RiskCheckResult(
                passed=True, 
                details=f"槓桿{leverage}x在安全範圍內"
            )
        else:
            return RiskCheckResult(
                passed=False,
                blocked_rules=["leverage_cap"],
                details=f"槓桿{leverage}x超過上限{rule.threshold}x",
                risk_level="HIGH"
            )
            
    def check_dist_to_liquidation(self, symbol: str, dist_pct: float) -> RiskCheckResult:
        """檢查距爆倉距離"""
        rule = self.rules.get("dist_to_liq_min")
        if not rule or not rule.enabled:
            return RiskCheckResult(passed=True, details="距爆倉距離檢查已禁用")
            
        if rule.check(dist_pct):
            return RiskCheckResult(
                passed=True,
                details=f"距爆倉距離{dist_pct:.1f}%安全"
            )
        else:
            return RiskCheckResult(
                passed=False,
                blocked_rules=["dist_to_liq_min"],
                details=f"距爆倉距離{dist_pct:.1f}%過近，低於{rule.threshold}%",
                risk_level="CRITICAL"
            )
            
    def check_daily_max_loss(self, symbol: str, loss_pct: float) -> RiskCheckResult:
        """檢查單日最大虧損"""
        rule = self.rules.get("daily_max_loss")
        if not rule or not rule.enabled:
            return RiskCheckResult(passed=True, details="單日最大虧損檢查已禁用")
            
        if rule.check(loss_pct):
            return RiskCheckResult(
                passed=True,
                details=f"當日虧損{loss_pct:.1f}%在安全範圍內"
            )
        else:
            return RiskCheckResult(
                passed=False,
                blocked_rules=["daily_max_loss"],
                details=f"當日虧損{loss_pct:.1f}%超過上限{rule.threshold}%",
                risk_level="CRITICAL"
            )
            
    def check_consecutive_loss_cooldown(self, symbol: str, consecutive_losses: int) -> RiskCheckResult:
        """檢查連續虧損冷卻"""
        rule = self.rules.get("consecutive_loss_cooldown")
        if not rule or not rule.enabled:
            return RiskCheckResult(passed=True, details="連續虧損冷卻檢查已禁用")
            
        if rule.check(consecutive_losses):
            return RiskCheckResult(
                passed=True,
                details=f"連續虧損{consecutive_losses}次在安全範圍內"
            )
        else:
            return RiskCheckResult(
                passed=False,
                blocked_rules=["consecutive_loss_cooldown"],
                details=f"連續虧損{consecutive_losses}次達到上限{rule.threshold}次，需要冷卻",
                risk_level="HIGH"
            )
            
    def check_max_slippage(self, symbol: str, estimated_slippage_bps: float) -> RiskCheckResult:
        """檢查滑點上限"""
        rule = self.rules.get("max_slippage")
        if not rule or not rule.enabled:
            return RiskCheckResult(passed=True, details="滑點上限檢查已禁用")
            
        if rule.check(estimated_slippage_bps):
            return RiskCheckResult(
                passed=True,
                details=f"預估滑點{estimated_slippage_bps:.1f}bps在安全範圍內"
            )
        else:
            return RiskCheckResult(
                passed=False,
                blocked_rules=["max_slippage"],
                details=f"預估滑點{estimated_slippage_bps:.1f}bps超過上限{rule.threshold}bps",
                risk_level="MEDIUM"
            )
            
    def comprehensive_risk_check(self, signal, symbol: str, df) -> RiskCheckResult:
        """綜合風控檢查"""
        blocked_rules = []
        all_details = []
        max_risk_level = "LOW"
        
        try:
            # 獲取當前槓桿
            leverage = self.trader.leverage
            
            # 檢查槓桿上限
            leverage_result = self.check_leverage_cap(symbol, leverage)
            if not leverage_result.passed:
                blocked_rules.extend(leverage_result.blocked_rules)
                all_details.append(leverage_result.details)
                if leverage_result.risk_level == "CRITICAL":
                    max_risk_level = "CRITICAL"
                elif leverage_result.risk_level == "HIGH" and max_risk_level != "CRITICAL":
                    max_risk_level = "HIGH"
                    
            # 計算距爆倉距離（簡化計算）
            current_price = df['close'].iloc[-1] if not df.empty else 0
            dist_to_liq = self._calculate_dist_to_liquidation(symbol, current_price, leverage)
            liq_result = self.check_dist_to_liquidation(symbol, dist_to_liq)
            if not liq_result.passed:
                blocked_rules.extend(liq_result.blocked_rules)
                all_details.append(liq_result.details)
                if liq_result.risk_level == "CRITICAL":
                    max_risk_level = "CRITICAL"
                    
            # 檢查單日虧損
            daily_loss_pct = self._get_daily_loss_percentage(symbol)
            loss_result = self.check_daily_max_loss(symbol, daily_loss_pct)
            if not loss_result.passed:
                blocked_rules.extend(loss_result.blocked_rules)
                all_details.append(loss_result.details)
                if loss_result.risk_level == "CRITICAL":
                    max_risk_level = "CRITICAL"
                    
            # 檢查連續虧損冷卻
            consecutive_losses = self._get_consecutive_losses(symbol)
            cooldown_result = self.check_consecutive_loss_cooldown(symbol, consecutive_losses)
            if not cooldown_result.passed:
                blocked_rules.extend(cooldown_result.blocked_rules)
                all_details.append(cooldown_result.details)
                if cooldown_result.risk_level == "HIGH" and max_risk_level != "CRITICAL":
                    max_risk_level = "HIGH"
                    
            # 檢查滑點上限（簡化估算）
            estimated_slippage = self._estimate_slippage(symbol, df)
            slippage_result = self.check_max_slippage(symbol, estimated_slippage)
            if not slippage_result.passed:
                blocked_rules.extend(slippage_result.blocked_rules)
                all_details.append(slippage_result.details)
                if slippage_result.risk_level == "MEDIUM" and max_risk_level not in ["HIGH", "CRITICAL"]:
                    max_risk_level = "MEDIUM"
                    
            # 綜合結果
            passed = len(blocked_rules) == 0
            details = "; ".join(all_details) if all_details else "所有風控檢查通過"
            
            return RiskCheckResult(
                passed=passed,
                blocked_rules=blocked_rules,
                details=details,
                risk_level=max_risk_level
            )
            
        except Exception as e:
            logging.error(f"風控檢查發生錯誤: {e}")
            return RiskCheckResult(
                passed=False,
                blocked_rules=["system_error"],
                details=f"風控檢查系統錯誤: {str(e)}",
                risk_level="CRITICAL"
            )
            
    def _calculate_dist_to_liquidation(self, symbol: str, current_price: float, leverage: float) -> float:
        """計算距爆倉距離（簡化計算）"""
        try:
            # 簡化計算：假設爆倉價格為當前價格的 1/leverage
            liquidation_price = current_price * (1 - 1/leverage)
            dist_pct = ((current_price - liquidation_price) / current_price) * 100
            return max(0, dist_pct)
        except:
            return 50.0  # 預設安全距離
            
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
            
    def _get_consecutive_losses(self, symbol: str) -> int:
        """獲取連續虧損次數"""
        try:
            from trading_api.models import TradingPair
            
            trading_pair = TradingPair.objects.get(symbol=symbol)
            return trading_pair.consecutive_stop_loss
        except:
            return 0
            
    def _estimate_slippage(self, symbol: str, df) -> float:
        """估算滑點（簡化計算）"""
        try:
            if df.empty or len(df) < 2:
                return 1.0  # 預設1bps
                
            # 基於價格波動估算滑點
            price_volatility = df['close'].pct_change().std() * 100
            estimated_slippage = min(price_volatility * 10, 10.0)  # 限制在10bps內
            return max(estimated_slippage, 0.5)  # 最少0.5bps
        except:
            return 2.0  # 預設2bps
