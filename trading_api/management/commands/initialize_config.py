import json
from django.core.management.base import BaseCommand
from trading_api.models import TraderConfig
from trading.constants import DEFAULT_CONFIG

class Command(BaseCommand):
    help = '初始化所有配置，確保與舊的 config.py 完全對應'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('正在初始化所有配置...'))

        # 配置描述
        config_descriptions = {
            # 交易所配置
            'EXCHANGE': '交易所類型 (CCXT/BINANCE/BYBIT/OKX/BINGX/BITGET)',
            'EXCHANGE_NAME': '具體交易所名稱',
            'USE_TESTNET': '是否使用測試網 (True/False)',
            'TEST_MODE': '是否啟用模擬交易模式 (不會真實下單)',
            
            # 交易對配置
            'SYMBOLS': '要交易的幣種列表 (JSON 格式)',
            
            # 槓桿配置
            'LEVERAGE': '所有交易對的統一槓桿倍數',
            
            # 資金管理配置
            'BASE_POSITION_RATIO': '基礎資金比例',
            'MIN_POSITION_RATIO': '最小資金比例',
            'MAX_POSITION_RATIO': '最大資金比例',
            
            # 止盈止損配置
            'EXIT_MODE': '止盈止損模式 (PERCENTAGE/AMOUNT/ATR/HYBRID)',
            'PRICE_TAKE_PROFIT_PERCENT': '止盈百分比（例如：20.0 表示 20%）',
            'PRICE_STOP_LOSS_PERCENT': '止損百分比（例如：1.0 表示 1%）',
            'AMOUNT_TAKE_PROFIT_USDT': '止盈金額（USDT）',
            'AMOUNT_STOP_LOSS_USDT': '止損金額（USDT）',
            'ATR_TAKE_PROFIT_MULTIPLIER': 'ATR 止盈倍數',
            'ATR_STOP_LOSS_MULTIPLIER': 'ATR 止損倍數',
            'HYBRID_MIN_TAKE_PROFIT_USDT': '混合模式：最小止盈金額',
            'HYBRID_MAX_TAKE_PROFIT_USDT': '混合模式：最大止盈金額',
            'HYBRID_MIN_STOP_LOSS_USDT': '混合模式：最小止損金額',
            'HYBRID_MAX_STOP_LOSS_USDT': '混合模式：最大止損金額',
            
            # 風控配置
            'MAX_CONSECUTIVE_STOP_LOSS': '最大連續止損次數',
            'ENABLE_TRADE_LOG': '是否啟用交易日誌',
            'ENABLE_TRADE_LIMITS': '是否啟用每日/每小時開倉次數限制',
            'MAX_TRADES_PER_HOUR': '每小時最大開倉次數',
            'MAX_TRADES_PER_DAY': '每日最大開倉次數',
            'MAX_DAILY_LOSS_PERCENT': '每日最大虧損百分比',
            
            # 系統配置
            'GLOBAL_INTERVAL_SECONDS': '每次交易循環的間隔秒數',
            
            # 精度配置
            'SYMBOL_PRECISION': '每個交易對的數量精度 (JSON 格式)',
            'SYMBOL_INTERVALS': '每個交易對使用的 K 線時間週期 (JSON 格式)',
            'SYMBOL_INTERVAL_SECONDS': '每個幣種的交易判斷頻率（單位：秒）(JSON 格式)',
        }

        # 處理每個配置
        for key, value in DEFAULT_CONFIG.items():
            # 將非字串、非數字的值（如列表、字典、布林值）轉換為字串
            if isinstance(value, (list, dict)):
                value_str = json.dumps(value)
                value_type = 'list' if isinstance(value, list) else 'dict'
            elif isinstance(value, bool):
                value_str = str(value)
                value_type = 'bool'
            elif isinstance(value, int):
                value_str = str(value)
                value_type = 'int'
            elif isinstance(value, float):
                value_str = str(value)
                value_type = 'float'
            else:
                value_str = str(value)
                value_type = 'str'

            description = config_descriptions.get(key, f'{key} 配置')

            obj, created = TraderConfig.objects.update_or_create(
                key=key,
                defaults={
                    'value': value_str,
                    'value_type': value_type,
                    'description': description
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ 新增配置: {key} = {value_str}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'🔄 更新配置: {key} = {value_str}'))

        self.stdout.write(self.style.SUCCESS('🎉 所有配置初始化完成！'))
        self.stdout.write(self.style.WARNING('⚠️  請記得設定您的 API 金鑰：'))
        self.stdout.write(self.style.WARNING('   - SYRMAX_API_KEY'))
        self.stdout.write(self.style.WARNING('   - SYRMAX_API_SECRET'))
        self.stdout.write(self.style.WARNING('   - SYRMAX_EXCHANGE'))
        self.stdout.write(self.style.WARNING('   - SYRMAX_EXCHANGE_NAME'))
