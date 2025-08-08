# SyrmaX - 高頻自動加密貨幣交易系統

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 如何將修改同步到GitHub

當您對代碼進行修改後，可以按照以下步驟將修改同步到GitHub：

1. 打開終端（命令提示符或PowerShell）
2. 導航到項目目錄：
   ```
   cd 您的項目路徑
   ```
3. 添加所有修改的文件到暫存區：
   ```
   git add .
   ```
4. 提交您的修改（添加描述性的提交信息）：
   ```
   git commit -m "描述您所做的修改"
   ```
5. 將修改推送到GitHub：
   ```
   git push origin main
   ```


> 讓一般使用者能用「策略包」秒級執行多幣種自動交易，支援多交易所切換、完善風控、訂閱制商業模式

## 🎯 專案目標

- **策略包交易**：預設多種策略組合，一鍵啟用自動交易
- **多交易所支援**：Binance、Bybit、OKX、BingX、Bitget
- **完善風控**：止盈止損、每日限額、連續止損控制
- **即時監控**：Web UI 即時查看交易狀態與績效
- **商業化準備**：訂閱制、多用戶、API 管理
- **用戶認證系統**：完整的註冊、登入、驗證 API
- **社交登入**：支援 Google、Facebook 等第三方登入
- **Email 驗證**：完整的 Email 發送和驗證功能

## 🏗️ 技術架構

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web/App UI    │    │   Trading Bot   │    │   Admin Panel   │
│   (React)       │    │   (Python)      │    │   (Django)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   Strategy      │    │   Database      │
│   (Real-time)   │    │   Engine        │    │   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Exchange      │    │   Risk          │    │   Cache         │
│   APIs          │    │   Management    │    │   (Redis)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心模組

- **資料接收層**：多交易所 API 整合
- **策略層**：15+ 技術指標策略，3種風險模式
- **風控層**：止盈止損、頻率限制、資金管理
- **下單層**：統一訂單介面，支援測試網
- **資產層**：持倉管理、績效追蹤、統計分析
- **認證層**：用戶註冊、登入、JWT Token 管理
- **社交層**：Google、Facebook 第三方登入
- **通訊層**：Email 發送、驗證、通知

## 🚀 快速開始

### 環境需求

- Python 3.8+
- Node.js 16+ (前端開發)
- PostgreSQL 12+ (推薦)
- Redis 6+ (快取)

### 安裝步驟

#### 1. 克隆專案
```bash
git clone https://github.com/your-username/SyrmaX_bot.git
cd SyrmaX_bot
```

#### 2. 建立虛擬環境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

#### 3. 安裝依賴
```bash
pip install -r requirements.txt
```

#### 4. 環境變數設定
```bash
# 複製環境變數範例
cp .env.example .env

# 編輯 .env 檔案
SYRMAX_API_KEY=your_api_key
SYRMAX_API_SECRET=your_api_secret
SYRMAX_EXCHANGE=BINANCE
SYRMAX_EXCHANGE_NAME=BINANCE
SYRMAX_USE_TESTNET=true
SYRMAX_TEST_MODE=true
```

#### 5. 資料庫設定
```bash
# 執行資料庫遷移
python manage.py makemigrations
python manage.py migrate

# 建立超級用戶
python manage.py createsuperuser
```

#### 6. 啟動服務
```bash
# 啟動 Django 開發伺服器
python manage.py runserver

# 啟動交易機器人 (新終端)
python manage.py runbot

# 啟動前端開發伺服器 (新終端)
cd frontend
npm install
npm run dev
```

### 訪問應用

- **Django 管理後台**：http://127.0.0.1:8000/admin/
- **API 文檔**：http://127.0.0.1:8000/api/
- **前端應用**：http://localhost:3000

## 📊 功能特色

### 策略系統
- **15+ 技術指標策略**：EMA、RSI、布林通道、ATR等
- **3種風險模式**：激進、平衡、保守
- **策略組合包**：預設組合，一鍵啟用
- **自動投票機制**：多策略信號整合

### 交易所支援
- ✅ **Binance**：完整支援，測試網可用
- ✅ **Bybit**：完整支援，測試網可用
- ✅ **OKX**：完整支援，測試網可用
- 🔄 **BingX**：基礎支援，CCXT整合
- 🔄 **Bitget**：基礎支援，CCXT整合

### 風控系統
- **止盈止損**：4種模式（百分比、固定金額、ATR動態、混合）
- **頻率限制**：每小時/每日交易次數限制
- **資金管理**：動態倉位大小，最大回撤控制
- **連續止損**：自動暫停交易機制
- **波動率風險調整**：基於ATR異常放大監控，自動暫停交易和調整倉位大小
- **最大同時持倉數量限制**：限制機器人同時開啟的交易對數量，控制整體風險暴露

### 監控功能
- **即時價格**：WebSocket 即時更新
- **交易歷史**：詳細交易記錄與分析
- **績效統計**：日/週/月績效報表
- **系統狀態**：機器人運行狀態監控

## 🔧 配置說明

### 交易所配置

#### Binance
```python
# 主網
SYRMAX_EXCHANGE=BINANCE
SYRMAX_USE_TESTNET=false

# 測試網
SYRMAX_EXCHANGE=BINANCE
SYRMAX_USE_TESTNET=true
```

#### Bybit
```python
SYRMAX_EXCHANGE=BYBIT
SYRMAX_USE_TESTNET=true  # 支援測試網
```

#### OKX
```python
SYRMAX_EXCHANGE=OKX
SYRMAX_USE_TESTNET=true
# 需要額外的 passphrase 參數
```

### 交易配置

```python
# 交易對
SYMBOLS=["BTCUSDT", "ETHUSDT"]

# 槓桿設定
LEVERAGE=30

# 資金管理
BASE_POSITION_RATIO=0.3
MIN_POSITION_RATIO=0.01
MAX_POSITION_RATIO=0.8

# 風控參數
MAX_TRADES_PER_HOUR=10
MAX_TRADES_PER_DAY=50
MAX_DAILY_LOSS_PERCENT=25.0

# 波動率風險調整配置
ENABLE_VOLATILITY_RISK_ADJUSTMENT=true
VOLATILITY_THRESHOLD_MULTIPLIER=2.0
VOLATILITY_PAUSE_THRESHOLD=3.0
VOLATILITY_RECOVERY_THRESHOLD=1.5
VOLATILITY_PAUSE_DURATION_MINUTES=30

# 最大同時持倉數量限制配置
ENABLE_MAX_POSITION_LIMIT=true
MAX_SIMULTANEOUS_POSITIONS=3
```

### 策略配置

```python
# 策略組合模式
COMBO_MODE_AGGRESSIVE="aggressive"    # 激進模式
COMBO_MODE_BALANCED="balanced"        # 平衡模式
COMBO_MODE_CONSERVATIVE="conservative" # 保守模式
COMBO_MODE_AUTO="auto"                # 自動模式
```

## 📈 API 文檔

### 核心端點

#### 交易相關
```http
GET    /api/trading-pairs/          # 獲取交易對列表
GET    /api/positions/              # 獲取持倉列表
GET    /api/trades/                 # 獲取交易歷史
GET    /api/daily-stats/            # 獲取每日統計
```

#### 策略相關
```http
GET    /api/strategy-combos/        # 獲取策略組合
POST   /api/strategy-combos/        # 創建策略組合
PUT    /api/strategy-combos/{id}/   # 更新策略組合
DELETE /api/strategy-combos/{id}/   # 刪除策略組合
```

#### 配置相關
```http
GET    /api/trader-configs/         # 獲取交易配置
PUT    /api/trader-configs/{key}/   # 更新配置
GET    /api/trader-status/          # 獲取機器人狀態
```

### WebSocket 即時資料

```javascript
// 連接 WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/trading/');

// 訂閱價格更新
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'price',
  symbol: 'BTCUSDT'
}));

// 接收即時資料
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('價格更新:', data);
};
```

## 🛠️ 開發指南

### 專案結構

```
SyrmaX_bot/
├── exchange/              # 交易所客戶端
│   ├── base.py           # 基礎介面
│   ├── binance_client.py # Binance 客戶端
│   ├── bybit_client.py   # Bybit 客戶端
│   ├── okx_client.py     # OKX 客戶端
│   └── ccxt_client.py    # CCXT 通用客戶端
├── strategy/              # 策略模組
│   ├── base.py           # 策略基礎
│   ├── aggressive.py     # 激進策略
│   ├── balanced.py       # 平衡策略
│   └── conservative.py   # 保守策略
├── trading/              # 交易核心
│   ├── trader.py         # 主要交易邏輯
│   ├── constants.py      # 常數定義
│   ├── config_manager.py # 配置管理
│   └── testnet_handler.py # 測試網處理
├── trading_api/          # Django API
│   ├── models.py         # 資料模型
│   ├── views.py          # API 視圖
│   ├── serializers.py    # 序列化器
│   └── urls.py           # URL 路由
├── docs/                 # 文檔
│   ├── database_evaluation.md
│   └── frontend_architecture.md
└── frontend/             # React 前端 (待開發)
```

### 新增交易所

1. 在 `exchange/` 目錄建立新的客戶端檔案
2. 繼承 `ExchangeClient` 基礎類別
3. 實作所有必要方法
4. 在 `load_exchange_client.py` 中註冊

```python
# exchange/new_exchange_client.py
from exchange.base import ExchangeClient

class NewExchangeClient(ExchangeClient):
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        # 初始化邏輯
        pass
    
    def get_price(self, symbol: str) -> float:
        # 獲取價格邏輯
        pass
    
    # 實作其他必要方法...
```

### 新增策略

1. 在對應的策略檔案中新增函數
2. 在 `strategy/base.py` 中註冊
3. 更新策略組合配置

```python
# strategy/balanced.py
def strategy_new_indicator(df: pd.DataFrame) -> int:
    """
    新策略實作
    
    Returns:
        int: 1 (買入), -1 (賣出), 0 (持有)
    """
    # 策略邏輯
    return signal
```

### 測試

```bash
# 執行單元測試
python manage.py test

# 執行特定測試
python manage.py test trading_api.tests

# 執行測試網測試
python manage.py test --settings=syrmax_api.test_settings
```

## 🔒 安全注意事項

### API 金鑰安全
- 使用環境變數儲存敏感資訊
- 定期輪換 API 金鑰
- 設定適當的 API 權限
- 啟用 IP 白名單

### 風控建議
- 先使用測試網進行測試
- 設定合理的止損限制
- 監控交易頻率
- 定期檢查系統狀態

### 部署安全
- 使用 HTTPS
- 設定防火牆規則
- 定期備份資料
- 監控系統日誌

## 📝 更新日誌

### v1.0.0 (2024-01-XX)
- ✅ 完成核心交易功能
- ✅ 支援 Binance、Bybit、OKX
- ✅ 實作 15+ 技術指標策略
- ✅ 建立風控系統
- ✅ 完成 Django API 後端
- 🔄 前端開發進行中

### 即將推出
- 🔄 React 前端 UI
- 🔄 WebSocket 即時更新
- 🔄 更多交易所支援
- 🔄 進階策略編輯器
- 🔄 手機 App

## 🤝 貢獻指南

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 開發規範
- 遵循 PEP 8 Python 程式碼風格
- 撰寫單元測試
- 更新相關文檔
- 使用有意義的提交訊息

## 📄 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 📞 支援

- **文檔**：查看 [docs/](docs/) 目錄
- **問題回報**：開啟 [GitHub Issue](https://github.com/your-username/SyrmaX_bot/issues)
- **討論**：加入 [Discord 社群](https://discord.gg/syrmax)
- **郵件**：contact@syrmax.com

## ⚠️ 免責聲明

本軟體僅供教育和研究用途。加密貨幣交易具有高風險，可能導致資金損失。使用者應自行承擔交易風險，開發者不承擔任何責任。

---

**SyrmaX** - 讓加密貨幣交易更簡單、更安全、更智能 🚀
