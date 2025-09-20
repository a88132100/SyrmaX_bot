from django.core.management.base import BaseCommand
from trading_api.models import TraderStatus
from django.utils import timezone

class Command(BaseCommand):
    help = '重置交易次數限制'

    def handle(self, *args, **options):
        self.stdout.write("=== 重置交易次數限制 ===")
        
        try:
            # 獲取交易器狀態
            trader_status = TraderStatus.objects.get(pk=1)
            
            # 重置交易次數
            trader_status.hourly_trade_count = 0
            trader_status.daily_trade_count = 0
            trader_status.last_hourly_reset = timezone.now()
            trader_status.last_daily_reset_date = timezone.localdate()
            trader_status.save()
            
            self.stdout.write("✅ 交易次數已重置")
            self.stdout.write(f"每小時交易次數: {trader_status.hourly_trade_count}")
            self.stdout.write(f"每日交易次數: {trader_status.daily_trade_count}")
            
        except TraderStatus.DoesNotExist:
            self.stdout.write("❌ TraderStatus 記錄不存在")
        except Exception as e:
            self.stdout.write(f"❌ 重置失敗: {e}")
