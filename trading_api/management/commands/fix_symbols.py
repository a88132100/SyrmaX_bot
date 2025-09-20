import logging
import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from trading_api.models import TraderConfig, TradingPair

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '專門修復交易幣種配置問題，確保SYMBOLS配置與實際使用的幣種一致'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            type=str,
            help='要設置的幣種列表，用逗號分隔 (例如: BTCUSDT,ETHUSDT)',
            default='BTCUSDT,ETHUSDT'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='強制更新，即使配置看起來是正確的'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('開始修復交易幣種配置...'))
        
        # 解析幣種參數
        symbols_input = options['symbols']
        symbols_list = [s.strip() for s in symbols_input.split(',') if s.strip()]
        
        self.stdout.write(f'目標幣種列表: {symbols_list}')
        
        try:
            # 1. 檢查並修復SYMBOLS配置
            self.stdout.write('\n=== 修復SYMBOLS配置 ===')
            try:
                symbols_config = TraderConfig.objects.get(key='SYMBOLS')
                current_value = symbols_config.value
                current_type = symbols_config.value_type
                
                self.stdout.write(f'當前SYMBOLS配置值: {current_value}')
                self.stdout.write(f'當前SYMBOLS配置類型: {current_type}')
                
                # 檢查是否需要更新
                needs_update = False
                
                # 嘗試解析當前值
                try:
                    if current_type == 'list':
                        parsed_symbols = json.loads(current_value)
                        if parsed_symbols != symbols_list:
                            needs_update = True
                            self.stdout.write(f'解析後的幣種列表與目標不符: {parsed_symbols} vs {symbols_list}')
                        else:
                            self.stdout.write('✅ 幣種列表配置正確')
                    else:
                        needs_update = True
                        self.stdout.write(f'配置類型錯誤，期望list但實際是{current_type}')
                except json.JSONDecodeError:
                    needs_update = True
                    self.stdout.write('JSON解析失敗，需要更新配置')
                
                # 更新配置
                if needs_update or options['force']:
                    symbols_config.value = json.dumps(symbols_list, ensure_ascii=False)
                    symbols_config.value_type = 'list'
                    symbols_config.save()
                    self.stdout.write(f'✅ 已更新SYMBOLS配置: {symbols_config.value}')
                else:
                    self.stdout.write('SYMBOLS配置無需更新')
                    
            except TraderConfig.DoesNotExist:
                self.stdout.write('未找到SYMBOLS配置，創建新配置')
                TraderConfig.objects.create(
                    key='SYMBOLS',
                    value=json.dumps(symbols_list, ensure_ascii=False),
                    value_type='list',
                    description='交易幣種列表'
                )
                self.stdout.write(f'✅ 已創建SYMBOLS配置: {symbols_list}')
            
            # 2. 同步TradingPair數據庫記錄
            self.stdout.write('\n=== 同步交易對數據庫記錄 ===')
            
            # 獲取現有的交易對
            existing_pairs = TradingPair.objects.all()
            existing_symbols = [pair.symbol for pair in existing_pairs]
            
            self.stdout.write(f'數據庫中現有的交易對: {existing_symbols}')
            
            # 刪除不在目標列表中的交易對
            for symbol in existing_symbols:
                if symbol not in symbols_list:
                    TradingPair.objects.filter(symbol=symbol).delete()
                    self.stdout.write(f'已刪除不在配置中的交易對: {symbol}')
            
            # 創建目標列表中的交易對
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
            
            # 3. 檢查其他相關配置
            self.stdout.write('\n=== 檢查相關配置 ===')
            
            # 檢查SYMBOL_INTERVALS配置
            try:
                intervals_config = TraderConfig.objects.get(key='SYMBOL_INTERVALS')
                try:
                    intervals_dict = json.loads(intervals_config.value)
                    # 更新為只包含目標幣種的配置
                    updated_intervals = {symbol: intervals_dict.get(symbol, '1m') for symbol in symbols_list}
                    if updated_intervals != intervals_dict:
                        intervals_config.value = json.dumps(updated_intervals, ensure_ascii=False)
                        intervals_config.save()
                        self.stdout.write(f'✅ 已更新SYMBOL_INTERVALS配置: {updated_intervals}')
                    else:
                        self.stdout.write('✅ SYMBOL_INTERVALS配置正確')
                except json.JSONDecodeError:
                    # 創建新的配置
                    new_intervals = {symbol: '1m' for symbol in symbols_list}
                    intervals_config.value = json.dumps(new_intervals, ensure_ascii=False)
                    intervals_config.save()
                    self.stdout.write(f'✅ 已修復SYMBOL_INTERVALS配置: {new_intervals}')
            except TraderConfig.DoesNotExist:
                # 創建新配置
                new_intervals = {symbol: '1m' for symbol in symbols_list}
                TraderConfig.objects.create(
                    key='SYMBOL_INTERVALS',
                    value=json.dumps(new_intervals, ensure_ascii=False),
                    value_type='dict',
                    description='各交易對的K線週期'
                )
                self.stdout.write(f'✅ 已創建SYMBOL_INTERVALS配置: {new_intervals}')
            
            # 4. 驗證修復結果
            self.stdout.write('\n=== 驗證修復結果 ===')
            
            # 重新讀取配置
            symbols_config = TraderConfig.objects.get(key='SYMBOLS')
            final_symbols = json.loads(symbols_config.value)
            final_pairs = TradingPair.objects.all()
            final_pair_symbols = [pair.symbol for pair in final_pairs]
            
            self.stdout.write(f'最終SYMBOLS配置: {final_symbols}')
            self.stdout.write(f'最終交易對記錄: {final_pair_symbols}')
            
            if set(final_symbols) == set(final_pair_symbols):
                self.stdout.write(self.style.SUCCESS('✅ 幣種配置修復成功！配置與數據庫記錄完全一致'))
            else:
                self.stdout.write(self.style.ERROR('❌ 幣種配置修復失敗！配置與數據庫記錄不一致'))
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n幣種配置修復完成！\n'
                    f'目標幣種: {symbols_list}\n'
                    f'配置幣種: {final_symbols}\n'
                    f'數據庫記錄: {final_pair_symbols}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'修復幣種配置時發生錯誤: {e}')
            )
            raise
