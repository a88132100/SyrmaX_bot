# monitoring_dashboard.py
"""
監控告警與性能分析系統
實時監控儀表板、智能告警、性能分析工具
"""

import logging
import time
import threading
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
from collections import deque, defaultdict
import warnings
warnings.filterwarnings('ignore')

# 配置日誌
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """告警等級枚舉"""
    INFO = "INFO"           # 信息
    WARNING = "WARNING"     # 警告
    CRITICAL = "CRITICAL"   # 嚴重
    EMERGENCY = "EMERGENCY" # 緊急

class AlertStatus(Enum):
    """告警狀態枚舉"""
    ACTIVE = "ACTIVE"       # 活躍
    ACKNOWLEDGED = "ACKNOWLEDGED"  # 已確認
    RESOLVED = "RESOLVED"   # 已解決
    EXPIRED = "EXPIRED"     # 已過期

@dataclass
class PerformanceMetric:
    """性能指標數據類"""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    category: str
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None

@dataclass
class AlertRule:
    """告警規則數據類"""
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str  # ">", "<", ">=", "<=", "==", "!="
    threshold: float
    alert_level: AlertLevel
    cooldown_minutes: int = 5
    enabled: bool = True

@dataclass
class Alert:
    """告警數據類"""
    alert_id: str
    rule_id: str
    timestamp: datetime
    alert_level: AlertLevel
    status: AlertStatus
    message: str
    metric_value: float
    threshold: float
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

@dataclass
class SystemHealth:
    """系統健康狀態數據類"""
    timestamp: datetime
    overall_score: float  # 0-100
    status: str  # "HEALTHY", "WARNING", "CRITICAL"
    component_scores: Dict[str, float]
    recommendations: List[str]

class MonitoringDashboard:
    """監控告警與性能分析儀表板"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.monitoring = False
        self.monitor_thread = None
        
        # 性能指標存儲
        self.performance_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.current_metrics: Dict[str, float] = {}
        
        # 告警系統
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # 性能分析
        self.performance_history: Dict[str, List[float]] = defaultdict(list)
        self.trend_analysis: Dict[str, Dict[str, float]] = {}
        
        # 回調函數
        self.alert_callbacks: List[Callable] = []
        self.health_callbacks: List[Callable] = []
        
        # 配置
        self.monitor_interval = self.config.get('monitor_interval', 10)  # 秒
        self.alert_cooldown = self.config.get('alert_cooldown', 300)  # 秒
        self.performance_window = self.config.get('performance_window', 3600)  # 秒
        
        # 初始化默認告警規則
        self._init_default_alert_rules()
        
        logger.info("監控告警儀表板初始化完成")
    
    def _init_default_alert_rules(self):
        """初始化默認告警規則"""
        default_rules = [
            AlertRule(
                rule_id="cpu_high",
                name="CPU使用率過高",
                description="CPU使用率超過80%",
                metric_name="cpu_percent",
                condition=">",
                threshold=80.0,
                alert_level=AlertLevel.WARNING,
                cooldown_minutes=5
            ),
            AlertRule(
                rule_id="cpu_critical",
                name="CPU使用率嚴重",
                description="CPU使用率超過95%",
                metric_name="cpu_percent",
                condition=">",
                threshold=95.0,
                alert_level=AlertLevel.CRITICAL,
                cooldown_minutes=2
            ),
            AlertRule(
                rule_id="memory_high",
                name="內存使用率過高",
                description="內存使用率超過85%",
                metric_name="memory_percent",
                condition=">",
                threshold=85.0,
                alert_level=AlertLevel.WARNING,
                cooldown_minutes=5
            ),
            AlertRule(
                rule_id="memory_critical",
                name="內存使用率嚴重",
                description="內存使用率超過95%",
                metric_name="memory_percent",
                condition=">",
                threshold=95.0,
                alert_level=AlertLevel.CRITICAL,
                cooldown_minutes=2
            ),
            AlertRule(
                rule_id="disk_high",
                name="磁盤使用率過高",
                description="磁盤使用率超過90%",
                metric_name="disk_percent",
                condition=">",
                threshold=90.0,
                alert_level=AlertLevel.WARNING,
                cooldown_minutes=10
            ),
            AlertRule(
                rule_id="api_response_slow",
                name="API響應過慢",
                description="API響應時間超過1000ms",
                metric_name="api_response_time",
                condition=">",
                threshold=1000.0,
                alert_level=AlertLevel.WARNING,
                cooldown_minutes=3
            ),
            AlertRule(
                rule_id="error_rate_high",
                name="錯誤率過高",
                description="錯誤率超過5%",
                metric_name="error_rate",
                condition=">",
                threshold=5.0,
                alert_level=AlertLevel.WARNING,
                cooldown_minutes=5
            )
        ]
        
        for rule in default_rules:
            self.add_alert_rule(rule)
    
    def start_monitoring(self):
        """開始監控"""
        if self.monitoring:
            logger.warning("監控儀表板已在運行中")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("監控儀表板已啟動")
    
    def stop_monitoring(self):
        """停止監控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("監控儀表板已停止")
    
    def _monitor_loop(self):
        """監控主循環"""
        while self.monitoring:
            try:
                # 收集性能指標
                self._collect_performance_metrics()
                
                # 檢查告警規則
                self._check_alert_rules()
                
                # 更新性能分析
                self._update_performance_analysis()
                
                # 觸發健康回調
                self._trigger_health_callbacks()
                
                # 等待下次監控
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"監控循環中發生錯誤: {e}")
                time.sleep(5)
    
    def _collect_performance_metrics(self):
        """收集性能指標"""
        try:
            import psutil
            
            # 系統性能指標
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 記錄指標
            self._record_metric("cpu_percent", cpu_percent, "%", "system", 80.0, 95.0)
            self._record_metric("memory_percent", memory.percent, "%", "system", 85.0, 95.0)
            self._record_metric("disk_percent", disk.percent, "%", "system", 90.0, 95.0)
            
            # 網絡指標
            network_io = psutil.net_io_counters()
            self._record_metric("network_bytes_sent", network_io.bytes_sent, "bytes", "network")
            self._record_metric("network_bytes_recv", network_io.bytes_recv, "bytes", "network")
            
            # 進程指標
            process_count = len(psutil.pids())
            self._record_metric("process_count", process_count, "count", "system")
            
            # 模擬API響應時間（實際應用中應該從真實API獲取）
            api_response_time = np.random.normal(150, 50)  # 模擬150ms平均響應時間
            self._record_metric("api_response_time", max(0, api_response_time), "ms", "api", 1000.0, 2000.0)
            
            # 模擬錯誤率（實際應用中應該從系統監控器獲取）
            error_rate = np.random.exponential(0.5)  # 模擬0.5%平均錯誤率
            self._record_metric("error_rate", min(100, error_rate), "%", "system", 5.0, 10.0)
            
        except Exception as e:
            logger.error(f"收集性能指標失敗: {e}")
    
    def _record_metric(self, name: str, value: float, unit: str, category: str, 
                       threshold_warning: Optional[float] = None, 
                       threshold_critical: Optional[float] = None):
        """記錄性能指標"""
        try:
            metric = PerformanceMetric(
                timestamp=datetime.now(timezone.utc),
                metric_name=name,
                value=value,
                unit=unit,
                category=category,
                threshold_warning=threshold_warning,
                threshold_critical=threshold_critical
            )
            
            # 存儲到隊列
            self.performance_metrics[name].append(metric)
            
            # 更新當前值
            self.current_metrics[name] = value
            
            # 添加到歷史記錄
            self.performance_history[name].append(value)
            
            # 限制歷史記錄大小
            if len(self.performance_history[name]) > 10000:
                self.performance_history[name] = self.performance_history[name][-5000:]
                
        except Exception as e:
            logger.error(f"記錄指標失敗: {e}")
    
    def _check_alert_rules(self):
        """檢查告警規則"""
        try:
            for rule_id, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                
                # 檢查指標是否存在
                if rule.metric_name not in self.current_metrics:
                    continue
                
                current_value = self.current_metrics[rule.metric_name]
                
                # 檢查告警條件
                should_alert = self._evaluate_alert_condition(
                    current_value, rule.condition, rule.threshold
                )
                
                if should_alert:
                    # 檢查冷卻期
                    if self._can_trigger_alert(rule_id, rule.cooldown_minutes):
                        self._trigger_alert(rule, current_value)
                        
        except Exception as e:
            logger.error(f"檢查告警規則失敗: {e}")
    
    def _evaluate_alert_condition(self, value: float, condition: str, threshold: float) -> bool:
        """評估告警條件"""
        try:
            if condition == ">":
                return value > threshold
            elif condition == ">=":
                return value >= threshold
            elif condition == "<":
                return value < threshold
            elif condition == "<=":
                return value <= threshold
            elif condition == "==":
                return abs(value - threshold) < 0.001
            elif condition == "!=":
                return abs(value - threshold) >= 0.001
            else:
                return False
        except Exception as e:
            logger.error(f"評估告警條件失敗: {e}")
            return False
    
    def _can_trigger_alert(self, rule_id: str, cooldown_minutes: int) -> bool:
        """檢查是否可以觸發告警（冷卻期檢查）"""
        try:
            if rule_id in self.active_alerts:
                alert = self.active_alerts[rule_id]
                cooldown_seconds = cooldown_minutes * 60
                time_since_last_alert = (datetime.now(timezone.utc) - alert.timestamp).total_seconds()
                return time_since_last_alert >= cooldown_seconds
            
            return True
            
        except Exception as e:
            logger.error(f"檢查告警冷卻期失敗: {e}")
            return True
    
    def _trigger_alert(self, rule: AlertRule, current_value: float):
        """觸發告警"""
        try:
            alert_id = f"{rule.rule_id}_{int(time.time())}"
            
            alert = Alert(
                alert_id=alert_id,
                rule_id=rule.rule_id,
                timestamp=datetime.now(timezone.utc),
                alert_level=rule.alert_level,
                status=AlertStatus.ACTIVE,
                message=f"{rule.description}: 當前值 {current_value:.2f}{rule.metric_name.split('_')[-1] if '_' in rule.metric_name else ''}",
                metric_value=current_value,
                threshold=rule.threshold
            )
            
            # 添加到活躍告警
            self.active_alerts[rule.rule_id] = alert
            
            # 添加到歷史記錄
            self.alert_history.append(alert)
            
            # 觸發告警回調
            self._trigger_alert_callbacks(alert)
            
            logger.warning(f"告警觸發: {rule.name} - {alert.message}")
            
        except Exception as e:
            logger.error(f"觸發告警失敗: {e}")
    
    def _update_performance_analysis(self):
        """更新性能分析"""
        try:
            for metric_name, values in self.performance_history.items():
                if len(values) < 10:  # 需要足夠的數據點
                    continue
                
                # 計算統計指標
                recent_values = values[-100:]  # 最近100個值
                
                analysis = {
                    'current': recent_values[-1] if recent_values else 0,
                    'average': np.mean(recent_values),
                    'std': np.std(recent_values),
                    'min': np.min(recent_values),
                    'max': np.max(recent_values),
                    'trend': self._calculate_trend(recent_values),
                    'volatility': np.std(recent_values) / np.mean(recent_values) if np.mean(recent_values) > 0 else 0
                }
                
                self.trend_analysis[metric_name] = analysis
                
        except Exception as e:
            logger.error(f"更新性能分析失敗: {e}")
    
    def _calculate_trend(self, values: List[float]) -> str:
        """計算趨勢方向"""
        try:
            if len(values) < 10:
                return "STABLE"
            
            # 使用線性回歸計算趨勢
            x = np.arange(len(values))
            y = np.array(values)
            
            # 計算斜率
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 0.01:
                return "INCREASING"
            elif slope < -0.01:
                return "DECREASING"
            else:
                return "STABLE"
                
        except Exception as e:
            logger.error(f"計算趨勢失敗: {e}")
            return "UNKNOWN"
    
    def _trigger_alert_callbacks(self, alert: Alert):
        """觸發告警回調"""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回調執行失敗: {e}")
    
    def _trigger_health_callbacks(self):
        """觸發健康回調"""
        try:
            health = self.get_system_health()
            for callback in self.health_callbacks:
                try:
                    callback(health)
                except Exception as e:
                    logger.error(f"健康回調執行失敗: {e}")
        except Exception as e:
            logger.error(f"觸發健康回調失敗: {e}")
    
    def add_alert_rule(self, rule: AlertRule):
        """添加告警規則"""
        try:
            self.alert_rules[rule.rule_id] = rule
            logger.info(f"添加告警規則: {rule.name}")
        except Exception as e:
            logger.error(f"添加告警規則失敗: {e}")
    
    def remove_alert_rule(self, rule_id: str):
        """移除告警規則"""
        try:
            if rule_id in self.alert_rules:
                del self.alert_rules[rule_id]
                logger.info(f"移除告警規則: {rule_id}")
        except Exception as e:
            logger.error(f"移除告警規則失敗: {e}")
    
    def acknowledge_alert(self, rule_id: str, user: str):
        """確認告警"""
        try:
            if rule_id in self.active_alerts:
                alert = self.active_alerts[rule_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_by = user
                alert.acknowledged_at = datetime.now(timezone.utc)
                logger.info(f"告警已確認: {rule_id} by {user}")
        except Exception as e:
            logger.error(f"確認告警失敗: {e}")
    
    def resolve_alert(self, rule_id: str, user: str):
        """解決告警"""
        try:
            if rule_id in self.active_alerts:
                alert = self.active_alerts[rule_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_by = user
                alert.resolved_at = datetime.now(timezone.utc)
                
                # 從活躍告警中移除
                del self.active_alerts[rule_id]
                
                logger.info(f"告警已解決: {rule_id} by {user}")
        except Exception as e:
            logger.error(f"解決告警失敗: {e}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """獲取當前指標"""
        try:
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'metrics': self.current_metrics.copy(),
                'performance_metrics': {
                    name: [asdict(m) for m in list(queue)[-10:]]  # 最近10個指標
                    for name, queue in self.performance_metrics.items()
                }
            }
        except Exception as e:
            logger.error(f"獲取當前指標失敗: {e}")
            return {}
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """獲取告警摘要"""
        try:
            active_alerts = [alert for alert in self.active_alerts.values() 
                           if alert.status == AlertStatus.ACTIVE]
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'active_alerts_count': len(active_alerts),
                'active_alerts': [asdict(alert) for alert in active_alerts],
                'alert_history_count': len(self.alert_history),
                'alert_rules_count': len(self.alert_rules)
            }
        except Exception as e:
            logger.error(f"獲取告警摘要失敗: {e}")
            return {}
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """獲取性能分析"""
        try:
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'trend_analysis': self.trend_analysis.copy(),
                'performance_history': {
                    name: values[-100:] if len(values) > 100 else values
                    for name, values in self.performance_history.items()
                }
            }
        except Exception as e:
            logger.error(f"獲取性能分析失敗: {e}")
            return {}
    
    def get_system_health(self) -> SystemHealth:
        """獲取系統健康狀態"""
        try:
            # 計算組件分數
            component_scores = {}
            recommendations = []
            
            # CPU健康度
            if 'cpu_percent' in self.current_metrics:
                cpu_score = max(0, 100 - self.current_metrics['cpu_percent'])
                component_scores['cpu'] = cpu_score
                if cpu_score < 20:
                    recommendations.append("CPU使用率過高，建議檢查系統負載")
            
            # 內存健康度
            if 'memory_percent' in self.current_metrics:
                memory_score = max(0, 100 - self.current_metrics['memory_percent'])
                component_scores['memory'] = memory_score
                if memory_score < 15:
                    recommendations.append("內存使用率過高，建議清理內存或重啟服務")
            
            # 磁盤健康度
            if 'disk_percent' in self.current_metrics:
                disk_score = max(0, 100 - self.current_metrics['disk_percent'])
                component_scores['disk'] = disk_score
                if disk_score < 10:
                    recommendations.append("磁盤空間不足，建議清理舊文件")
            
            # API健康度
            if 'api_response_time' in self.current_metrics:
                api_time = self.current_metrics['api_response_time']
                if api_time < 100:
                    api_score = 100
                elif api_time < 500:
                    api_score = 80
                elif api_time < 1000:
                    api_score = 60
                else:
                    api_score = 20
                component_scores['api'] = api_score
                if api_score < 40:
                    recommendations.append("API響應時間過長，建議檢查網絡連接")
            
            # 計算總體健康分數
            if component_scores:
                overall_score = np.mean(list(component_scores.values()))
            else:
                overall_score = 50
            
            # 確定整體狀態
            if overall_score >= 80:
                status = "HEALTHY"
            elif overall_score >= 60:
                status = "WARNING"
            else:
                status = "CRITICAL"
            
            return SystemHealth(
                timestamp=datetime.now(timezone.utc),
                overall_score=overall_score,
                status=status,
                component_scores=component_scores,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"獲取系統健康狀態失敗: {e}")
            return SystemHealth(
                timestamp=datetime.now(timezone.utc),
                overall_score=0,
                status="UNKNOWN",
                component_scores={},
                recommendations=["無法獲取系統健康狀態"]
            )
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """獲取儀表板摘要"""
        try:
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'system_health': asdict(self.get_system_health()),
                'current_metrics': self.get_current_metrics(),
                'alert_summary': self.get_alert_summary(),
                'performance_analysis': self.get_performance_analysis()
            }
        except Exception as e:
            logger.error(f"獲取儀表板摘要失敗: {e}")
            return {}
    
    def add_alert_callback(self, callback: Callable):
        """添加告警回調"""
        self.alert_callbacks.append(callback)
    
    def add_health_callback(self, callback: Callable):
        """添加健康監控回調"""
        self.health_callbacks.append(callback)
    
    def export_dashboard_data(self, filepath: str):
        """導出儀表板數據"""
        try:
            data = {
                'dashboard_summary': self.get_dashboard_summary(),
                'performance_history': dict(self.performance_history),
                'alert_history': [asdict(alert) for alert in self.alert_history],
                'alert_rules': [asdict(rule) for rule in self.alert_rules.values()]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"儀表板數據已導出到: {filepath}")
            
        except Exception as e:
            logger.error(f"導出儀表板數據失敗: {e}")

# 創建全局實例
monitoring_dashboard = MonitoringDashboard()

# 便捷函數
def start_monitoring_dashboard():
    """便捷函數：啟動監控告警儀表板"""
    monitoring_dashboard.start_monitoring()

def stop_monitoring_dashboard():
    """便捷函數：停止監控告警儀表板"""
    monitoring_dashboard.stop_monitoring()

def get_dashboard_summary() -> Dict[str, Any]:
    """便捷函數：獲取儀表板摘要"""
    return monitoring_dashboard.get_dashboard_summary()

def add_alert_rule(rule: AlertRule):
    """便捷函數：添加告警規則"""
    monitoring_dashboard.add_alert_rule(rule)

def acknowledge_alert(rule_id: str, user: str):
    """便捷函數：確認告警"""
    monitoring_dashboard.acknowledge_alert(rule_id, user)

def resolve_alert(rule_id: str, user: str):
    """便捷函數：解決告警"""
    monitoring_dashboard.resolve_alert(rule_id, user)
