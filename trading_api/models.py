from django.db import models
from django.utils import timezone

# Create your models here.

class TraderConfig(models.Model):
    """
    交易機器人的全局配置 (原始的 key-value 形式)
    """
    key = models.CharField(max_length=100, unique=True, primary_key=True, verbose_name="配置鍵")
    value = models.TextField(verbose_name="配置值")
    value_type = models.CharField(
        max_length=20, 
        default='str', 
        verbose_name="值類型",
        help_text="例如: str, int, float, bool, list, dict"
    )
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="描述")

    class Meta:
        verbose_name = "交易配置"
        verbose_name_plural = "交易配置"

    def __str__(self):
        return f"{self.key} = {self.value}"

class TradingPair(models.Model):
    symbol = models.CharField(max_length=20, primary_key=True, verbose_name="交易對符號")
    interval = models.CharField(max_length=10, default="1m", verbose_name="K線週期")
    precision = models.IntegerField(default=0, verbose_name="數量精度")
    average_atr = models.FloatField(null=True, blank=True, verbose_name="歷史平均ATR")
    consecutive_stop_loss = models.IntegerField(default=0, verbose_name="連續止損次數")
    last_trade_time = models.DateTimeField(null=True, blank=True, verbose_name="上次交易時間") # 新增，用於冷卻

    class Meta:
        verbose_name = "交易對"
        verbose_name_plural = "交易對"

    def __str__(self):
        return self.symbol

class Position(models.Model):
    trading_pair = models.OneToOneField(TradingPair, on_delete=models.CASCADE, primary_key=True, verbose_name="交易對")
    active = models.BooleanField(default=False, verbose_name="是否活躍")
    side = models.CharField(max_length=4, verbose_name="持倉方向") # BUY/SELL
    entry_price = models.FloatField(verbose_name="開倉價格")
    quantity = models.FloatField(verbose_name="持倉數量")
    open_time = models.DateTimeField(default=timezone.now, verbose_name="開倉時間")

    class Meta:
        verbose_name = "持倉"
        verbose_name_plural = "持倉"

    def __str__(self):
        return f"{self.trading_pair.symbol} - {self.side} {self.quantity}"

class Trade(models.Model):
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE, verbose_name="交易對")
    trade_time = models.DateTimeField(default=timezone.now, verbose_name="交易時間")
    side = models.CharField(max_length=4, verbose_name="交易方向") # BUY/SELL (通常是平倉方向)
    entry_price = models.FloatField(verbose_name="開倉價格")
    exit_price = models.FloatField(verbose_name="平倉價格")
    quantity = models.FloatField(verbose_name="交易數量")
    pnl = models.FloatField(verbose_name="損益")
    reason = models.CharField(max_length=100, verbose_name="平倉原因")

    class Meta:
        verbose_name = "交易記錄"
        verbose_name_plural = "交易記錄"
        ordering = ['-trade_time'] # 按時間倒序排列

    def __str__(self):
        return f"{self.trading_pair.symbol} {self.side} {self.pnl:.2f} @ {self.trade_time.strftime('%Y-%m-%d %H:%M:%S')}"

class DailyStats(models.Model):
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE, verbose_name="交易對")
    date = models.DateField(default=timezone.localdate, verbose_name="日期")
    pnl = models.FloatField(default=0.0, verbose_name="當日累積損益")
    start_balance = models.FloatField(default=0.0, verbose_name="當日起始資金")
    max_daily_loss_pct = models.FloatField(default=0.25, verbose_name="最大當日虧損百分比")

    class Meta:
        verbose_name = "每日統計"
        verbose_name_plural = "每日統計"
        unique_together = ('trading_pair', 'date') # 確保每天每個交易對只有一條記錄

    def __str__(self):
        return f"{self.trading_pair.symbol} {self.date} PnL: {self.pnl:.2f}"

class TraderStatus(models.Model):
    is_trading_enabled = models.BooleanField(default=True, verbose_name="交易是否啟用")
    stop_signal_received = models.BooleanField(default=False, verbose_name="是否收到停止信號")
    last_daily_reset_date = models.DateField(default=timezone.localdate, verbose_name="上次每日重置日期")

    class Meta:
        verbose_name = "交易員狀態"
        verbose_name_plural = "交易員狀態"

    def __str__(self):
        return f"交易啟用: {self.is_trading_enabled}, 停止信號: {self.stop_signal_received}"

# 新增組合包模式選項 (現在定義在這裡，供 StrategyCombo 使用)
COMBO_MODE_CHOICES = [
    ('aggressive', '激進 (Aggressive)'),
    ('balanced', '平衡 (Balanced)'),
    ('conservative', '保守 (Conservative)'),
    ('auto', '自動判斷 (Auto-detect)'),
    ('custom', '自定義 (Custom)'),
]

class StrategyCombo(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="策略組合名稱")
    description = models.TextField(blank=True, verbose_name="描述")
    # conditions 字段將以 JSON 格式儲存策略條件列表
    conditions = models.JSONField(default=list, blank=True, verbose_name="策略條件")
    is_active = models.BooleanField(default=False, verbose_name="是否啟用") # 保持此欄位，用於啟用/停用某個策略模式

    # 新增 combo_mode 字段，取代原有的 strategy_style 字段
    combo_mode = models.CharField(
        max_length=20,
        choices=COMBO_MODE_CHOICES,
        default='balanced', # 預設為平衡
        verbose_name="啟用組合包模式" # 新的顯示名稱
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="創建時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "策略組合"
        verbose_name_plural = "策略組合"
        # 確保只有一個 StrategyCombo 實例可以被設置為 is_active=True
        # 你需要在 admin.py 進行額外檢查或在程式碼中強制執行
        # 或者更簡單的方式是，只在機器人運行時選取第一個 is_active=True 的組合
        # 或讓使用者一次只能啟用一個

    def __str__(self):
        return f"{self.name} ({self.get_combo_mode_display()}) - {'啟用中' if self.is_active else '未啟用'}"
