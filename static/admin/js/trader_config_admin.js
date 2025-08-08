// 交易配置管理後台的動態表單 JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // 獲取配置鍵選擇器和配置值字段
    const keySelector = document.querySelector('.config-key-selector');
    const valueField = document.querySelector('#id_value');
    const valueFieldContainer = valueField ? valueField.closest('.form-row') : null;
    
    if (keySelector && valueField) {
        // 定義不同配置鍵對應的表單類型
        const fieldTypes = {
            'USE_TESTNET': 'bool_choice',
            'TEST_MODE': 'bool_choice',
            'ENABLE_TRADE_LOG': 'bool_choice',
            'ENABLE_TRADE_LIMITS': 'bool_choice',
            'AUTO_SET_LEVERAGE': 'bool_choice',
            'ENABLE_VOLATILITY_RISK_ADJUSTMENT': 'bool_choice',
            'EXCHANGE_NAME': 'exchange_choice',
            'EXIT_MODE': 'exit_mode_choice',
            'LEVERAGE': 'integer',
            'MAX_CONSECUTIVE_STOP_LOSS': 'integer',
            'GLOBAL_INTERVAL_SECONDS': 'integer',
            'MAX_TRADES_PER_HOUR': 'integer',
            'MAX_TRADES_PER_DAY': 'integer',
            'VOLATILITY_PAUSE_DURATION_MINUTES': 'integer',
            'ATR_LENGTH': 'integer',
            'BASE_POSITION_RATIO': 'float',
            'MIN_POSITION_RATIO': 'float',
            'MAX_POSITION_RATIO': 'float',
            'RISK_PER_TRADE_PCT': 'float',
            'PRICE_TAKE_PROFIT_PERCENT': 'float',
            'PRICE_STOP_LOSS_PERCENT': 'float',
            'AMOUNT_TAKE_PROFIT_USDT': 'float',
            'AMOUNT_STOP_LOSS_USDT': 'float',
            'ATR_TAKE_PROFIT_MULTIPLIER': 'float',
            'ATR_STOP_LOSS_MULTIPLIER': 'float',
            'ATR_MULTIPLIER': 'float',
            'HYBRID_MIN_TAKE_PROFIT_USDT': 'float',
            'HYBRID_MAX_TAKE_PROFIT_USDT': 'float',
            'HYBRID_MIN_STOP_LOSS_USDT': 'float',
            'HYBRID_MAX_STOP_LOSS_USDT': 'float',
            'MAX_DAILY_LOSS_PCT': 'float',
            'VOLATILITY_THRESHOLD_MULTIPLIER': 'float',
            'VOLATILITY_PAUSE_THRESHOLD': 'float',
            'VOLATILITY_RECOVERY_THRESHOLD': 'float',
            'SYMBOLS': 'list',
            'SYMBOL_INTERVALS': 'dict',
            'SYMBOL_INTERVAL_SECONDS': 'dict',
            'RISK_LIMIT_TIERS': 'list',
        };

        // 定義選項
        const booleanChoices = [
            ['True', '開啟'],
            ['False', '關閉']
        ];
        
        const exchangeChoices = [
            ['BINANCE', 'Binance'],
            ['BYBIT', 'Bybit'],
            ['OKX', 'OKX'],
            ['BINGX', 'BingX'],
            ['BITGET', 'Bitget']
        ];
        
        const exitModeChoices = [
            ['PERCENTAGE', '百分比'],
            ['AMOUNT', '固定金額'],
            ['ATR', 'ATR動態'],
            ['HYBRID', '混合模式']
        ];

        // 更新表單字段的函數
        function updateValueField() {
            const selectedKey = keySelector.value;
            const fieldType = fieldTypes[selectedKey] || 'string';
            
            // 移除現有的字段
            if (valueFieldContainer) {
                const existingField = valueFieldContainer.querySelector('#id_value');
                if (existingField) {
                    existingField.remove();
                }
            }
            
            // 創建新的字段
            let newField;
            let label = '配置值';
            
            switch (fieldType) {
                case 'bool_choice':
                    newField = createSelectField(booleanChoices, label);
                    break;
                case 'exchange_choice':
                    newField = createSelectField(exchangeChoices, label);
                    break;
                case 'exit_mode_choice':
                    newField = createSelectField(exitModeChoices, label);
                    break;
                case 'integer':
                    newField = createNumberField('number', label, '整數');
                    break;
                case 'float':
                    newField = createNumberField('number', label, '浮點數', '0.01');
                    break;
                case 'list':
                    newField = createTextareaField(label, '請輸入逗號分隔的值，例如: BTCUSDT, ETHUSDT', 3);
                    break;
                case 'dict':
                    newField = createTextareaField(label, '請輸入 JSON 格式，例如: {"BTCUSDT": 3, "ETHUSDT": 5}', 5);
                    break;
                default:
                    newField = createTextField(label, '文字輸入');
                    break;
            }
            
            // 插入新字段
            if (valueFieldContainer) {
                valueFieldContainer.appendChild(newField);
            }
        }
        
        // 創建選擇框字段
        function createSelectField(choices, label) {
            const container = document.createElement('div');
            container.className = 'form-row';
            
            const labelElement = document.createElement('label');
            labelElement.textContent = label;
            labelElement.setAttribute('for', 'id_value');
            
            const select = document.createElement('select');
            select.id = 'id_value';
            select.name = 'value';
            select.className = 'form-control';
            
            // 添加選項
            choices.forEach(([value, text]) => {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = text;
                select.appendChild(option);
            });
            
            container.appendChild(labelElement);
            container.appendChild(select);
            return container;
        }
        
        // 創建數字輸入字段
        function createNumberField(type, label, placeholder, step = '1') {
            const container = document.createElement('div');
            container.className = 'form-row';
            
            const labelElement = document.createElement('label');
            labelElement.textContent = label;
            labelElement.setAttribute('for', 'id_value');
            
            const input = document.createElement('input');
            input.type = type;
            input.id = 'id_value';
            input.name = 'value';
            input.className = 'form-control';
            input.placeholder = placeholder;
            input.step = step;
            
            container.appendChild(labelElement);
            container.appendChild(input);
            return container;
        }
        
        // 創建文字輸入字段
        function createTextField(label, placeholder) {
            const container = document.createElement('div');
            container.className = 'form-row';
            
            const labelElement = document.createElement('label');
            labelElement.textContent = label;
            labelElement.setAttribute('for', 'id_value');
            
            const input = document.createElement('input');
            input.type = 'text';
            input.id = 'id_value';
            input.name = 'value';
            input.className = 'form-control';
            input.placeholder = placeholder;
            
            container.appendChild(labelElement);
            container.appendChild(input);
            return container;
        }
        
        // 創建文字區域字段
        function createTextareaField(label, placeholder, rows = 3) {
            const container = document.createElement('div');
            container.className = 'form-row';
            
            const labelElement = document.createElement('label');
            labelElement.textContent = label;
            labelElement.setAttribute('for', 'id_value');
            
            const textarea = document.createElement('textarea');
            textarea.id = 'id_value';
            textarea.name = 'value';
            textarea.className = 'form-control';
            textarea.placeholder = placeholder;
            textarea.rows = rows;
            
            container.appendChild(labelElement);
            container.appendChild(textarea);
            return container;
        }
        
        // 監聽選擇器變化
        keySelector.addEventListener('change', updateValueField);
        
        // 初始化表單
        if (keySelector.value) {
            updateValueField();
        }
    }
});
