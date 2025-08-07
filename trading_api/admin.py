from django.contrib import admin
from django import forms
import json
from .models import TraderConfig, TradingPair, Position, Trade, DailyStats, TraderStatus, StrategyCombo, COMBO_MODE_CHOICES
# Import strategy_bundles from strategy.base (used for StrategyComboForm to get strategy names)
from strategy.base import strategy_bundles

# 定義配置鍵的中文翻譯
# This dictionary maps config keys to their display names in the admin.
CONFIG_KEY_TRANSLATIONS = {
    'EXCHANGE': '交易所類型',
    'EXCHANGE_NAME': '交易所名稱',
    'USE_TESTNET': '是否使用測試網',
    'API_KEY': 'API 金鑰 (Key)',
    'API_SECRET': 'API 密鑰 (Secret)',
    'SYMBOLS': '交易幣種 (逗號分隔)',
    'TEST_MODE': '是否為測試模式',
    'LEVERAGE': '交易槓桿倍數',
    'BASE_POSITION_RATIO': '基礎資金比例',
    'MIN_POSITION_RATIO': '最小資金比例',
    'MAX_POSITION_RATIO': '最大資金比例',
    'EXIT_MODE': '止盈止損模式',
    'PRICE_TAKE_PROFIT_PERCENT': '百分比止盈',
    'PRICE_STOP_LOSS_PERCENT': '百分比止損',
    'AMOUNT_TAKE_PROFIT_USDT': '固定金額止盈 (USDT)',
    'AMOUNT_STOP_LOSS_USDT': '固定金額止損 (USDT)',
    'ATR_TAKE_PROFIT_MULTIPLIER': 'ATR止盈倍數',
    'ATR_STOP_LOSS_MULTIPLIER': 'ATR止損倍數',
    'HYBRID_MIN_TAKE_PROFIT_USDT': '混合模式：最小止盈金額 (USDT)',
    'HYBRID_MAX_TAKE_PROFIT_USDT': '混合模式：最大止盈金額 (USDT)',
    'HYBRID_MIN_STOP_LOSS_USDT': '混合模式：最小止損金額 (USDT)',
    'HYBRID_MAX_STOP_LOSS_USDT': '混合模式：最大止損金額 (USDT)',
    'MAX_CONSECUTIVE_STOP_LOSS': '最大連續止損次數',
    'ENABLE_TRADE_LOG': '啟用交易日誌',
    'ENABLE_TRADE_LIMITS': '啟用開倉次數限制',
    'SYMBOL_INTERVALS': 'K線週期 (JSON 格式)',
    'SYMBOL_INTERVAL_SECONDS': '交易判斷頻率（秒，JSON 格式，例如: {\"BTCUSDT\": 3, \"ETHUSDT\": 5}）',
    'GLOBAL_INTERVAL_SECONDS': '全局交易判斷頻率（秒）',
    'RISK_LIMIT_TIERS': '交易所風險限額階梯 (JSON 格式，例如: [[100000, 20], [200000, 10]])',
    'MAX_DAILY_LOSS_PCT': '每日最大虧損百分比',
    # 如果你還有其他配置項，可以在這裡繼續添加翻譯
}

# 定義每個配置鍵的預期數據類型，用於動態生成表單字段
CONFIG_FIELD_TYPES = {
    'USE_TESTNET': bool,
    'TEST_MODE': bool,
    'ENABLE_TRADE_LOG': bool,
    'ENABLE_TRADE_LIMITS': bool,
    'LEVERAGE': int,
    'MAX_CONSECUTIVE_STOP_LOSS': int,
    'GLOBAL_INTERVAL_SECONDS': int,
    'BASE_POSITION_RATIO': float,
    'MIN_POSITION_RATIO': float,
    'MAX_POSITION_RATIO': float,
    'PRICE_TAKE_PROFIT_PERCENT': float,
    'PRICE_STOP_LOSS_PERCENT': float,
    'AMOUNT_TAKE_PROFIT_USDT': float,
    'AMOUNT_STOP_LOSS_USDT': float,
    'ATR_TAKE_PROFIT_MULTIPLIER': float,
    'ATR_STOP_LOSS_MULTIPLIER': float,
    'HYBRID_MIN_TAKE_PROFIT_USDT': float,
    'HYBRID_MAX_TAKE_PROFIT_USDT': float,
    'HYBRID_MIN_STOP_LOSS_USDT': float,
    'HYBRID_MAX_STOP_LOSS_USDT': float,
    'SYMBOLS': list, # Custom handling for comma-separated string
    'SYMBOL_INTERVALS': dict, # Custom handling for JSON string
    'SYMBOL_INTERVAL_SECONDS': dict, # Custom handling for JSON string
    'EXIT_MODE': str, # 保持為 str，但會在 get_form 中動態變為 ChoiceField
    'RISK_LIMIT_TIERS': list, # 存儲為 JSON 字符串，解析為列表
    'MAX_DAILY_LOSS_PCT': float,
    # Default is string for others
}

# 止盈止損模式選項
EXIT_MODE_CHOICES = [
    ('PERCENTAGE', '百分比'),
    ('AMOUNT', '固定金額'),
    ('ATR', 'ATR動態'),
    ('HYBRID', '混合模式'),
]


class TraderConfigForm(forms.ModelForm):
    # value 字段將預設為 CharField，以便在 get_form 中動態替換為正確的類型。
    value = forms.CharField(label="配置值", required=False, widget=forms.Textarea)

    class Meta:
        model = TraderConfig
        fields = ('value',)

    def clean_value(self):
        # 獲取 config_key，對於編輯模式，從 instance 中獲取；對於新增模式，從 cleaned_data 中獲取
        config_key = None
        if self.instance and self.instance.pk: # 如果是編輯現有實例
            config_key = self.instance.key
        elif 'key' in self.cleaned_data: # 如果是新增實例，key 會在 cleaned_data 中
            config_key = self.cleaned_data.get('key')
        
        # 如果 config_key 仍然為 None (極端情況)，則預設為字符串類型
        field_type = CONFIG_FIELD_TYPES.get(config_key, str) if config_key else str

        value = self.cleaned_data.get('value')

        # 根據字段類型，將輸入的 value 轉換為字符串形式存儲
        if field_type == bool:
            return str(value) # 布林值存儲為 'True' 或 'False'
        elif field_type == int:
            try:
                if value == '': return '' # 允許空字符串作為可選字段
                return str(int(value))
            except (ValueError, TypeError):
                raise forms.ValidationError("請輸入有效的整數。")
        elif field_type == float:
            try:
                if value == '': return '' # 允許空字符串作為可選字段
                return str(float(value))
            except (ValueError, TypeError):
                raise forms.ValidationError("請輸入有效的浮點數。")
        elif field_type == list: # 對於 SYMBOLS (逗號分隔的字符串)
            if value:
                clean_list = [s.strip() for s in value.split(',') if s.strip()]
                return json.dumps(clean_list, ensure_ascii=False)
            return "[]" 
        elif field_type == dict: # 對於 JSON 字段
            try:
                if value == '': return "{}"
                parsed_json = json.loads(value)
                return json.dumps(parsed_json, ensure_ascii=False)
            except json.JSONDecodeError:
                raise forms.ValidationError("請輸入有效的 JSON 格式。")
        return str(value) # 其他類型直接存儲為字符串

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance

@admin.register(TraderConfig)
class TraderConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'value_type', 'description')
    fields = ('key', 'value', 'value_type', 'description')
    search_fields = ('key',)

    def get_form(self, request, obj=None, **kwargs):
        # 動態創建一個新的表單類別來修改字段
        class CurrentTraderConfigForm(TraderConfigForm):
            pass

        if obj: # 編輯現有實例時
            config_key = obj.key
            field_type = CONFIG_FIELD_TYPES.get(config_key, str)
            display_label = CONFIG_KEY_TRANSLATIONS.get(config_key, config_key)

            # 動態為 'value' 字段創建正確的表單字段類型
            if field_type == bool:
                CurrentTraderConfigForm.base_fields['value'] = forms.BooleanField(
                    label=display_label,
                    required=False,
                    widget=forms.CheckboxInput(),
                    initial=obj.value == 'True'
                )
            elif field_type == int:
                CurrentTraderConfigForm.base_fields['value'] = forms.IntegerField(
                    label=display_label,
                    required=False,
                    widget=forms.NumberInput(),
                    initial=int(obj.value) if obj.value else None
                )
            elif field_type == float:
                CurrentTraderConfigForm.base_fields['value'] = forms.FloatField(
                    label=display_label,
                    required=False,
                    widget=forms.NumberInput(attrs={'step': '0.01'}),
                    initial=float(obj.value) if obj.value else None
                )
            elif field_type == list:
                CurrentTraderConfigForm.base_fields['value'] = forms.CharField(
                    label=display_label,
                    required=False,
                    widget=forms.Textarea(attrs={'rows': 3}),
                    initial=", ".join(json.loads(obj.value)) if obj.value else "" 
                )
            elif field_type == dict:
                CurrentTraderConfigForm.base_fields['value'] = forms.CharField(
                    label=display_label,
                    required=False,
                    widget=forms.Textarea(attrs={'rows': 5, 'cols': 40}),
                    initial=json.dumps(json.loads(obj.value), indent=2, ensure_ascii=False) if obj.value else "{}"
                )
            elif config_key == 'EXIT_MODE': # 新增：處理 EXIT_MODE 的下拉選單
                CurrentTraderConfigForm.base_fields['value'] = forms.ChoiceField(
                    label=display_label,
                    required=False,
                    choices=EXIT_MODE_CHOICES,
                    initial=obj.value
                )
            else: # 預設為 CharField (字符串)
                CurrentTraderConfigForm.base_fields['value'] = forms.CharField(
                    label=display_label,
                    required=False,
                    widget=forms.TextInput(), 
                    initial=obj.value
                )
            
            # 確保 Meta.fields 只包含 value
            CurrentTraderConfigForm.Meta.fields = ('value',)

        else: # 新增實例時
            # 為新增模式添加 key 字段
            CurrentTraderConfigForm.base_fields['key'] = forms.CharField(
                label="配置鍵名 (英文，例如: API_KEY)",
                required=True, # Key 在新增時是必須的
                widget=forms.TextInput()
            )
            CurrentTraderConfigForm.base_fields['value'].label = "配置值 (預設為文字輸入)"
            CurrentTraderConfigForm.base_fields['value'].widget = forms.TextInput() 
            # 確保 Meta.fields 包含 key 和 value
            CurrentTraderConfigForm.Meta.fields = ('key', 'value',)

        return CurrentTraderConfigForm

    def get_fieldsets(self, request, obj=None):
        if obj: # 編輯現有實例時，只顯示 value 字段
            return [
                (None, {'fields': ('value',)}),
            ]
        else: # 新增實例時，顯示 key 和 value 字段
            return [
                (None, {'fields': ('key', 'value',)}),
            ]

    # Custom method to display key with Chinese translation in list view
    def key_display(self, obj):
        return CONFIG_KEY_TRANSLATIONS.get(obj.key, obj.key)
    key_display.short_description = "配置鍵名"

    # Custom method to display value, especially for complex types, in list view
    def value_display(self, obj):
        field_type = CONFIG_FIELD_TYPES.get(obj.key, str)
        if field_type == bool:
            return "是" if obj.value == 'True' else "否"
        elif field_type == list:
            try:
                return ", ".join(json.loads(obj.value))
            except (json.JSONDecodeError, TypeError):
                return obj.value
        elif field_type == dict:
            try:
                parsed = json.loads(obj.value)
                return json.dumps(parsed, indent=2, ensure_ascii=False)
            except (json.JSONDecodeError, TypeError):
                return obj.value
        return obj.value
    value_display.short_description = "配置值"


# --- StrategyCombo Admin 配置 (保持之前修改的) ---

# 所有可用策略名稱（與你的策略檔案一致）
# 這個列表現在將用於 StrategyComboForm 的 conditions 欄位（在 'custom' 模式下）
# Note: This list should ideally be derived from a central place or fetched dynamically from strategy.base
# For now, assuming it's correctly defined and matches strategy.base.py
ALL_STRATEGY_CHOICES = [
    ('strategy_ema3_ema8_crossover', 'EMA(3)/EMA(8) 均線交叉'),
    ('strategy_bollinger_breakout', '布林帶突破'),
    ('strategy_vwap_deviation', 'VWAP 偏離'),
    ('strategy_volume_spike', '成交量爆量'),
    ('strategy_cci_reversal', 'CCI 反轉'),
    ('strategy_rsi_mean_reversion', 'RSI 均值回歸'),
    ('strategy_atr_breakout', 'ATR 突破'),
    ('strategy_ma_channel', '均線通道突破'),
    ('strategy_volume_trend', '成交量遞增'),
    ('strategy_cci_mid_trend', 'CCI 中期趨勢'),
    ('strategy_long_ema_crossover', 'EMA(50)/EMA(200) 黃金交叉'),
    ('strategy_adx_trend', 'ADX 趨勢強度'),
    ('strategy_bollinger_mean_reversion', '布林帶均值回歸'),
    ('strategy_ichimoku_cloud', 'Ichimoku 雲圖'),
    ('strategy_atr_mean_reversion', 'ATR 均值回歸'),
]

class StrategyComboForm(forms.ModelForm):
    # 將 model 的 conditions 欄位替換為一個 MultipleChoiceField (多選框)
    # 這只會在 combo_mode = 'custom' 時顯示
    conditions = forms.MultipleChoiceField( # 注意這裡直接使用 'conditions' 作為字段名
        label="自定義策略條件",
        choices=ALL_STRATEGY_CHOICES, # 使用上面定義的所有單一策略
        widget=forms.CheckboxSelectMultiple, # 使用多選框樣式
        required=False, # 非必填
        help_text="當選擇 '自定義' 模式時，選擇組成此策略組合的單一策略條件。",
    )

    class Meta:
        model = StrategyCombo
        # 這裡包含 combo_mode 和 conditions 欄位
        fields = ['name', 'description', 'is_active', 'combo_mode', 'conditions']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果是編輯現有對象，將 model 的 conditions 數據載入到 forms.MultipleChoiceField 中
        if self.instance.pk and self.instance.conditions:
            # conditions 儲存為 [{'type': 'strategy_name'}, ...] 格式
            selected_conditions_types = [d['type'] for d in self.instance.conditions if isinstance(d, dict) and 'type' in d]
            self.initial['conditions'] = selected_conditions_types # 直接設置 initial

        # 確保 combo_mode 下拉選單有正確的類別，以便 JavaScript 識別
        self.fields['combo_mode'].widget.attrs['class'] = 'strategy-combo-mode-selector'
        # 確保 conditions 多選框有正確的類別
        self.fields['conditions'].widget.attrs['class'] = 'custom-strategies-checkboxes'
        
        # 初始載入時，如果不是 'custom' 模式，則隱藏 conditions 字段
        if self.instance and self.instance.combo_mode != 'custom':
            self.fields['conditions'].widget = forms.HiddenInput()

    def clean_conditions(self):
        # 僅在 combo_mode 為 'custom' 時才處理 conditions
        combo_mode = self.cleaned_data.get('combo_mode')
        conditions = self.cleaned_data.get('conditions')

        if combo_mode == 'custom' and conditions:
            # 如果是自定義模式且有選擇，則將選擇的策略轉換為 JSONField 所需的格式
            return [{'type': cond_type} for cond_type in conditions]
        elif combo_mode == 'custom' and not conditions:
            # 如果是自定義模式但沒有選擇任何策略，返回空列表
            return []
        else:
            # 如果不是自定義模式，則清空 conditions
            return []
            
    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance


@admin.register(StrategyCombo)
class StrategyComboAdmin(admin.ModelAdmin):
    form = StrategyComboForm # 使用自定義的表單
    list_display = ('name', 'combo_mode', 'is_active', 'view_conditions_summary') # 顯示 combo_mode 和自定義的摘要函數
    list_editable = ('is_active',) # 允許直接在列表頁面編輯啟用狀態
    search_fields = ('name', 'description')
    list_filter = ('combo_mode', 'is_active') # 允許按組合包模式和啟用狀態過濾

    # 定義一個方法來顯示策略條件的摘要，而不是直接顯示 JSON
    def view_conditions_summary(self, obj):
        if obj.combo_mode == 'custom' and obj.conditions:
            strategy_names = [d.get('type', '未知策略') for d in obj.conditions if isinstance(d, dict)]
            # 查找策略的中文名
            display_names = []
            for s_name in strategy_names:
                for choice_value, choice_label in ALL_STRATEGY_CHOICES:
                    if choice_value == s_name:
                        display_names.append(choice_label)
                        break
                else:
                    display_names.append(s_name) # 如果找不到中文名，顯示英文名
            return ", ".join(display_names)
        elif obj.combo_mode == 'custom' and not obj.conditions:
            return "自定義模式，但未選擇任何策略"
        else:
            # Get the display name for the combo_mode from its choices
            combo_mode_display = dict(COMBO_MODE_CHOICES).get(obj.combo_mode, obj.combo_mode)
            return f"使用預設 '{combo_mode_display}' 策略組合"
    view_conditions_summary.short_description = '策略條件摘要' # 列表顯示的列名

    # 確保一次只能有一個 StrategyCombo 實例被設置為 is_active=True
    def save_model(self, request, obj, form, change):
        if obj.is_active:
            # 如果當前對象被設置為 active，則將所有其他對象設置為非 active
            StrategyCombo.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)

    class Media:
        js = ("admin/js/strategy_combo_admin.js",) # 這個 JS 文件需要你手動創建或修改

# 註冊其他模型 (保持現有)
admin.site.register(TradingPair)
admin.site.register(Position)
admin.site.register(Trade)
admin.site.register(DailyStats)
admin.site.register(TraderStatus)
