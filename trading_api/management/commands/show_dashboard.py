import json
from django.core.management.base import BaseCommand
from django.apps import apps

# Ensure Django is set up if it's not already
if not apps.ready:
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syrmax_api.settings')
    import django
    django.setup()

from trading.monitoring_dashboard import get_dashboard_summary

class Command(BaseCommand):
    help = '顯示 SyrmaX 監控儀表板摘要'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='輸出格式 (text 或 json)'
        )
        parser.add_argument(
            '--export',
            type=str,
            help='導出數據到指定文件'
        )

    def handle(self, *args, **options):
        try:
            summary = get_dashboard_summary()
            
            if options['export']:
                # 導出到文件
                with open(options['export'], 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
                self.stdout.write(
                    self.style.SUCCESS(f'監控數據已導出到: {options["export"]}')
                )
            
            if options['format'] == 'json':
                # JSON 格式輸出
                self.stdout.write(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
            else:
                # 文本格式輸出
                self._display_text_summary(summary)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'獲取監控數據失敗: {e}')
            )

    def _display_text_summary(self, summary):
        """以文本格式顯示監控摘要"""
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('SyrmaX 監控儀表板摘要'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # 系統健康狀態
        system_health = summary.get('system_health', {})
        self.stdout.write(f"\n📊 系統健康狀態:")
        self.stdout.write(f"   整體評分: {system_health.get('overall_score', 0):.1f}/100")
        self.stdout.write(f"   狀態: {system_health.get('status', 'UNKNOWN')}")
        
        # 組件評分
        component_scores = system_health.get('component_scores', {})
        if component_scores:
            self.stdout.write(f"   組件評分:")
            for component, score in component_scores.items():
                self.stdout.write(f"     {component}: {score:.1f}/100")
        
        # 建議
        recommendations = system_health.get('recommendations', [])
        if recommendations:
            self.stdout.write(f"   建議:")
            for rec in recommendations:
                self.stdout.write(f"     • {rec}")
        
        # 當前指標
        current_metrics = summary.get('current_metrics', {}).get('metrics', {})
        if current_metrics:
            self.stdout.write(f"\n📈 當前指標:")
            for metric, value in current_metrics.items():
                self.stdout.write(f"   {metric}: {value:.2f}")
        
        # 告警摘要
        alert_summary = summary.get('alert_summary', {})
        self.stdout.write(f"\n🚨 告警摘要:")
        self.stdout.write(f"   活躍告警: {alert_summary.get('active_alerts_count', 0)}")
        self.stdout.write(f"   告警歷史: {alert_summary.get('alert_history_count', 0)}")
        self.stdout.write(f"   告警規則: {alert_summary.get('alert_rules_count', 0)}")
        
        # 活躍告警詳情
        active_alerts = alert_summary.get('active_alerts', [])
        if active_alerts:
            self.stdout.write(f"   活躍告警詳情:")
            for alert in active_alerts:
                self.stdout.write(f"     • {alert.get('message', 'N/A')} (級別: {alert.get('alert_level', 'N/A')})")
        
        # 性能分析
        performance_analysis = summary.get('performance_analysis', {})
        if performance_analysis:
            self.stdout.write(f"\n📊 性能分析:")
            trend_analysis = performance_analysis.get('trend_analysis', {})
            for metric, analysis in trend_analysis.items():
                self.stdout.write(f"   {metric}:")
                self.stdout.write(f"     當前值: {analysis.get('current', 0):.2f}")
                self.stdout.write(f"     平均值: {analysis.get('average', 0):.2f}")
                self.stdout.write(f"     趨勢: {analysis.get('trend', 'UNKNOWN')}")
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
