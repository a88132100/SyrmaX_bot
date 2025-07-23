import json
from django.core.management.base import BaseCommand
from combos.models import Combo
from django.utils.dateparse import parse_datetime

class Command(BaseCommand):
    help = '將 combos.generated.json 的所有資料匯入 Combo model，若名稱重複則更新，否則新增。'

    def handle(self, *args, **options):
        with open('combos.generated.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            combo, created = Combo.objects.update_or_create(
                name=item['name'],
                defaults={
                    'description': item.get('description', ''),
                    'conditions': item.get('conditions', []),
                    'is_active': item.get('is_active', False),
                    'combo_mode': item.get('combo_mode', ''),
                    'created_at': parse_datetime(item.get('created_at')) if item.get('created_at') else None,
                    'updated_at': parse_datetime(item.get('updated_at')) if item.get('updated_at') else None,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'已新增：{combo.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'已更新：{combo.name}'))
        self.stdout.write(self.style.SUCCESS('combos.generated.json 匯入完成！')) 