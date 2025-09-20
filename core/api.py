# core/api.py
"""
稽核層API端點
提供稽核報告查詢和配置管理
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging
from datetime import datetime, timedelta


class AuditAPIView(View):
    """稽核API視圖"""
    
    def get(self, request):
        """獲取稽核報告"""
        try:
            # 獲取參數
            date = request.GET.get('date')
            if not date:
                date = datetime.now().strftime("%Y%m%d")
                
            # 這裡需要從全局獲取稽核整合實例
            # 在實際使用中，應該通過某種方式獲取到trader實例
            from core.audit_integration import AuditIntegration
            
            # 創建模擬交易器（實際使用中應該從全局獲取）
            class MockTrader:
                def get_config(self, key, default=None):
                    return default
                    
            trader = MockTrader()
            integration = AuditIntegration(trader)
            
            if not integration.is_enabled():
                return JsonResponse({"error": "稽核層未啟用"}, status=400)
                
            # 獲取稽核報告
            report = integration.get_audit_report(date)
            
            return JsonResponse({
                "success": True,
                "date": date,
                "report": report
            })
            
        except Exception as e:
            logging.error(f"獲取稽核報告失敗: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    
    def post(self, request):
        """更新稽核配置"""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'enable_audit':
                # 啟用稽核層
                # 這裡需要實際的配置更新邏輯
                return JsonResponse({"success": True, "message": "稽核層已啟用"})
                
            elif action == 'disable_audit':
                # 禁用稽核層
                return JsonResponse({"success": True, "message": "稽核層已禁用"})
                
            elif action == 'update_risk_rules':
                # 更新風控規則
                rules = data.get('rules', {})
                # 這裡需要實際的規則更新邏輯
                return JsonResponse({"success": True, "message": "風控規則已更新"})
                
            else:
                return JsonResponse({"error": "未知操作"}, status=400)
                
        except Exception as e:
            logging.error(f"更新稽核配置失敗: {e}")
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AuditConfigAPIView(View):
    """稽核配置API視圖"""
    
    def get(self, request):
        """獲取稽核配置"""
        try:
            # 這裡應該從數據庫獲取實際配置
            config = {
                "audit_enabled": True,
                "risk_rules": {
                    "leverage_cap": 2.0,
                    "dist_to_liq_min": 15.0,
                    "daily_max_loss": 3.0,
                    "consecutive_loss_cooldown": 3,
                    "max_slippage_bps": 5.0
                },
                "explain_templates": ["trend_atr_v2", "range_revert_v1"],
                "logging": {
                    "log_dir": "data/audit",
                    "batch_seconds": 2,
                    "batch_size": 100
                }
            }
            
            return JsonResponse({
                "success": True,
                "config": config
            })
            
        except Exception as e:
            logging.error(f"獲取稽核配置失敗: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    
    def post(self, request):
        """更新稽核配置"""
        try:
            data = json.loads(request.body)
            
            # 這裡應該實際更新數據庫配置
            # 目前只是返回成功響應
            
            return JsonResponse({
                "success": True,
                "message": "配置已更新",
                "updated_config": data
            })
            
        except Exception as e:
            logging.error(f"更新稽核配置失敗: {e}")
            return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def audit_events_api(request):
    """獲取稽核事件API"""
    try:
        date = request.GET.get('date')
        event_type = request.GET.get('event_type')
        symbol = request.GET.get('symbol')
        
        if not date:
            date = datetime.now().strftime("%Y%m%d")
            
        # 這裡應該從稽核日誌中獲取事件
        # 目前返回模擬數據
        events = [
            {
                "event_type": "signal_generated",
                "timestamp": datetime.now().isoformat(),
                "symbol": "BTCUSDT",
                "side": "long",
                "confidence": 0.8
            },
            {
                "event_type": "risk_checked",
                "timestamp": datetime.now().isoformat(),
                "symbol": "BTCUSDT",
                "passed": True,
                "risk_level": "NORMAL"
            }
        ]
        
        # 根據參數過濾
        if event_type:
            events = [e for e in events if e.get('event_type') == event_type]
        if symbol:
            events = [e for e in events if e.get('symbol') == symbol]
            
        return JsonResponse({
            "success": True,
            "date": date,
            "events": events,
            "total": len(events)
        })
        
    except Exception as e:
        logging.error(f"獲取稽核事件失敗: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def audit_dashboard_api(request):
    """稽核儀表板API"""
    try:
        # 獲取今日統計
        today = datetime.now().strftime("%Y%m%d")
        
        # 這裡應該從實際數據計算
        dashboard_data = {
            "date": today,
            "summary": {
                "total_events": 150,
                "signal_events": 50,
                "risk_events": 50,
                "explain_events": 50,
                "order_events": 25
            },
            "risk_analysis": {
                "total_checks": 50,
                "passed": 45,
                "rejected": 5,
                "pass_rate": 90.0
            },
            "order_analysis": {
                "submitted": 25,
                "filled": 20,
                "rejected": 5,
                "fill_rate": 80.0
            },
            "recent_events": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "event_type": "signal_generated",
                    "symbol": "BTCUSDT",
                    "side": "long",
                    "confidence": 0.8
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "event_type": "risk_checked",
                    "symbol": "BTCUSDT",
                    "passed": True,
                    "risk_level": "NORMAL"
                }
            ]
        }
        
        return JsonResponse({
            "success": True,
            "dashboard": dashboard_data
        })
        
    except Exception as e:
        logging.error(f"獲取稽核儀表板失敗: {e}")
        return JsonResponse({"error": str(e)}, status=500)
