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
    hourly_trade_count = models.IntegerField(default=0, verbose_name="本小時開倉次數")
    daily_trade_count = models.IntegerField(default=0, verbose_name="本日開倉次數")
    last_hourly_reset = models.DateTimeField(default=timezone.now, verbose_name="上次小時重置時間")

    class Meta:
        verbose_name = "交易員狀態"
        verbose_name_plural = "交易員狀態"

    def __str__(self):
        return f"交易員狀態 - 交易啟用: {self.is_trading_enabled}, 小時計數: {self.hourly_trade_count}, 日計數: {self.daily_trade_count}"

class VolatilityPauseStatus(models.Model):
    """
    波動率暫停狀態模型
    用於記錄每個交易對的波動率暫停狀態
    """
    trading_pair = models.OneToOneField(TradingPair, on_delete=models.CASCADE, primary_key=True, verbose_name="交易對")
    is_paused = models.BooleanField(default=False, verbose_name="是否因波動率暫停")
    pause_start_time = models.DateTimeField(null=True, blank=True, verbose_name="暫停開始時間")
    pause_reason = models.CharField(max_length=255, blank=True, null=True, verbose_name="暫停原因")
    current_atr_ratio = models.FloatField(default=1.0, verbose_name="當前ATR比率")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="最後更新時間")

    class Meta:
        verbose_name = "波動率暫停狀態"
        verbose_name_plural = "波動率暫停狀態"

    def __str__(self):
        status = "暫停中" if self.is_paused else "正常"
        return f"{self.trading_pair.symbol} - {status} (ATR比率: {self.current_atr_ratio:.2f})"

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

# ===== 新增：完整的交易日誌系統 =====

class OrderStatus(models.Model):
    """
    訂單狀態枚舉模型
    """
    STATUS_CHOICES = [
        ('PENDING', '待處理'),
        ('SUBMITTED', '已提交'),
        ('PARTIAL_FILLED', '部分成交'),
        ('FILLED', '完全成交'),
        ('CANCELLED', '已取消'),
        ('REJECTED', '被拒絕'),
        ('EXPIRED', '已過期'),
    ]
    
    code = models.CharField(max_length=20, choices=STATUS_CHOICES, unique=True, verbose_name="狀態代碼")
    name = models.CharField(max_length=50, verbose_name="狀態名稱")
    description = models.TextField(blank=True, verbose_name="狀態描述")
    
    class Meta:
        verbose_name = "訂單狀態"
        verbose_name_plural = "訂單狀態"
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class DetailedTradeLog(models.Model):
    """
    詳細的交易日誌記錄
    記錄每筆交易的完整信息，包括訂單狀態、時間戳、風險指標等
    """
    # 基本信息
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE, verbose_name="交易對")
    strategy_name = models.CharField(max_length=100, verbose_name="策略名稱")
    combo_mode = models.CharField(max_length=20, verbose_name="策略組合模式")
    
    # 訂單信息
    order_id = models.CharField(max_length=100, unique=True, verbose_name="內部訂單ID")
    exchange_order_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="交易所訂單ID")
    order_status = models.CharField(max_length=20, verbose_name="訂單狀態")
    
    # 交易方向
    side = models.CharField(max_length=4, verbose_name="交易方向") # BUY/SELL
    order_type = models.CharField(max_length=20, default='MARKET', verbose_name="訂單類型")
    
    # 價格信息
    entry_price = models.FloatField(verbose_name="開倉價格")
    exit_price = models.FloatField(null=True, blank=True, verbose_name="平倉價格")
    target_price = models.FloatField(null=True, blank=True, verbose_name="目標價格")
    stop_loss_price = models.FloatField(null=True, blank=True, verbose_name="止損價格")
    take_profit_price = models.FloatField(null=True, blank=True, verbose_name="止盈價格")
    
    # 數量信息
    quantity = models.FloatField(verbose_name="訂單數量")
    filled_quantity = models.FloatField(default=0.0, verbose_name="已成交數量")
    remaining_quantity = models.FloatField(default=0.0, verbose_name="剩餘數量")
    
    # 時間戳記錄
    order_created_time = models.DateTimeField(auto_now_add=True, verbose_name="訂單創建時間")
    order_submitted_time = models.DateTimeField(null=True, blank=True, verbose_name="訂單提交時間")
    first_fill_time = models.DateTimeField(null=True, blank=True, verbose_name="首次成交時間")
    last_fill_time = models.DateTimeField(null=True, blank=True, verbose_name="最後成交時間")
    order_completed_time = models.DateTimeField(null=True, blank=True, verbose_name="訂單完成時間")
    order_cancelled_time = models.DateTimeField(null=True, blank=True, verbose_name="訂單取消時間")
    
    # 財務信息
    commission = models.FloatField(default=0.0, verbose_name="手續費")
    slippage = models.FloatField(default=0.0, verbose_name="滑點成本")
    notional_value = models.FloatField(verbose_name="名義價值")
    realized_pnl = models.FloatField(default=0.0, verbose_name="已實現損益")
    unrealized_pnl = models.FloatField(default=0.0, verbose_name="未實現損益")
    
    # 風險指標
    leverage = models.FloatField(default=1.0, verbose_name="槓桿倍數")
    margin_used = models.FloatField(default=0.0, verbose_name="保證金使用量")
    margin_ratio = models.FloatField(default=0.0, verbose_name="保證金使用率")
    risk_reward_ratio = models.FloatField(null=True, blank=True, verbose_name="風險收益比")
    
    # 市場環境
    market_volatility = models.FloatField(null=True, blank=True, verbose_name="市場波動率")
    atr_value = models.FloatField(null=True, blank=True, verbose_name="ATR值")
    trend_strength = models.CharField(max_length=20, null=True, blank=True, verbose_name="趨勢強度")
    
    # 策略信號
    signal_strength = models.FloatField(null=True, blank=True, verbose_name="信號強度")
    signal_confidence = models.FloatField(null=True, blank=True, verbose_name="信號置信度")
    multiple_signals = models.JSONField(default=list, blank=True, verbose_name="多策略信號")
    
    # 執行質量
    execution_quality = models.CharField(max_length=20, default='NORMAL', verbose_name="執行質量")
    execution_delay = models.FloatField(null=True, blank=True, verbose_name="執行延遲(毫秒)")
    price_improvement = models.FloatField(default=0.0, verbose_name="價格改善")
    
    # 錯誤和異常
    error_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="錯誤代碼")
    error_message = models.TextField(blank=True, null=True, verbose_name="錯誤信息")
    retry_count = models.IntegerField(default=0, verbose_name="重試次數")
    
    # 備註和標籤
    notes = models.TextField(blank=True, null=True, verbose_name="備註")
    tags = models.JSONField(default=list, blank=True, verbose_name="標籤")
    
    # 審計信息
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="創建時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        verbose_name = "詳細交易日誌"
        verbose_name_plural = "詳細交易日誌"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['trading_pair', 'created_at']),
            models.Index(fields=['strategy_name', 'created_at']),
            models.Index(fields=['order_status', 'created_at']),
            models.Index(fields=['side', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.trading_pair.symbol} {self.side} {self.quantity} @ {self.entry_price} - {self.order_status}"
    
    def calculate_pnl(self):
        """計算損益"""
        if self.exit_price and self.entry_price:
            if self.side == 'BUY':
                self.realized_pnl = (self.exit_price - self.entry_price) * self.filled_quantity
            else:
                self.realized_pnl = (self.entry_price - self.exit_price) * self.filled_quantity
            self.realized_pnl -= self.commission + self.slippage
        return self.realized_pnl
    
    def get_execution_time(self):
        """獲取執行時間"""
        if self.order_completed_time and self.order_created_time:
            return (self.order_completed_time - self.order_created_time).total_seconds()
        return None
    
    def get_fill_rate(self):
        """獲取成交率"""
        if self.quantity > 0:
            return (self.filled_quantity / self.quantity) * 100
        return 0

class RiskMetrics(models.Model):
    """
    風險指標記錄
    記錄每個交易對的風險指標變化
    """
    trading_pair = models.ForeignKey(TradingPair, on_delete=models.CASCADE, verbose_name="交易對")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="記錄時間")
    
    # 持倉風險
    position_size = models.FloatField(verbose_name="持倉大小")
    position_value = models.FloatField(verbose_name="持倉價值")
    margin_used = models.FloatField(verbose_name="保證金使用量")
    margin_ratio = models.FloatField(verbose_name="保證金使用率")
    leverage = models.FloatField(verbose_name="槓桿倍數")
    
    # 市場風險
    current_price = models.FloatField(verbose_name="當前價格")
    price_change_24h = models.FloatField(verbose_name="24小時價格變化")
    volatility_24h = models.FloatField(verbose_name="24小時波動率")
    atr_value = models.FloatField(verbose_name="ATR值")
    
    # 風險限制
    max_position_size = models.FloatField(verbose_name="最大持倉大小")
    max_daily_loss = models.FloatField(verbose_name="最大日虧損")
    current_daily_loss = models.FloatField(verbose_name="當前日虧損")
    
    # 風險評分
    risk_score = models.FloatField(verbose_name="風險評分")
    risk_level = models.CharField(max_length=20, verbose_name="風險等級")
    
    class Meta:
        verbose_name = "風險指標"
        verbose_name_plural = "風險指標"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['trading_pair', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.trading_pair.symbol} - 風險評分: {self.risk_score} ({self.risk_level})"

class SystemLog(models.Model):
    """
    系統日誌記錄
    記錄系統運行狀態、錯誤、警告等信息
    """
    LOG_LEVEL_CHOICES = [
        ('DEBUG', '調試'),
        ('INFO', '信息'),
        ('WARNING', '警告'),
        ('ERROR', '錯誤'),
        ('CRITICAL', '嚴重'),
    ]
    
    LOG_CATEGORY_CHOICES = [
        ('SYSTEM', '系統'),
        ('TRADING', '交易'),
        ('STRATEGY', '策略'),
        ('RISK', '風險'),
        ('EXCHANGE', '交易所'),
        ('DATABASE', '數據庫'),
        ('NETWORK', '網絡'),
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="時間戳")
    level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES, verbose_name="日誌級別")
    category = models.CharField(max_length=20, choices=LOG_CATEGORY_CHOICES, verbose_name="日誌類別")
    
    # 基本信息
    message = models.TextField(verbose_name="日誌消息")
    module = models.CharField(max_length=100, verbose_name="模組名稱")
    function = models.CharField(max_length=100, verbose_name="函數名稱")
    line_number = models.IntegerField(verbose_name="行號")
    
    # 上下文信息
    trading_pair = models.CharField(max_length=20, blank=True, null=True, verbose_name="交易對")
    strategy_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="策略名稱")
    order_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="訂單ID")
    
    # 錯誤信息
    error_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="錯誤代碼")
    error_message = models.TextField(blank=True, null=True, verbose_name="錯誤信息")
    stack_trace = models.TextField(blank=True, null=True, verbose_name="堆疊追蹤")
    
    # 性能信息
    execution_time = models.FloatField(null=True, blank=True, verbose_name="執行時間(秒)")
    memory_usage = models.FloatField(null=True, blank=True, verbose_name="內存使用(MB)")
    cpu_usage = models.FloatField(null=True, blank=True, verbose_name="CPU使用率(%)")
    
    # 外部依賴
    exchange_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="交易所名稱")
    api_endpoint = models.CharField(max_length=200, blank=True, null=True, verbose_name="API端點")
    response_time = models.FloatField(null=True, blank=True, verbose_name="響應時間(毫秒)")
    
    # 標籤和分類
    tags = models.JSONField(default=list, blank=True, verbose_name="標籤")
    severity = models.CharField(max_length=20, default='NORMAL', verbose_name="嚴重程度")
    
    class Meta:
        verbose_name = "系統日誌"
        verbose_name_plural = "系統日誌"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['category', 'timestamp']),
            models.Index(fields=['trading_pair', 'timestamp']),
        ]
    
    def __str__(self):
        return f"[{self.level}] {self.category}: {self.message[:50]}..."
    
    def is_error(self):
        """判斷是否為錯誤日誌"""
        return self.level in ['ERROR', 'CRITICAL']
    
    def is_warning(self):
        """判斷是否為警告日誌"""
        return self.level == 'WARNING'
