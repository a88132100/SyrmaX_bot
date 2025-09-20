# API金鑰管理指南

## 概述

本系統提供了安全的API金鑰管理功能，讓用戶可以管理多個交易所的API金鑰，而無需將敏感信息寫死在代碼中。

## 功能特點

### 🔐 安全性
- API金鑰和密鑰安全存儲在數據庫中
- 支持遮罩顯示，保護敏感信息
- 用戶只能管理自己的API金鑰

### 🏢 多交易所支持
- **Binance** - 全球最大的加密貨幣交易所
- **Bybit** - 專業衍生品交易所
- **OKX** - 知名加密貨幣交易所
- **BingX** - 社交交易平台
- **Bitget** - 加密貨幣衍生品交易所

### 🌐 網絡支持
- **測試網 (TESTNET)** - 用於開發和測試
- **主網 (MAINNET)** - 用於實際交易

### ⚙️ 權限管理
- **交易權限** - 允許下單和交易
- **讀取權限** - 允許查看市場數據和賬戶信息
- **提現權限** - 允許提取資金（謹慎使用）

## 使用方法

### 1. 前端界面

訪問 `http://localhost:5173/api-keys` 進入API金鑰管理頁面。

#### 主要功能：
- **查看API金鑰列表** - 顯示所有已配置的API金鑰
- **添加新API金鑰** - 支持多個交易所和網絡
- **編輯API金鑰** - 修改權限和備註
- **驗證API金鑰** - 測試API連接是否正常
- **刪除API金鑰** - 移除不需要的API金鑰

#### 統計信息：
- 總金鑰數量
- 活躍金鑰數量
- 已驗證金鑰數量
- 支持的交易所數量

### 2. API接口

#### 獲取API金鑰列表
```http
GET /api/api-keys/
Authorization: Bearer <your_token>
```

#### 創建API金鑰
```http
POST /api/api-keys/
Content-Type: application/json
Authorization: Bearer <your_token>

{
    "exchange": "BINANCE",
    "network": "TESTNET",
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "passphrase": "your_passphrase",  // 僅OKX需要
    "is_active": true,
    "can_trade": true,
    "can_read": true,
    "can_withdraw": false,
    "notes": "備註信息"
}
```

#### 驗證API金鑰
```http
POST /api/api-keys/{key_id}/verify/
Authorization: Bearer <your_token>
```

#### 測試API連接
```http
POST /api/api-keys/{key_id}/test/
Authorization: Bearer <your_token>
```

#### 獲取API金鑰摘要
```http
GET /api/api-key-summary/
Authorization: Bearer <your_token>
```

## 安全建議

### 🔒 最佳實踐
1. **使用測試網** - 在開發和測試階段使用測試網API金鑰
2. **最小權限原則** - 只授予必要的權限（通常只需要交易和讀取權限）
3. **定期輪換** - 定期更換API金鑰
4. **監控使用** - 定期檢查API金鑰的使用情況
5. **備份重要數據** - 定期備份交易配置和歷史數據

### ⚠️ 注意事項
- **不要啟用提現權限** - 除非絕對必要，否則不要啟用提現權限
- **保護密鑰安全** - 不要在公共場所或不安全的網絡環境中輸入API金鑰
- **使用強密碼** - 為您的賬戶設置強密碼
- **定期檢查** - 定期檢查API金鑰的狀態和權限

## 故障排除

### 常見問題

#### 1. API金鑰驗證失敗
- 檢查API金鑰和密鑰是否正確
- 確認交易所是否支持該網絡（測試網/主網）
- 檢查API金鑰權限是否足夠

#### 2. 連接測試失敗
- 檢查網絡連接
- 確認交易所API服務是否正常
- 檢查API金鑰是否已啟用

#### 3. 權限不足
- 檢查API金鑰的權限設置
- 確認是否需要額外的權限（如OKX需要passphrase）

## 技術實現

### 數據庫模型
- `ExchangeAPIKey` - 存儲API金鑰信息
- 支持多用戶，每個用戶只能管理自己的API金鑰
- 使用UUID作為主鍵，提高安全性

### 前端技術
- React + TypeScript
- Ant Design UI組件
- React Query 數據管理
- 響應式設計

### 後端技術
- Django REST Framework
- JWT認證
- 權限控制
- 錯誤處理和日誌記錄

## 更新日誌

### v1.0.0 (2024-01-XX)
- 初始版本發布
- 支持5個主要交易所
- 基本CRUD操作
- 權限管理
- 前端管理界面

## 聯繫支持

如果您在使用過程中遇到問題，請：
1. 檢查本文檔的故障排除部分
2. 查看系統日誌
3. 聯繫技術支持團隊

---

**重要提醒**：API金鑰包含敏感信息，請妥善保管，不要與他人分享。
