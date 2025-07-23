import json
from django.core.management.base import BaseCommand, CommandError
from trading_api.models import TraderConfig
import config # 導入你的 config.py 文件

class Command(BaseCommand):
    help = 'Imports configuration settings from config.py into the TraderConfig model.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('正在從 config.py 導入配置到 TraderConfig 模型...'))

        # 配置 key 對應的中文描述
        config_descriptions = {
            'USE_TESTNET': '是否使用測試網 (True/False)',
            'API_KEY': '交易所 API Key (請務必修改)',
            'API_SECRET': '交易所 API Secret (請務必修改)',
            'SYMBOLS': '要交易的幣種列表 (JSON 格式)',
            'TEST_MODE': '是否啟用模擬交易模式 (不會真實下單)',
            'LEVERAGE': '所有交易對的統一槓桿倍數',
            'EXIT_MODE': '止盈止損模式 (PERCENTAGE/AMOUNT/ATR/HYBRID)',
            'AMOUNT_TAKE_PROFIT_USDT': '止盈金額（USDT）',
            'AMOUNT_STOP_LOSS_USDT': '止損金額（USDT）',
            'MAX_CONSECUTIVE_STOP_LOSS': '最大連續止損次數',
            'ENABLE_TRADE_LOG': '是否啟用交易日誌',
            'SYMBOL_INTERVALS': '每個交易對使用的 K 線時間週期 (JSON 格式)',
            'SYMBOL_INTERVAL_SECONDS': '每個幣種的交易判斷頻率（單位：秒）',
            'BASE_POSITION_RATIO': '基礎資金比例',
            'MIN_POSITION_RATIO': '最小資金比例',
            'MAX_POSITION_RATIO': '最大資金比例',
            'PRICE_TAKE_PROFIT_PERCENT': '止盈百分比（例如：20.0 表示 20%）',
            'PRICE_STOP_LOSS_PERCENT': '止損百分比（例如：1.0 表示 1%）',
            'ATR_TAKE_PROFIT_MULTIPLIER': 'ATR 止盈倍數',
            'ATR_STOP_LOSS_MULTIPLIER': 'ATR 止損倍數',
            'HYBRID_MIN_TAKE_PROFIT_USDT': '混合模式：最小止盈金額',
            'HYBRID_MAX_TAKE_PROFIT_USDT': '混合模式：最大止盈金額',
            'HYBRID_MIN_STOP_LOSS_USDT': '混合模式：最小止損金額',
            'HYBRID_MAX_STOP_LOSS_USDT': '混合模式：最大止損金額',
            'EXCHANGE_NAME': '目標交易所的 CCXT ID (例如: binance, bybit, okx)',
            'MAX_DAILY_LOSS_PCT': '每日最大虧損百分比 (例如 0.25 代表 25%)',
            'GLOBAL_INTERVAL_SECONDS': '每次交易循環的間隔秒數',
            'AUTO_SET_LEVERAGE': '啟動時是否自動設置槓桿',
            # 你可以根據 config.py 裡的欄位再補充
        }

        configurations_to_import = {
            'USE_TESTNET': config.USE_TESTNET,
            'API_KEY': config.API_KEY,
            'API_SECRET': config.API_SECRET,
            'SYMBOLS': config.SYMBOLS, # 列表需要序列化
            'TEST_MODE': config.TEST_MODE,
            'LEVERAGE': config.LEVERAGE,
            'EXIT_MODE': config.EXIT_MODE,
            'AMOUNT_TAKE_PROFIT_USDT': config.AMOUNT_TAKE_PROFIT_USDT,
            'AMOUNT_STOP_LOSS_USDT': config.AMOUNT_STOP_LOSS_USDT,
            'MAX_CONSECUTIVE_STOP_LOSS': config.MAX_CONSECUTIVE_STOP_LOSS,
            'ENABLE_TRADE_LOG': config.ENABLE_TRADE_LOG,
            'SYMBOL_INTERVALS': config.SYMBOL_INTERVALS, # 字典需要序列化
            'SYMBOL_INTERVAL_SECONDS': config.SYMBOL_INTERVAL_SECONDS, # 字典需要序列化
            'BASE_POSITION_RATIO': config.BASE_POSITION_RATIO,
            'MIN_POSITION_RATIO': config.MIN_POSITION_RATIO,
            'MAX_POSITION_RATIO': config.MAX_POSITION_RATIO,
            'PRICE_TAKE_PROFIT_PERCENT': config.PRICE_TAKE_PROFIT_PERCENT,
            'PRICE_STOP_LOSS_PERCENT': config.PRICE_STOP_LOSS_PERCENT,
            'ATR_TAKE_PROFIT_MULTIPLIER': config.ATR_TAKE_PROFIT_MULTIPLIER,
            'ATR_STOP_LOSS_MULTIPLIER': config.ATR_STOP_LOSS_MULTIPLIER,
            'HYBRID_MIN_TAKE_PROFIT_USDT': config.HYBRID_MIN_TAKE_PROFIT_USDT,
            'HYBRID_MAX_TAKE_PROFIT_USDT': config.HYBRID_MAX_TAKE_PROFIT_USDT,
            'HYBRID_MIN_STOP_LOSS_USDT': config.HYBRID_MIN_STOP_LOSS_USDT,
            'HYBRID_MAX_STOP_LOSS_USDT': config.HYBRID_MAX_STOP_LOSS_USDT,
            'EXCHANGE_NAME': getattr(config, 'EXCHANGE_NAME', ''),
            'MAX_DAILY_LOSS_PCT': getattr(config, 'MAX_DAILY_LOSS_PCT', ''),
            'GLOBAL_INTERVAL_SECONDS': getattr(config, 'GLOBAL_INTERVAL_SECONDS', ''),
            'AUTO_SET_LEVERAGE': getattr(config, 'AUTO_SET_LEVERAGE', ''),
        }

        for key, value in configurations_to_import.items():
            # 將非字串、非數字的值（如列表、字典、布林值）轉換為字串
            if isinstance(value, (list, dict)):
                value_str = json.dumps(value)
            elif isinstance(value, bool):
                value_str = str(value) # 轉換為 "True" 或 "False"
            else:
                value_str = str(value)

            description = config_descriptions.get(key, '')

            obj, created = TraderConfig.objects.update_or_create(
                key=key,
                defaults={'value': value_str, 'description': description}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'新增配置: {key} = {value_str}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'更新配置: {key} = {value_str}'))

        self.stdout.write(self.style.SUCCESS('配置導入完成！'))
