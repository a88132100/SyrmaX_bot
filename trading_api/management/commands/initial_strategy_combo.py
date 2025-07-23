from django.core.management.base import BaseCommand
from trading_api.models import StrategyCombo

class Command(BaseCommand):
    help = '自動建立五個預設策略組合（aggressive, balanced, conservative, auto, custom）'

    def handle(self, *args, **options):
        combos = [
            {
                'name': '激進策略組合',
                'description': '追求高報酬，風險較高，適合進取型投資人',
                'combo_mode': 'aggressive',
                'is_active': False,
                'conditions': [],
            },
            {
                'name': '平衡策略組合',
                'description': '風險與報酬平衡，適合大多數用戶',
                'combo_mode': 'balanced',
                'is_active': True,  # 預設啟用
                'conditions': [],
            },
            {
                'name': '保守策略組合',
                'description': '低風險，適合保守型投資人',
                'combo_mode': 'conservative',
                'is_active': False,
                'conditions': [],
            },
            {
                'name': '自動判斷組合',
                'description': '系統自動根據行情選擇最佳模式',
                'combo_mode': 'auto',
                'is_active': False,
                'conditions': [],
            },
            {
                'name': '自定義組合',
                'description': '用戶可自定義條件，靈活調整策略',
                'combo_mode': 'custom',
                'is_active': False,
                'conditions': [{"type": "example", "value": 1}],
            },
        ]

        for combo in combos:
            obj, created = StrategyCombo.objects.update_or_create(
                name=combo['name'],
                defaults={
                    'description': combo['description'],
                    'combo_mode': combo['combo_mode'],
                    'is_active': combo['is_active'],
                    'conditions': combo['conditions'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"已建立：{combo['name']}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"已更新：{combo['name']}"))
        self.stdout.write(self.style.SUCCESS('✅ 預設策略組合建立完成！')) 