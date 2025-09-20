# Generated manually for API key management

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('trading_api', '0004_orderstatus_systemlog_detailedtradelog_riskmetrics'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ExchangeAPIKey 模型
        migrations.CreateModel(
            name='ExchangeAPIKey',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('exchange', models.CharField(choices=[('BINANCE', 'Binance'), ('BYBIT', 'Bybit'), ('OKX', 'OKX'), ('BINGX', 'BingX'), ('BITGET', 'Bitget')], max_length=20)),
                ('network', models.CharField(choices=[('MAINNET', '主網'), ('TESTNET', '測試網')], default='TESTNET', max_length=10)),
                ('api_key', models.CharField(max_length=255)),
                ('api_secret', models.CharField(max_length=255)),
                ('passphrase', models.CharField(blank=True, max_length=255, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('last_verified', models.DateTimeField(blank=True, null=True)),
                ('can_trade', models.BooleanField(default=True)),
                ('can_withdraw', models.BooleanField(default=False)),
                ('can_read', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_keys', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '交易所API金鑰',
                'verbose_name_plural': '交易所API金鑰',
                'unique_together': {('user', 'exchange', 'network')},
            },
        ),
        
        # TradingConfig 模型
        migrations.CreateModel(
            name='TradingConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('default_exchange', models.CharField(choices=[('BINANCE', 'Binance'), ('BYBIT', 'Bybit'), ('OKX', 'OKX'), ('BINGX', 'BingX'), ('BITGET', 'Bitget')], default='BINANCE', max_length=20)),
                ('default_network', models.CharField(choices=[('MAINNET', '主網'), ('TESTNET', '測試網')], default='TESTNET', max_length=10)),
                ('default_leverage', models.FloatField(default=1.0)),
                ('max_position_ratio', models.FloatField(default=0.3)),
                ('min_position_ratio', models.FloatField(default=0.01)),
                ('max_trades_per_hour', models.IntegerField(default=10)),
                ('max_trades_per_day', models.IntegerField(default=50)),
                ('max_daily_loss_percent', models.FloatField(default=25.0)),
                ('enable_volatility_risk_adjustment', models.BooleanField(default=True)),
                ('volatility_threshold_multiplier', models.FloatField(default=2.0)),
                ('volatility_pause_threshold', models.FloatField(default=3.0)),
                ('volatility_recovery_threshold', models.FloatField(default=1.5)),
                ('volatility_pause_duration_minutes', models.IntegerField(default=30)),
                ('enable_max_position_limit', models.BooleanField(default=True)),
                ('max_simultaneous_positions', models.IntegerField(default=3)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='trading_config', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '交易配置',
                'verbose_name_plural': '交易配置',
            },
        ),
    ]
