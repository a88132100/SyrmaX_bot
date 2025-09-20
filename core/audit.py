# core/audit.py
"""
稽核日誌系統
實現JSONL日誌記錄和SQLite批次寫入
"""

import json
import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import threading
import queue
import time

from .events import BaseEvent, EventType


class AuditLogger:
    """稽核日誌記錄器"""
    
    def __init__(self, audit_dir: str = "data/audit", batch_seconds: int = 2, batch_size: int = 100):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        self.batch_seconds = batch_seconds
        self.batch_size = batch_size
        
        # 記憶體佇列
        self.event_queue = queue.Queue(maxsize=1000)
        
        # SQLite資料庫路徑
        self.db_path = self.audit_dir / "audit.db"
        
        # 初始化資料庫
        self._init_database()
        
        # 啟動批次寫入線程
        self.batch_thread = threading.Thread(target=self._batch_writer, daemon=True)
        self.running = True
        self.batch_thread.start()
        
        logging.info("稽核日誌系統已啟動")
        
    def _init_database(self):
        """初始化SQLite資料庫"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 創建事件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    account_id TEXT,
                    venue TEXT,
                    symbol TEXT,
                    strategy_id TEXT,
                    idempotency_key TEXT,
                    data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建風控檢查表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risk_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    passed BOOLEAN NOT NULL,
                    blocked_rules TEXT,
                    details TEXT,
                    risk_level TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建解釋表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS explanations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    template_used TEXT,
                    explanation TEXT,
                    quality TEXT,
                    word_count INTEGER,
                    confidence_score REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建訂單表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    order_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL,
                    price REAL,
                    status TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
            logging.info("稽核資料庫初始化完成")
            
        except Exception as e:
            logging.error(f"初始化稽核資料庫失敗: {e}")
            
    def log_event(self, event: BaseEvent):
        """記錄事件到佇列"""
        try:
            # 轉換為字典
            event_dict = event.dict()
            if hasattr(event.event_type, 'value'):
                event_dict['event_type'] = event.event_type.value
            else:
                event_dict['event_type'] = str(event.event_type)
            
            # 加入佇列
            self.event_queue.put(event_dict, timeout=1)
            
        except queue.Full:
            logging.warning("稽核事件佇列已滿，丟棄事件")
        except Exception as e:
            logging.error(f"記錄稽核事件失敗: {e}")
            
    def _batch_writer(self):
        """批次寫入線程"""
        batch = []
        last_write = time.time()
        
        while self.running:
            try:
                # 從佇列獲取事件
                try:
                    event = self.event_queue.get(timeout=1)
                    batch.append(event)
                except queue.Empty:
                    pass
                
                current_time = time.time()
                
                # 檢查是否需要寫入
                should_write = (
                    len(batch) >= self.batch_size or
                    (batch and current_time - last_write >= self.batch_seconds)
                )
                
                if should_write:
                    self._write_batch(batch)
                    batch = []
                    last_write = current_time
                    
            except Exception as e:
                logging.error(f"批次寫入線程錯誤: {e}")
                time.sleep(1)
                
    def _write_batch(self, batch: List[Dict[str, Any]]):
        """寫入批次事件"""
        if not batch:
            return
            
        try:
            # 寫入JSONL文件
            self._write_jsonl(batch)
            
            # 寫入SQLite資料庫
            self._write_sqlite(batch)
            
            logging.debug(f"批次寫入完成，事件數量: {len(batch)}")
            
        except Exception as e:
            logging.error(f"批次寫入失敗: {e}")
            
    def _write_jsonl(self, batch: List[Dict[str, Any]]):
        """寫入JSONL文件"""
        try:
            # 按日期分文件
            today = datetime.now().strftime("%Y%m%d")
            jsonl_file = self.audit_dir / f"{today}.jsonl"
            
            with open(jsonl_file, 'a', encoding='utf-8') as f:
                for event in batch:
                    # 處理datetime序列化
                    serializable_event = self._make_serializable(event)
                    f.write(json.dumps(serializable_event, ensure_ascii=False, default=str) + '\n')
                    
        except Exception as e:
            logging.error(f"寫入JSONL文件失敗: {e}")
            
    def _make_serializable(self, obj):
        """將對象轉換為可序列化格式"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif hasattr(obj, 'isoformat'):  # datetime對象
            return obj.isoformat()
        else:
            return obj
            
    def _write_sqlite(self, batch: List[Dict[str, Any]]):
        """寫入SQLite資料庫"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for event in batch:
                # 插入事件記錄
                cursor.execute("""
                    INSERT INTO events (event_type, timestamp, account_id, venue, symbol, 
                                     strategy_id, idempotency_key, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.get('event_type'),
                    event.get('ts'),
                    event.get('account_id'),
                    event.get('venue'),
                    event.get('symbol'),
                    event.get('strategy_id'),
                    event.get('idempotency_key'),
                    json.dumps(self._make_serializable(event), ensure_ascii=False, default=str)
                ))
                
                # 根據事件類型插入專門表
                event_type = event.get('event_type')
                
                if event_type == EventType.RISK_CHECKED.value:
                    risk_data = event.get('risk_result', {})
                    cursor.execute("""
                        INSERT INTO risk_checks (timestamp, symbol, passed, blocked_rules, 
                                               details, risk_level)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        event.get('ts'),
                        event.get('symbol'),
                        risk_data.get('passed', False),
                        json.dumps(risk_data.get('blocked_rules', [])),
                        risk_data.get('details', ''),
                        risk_data.get('risk_level', 'NORMAL')
                    ))
                    
                elif event_type == EventType.EXPLAIN_CREATED.value:
                    cursor.execute("""
                        INSERT INTO explanations (timestamp, symbol, template_used, explanation,
                                                quality, word_count, confidence_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event.get('ts'),
                        event.get('symbol'),
                        event.get('template_used'),
                        json.dumps(event.get('explanation', [])),
                        event.get('explanation_quality'),
                        event.get('word_count', 0),
                        event.get('confidence_score', 0.0)
                    ))
                    
                elif event_type in [EventType.ORDER_SUBMITTED.value, EventType.ORDER_FILLED.value]:
                    cursor.execute("""
                        INSERT INTO orders (timestamp, order_id, symbol, side, quantity, 
                                          price, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event.get('ts'),
                        event.get('order_id'),
                        event.get('symbol'),
                        event.get('side'),
                        event.get('quantity', 0.0),
                        event.get('price', 0.0),
                        event_type
                    ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"寫入SQLite資料庫失敗: {e}")
            
    def get_events_by_date(self, date: str) -> List[Dict[str, Any]]:
        """根據日期獲取事件"""
        try:
            jsonl_file = self.audit_dir / f"{date}.jsonl"
            if not jsonl_file.exists():
                return []
                
            events = []
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
                        
            return events
            
        except Exception as e:
            logging.error(f"讀取事件失敗: {e}")
            return []
            
    def get_risk_checks_by_date(self, date: str) -> List[Dict[str, Any]]:
        """根據日期獲取風控檢查記錄"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM risk_checks 
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp DESC
            """, (date,))
            
            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return results
            
        except Exception as e:
            logging.error(f"讀取風控檢查記錄失敗: {e}")
            return []
            
    def get_explanations_by_date(self, date: str) -> List[Dict[str, Any]]:
        """根據日期獲取解釋記錄"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM explanations 
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp DESC
            """, (date,))
            
            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return results
            
        except Exception as e:
            logging.error(f"讀取解釋記錄失敗: {e}")
            return []
            
    def generate_daily_report(self, date: str) -> Dict[str, Any]:
        """生成日報表"""
        try:
            # 獲取當日事件
            events = self.get_events_by_date(date)
            
            # 統計信息
            total_events = len(events)
            signal_events = [e for e in events if e.get('event_type') == EventType.SIGNAL_GENERATED.value]
            risk_events = [e for e in events if e.get('event_type') == EventType.RISK_CHECKED.value]
            explain_events = [e for e in events if e.get('event_type') == EventType.EXPLAIN_CREATED.value]
            order_events = [e for e in events if e.get('event_type') in [EventType.ORDER_SUBMITTED.value, EventType.ORDER_FILLED.value]]
            
            # 風控統計
            risk_passed = len([e for e in risk_events if e.get('risk_result', {}).get('passed', False)])
            risk_rejected = len(risk_events) - risk_passed
            
            # 訂單統計
            orders_submitted = len([e for e in order_events if e.get('event_type') == EventType.ORDER_SUBMITTED.value])
            orders_filled = len([e for e in order_events if e.get('event_type') == EventType.ORDER_FILLED.value])
            
            report = {
                'date': date,
                'summary': {
                    'total_events': total_events,
                    'signal_events': len(signal_events),
                    'risk_events': len(risk_events),
                    'explain_events': len(explain_events),
                    'order_events': len(order_events)
                },
                'risk_analysis': {
                    'total_checks': len(risk_events),
                    'passed': risk_passed,
                    'rejected': risk_rejected,
                    'pass_rate': risk_passed / len(risk_events) * 100 if risk_events else 0
                },
                'order_analysis': {
                    'submitted': orders_submitted,
                    'filled': orders_filled,
                    'fill_rate': orders_filled / orders_submitted * 100 if orders_submitted else 0
                },
                'events': events
            }
            
            return report
            
        except Exception as e:
            logging.error(f"生成日報表失敗: {e}")
            return {}
            
    def stop(self):
        """停止稽核日誌系統"""
        self.running = False
        if self.batch_thread.is_alive():
            self.batch_thread.join(timeout=5)
        logging.info("稽核日誌系統已停止")
