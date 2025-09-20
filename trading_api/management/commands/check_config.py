import logging
import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from trading_api.models import TraderConfig, TradingPair

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '檢查和修復交易機器人配置同步問題'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('開始檢查配置同步問題...'))
        
        try:
            # 1. 檢查SYMBOLS配置
            self.stdout.write('\n=== 檢查交易幣種配置 ===')
            try:
                symbols_config = TraderConfig.objects.get(key='SYMBOLS')
                self.stdout.write(f'後台SYMBOLS配置: {symbols_config.value}')
                
                # 解析JSON格式
                try:
                    symbols_list = json.loads(symbols_config.value)
                    self.stdout.write(f'解析後的幣種列表: {symbols_list}')
                    
                    # 檢查是否為列表格式
                    if not isinstance(symbols_list, list):
                        self.stdout.write(self.style.ERROR('SYMBOLS配置不是有效的列表格式'))
                        # 修復為默認格式
                        symbols_config.value = '["BTCUSDT", "ETHUSDT"]'
                        symbols_config.save()
                        self.stdout.write('已修復SYMBOLS配置格式')
                    else:
                        self.stdout.write(f'✅ SYMBOLS配置格式正確，共 {len(symbols_list)} 個幣種')
                        
                except json.JSONDecodeError as e:
                    self.stdout.write(self.style.ERROR(f'SYMBOLS配置JSON解析失敗: {e}'))
                    # 修復為默認格式
                    symbols_config.value = '["BTCUSDT", "ETHUSDT"]'
                    symbols_config.save()
                    self.stdout.write('已修復SYMBOLS配置JSON格式')
                    
            except TraderConfig.DoesNotExist:
                self.stdout.write(self.style.WARNING('未找到SYMBOLS配置，創建默認配置'))
                TraderConfig.objects.create(
                    key='SYMBOLS',
                    value='["BTCUSDT", "ETHUSDT"]',
                    value_type='list',
                    description='交易幣種列表'
                )
            
            # 2. 檢查槓桿配置
            self.stdout.write('\n=== 檢查槓桿配置 ===')
            try:
                leverage_config = TraderConfig.objects.get(key='LEVERAGE')
                self.stdout.write(f'後台LEVERAGE配置: {leverage_config.value}')
                
                # 檢查是否為有效數字
                try:
                    leverage_value = int(leverage_config.value)
                    self.stdout.write(f'✅ 槓桿值: {leverage_value}')
                except ValueError:
                    self.stdout.write(self.style.ERROR(f'LEVERAGE配置值無效: {leverage_config.value}'))
                    # 修復為默認值
                    leverage_config.value = '10'
                    leverage_config.save()
                    self.stdout.write('已修復LEVERAGE配置值')
                    
            except TraderConfig.DoesNotExist:
                self.stdout.write(self.style.WARNING('未找到LEVERAGE配置，創建默認配置'))
                TraderConfig.objects.create(
                    key='LEVERAGE',
                    value='10',
                    value_type='int',
                    description='交易槓桿倍數'
                )
            
            # 3. 檢查AUTO_SET_LEVERAGE配置
            self.stdout.write('\n=== 檢查自動設置槓桿配置 ===')
            try:
                auto_leverage_config = TraderConfig.objects.get(key='AUTO_SET_LEVERAGE')
                self.stdout.write(f'後台AUTO_SET_LEVERAGE配置: {auto_leverage_config.value}')
                
                # 檢查是否為有效布林值
                if auto_leverage_config.value.lower() in ['true', '1', 't', 'y', 'yes']:
                    self.stdout.write('✅ 自動設置槓桿: 啟用')
                else:
                    self.stdout.write('⚠️ 自動設置槓桿: 停用')
                    
            except TraderConfig.DoesNotExist:
                self.stdout.write(self.style.WARNING('未找到AUTO_SET_LEVERAGE配置，創建默認配置'))
                TraderConfig.objects.create(
                    key='AUTO_SET_LEVERAGE',
                    value='True',
                    value_type='bool',
                    description='是否自動設置槓桿'
                )
            
            # 4. 檢查交易對數據庫記錄
            self.stdout.write('\n=== 檢查交易對數據庫記錄 ===')
            trading_pairs = TradingPair.objects.all()
            self.stdout.write(f'數據庫中的交易對數量: {trading_pairs.count()}')
            
            for pair in trading_pairs:
                self.stdout.write(f'  - {pair.symbol} (間隔: {pair.interval}, 精度: {pair.precision})')
            
            # 5. 同步交易對配置
            self.stdout.write('\n=== 同步交易對配置 ===')
            try:
                symbols_config = TraderConfig.objects.get(key='SYMBOLS')
                symbols_list = json.loads(symbols_config.value)
                
                # 刪除不在配置中的交易對
                existing_symbols = [pair.symbol for pair in trading_pairs]
                for symbol in existing_symbols:
                    if symbol not in symbols_list:
                        TradingPair.objects.filter(symbol=symbol).delete()
                        self.stdout.write(f'已刪除不在配置中的交易對: {symbol}')
                
                # 創建配置中但數據庫中沒有的交易對
                for symbol in symbols_list:
                    pair, created = TradingPair.objects.get_or_create(
                        symbol=symbol,
                        defaults={
                            'interval': '1m',
                            'precision': 3,
                            'consecutive_stop_loss': 0
                        }
                    )
                    if created:
                        self.stdout.write(f'已創建交易對: {symbol}')
                    else:
                        self.stdout.write(f'交易對已存在: {symbol}')
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'同步交易對配置失敗: {e}'))
            
            # 6. 檢查K線週期配置
            self.stdout.write('\n=== 檢查K線週期配置 ===')
            try:
                intervals_config = TraderConfig.objects.get(key='SYMBOL_INTERVALS')
                self.stdout.write(f'後台SYMBOL_INTERVALS配置: {intervals_config.value}')
                
                # 解析JSON格式
                try:
                    intervals_dict = json.loads(intervals_config.value)
                    self.stdout.write(f'解析後的週期配置: {intervals_dict}')
                    
                    # 檢查是否為字典格式
                    if not isinstance(intervals_dict, dict):
                        self.stdout.write(self.style.ERROR('SYMBOL_INTERVALS配置不是有效的字典格式'))
                        # 修復為默認格式
                        intervals_config.value = '{"BTCUSDT": "1m", "ETHUSDT": "1m"}'
                        intervals_config.save()
                        self.stdout.write('已修復SYMBOL_INTERVALS配置格式')
                    else:
                        self.stdout.write('✅ SYMBOL_INTERVALS配置格式正確')
                        
                except json.JSONDecodeError as e:
                    self.stdout.write(self.style.ERROR(f'SYMBOL_INTERVALS配置JSON解析失敗: {e}'))
                    # 修復為默認格式
                    intervals_config.value = '{"BTCUSDT": "1m", "ETHUSDT": "1m"}'
                    intervals_config.save()
                    self.stdout.write('已修復SYMBOL_INTERVALS配置JSON格式')
                    
            except TraderConfig.DoesNotExist:
                self.stdout.write(self.style.WARNING('未找到SYMBOL_INTERVALS配置，創建默認配置'))
                TraderConfig.objects.create(
                    key='SYMBOL_INTERVALS',
                    value='{"BTCUSDT": "1m", "ETHUSDT": "1m"}',
                    value_type='dict',
                    description='各交易對的K線週期'
                )
            
            self.stdout.write(
                self.style.SUCCESS('\n配置檢查完成！請重新啟動機器人以應用更改。')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'檢查配置時發生錯誤: {e}')
            )
            raise
