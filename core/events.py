# core/events.py
"""
稽核層事件溯源模型
定義所有稽核相關的事件數據結構
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """事件類型枚舉"""
    SIGNAL_GENERATED = "signal_generated"
    RISK_CHECKED = "risk_checked"
    EXPLAIN_CREATED = "explain_created"
    ORDER_SUBMITTED = "order_submitted"
    ORDER_FILLED = "order_filled"
    ORDER_REJECTED = "order_rejected"
    ORDER_CANCELLED = "order_cancelled"
    POSITION_CHANGED = "position_changed"
    ENGINE_HEALTH = "engine_health"
    SIM_COMPARED = "sim_compared"


class RiskCheckResult(BaseModel):
    """風控檢查結果"""
    passed: bool = Field(description="是否通過風控檢查")
    blocked_rules: List[str] = Field(default_factory=list, description="被阻擋的規則列表")
    details: str = Field(default="", description="詳細說明")
    risk_level: str = Field(default="NORMAL", description="風險等級：LOW, NORMAL, HIGH, CRITICAL")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="檢查時間")


class BaseEvent(BaseModel):
    """基礎事件類"""
    event_type: EventType
    ts: datetime = Field(default_factory=datetime.utcnow, description="事件時間戳")
    account_id: str = Field(description="帳戶ID")
    venue: str = Field(description="交易所")
    symbol: str = Field(description="交易對")
    strategy_id: str = Field(description="策略ID")
    idempotency_key: str = Field(description="冪等性鍵值")
    
    class Config:
        use_enum_values = True


class SignalGenerated(BaseEvent):
    """信號生成事件"""
    event_type: EventType = EventType.SIGNAL_GENERATED
    side: str = Field(description="交易方向：long/short/flat")
    confidence: float = Field(description="信號信心度 0-1")
    indicators: Dict[str, float] = Field(description="技術指標數據")
    signal_strength: float = Field(description="信號強度")
    market_conditions: Dict[str, Any] = Field(default_factory=dict, description="市場環境數據")


class RiskChecked(BaseEvent):
    """風控檢查事件"""
    event_type: EventType = EventType.RISK_CHECKED
    risk_result: RiskCheckResult = Field(description="風控檢查結果")
    leverage: float = Field(description="槓桿倍數")
    daily_loss_used_pct: float = Field(description="當日虧損使用百分比")
    dist_to_liq_pct: float = Field(description="距爆倉距離百分比")
    cooldown: bool = Field(default=False, description="是否在冷卻期")
    risk_metrics: Dict[str, float] = Field(default_factory=dict, description="風險指標")


class ExplainCreated(BaseEvent):
    """解釋生成事件"""
    event_type: EventType = EventType.EXPLAIN_CREATED
    explanation: List[str] = Field(description="解釋內容列表")
    template_used: str = Field(description="使用的解釋模板")
    explanation_quality: str = Field(default="NORMAL", description="解釋品質：LOW, NORMAL, HIGH")
    word_count: int = Field(description="解釋字數")
    confidence_score: float = Field(description="解釋信心度")


class OrderSubmitted(BaseEvent):
    """訂單提交事件"""
    event_type: EventType = EventType.ORDER_SUBMITTED
    order_id: str = Field(description="訂單ID")
    side: str = Field(description="交易方向")
    quantity: float = Field(description="數量")
    price: float = Field(description="價格")
    order_type: str = Field(description="訂單類型")
    time_in_force: str = Field(default="GTC", description="訂單有效期")


class OrderFilled(BaseEvent):
    """訂單成交事件"""
    event_type: EventType = EventType.ORDER_FILLED
    order_id: str = Field(description="訂單ID")
    filled_quantity: float = Field(description="成交數量")
    filled_price: float = Field(description="成交價格")
    commission: float = Field(description="手續費")
    slippage: float = Field(description="滑點")
    execution_time: float = Field(description="執行時間(毫秒)")


class OrderRejected(BaseEvent):
    """訂單拒絕事件"""
    event_type: EventType = EventType.ORDER_REJECTED
    order_id: str = Field(description="訂單ID")
    rejection_reason: str = Field(description="拒絕原因")
    blocked_rules: List[str] = Field(description="被阻擋的規則")
    risk_level: str = Field(description="風險等級")


class OrderCancelled(BaseEvent):
    """訂單取消事件"""
    event_type: EventType = EventType.ORDER_CANCELLED
    order_id: str = Field(description="訂單ID")
    cancel_reason: str = Field(description="取消原因")
    cancelled_quantity: float = Field(description="取消數量")


class PositionChanged(BaseEvent):
    """倉位變化事件"""
    event_type: EventType = EventType.POSITION_CHANGED
    position_side: str = Field(description="倉位方向")
    position_size: float = Field(description="倉位大小")
    entry_price: float = Field(description="開倉價格")
    unrealized_pnl: float = Field(description="未實現損益")
    margin_used: float = Field(description="使用保證金")


class EngineHealth(BaseEvent):
    """引擎健康狀態事件"""
    event_type: EventType = EventType.ENGINE_HEALTH
    health_status: str = Field(description="健康狀態：HEALTHY, WARNING, CRITICAL")
    cpu_usage: float = Field(description="CPU使用率")
    memory_usage: float = Field(description="內存使用率")
    error_count: int = Field(description="錯誤計數")
    uptime: float = Field(description="運行時間(秒)")


class SimCompared(BaseEvent):
    """模擬vs實盤對比事件"""
    event_type: EventType = EventType.SIM_COMPARED
    sim_price: float = Field(description="模擬價格")
    live_price: float = Field(description="實盤價格")
    slippage_bps: float = Field(description="滑點(bps)")
    fee_diff: float = Field(description="手續費差異")
    reasons: List[str] = Field(description="偏差原因")
    comparison_quality: str = Field(description="對比品質")


# 事件工廠函數
def create_event(event_type: EventType, **kwargs) -> BaseEvent:
    """創建事件的工廠函數"""
    event_classes = {
        EventType.SIGNAL_GENERATED: SignalGenerated,
        EventType.RISK_CHECKED: RiskChecked,
        EventType.EXPLAIN_CREATED: ExplainCreated,
        EventType.ORDER_SUBMITTED: OrderSubmitted,
        EventType.ORDER_FILLED: OrderFilled,
        EventType.ORDER_REJECTED: OrderRejected,
        EventType.ORDER_CANCELLED: OrderCancelled,
        EventType.POSITION_CHANGED: PositionChanged,
        EventType.ENGINE_HEALTH: EngineHealth,
        EventType.SIM_COMPARED: SimCompared,
    }
    
    event_class = event_classes.get(event_type)
    if not event_class:
        raise ValueError(f"未知的事件類型: {event_type}")
    
    return event_class(**kwargs)
