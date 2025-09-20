import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from trading_api.models import DailyStats, TradingPair, TraderConfig

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '修復數據庫中的DailyStats問題，確保所有必要字段都有正確的默認值'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('開始修復數據庫問題...'))
        
        try:
            # 1. 確保有交易對存在
            trading_pairs = TradingPair.objects.all()
            if not trading_pairs.exists():
                self.stdout.write(self.style.WARNING('沒有找到任何交易對，創建默認交易對...'))
                default_symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT']
                for symbol in default_symbols:
                    TradingPair.objects.get_or_create(
                        symbol=symbol,
                        defaults={
                            'interval': '1m',
                            'precision': 3,
                            'consecutive_stop_loss': 0
                        }
                    )
                trading_pairs = TradingPair.objects.all()
                self.stdout.write(f'已創建 {trading_pairs.count()} 個默認交易對')
            
            # 2. 獲取配置值
            try:
                max_daily_loss_config = TraderConfig.objects.get(key='MAX_DAILY_LOSS_PCT')
                # 檢查配置值是否為空或無效
                if max_daily_loss_config.value and max_daily_loss_config.value.strip():
                    try:
                        max_daily_loss_pct = float(max_daily_loss_config.value)
                    except ValueError:
                        self.stdout.write(self.style.WARNING(f'MAX_DAILY_LOSS_PCT配置值無效: "{max_daily_loss_config.value}"，使用默認值'))
                        max_daily_loss_pct = 0.25
                        # 修復無效的配置值
                        max_daily_loss_config.value = '0.25'
                        max_daily_loss_config.save()
                else:
                    self.stdout.write(self.style.WARNING('MAX_DAILY_LOSS_PCT配置值為空，使用默認值並修復配置'))
                    max_daily_loss_pct = 0.25
                    # 修復空的配置值
                    max_daily_loss_config.value = '0.25'
                    max_daily_loss_config.save()
            except TraderConfig.DoesNotExist:
                max_daily_loss_pct = 0.25
                self.stdout.write(f'未找到MAX_DAILY_LOSS_PCT配置，使用默認值: {max_daily_loss_pct}')
                # 創建缺失的配置項
                TraderConfig.objects.create(
                    key='MAX_DAILY_LOSS_PCT',
                    value='0.25',
                    value_type='float',
                    description='每日最大虧損百分比'
                )
            
            # 2.1 清理和修復所有配置項
            self.stdout.write('檢查並修復所有配置項...')
            config_fixes = 0
            
            # 定義關鍵配置的默認值
            default_configs = {
                'MAX_DAILY_LOSS_PCT': ('0.25', 'float'),
                'LEVERAGE': ('10', 'int'),
                'BASE_POSITION_RATIO': ('0.3', 'float'),
                'MIN_POSITION_RATIO': ('0.01', 'float'),
                'MAX_POSITION_RATIO': ('0.8', 'float'),
                'MAX_TRADES_PER_HOUR': ('5', 'int'),
                'MAX_TRADES_PER_DAY': ('100', 'int'),
                'GLOBAL_INTERVAL_SECONDS': ('3', 'int'),
                'ENABLE_TRADE_LOG': ('True', 'bool'),
                'ENABLE_VOLATILITY_RISK_ADJUSTMENT': ('True', 'bool'),
                'VOLATILITY_THRESHOLD_MULTIPLIER': ('2.0', 'float'),
                'VOLATILITY_PAUSE_THRESHOLD': ('3.0', 'float'),
                'VOLATILITY_RECOVERY_THRESHOLD': ('1.5', 'float'),
                'VOLATILITY_PAUSE_DURATION_MINUTES': ('30', 'int'),
                'ENABLE_MAX_POSITION_LIMIT': ('True', 'bool'),
                'MAX_SIMULTANEOUS_POSITIONS': ('3', 'int'),
                'ATR_LENGTH': ('14', 'int'),
                'ATR_MULTIPLIER': ('2.0', 'float'),
                'EXCHANGE': ('BINANCE', 'str'),
                'USE_TESTNET': ('True', 'bool'),
                'TEST_MODE': ('True', 'bool'),
                'SYMBOLS': ('["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"]', 'list'),
                'EXIT_MODE': ('PERCENTAGE', 'str'),
                'PRICE_TAKE_PROFIT_PERCENT': ('20.0', 'float'),
                'PRICE_STOP_LOSS_PERCENT': ('1.0', 'float'),
            }
            
            for key, (default_value, value_type) in default_configs.items():
                try:
                    config_obj = TraderConfig.objects.get(key=key)
                    # 檢查配置值是否為空或無效
                    if not config_obj.value or not config_obj.value.strip():
                        config_obj.value = default_value
                        config_obj.value_type = value_type
                        config_obj.save()
                        self.stdout.write(f'已修復空配置: {key} = {default_value}')
                        config_fixes += 1
                    elif value_type == 'float' and config_obj.value_type == 'float':
                        # 檢查浮點數配置是否有效
                        try:
                            float(config_obj.value)
                        except ValueError:
                            config_obj.value = default_value
                            config_obj.save()
                            self.stdout.write(f'已修復無效浮點數配置: {key} = {default_value}')
                            config_fixes += 1
                    elif value_type == 'int' and config_obj.value_type == 'int':
                        # 檢查整數配置是否有效
                        try:
                            int(config_obj.value)
                        except ValueError:
                            config_obj.value = default_value
                            config_obj.save()
                            self.stdout.write(f'已修復無效整數配置: {key} = {default_value}')
                            config_fixes += 1
                except TraderConfig.DoesNotExist:
                    # 創建缺失的配置項
                    TraderConfig.objects.create(
                        key=key,
                        value=default_value,
                        value_type=value_type,
                        description=f'{key} 配置項'
                    )
                    self.stdout.write(f'已創建缺失配置: {key} = {default_value}')
                    config_fixes += 1
            
            if config_fixes > 0:
                self.stdout.write(f'配置修復完成，共修復 {config_fixes} 個配置項')
            else:
                self.stdout.write('所有配置項都正常，無需修復')
            
            # 3. 修復今天的DailyStats記錄
            today = timezone.localdate()
            fixed_count = 0
            
            for trading_pair in trading_pairs:
                try:
                    daily_stats, created = DailyStats.objects.get_or_create(
                        trading_pair=trading_pair,
                        date=today,
                        defaults={
                            'start_balance': 1000.0,  # 默認起始資金
                            'pnl': 0.0,
                            'max_daily_loss_pct': max_daily_loss_pct
                        }
                    )
                    
                    if not created:
                        # 更新現有記錄，確保所有字段都有值
                        if daily_stats.max_daily_loss_pct is None:
                            daily_stats.max_daily_loss_pct = max_daily_loss_pct
                        if daily_stats.start_balance is None:
                            daily_stats.start_balance = 1000.0
                        if daily_stats.pnl is None:
                            daily_stats.pnl = 0.0
                        daily_stats.save()
                        self.stdout.write(f'已修復 {trading_pair.symbol} 的DailyStats記錄')
                    else:
                        self.stdout.write(f'已創建 {trading_pair.symbol} 的DailyStats記錄')
                    
                    fixed_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'修復 {trading_pair.symbol} 的DailyStats失敗: {e}')
                    )
            
            # 4. 檢查並修復歷史記錄
            historical_fixed = 0
            for daily_stats in DailyStats.objects.filter(max_daily_loss_pct__isnull=True):
                daily_stats.max_daily_loss_pct = max_daily_loss_pct
                daily_stats.save()
                historical_fixed += 1
            
            if historical_fixed > 0:
                self.stdout.write(f'已修復 {historical_fixed} 條歷史DailyStats記錄')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'數據庫修復完成！共處理 {fixed_count} 個交易對，'
                    f'修復 {historical_fixed} 條歷史記錄'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'修復數據庫時發生錯誤: {e}')
            )
            raise
