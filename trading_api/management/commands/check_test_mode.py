from django.core.management.base import BaseCommand
from trading_api.models import TraderConfig

class Command(BaseCommand):
    help = '檢查 TEST_MODE 配置'

    def handle(self, *args, **options):
        self.stdout.write("=== 檢查 TEST_MODE 配置 ===")
        
        # 檢查 TEST_MODE 配置
        test_mode_config = TraderConfig.objects.filter(key='TEST_MODE').first()
        if test_mode_config:
            self.stdout.write(f"TEST_MODE 配置值: {test_mode_config.value}")
            self.stdout.write(f"配置類型: {test_mode_config.value_type}")
            self.stdout.write(f"描述: {test_mode_config.description}")
            
            # 轉換為布林值
            if test_mode_config.value_type == 'bool':
                bool_value = test_mode_config.value.lower() == 'true'
                self.stdout.write(f"布林值: {bool_value}")
            else:
                self.stdout.write("⚠️ 配置類型不是 bool，可能導致問題")
        else:
            self.stdout.write("❌ TEST_MODE 配置不存在")
            
        # 檢查所有相關配置
        self.stdout.write("\n=== 所有相關配置 ===")
        related_configs = TraderConfig.objects.filter(key__icontains='TEST')
        for config in related_configs:
            self.stdout.write(f"{config.key}: {config.value} ({config.value_type})")
