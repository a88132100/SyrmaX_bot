# SyrmaX Frontend v2

全新的 SyrmaX 前端界面，採用現代化設計系統和組件架構。

## 技術棧

- **React 18** - 前端框架
- **TypeScript** - 類型安全
- **Tailwind CSS** - 樣式框架
- **Lucide React** - 圖標庫
- **Framer Motion** - 動畫庫
- **Vite** - 構建工具

## 設計系統

### 按鈕系統 (SxButton)

統一的按鈕組件，支援多種變體和尺寸：

- **變體**: primary, secondary, outline, ghost, success, warning, danger, icon, destructive
- **尺寸**: lg, md, sm
- **狀態**: hover, active, loading, disabled
- **圖標**: 支援 leftIcon 和 rightIcon

### 顏色系統

- **主色**: 漸層描邊 (#22D3EE → #A78BFA)
- **語意色**: 成功 (#10B981), 警告 (#F59E0B), 危險 (#EF4444), 資訊 (#60A5FA)
- **暗色主題**: 背景 (#0B1220), 卡片 (#0D1426)

### 響應式設計

- **容器**: max-w-[1280px] mx-auto px-6 md:px-8
- **KPI 網格**: grid-cols-1 md:grid-cols-2 xl:grid-cols-4
- **快捷功能**: grid-cols-1 md:grid-cols-3

## 功能頁面

1. **儀表板** (`/dashboard`) - Hero + KPI 4 卡 + 快捷 6 卡
2. **API 金鑰管理** (`/api-keys`) - 金鑰列表、測試、編輯
3. **交易對管理** (`/pairs`) - 交易對配置、模板
4. **持倉監控** (`/positions`) - 實時監控、風險控制
5. **交易記錄** (`/history`) - 歷史記錄、分析報告
6. **策略配置** (`/strategies`) - 策略創建、回測
7. **系統監控** (`/system`) - 系統狀態、日誌

## 開發

```bash
# 安裝依賴
npm install

# 啟動開發服務器
npm run dev

# 構建生產版本
npm run build
```

## 快捷鍵

- `/` - 搜尋
- `Shift + N` - 新增
- `G + A` - 到 API 金鑰
- `G + P` - 到 交易對
- `G + S` - 到 策略

## 無障礙設計

- 按鈕提供 aria-label
- 危險操作二段確認
- 鍵盤導航支援
- 高對比度支援