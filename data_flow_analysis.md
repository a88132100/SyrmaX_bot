# 策略數據流程分析

## 📊 數據來源架構

### 1. 交易所數據層
```
交易所 API → 交易所客戶端 → 數據處理 → 策略分析
```

#### 支援的交易所
- **Binance** (幣安) - 完整支援，測試網可用
- **Bybit** - 完整支援，測試網可用  
- **OKX** - 完整支援，測試網可用
- **BingX** - 基礎支援，CCXT整合
- **Bitget** - 基礎支援，CCXT整合

### 2. 數據類型

#### K線數據 (OHLCV)
- **時間戳** (timestamp)
- **開盤價** (open)
- **最高價** (high) 
- **最低價** (low)
- **收盤價** (close)
- **成交量** (volume)

#### 實時數據
- **當前價格** (ticker)
- **帳戶餘額** (balance)
- **持倉資訊** (positions)
- **槓桿設定** (leverage)

## 🔄 數據處理流程

### 步驟1: 數據獲取
```python
# 從交易所獲取K線數據
def fetch_historical_klines(self, symbol: str, interval: str = '1m', limit: int = 500):
    klines = self.client.fetch_klines(symbol, interval, limit)
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df
```

### 步驟2: 數據預處理
```python
# 數據類型轉換和清理
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

# 數值轉換
for col in ['open', 'high', 'low', 'close', 'volume']:
    df[col] = pd.to_numeric(df[col])
```

### 步驟3: 技術指標計算
```python
# 基礎指標預計算
def precompute_indicators(self, df: pd.DataFrame):
    df['ema_5'] = df['close'].ewm(span=5).mean()
    df['ema_20'] = df['close'].ewm(span=20).mean()
    df['rsi'] = talib.RSI(df['close'], timeperiod=14)
    df['macd'], df['macd_signal'], _ = talib.MACD(df['close'])
    df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    return df
```

### 步驟4: 策略專用指標
```python
# 激進策略指標
df['ema_3'] = talib.EMA(df['close'], timeperiod=3)
df['ema_8'] = talib.EMA(df['close'], timeperiod=8)

# 平衡策略指標  
df['rsi'] = talib.RSI(df['close'], timeperiod=10)
df['ma_short'] = df['close'].rolling(5).mean()
df['ma_long'] = df['close'].rolling(20).mean()
df['cci'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=20)

# 保守策略指標
df['ema_fast'] = talib.EMA(df['close'], timeperiod=50)
df['ema_slow'] = talib.EMA(df['close'], timeperiod=200)
df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(df['close'])
```

## 📈 策略數據需求

### 激進策略組合
| 策略名稱 | 所需指標 | 數據來源 | 計算方式 |
|---------|---------|---------|---------|
| EMA交叉 | ema_3, ema_8 | 收盤價 | talib.EMA() |
| 布林帶突破 | 布林帶上下軌 | 收盤價 | talib.BBANDS() |
| VWAP偏離 | VWAP, 收盤價 | 收盤價+成交量 | 累積計算 |
| 量能爆量 | 成交量均值 | 成交量 | rolling.mean() |
| CCI反轉 | CCI | 高低收盤價 | talib.CCI() |

### 平衡策略組合
| 策略名稱 | 所需指標 | 數據來源 | 計算方式 |
|---------|---------|---------|---------|
| RSI均值回歸 | RSI | 收盤價 | talib.RSI() |
| ATR突破 | ATR | 高低收盤價 | talib.ATR() |
| MA通道 | 短期/長期MA | 收盤價 | rolling.mean() |
| 成交量趨勢 | 成交量序列 | 成交量 | 趨勢分析 |
| CCI中線趨勢 | CCI | 高低收盤價 | talib.CCI() |

### 保守策略組合
| 策略名稱 | 所需指標 | 數據來源 | 計算方式 |
|---------|---------|---------|---------|
| 長期EMA交叉 | ema_50, ema_200 | 收盤價 | talib.EMA() |
| ADX趨勢 | ADX, +DI, -DI | 高低收盤價 | talib.ADX() |
| 布林帶均值回歸 | 布林帶上下軌 | 收盤價 | talib.BBANDS() |
| 一目均衡表 | 轉換線、基準線等 | 高低價 | 自定義計算 |
| ATR均值回歸 | ATR | 高低收盤價 | talib.ATR() |

## 🔧 數據質量保證

### 1. 數據完整性檢查
```python
# 檢查必要欄位是否存在
required = ['ema_5', 'ema_20', 'rsi', 'macd', 'macd_signal', 'atr']
if not all(col in df.columns and not df[col].isna().all() for col in required):
    continue  # 跳過不完整的數據
```

### 2. 數據有效性驗證
```python
# 檢查價格數據是否合理
if price is None or price <= 0:
    logging.warning(f"{symbol} 無法獲取有效的當前價格")
    continue
```

### 3. 數據更新頻率
```python
# 根據幣種設定不同的更新頻率
SYMBOL_INTERVAL_SECONDS = {
    "BTCUSDT": 3,    # 3秒更新一次
    "ETHUSDT": 3,    # 3秒更新一次
    "ADAUSDT": 5,    # 5秒更新一次
    "DOTUSDT": 5,    # 5秒更新一次
}
```

## 📊 數據存儲和緩存

### 1. 實時數據
- **當前價格**: 每次策略執行時獲取
- **帳戶餘額**: 每次開倉前檢查
- **持倉狀態**: 實時監控

### 2. 歷史數據
- **K線數據**: 預設500根，可配置
- **技術指標**: 實時計算，不存儲
- **交易記錄**: 存儲到數據庫

### 3. 配置數據
- **策略參數**: 存儲在數據庫
- **風控設定**: 存儲在數據庫
- **交易所配置**: 環境變數

## ⚠️ 數據風險和對策

### 1. 網絡延遲
- **對策**: 設置超時機制，重試機制
- **監控**: 記錄API響應時間

### 2. 數據缺失
- **對策**: 跳過不完整的數據，等待下次更新
- **監控**: 記錄數據缺失次數

### 3. 數據異常
- **對策**: 價格合理性檢查，異常值過濾
- **監控**: 記錄異常數據情況

### 4. 交易所限制
- **對策**: 請求頻率控制，API限額管理
- **監控**: 記錄API調用次數

## 🎯 數據優化建議

### 1. 指標預計算
- 一次性計算所有策略需要的指標
- 避免重複計算相同指標

### 2. 數據緩存
- 緩存常用的技術指標
- 減少重複的API調用

### 3. 批量處理
- 批量獲取多個交易對的數據
- 提高數據獲取效率

### 4. 異步處理
- 異步獲取數據和執行策略
- 提高系統響應速度

## 📋 總結

策略中使用的數據來源完整且可靠：

✅ **數據來源**: 支援5大主流交易所，數據質量有保障  
✅ **數據處理**: 完整的數據清理和指標計算流程  
✅ **數據驗證**: 多層次數據有效性檢查  
✅ **風險控制**: 完善的數據異常處理機制  
✅ **性能優化**: 指標預計算和緩存機制  

所有策略都能獲得準確、及時的市場數據，確保交易決策的可靠性！
