import json
from django.core.management.base import BaseCommand
from trading_api.models import TraderConfig

class Command(BaseCommand):
    help = '清空並初始化交易機器人的預設配置'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('正在清空現有的 TraderConfig 數據...'))
        
        # 刪除所有現有的配置
        count, _ = TraderConfig.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(f'成功刪除 {count} 條舊配置。'))
        self.stdout.write(self.style.WARNING('正在寫入新的預設配置...'))

        # 定義預設配置
        default_configs = [
            # --- 交易所連接配置 ---
            {'key': 'EXCHANGE_NAME', 'value': 'binance', 'value_type': 'str', 'description': '目標交易所的 CCXT ID (例如: binance, bybit, okx)'},
            {'key': 'USE_TESTNET', 'value': 'True', 'value_type': 'bool', 'description': '是否使用測試網 (True/False)'},
            {'key': 'API_KEY', 'value': 'YOUR_TESTNET_API_KEY', 'value_type': 'str', 'description': '交易所 API Key (請務必修改)'},
            {'key': 'API_SECRET', 'value': 'YOUR_TESTNET_API_SECRET', 'value_type': 'str', 'description': '交易所 API Secret (請務必修改)'},
            # --- 槓桿自動設置開關 ---
            {'key': 'AUTO_SET_LEVERAGE', 'value': 'True', 'value_type': 'bool', 'description': '啟動時是否自動設置槓桿'},
            
            # --- 核心交易參數 ---
            {'key': 'SYMBOLS', 'value': json.dumps(['BTC/USDT', 'ETH/USDT']), 'value_type': 'list', 'description': '要交易的幣種列表 (JSON 格式)'},
            {'key': 'LEVERAGE', 'value': '10', 'value_type': 'int', 'description': '所有交易對的統一槓桿倍數'},
            {'key': 'GLOBAL_INTERVAL_SECONDS', 'value': '3', 'value_type': 'int', 'description': '每次交易循環的間隔秒數'},
            {'key': 'TEST_MODE', 'value': 'False', 'value_type': 'bool', 'description': '是否啟用模擬交易模式 (不會真實下單)'},

            # --- 風險控制參數 ---
            {'key': 'MAX_DAILY_LOSS_PCT', 'value': '0.25', 'value_type': 'float', 'description': '每日最大虧損百分比 (例如 0.25 代表 25%)'},
            {'key': 'RISK_PER_TRADE_PCT', 'value': '0.02', 'value_type': 'float', 'description': '單筆交易的風險百分比 (例如 0.02 代表 2%)'},
            
            # --- 策略相關參數 ---
            {'key': 'SYMBOL_INTERVALS', 'value': json.dumps({'BTC/USDT': '1m', 'ETH/USDT': '1m'}), 'value_type': 'dict', 'description': '每個交易對使用的 K 線時間週期 (JSON 格式)'},
            {'key': 'ATR_LENGTH', 'value': '14', 'value_type': 'int', 'description': '計算 ATR 指標的週期長度'},
            {'key': 'ATR_MULTIPLIER', 'value': '2.0', 'value_type': 'float', 'description': '用於計算止損的 ATR 乘數'},
        ]

        # 寫入數據庫
        for config_data in default_configs:
            TraderConfig.objects.create(**config_data)
            self.stdout.write(f"  - 已創建: {config_data['key']} = {config_data['value']}")

        self.stdout.write(self.style.SUCCESS('✅ 成功寫入所有預設配置！'))
        self.stdout.write('---' * 20)
        self.stdout.write(self.style.NOTICE('下一步重要操作：'))
        self.stdout.write(self.style.NOTICE('1. 請登入 Django Admin 後台。'))
        self.stdout.write(self.style.NOTICE("2. 找到 'Trading_Api' -> 'Trader Configs'。"))
        self.stdout.write(self.style.NOTICE("3. 將 'API_KEY' 和 'API_SECRET' 的值修改為您自己的有效金鑰。"))
        self.stdout.write(self.style.NOTICE("   - 如果 USE_TESTNET 為 True, 請使用測試網的金鑰。"))
        self.stdout.write(self.style.NOTICE("   - 如果 USE_TESTNET 為 False, 請使用主網的真實金鑰。"))
        self.stdout.write('---' * 20) 