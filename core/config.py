# core/config.py
"""
稽核層配置管理
擴展現有TraderConfig系統
"""

from typing import Dict, Any
import logging


class AuditConfig:
    """稽核層配置管理"""
    
    def __init__(self, trader):
        self.trader = trader
        self._setup_default_configs()
        
    def _setup_default_configs(self):
        """設置預設稽核配置"""
        default_configs = {
            # 稽核層開關
            'AUDIT_ENABLED': ('true', 'bool', '是否啟用稽核層'),
            
            # 風控規則配置
            'AUDIT_LEVERAGE_CAP': ('2.0', 'float', '稽核層槓桿上限'),
            'AUDIT_DIST_TO_LIQ_MIN': ('15.0', 'float', '距爆倉最小距離百分比'),
            'AUDIT_DAILY_MAX_LOSS': ('3.0', 'float', '單日最大虧損百分比'),
            'AUDIT_CONSECUTIVE_LOSS_COOLDOWN': ('3', 'int', '連續虧損冷卻次數'),
            'AUDIT_MAX_SLIPPAGE_BPS': ('5.0', 'float', '最大滑點限制(bps)'),
            
            # 解釋模板配置
            'AUDIT_EXPLAIN_TEMPLATES': ('["trend_atr_v2", "range_revert_v1"]', 'list', '啟用的解釋模板'),
            'AUDIT_EXPLAIN_QUALITY_THRESHOLD': ('NORMAL', 'str', '解釋品質閾值'),
            
            # 日誌配置
            'AUDIT_LOG_DIR': ('data/audit', 'str', '稽核日誌目錄'),
            'AUDIT_BATCH_SECONDS': ('2', 'int', '批次寫入間隔(秒)'),
            'AUDIT_BATCH_SIZE': ('100', 'int', '批次寫入大小'),
            
            # 性能配置
            'AUDIT_MAX_QUEUE_SIZE': ('1000', 'int', '最大佇列大小'),
            'AUDIT_TIMEOUT_SECONDS': ('5', 'int', '稽核檢查超時時間'),
        }
        
        # 檢查並創建配置
        for key, (value, value_type, description) in default_configs.items():
            try:
                existing_config = self.trader.get_config(key)
                if existing_config is None:
                    # 配置不存在，創建預設配置
                    self._create_config(key, value, value_type, description)
                    logging.info(f"創建稽核配置: {key} = {value}")
            except Exception as e:
                logging.error(f"檢查稽核配置 {key} 失敗: {e}")
                
    def _create_config(self, key: str, value: str, value_type: str, description: str):
        """創建配置項"""
        try:
            from trading_api.models import TraderConfig
            
            TraderConfig.objects.create(
                key=key,
                value=value,
                value_type=value_type,
                description=description
            )
        except Exception as e:
            logging.error(f"創建配置 {key} 失敗: {e}")
            
    def get_audit_config(self, key: str, default=None):
        """獲取稽核配置"""
        return self.trader.get_config(key, default=default)
        
    def update_audit_config(self, key: str, value: Any):
        """更新稽核配置"""
        try:
            from trading_api.models import TraderConfig
            
            config = TraderConfig.objects.get(key=key)
            config.value = str(value)
            config.save()
            
            # 更新緩存
            self.trader.configs[key] = value
            
            logging.info(f"更新稽核配置: {key} = {value}")
            
        except TraderConfig.DoesNotExist:
            logging.error(f"配置 {key} 不存在")
        except Exception as e:
            logging.error(f"更新配置 {key} 失敗: {e}")
            
    def get_risk_rules_config(self) -> Dict[str, Any]:
        """獲取風控規則配置"""
        return {
            'leverage_cap': self.get_audit_config('AUDIT_LEVERAGE_CAP', 2.0),
            'dist_to_liq_min': self.get_audit_config('AUDIT_DIST_TO_LIQ_MIN', 15.0),
            'daily_max_loss': self.get_audit_config('AUDIT_DAILY_MAX_LOSS', 3.0),
            'consecutive_loss_cooldown': self.get_audit_config('AUDIT_CONSECUTIVE_LOSS_COOLDOWN', 3),
            'max_slippage_bps': self.get_audit_config('AUDIT_MAX_SLIPPAGE_BPS', 5.0)
        }
        
    def get_explain_config(self) -> Dict[str, Any]:
        """獲取解釋配置"""
        return {
            'templates': self.get_audit_config('AUDIT_EXPLAIN_TEMPLATES', ["trend_atr_v2", "range_revert_v1"]),
            'quality_threshold': self.get_audit_config('AUDIT_EXPLAIN_QUALITY_THRESHOLD', 'NORMAL')
        }
        
    def get_logging_config(self) -> Dict[str, Any]:
        """獲取日誌配置"""
        return {
            'log_dir': self.get_audit_config('AUDIT_LOG_DIR', 'data/audit'),
            'batch_seconds': self.get_audit_config('AUDIT_BATCH_SECONDS', 2),
            'batch_size': self.get_audit_config('AUDIT_BATCH_SIZE', 100)
        }
        
    def get_performance_config(self) -> Dict[str, Any]:
        """獲取性能配置"""
        return {
            'max_queue_size': self.get_audit_config('AUDIT_MAX_QUEUE_SIZE', 1000),
            'timeout_seconds': self.get_audit_config('AUDIT_TIMEOUT_SECONDS', 5)
        }
        
    def is_audit_enabled(self) -> bool:
        """檢查稽核層是否啟用"""
        return self.get_audit_config('AUDIT_ENABLED', True)
        
    def enable_audit(self):
        """啟用稽核層"""
        self.update_audit_config('AUDIT_ENABLED', True)
        
    def disable_audit(self):
        """禁用稽核層"""
        self.update_audit_config('AUDIT_ENABLED', False)
