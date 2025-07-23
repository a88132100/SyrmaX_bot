import time
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps

# Ensure Django is set up if it's not already
if not apps.ready:
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syrmax_api.settings') # 替換為您的 Django 專案 settings
    import django
    django.setup()

from trading.trader import MultiSymbolTrader
from trading_api.models import TraderStatus # 導入 TraderStatus 模型

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '運行 SyrmaX 自動交易機器人'

    def handle(self, *args, **options):
        logger.info("SyrmaX 交易機器人啟動中...")

        # 確保 TraderStatus 存在
        trader_status, created = TraderStatus.objects.get_or_create(pk=1)
        if created:
            logger.info("TraderStatus 記錄已創建。")
        
        # 檢查是否已收到停止信號
        if trader_status.stop_signal_received:
            logger.warning("檢測到停止信號，機器人將不會啟動。請通過管理後台或 API 重置狀態。")
            return

        # 設置 stop_signal_received 為 False，因為機器人即將啟動
        trader_status.stop_signal_received = False
        trader_status.save()

        trader = MultiSymbolTrader()
        logger.info("MultiSymbolTrader 初始化完成。")

        try:
            while not trader_status.stop_signal_received:
                trader.run_trading_cycle()
                # 從數據庫獲取全局的 interval_seconds
                global_interval_seconds = trader.get_config('GLOBAL_INTERVAL_SECONDS', type=int, default=3)
                time.sleep(global_interval_seconds)
                # 每次循環重新載入狀態，以響應外部的停止信號
                trader_status.refresh_from_db()

        except KeyboardInterrupt:
            logger.info("機器人收到停止指令 (KeyboardInterrupt)，正在關閉...")
        except Exception as e:
            logger.critical(f"機器人運行時發生致命錯誤: {e}", exc_info=True)
        finally:
            logger.info("SyrmaX 交易機器人已關閉。") 