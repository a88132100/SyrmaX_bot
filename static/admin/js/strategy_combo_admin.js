// C:\Users\user\Desktop\SyrmaX_bot\static\admin\js\strategy_combo_admin.js

(function($) {
    $(document).ready(function() {
        // Mapping of preset names to their associated strategy types
        // This must match STRATEGY_PRESETS in admin.py
        const STRATEGY_PRESETS_JS = {
            "aggressive": [
                "strategy_ema3_ema8_crossover",
                "strategy_bollinger_breakout",
                "strategy_volume_spike",
                "strategy_cci_reversal",
                "strategy_vwap_deviation",
            ],
            "balanced": [
                "strategy_rsi_mean_reversion",
                "strategy_atr_breakout",
                "strategy_ma_channel",
                "strategy_volume_trend",
                "strategy_cci_mid_trend",
            ],
            "conservative": [
                "strategy_long_ema_crossover",
                "strategy_adx_trend",
                "strategy_bollinger_mean_reversion",
                "strategy_ichimoku_cloud",
                "strategy_atr_mean_reversion",
            ]
        };

        function updateStrategyConditions(selectElement) {
            const selectedPreset = $(selectElement).val();
            const $conditionsCheckboxes = $('.strategy-conditions-checkboxes input[type="checkbox"]');

            // Uncheck all conditions first
            $conditionsCheckboxes.prop('checked', false);

            if (selectedPreset && selectedPreset !== "") {
                const presetConditions = STRATEGY_PRESETS_JS[selectedPreset];
                if (presetConditions) {
                    presetConditions.forEach(function(condType) {
                        $conditionsCheckboxes.filter('[value="' + condType + '"]').prop('checked', true);
                    });
                }
            }
        }

        // Attach the function to the window object so it can be called from onchange
        window.updateStrategyConditions = updateStrategyConditions;

        // Initial call on page load if a preset is already selected
        const initialPreset = $('#id_strategy_style_preset').val();
        if (initialPreset && initialPreset !== "") {
            updateStrategyConditions($('#id_strategy_style_preset')[0]);
        }

        // 選擇策略模式下拉選單
        var $comboModeSelector = $('.strategy-combo-mode-selector');
        // 選擇自定義策略多選框組的父元素，通常是其所在的 `div.form-row` 或 `div.field-conditions`
        // 根據 Django Admin 的實際 HTML 結構調整選擇器
        var $customStrategiesField = $('.field-conditions'); 

        // 定義顯示/隱藏自定義策略字段的函數
        function toggleCustomStrategies() {
            if ($comboModeSelector.val() === 'custom') {
                $customStrategiesField.show(); // 顯示自定義策略字段
            } else {
                $customStrategiesField.hide(); // 隱藏自定義策略字段
            }
        }

        // 頁面載入時先執行一次，確保初始狀態正確
        toggleCustomStrategies();

        // 當策略模式下拉選單改變時，重新執行顯示/隱藏函數
        $comboModeSelector.on('change', toggleCustomStrategies);
    });
})(django.jQuery);