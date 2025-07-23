from django.core.management.base import BaseCommand
from trading_api.models import StrategyCombo
import json
from django.core.serializers.json import DjangoJSONEncoder

class Command(BaseCommand):
    help = '將所有策略組合（StrategyCombo）匯出成 combos.generated.json 檔案'

    def handle(self, *args, **options):
        # 取得所有策略組合
        combos = StrategyCombo.objects.all()
        # 將每個策略組合轉成 dict
        data = []
        for combo in combos:
            data.append({
                'name': combo.name,
                'description': combo.description,
                'conditions': combo.conditions,
                'is_active': combo.is_active,
                'combo_mode': combo.combo_mode,
                'created_at': combo.created_at.isoformat() if combo.created_at else None,
                'updated_at': combo.updated_at.isoformat() if combo.updated_at else None,
            })
        # 匯出成 JSON 檔案
        with open('combos.generated.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder)
        self.stdout.write(self.style.SUCCESS('已成功匯出所有策略組合到 combos.generated.json')) 