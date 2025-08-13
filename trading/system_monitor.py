# system_monitor.py
"""
系統監控模組
監控系統健康狀態、捕捉錯誤、自動重連等
"""

import logging
import psutil
import time
import threading
import requests
import socket
import os
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import traceback
import queue

# 配置日誌
logger = logging.getLogger(__name__)

class SystemStatus(Enum):
    """系統狀態枚舉"""
    HEALTHY = "HEALTHY"           # 健康
    WARNING = "WARNING"           # 警告
    CRITICAL = "CRITICAL"         # 嚴重
    OFFLINE = "OFFLINE"           # 離線
    RECONNECTING = "RECONNECTING" # 重連中

class ErrorSeverity(Enum):
    """錯誤嚴重程度枚舉"""
    LOW = "LOW"           # 低 - 不影響交易
    MEDIUM = "MEDIUM"     # 中 - 部分功能受影響
    HIGH = "HIGH"         # 高 - 主要功能受影響
    CRITICAL = "CRITICAL" # 嚴重 - 系統無法運行

@dataclass
class SystemMetrics:
    """系統指標數據類"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, float]
    process_count: int
    system_status: SystemStatus

@dataclass
class ErrorRecord:
    """錯誤記錄數據類"""
    timestamp: datetime
    error_type: str
    error_message: str
    severity: ErrorSeverity
    component: str
    stack_trace: str
    context: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    resolution_method: Optional[str] = None

@dataclass
class ConnectionStatus:
    """連接狀態數據類"""
    component: str
    status: SystemStatus
    last_check: datetime
    response_time: float
    error_count: int
    last_error: Optional[str] = None
    auto_reconnect: bool = True
    max_retries: int = 3

class SystemMonitor:
    """系統監控器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.monitoring = False
        self.monitor_thread = None
        self.metrics_history: List[SystemMetrics] = []
        self.error_history: List[ErrorRecord] = []
        self.connection_status: Dict[str, ConnectionStatus] = {}
        self.health_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        
        # 監控配置
        self.monitor_interval = self.config.get('monitor_interval', 30)  # 秒
        self.max_history_size = self.config.get('max_history_size', 1000)
        self.cpu_threshold = self.config.get('cpu_threshold', 80.0)
        self.memory_threshold = self.config.get('memory_threshold', 85.0)
        self.disk_threshold = self.config.get('disk_threshold', 90.0)
        
        # 初始化連接狀態監控
        self._init_connection_monitoring()
        
        logger.info("系統監控器初始化完成")
    
    def _init_connection_monitoring(self):
        """初始化連接狀態監控"""
        # 監控交易所API連接
        self.connection_status['binance_api'] = ConnectionStatus(
            component='binance_api',
            status=SystemStatus.OFFLINE,
            last_check=datetime.now(timezone.utc),
            response_time=0.0,
            error_count=0
        )
        
        self.connection_status['bybit_api'] = ConnectionStatus(
            component='bybit_api',
            status=SystemStatus.OFFLINE,
            last_check=datetime.now(timezone.utc),
            response_time=0.0,
            error_count=0
        )
        
        self.connection_status['okx_api'] = ConnectionStatus(
            component='okx_api',
            status=SystemStatus.OFFLINE,
            last_check=datetime.now(timezone.utc),
            response_time=0.0,
            error_count=0
        )
        
        # 監控數據庫連接
        self.connection_status['database'] = ConnectionStatus(
            component='database',
            status=SystemStatus.OFFLINE,
            last_check=datetime.now(timezone.utc),
            response_time=0.0,
            error_count=0
        )
        
        # 監控網絡連接
        self.connection_status['internet'] = ConnectionStatus(
            component='internet',
            status=SystemStatus.OFFLINE,
            last_check=datetime.now(timezone.utc),
            response_time=0.0,
            error_count=0
        )
    
    def start_monitoring(self):
        """開始系統監控"""
        if self.monitoring:
            logger.warning("系統監控已在運行中")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("系統監控已啟動")
    
    def stop_monitoring(self):
        """停止系統監控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("系統監控已停止")
    
    def _monitor_loop(self):
        """監控主循環"""
        while self.monitoring:
            try:
                # 收集系統指標
                metrics = self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # 檢查連接狀態
                self._check_connections()
                
                # 清理歷史記錄
                self._cleanup_history()
                
                # 觸發健康回調
                self._trigger_health_callbacks(metrics)
                
                # 等待下次監控
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"監控循環中發生錯誤: {e}")
                self.record_error("monitor_loop", str(e), ErrorSeverity.HIGH, "system_monitor")
                time.sleep(5)  # 錯誤後等待5秒再繼續
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """收集系統指標"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 內存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盤使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # 網絡IO
            network_io = psutil.net_io_counters()
            network_stats = {
                'bytes_sent': network_io.bytes_sent,
                'bytes_recv': network_io.bytes_recv,
                'packets_sent': network_io.packets_sent,
                'packets_recv': network_io.packets_recv
            }
            
            # 進程數量
            process_count = len(psutil.pids())
            
            # 判斷系統狀態
            if (cpu_percent > self.cpu_threshold or 
                memory_percent > self.memory_threshold or 
                disk_percent > self.disk_threshold):
                system_status = SystemStatus.WARNING
            elif (cpu_percent > 95 or 
                  memory_percent > 95 or 
                  disk_percent > 95):
                system_status = SystemStatus.CRITICAL
            else:
                system_status = SystemStatus.HEALTHY
            
            return SystemMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io=network_stats,
                process_count=process_count,
                system_status=system_status
            )
            
        except Exception as e:
            logger.error(f"收集系統指標失敗: {e}")
            return SystemMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                network_io={},
                process_count=0,
                system_status=SystemStatus.CRITICAL
            )
    
    def _check_connections(self):
        """檢查連接狀態"""
        try:
            # 檢查互聯網連接
            self._check_internet_connection()
            
            # 檢查交易所API連接
            self._check_exchange_connections()
            
            # 檢查數據庫連接
            self._check_database_connection()
            
        except Exception as e:
            logger.error(f"檢查連接狀態失敗: {e}")
    
    def _check_internet_connection(self):
        """檢查互聯網連接"""
        try:
            start_time = time.time()
            
            # 嘗試連接多個網站
            test_urls = [
                'https://www.google.com',
                'https://www.baidu.com',
                'https://www.binance.com'
            ]
            
            connected = False
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        connected = True
                        break
                except:
                    continue
            
            response_time = (time.time() - start_time) * 1000  # 轉換為毫秒
            
            status = self.connection_status['internet']
            status.last_check = datetime.now(timezone.utc)
            status.response_time = response_time
            
            if connected:
                status.status = SystemStatus.HEALTHY
                status.error_count = 0
                status.last_error = None
            else:
                status.status = SystemStatus.OFFLINE
                status.error_count += 1
                status.last_error = "無法連接到互聯網"
                
        except Exception as e:
            logger.error(f"檢查互聯網連接失敗: {e}")
            self.connection_status['internet'].status = SystemStatus.CRITICAL
    
    def _check_exchange_connections(self):
        """檢查交易所API連接"""
        # 這裡可以實現具體的交易所API連接檢查
        # 目前使用模擬數據
        exchanges = ['binance_api', 'bybit_api', 'okx_api']
        
        for exchange in exchanges:
            try:
                status = self.connection_status[exchange]
                status.last_check = datetime.now(timezone.utc)
                
                # 模擬連接檢查（實際應用中應該調用真實的API）
                if exchange == 'binance_api':
                    # 模擬Binance API檢查
                    status.status = SystemStatus.HEALTHY
                    status.response_time = 150.0  # 150ms
                    status.error_count = 0
                elif exchange == 'bybit_api':
                    # 模擬Bybit API檢查
                    status.status = SystemStatus.HEALTHY
                    status.response_time = 200.0  # 200ms
                    status.error_count = 0
                elif exchange == 'okx_api':
                    # 模擬OKX API檢查
                    status.status = SystemStatus.HEALTHY
                    status.response_time = 180.0  # 180ms
                    status.error_count = 0
                    
            except Exception as e:
                logger.error(f"檢查{exchange}連接失敗: {e}")
                self.connection_status[exchange].status = SystemStatus.CRITICAL
    
    def _check_database_connection(self):
        """檢查數據庫連接"""
        try:
            status = self.connection_status['database']
            status.last_check = datetime.now(timezone.utc)
            
            # 檢查SQLite數據庫文件是否存在
            db_path = "db.sqlite3"
            if os.path.exists(db_path):
                # 嘗試讀取數據庫
                try:
                    import sqlite3
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                    conn.close()
                    
                    status.status = SystemStatus.HEALTHY
                    status.response_time = 50.0  # 50ms
                    status.error_count = 0
                    status.last_error = None
                    
                except Exception as e:
                    status.status = SystemStatus.CRITICAL
                    status.error_count += 1
                    status.last_error = f"數據庫讀取失敗: {e}"
            else:
                status.status = SystemStatus.OFFLINE
                status.error_count += 1
                status.last_error = "數據庫文件不存在"
                
        except Exception as e:
            logger.error(f"檢查數據庫連接失敗: {e}")
            self.connection_status['database'].status = SystemStatus.CRITICAL
    
    def record_error(self, error_type: str, error_message: str, 
                    severity: ErrorSeverity, component: str, 
                    context: Dict[str, Any] = None):
        """記錄錯誤"""
        try:
            error_record = ErrorRecord(
                timestamp=datetime.now(timezone.utc),
                error_type=error_type,
                error_message=error_message,
                severity=severity,
                component=component,
                stack_trace=traceback.format_exc(),
                context=context or {}
            )
            
            self.error_history.append(error_record)
            
            # 觸發錯誤回調
            self._trigger_error_callbacks(error_record)
            
            # 根據錯誤嚴重程度決定處理方式
            if severity == ErrorSeverity.CRITICAL:
                self._handle_critical_error(error_record)
            elif severity == ErrorSeverity.HIGH:
                self._handle_high_error(error_record)
            
            logger.error(f"錯誤記錄: {error_type} - {error_message} (嚴重程度: {severity.value})")
            
        except Exception as e:
            logger.error(f"記錄錯誤失敗: {e}")
    
    def _handle_critical_error(self, error_record: ErrorRecord):
        """處理嚴重錯誤"""
        logger.critical(f"檢測到嚴重錯誤: {error_record.error_type}")
        
        # 這裡可以實現自動恢復策略
        # 例如：重啟服務、切換備用系統等
        
        # 觸發人工干預
        self._trigger_manual_intervention(error_record)
    
    def _handle_high_error(self, error_record: ErrorRecord):
        """處理高級錯誤"""
        logger.warning(f"檢測到高級錯誤: {error_record.error_type}")
        
        # 嘗試自動恢復
        if self._can_auto_recover(error_record):
            self._attempt_auto_recovery(error_record)
    
    def _can_auto_recover(self, error_record: ErrorRecord) -> bool:
        """判斷是否可以自動恢復"""
        # 根據錯誤類型和組件判斷
        auto_recoverable_errors = [
            'connection_timeout',
            'api_rate_limit',
            'temporary_network_issue'
        ]
        
        return (error_record.error_type in auto_recoverable_errors and
                error_record.component in ['binance_api', 'bybit_api', 'okx_api'])
    
    def _attempt_auto_recovery(self, error_record: ErrorRecord):
        """嘗試自動恢復"""
        try:
            logger.info(f"嘗試自動恢復錯誤: {error_record.error_type}")
            
            # 實現具體的恢復邏輯
            if error_record.component.endswith('_api'):
                self._reconnect_exchange_api(error_record.component)
            
            # 標記錯誤為已解決
            error_record.resolved = True
            error_record.resolution_time = datetime.now(timezone.utc)
            error_record.resolution_method = "auto_recovery"
            
        except Exception as e:
            logger.error(f"自動恢復失敗: {e}")
    
    def _reconnect_exchange_api(self, component: str):
        """重連交易所API"""
        try:
            status = self.connection_status[component]
            status.status = SystemStatus.RECONNECTING
            
            logger.info(f"正在重連 {component}...")
            
            # 模擬重連過程
            time.sleep(2)
            
            # 重連成功
            status.status = SystemStatus.HEALTHY
            status.error_count = 0
            status.last_error = None
            
            logger.info(f"{component} 重連成功")
            
        except Exception as e:
            logger.error(f"重連 {component} 失敗: {e}")
            status.status = SystemStatus.CRITICAL
    
    def _trigger_manual_intervention(self, error_record: ErrorRecord):
        """觸發人工干預"""
        logger.critical(f"需要人工干預！錯誤: {error_record.error_type}")
        
        # 這裡可以實現通知機制
        # 例如：發送郵件、短信、Slack通知等
        
        # 記錄人工干預觸發
        error_record.context['manual_intervention_triggered'] = True
        error_record.context['intervention_time'] = datetime.now(timezone.utc).isoformat()
    
    def _trigger_health_callbacks(self, metrics: SystemMetrics):
        """觸發健康回調"""
        for callback in self.health_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"健康回調執行失敗: {e}")
    
    def _trigger_error_callbacks(self, error_record: ErrorRecord):
        """觸發錯誤回調"""
        for callback in self.error_callbacks:
            try:
                callback(error_record)
            except Exception as e:
                logger.error(f"錯誤回調執行失敗: {e}")
    
    def _cleanup_history(self):
        """清理歷史記錄"""
        # 清理系統指標歷史
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
        
        # 清理錯誤歷史（保留最近1000條）
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    def add_health_callback(self, callback: Callable):
        """添加健康監控回調"""
        self.health_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """添加錯誤處理回調"""
        self.error_callbacks.append(callback)
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態摘要"""
        try:
            latest_metrics = self.metrics_history[-1] if self.metrics_history else None
            latest_errors = self.error_history[-5:] if self.error_history else []  # 最近5個錯誤
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'system_status': latest_metrics.system_status.value if latest_metrics else 'UNKNOWN',
                'metrics': asdict(latest_metrics) if latest_metrics else {},
                'connections': {k: asdict(v) for k, v in self.connection_status.items()},
                'recent_errors': [asdict(error) for error in latest_errors],
                'error_summary': {
                    'total_errors': len(self.error_history),
                    'critical_errors': len([e for e in self.error_history if e.severity == ErrorSeverity.CRITICAL]),
                    'high_errors': len([e for e in self.error_history if e.severity == ErrorSeverity.HIGH]),
                    'unresolved_errors': len([e for e in self.error_history if not e.resolved])
                }
            }
        except Exception as e:
            logger.error(f"獲取系統狀態失敗: {e}")
            return {}
    
    def export_metrics(self, filepath: str):
        """導出監控指標到文件"""
        try:
            data = {
                'metrics_history': [asdict(m) for m in self.metrics_history],
                'error_history': [asdict(e) for e in self.error_history],
                'connection_status': {k: asdict(v) for k, v in self.connection_status.items()}
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"監控指標已導出到: {filepath}")
            
        except Exception as e:
            logger.error(f"導出監控指標失敗: {e}")

# 創建全局實例
system_monitor = SystemMonitor()

# 便捷函數
def start_system_monitoring():
    """便捷函數：啟動系統監控"""
    system_monitor.start_monitoring()

def stop_system_monitoring():
    """便捷函數：停止系統監控"""
    system_monitor.stop_monitoring()

def record_system_error(error_type: str, error_message: str, 
                       severity: ErrorSeverity, component: str, 
                       context: Dict[str, Any] = None):
    """便捷函數：記錄系統錯誤"""
    system_monitor.record_error(error_type, error_message, severity, component, context)

def get_system_status() -> Dict[str, Any]:
    """便捷函數：獲取系統狀態"""
    return system_monitor.get_system_status()
