from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('trading_api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='traderstatus',
            name='hourly_trade_count',
            field=models.IntegerField(default=0, verbose_name='本小時開倉次數'),
        ),
        migrations.AddField(
            model_name='traderstatus',
            name='daily_trade_count',
            field=models.IntegerField(default=0, verbose_name='本日開倉次數'),
        ),
        migrations.AddField(
            model_name='traderstatus',
            name='last_hourly_reset',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='上次小時重置時間'),
        ),
    ]