# SyrmaX 稽核/解釋層

## 概述

稽核/解釋層是SyrmaX交易機器人的核心安全組件，提供：

1. **強制風控檢查** - 多層風控保護，確保交易安全
2. **智能解釋生成** - 自動生成人話解釋，說明每筆交易的決策依據
3. **完整稽核日誌** - 記錄所有交易過程，便於分析和監管
4. **實時監控** - 提供稽核儀表板和API查詢

## 架構設計

```
信號生成 → 解釋生成（並行）
    ↓
現有風控檢查 → 稽核記錄
    ↓
稽核風控檢查 → 稽核記錄
    ↓
決策：取最嚴格結果
    ↓
下單/拒絕 → 稽核記錄
```

## 核心組件

### 1. 事件模型 (`events.py`)
- **SignalGenerated**: 信號生成事件
- **RiskChecked**: 風控檢查事件
- **ExplainCreated**: 解釋生成事件
- **OrderSubmitted/OrderFilled/OrderRejected**: 訂單事件
- **RiskCheckResult**: 風控檢查結果

### 2. 風控系統 (`risk.py`)
- **AuditRiskManager**: 風控管理器
- **RiskRule**: 風控規則定義
- 預設規則：
  - 槓桿上限檢查
  - 距爆倉距離檢查
  - 單日最大虧損檢查
  - 連續虧損冷卻檢查
  - 滑點上限檢查

### 3. 解釋系統 (`explain.py`)
- **ExplanationGenerator**: 解釋生成器
- **5種母模板**：
  - `trend_atr_v2`: 趨勢追蹤ATR模板
  - `range_revert_v1`: 區間反轉模板
  - `breakout_pullback`: 突破回抽模板
  - `momentum_volume`: 動量量能模板
  - `mean_reversion`: 均值回歸模板

### 4. 稽核日誌 (`audit.py`)
- **AuditLogger**: 稽核日誌記錄器
- **雙重存儲**：JSONL文件 + SQLite資料庫
- **批次寫入**：提高性能，減少I/O開銷
- **日報表生成**：自動生成每日稽核報告

### 5. 執行管道 (`execution.py`)
- **AuditPipeline**: 稽核執行管道
- 整合風控檢查、解釋生成和稽核記錄
- 統一的決策邏輯

### 6. 系統整合 (`audit_integration.py`)
- **AuditIntegration**: 稽核整合器
- 與現有交易系統無縫整合
- 提供統一的API介面

## 配置管理

稽核層配置通過現有的`TraderConfig`系統管理：

### 基本配置
```python
AUDIT_ENABLED = True  # 是否啟用稽核層
```

### 風控規則配置
```python
AUDIT_LEVERAGE_CAP = 2.0                    # 槓桿上限
AUDIT_DIST_TO_LIQ_MIN = 15.0                # 距爆倉最小距離(%)
AUDIT_DAILY_MAX_LOSS = 3.0                  # 單日最大虧損(%)
AUDIT_CONSECUTIVE_LOSS_COOLDOWN = 3         # 連續虧損冷卻次數
AUDIT_MAX_SLIPPAGE_BPS = 5.0                # 最大滑點限制(bps)
```

### 解釋模板配置
```python
AUDIT_EXPLAIN_TEMPLATES = ["trend_atr_v2", "range_revert_v1"]  # 啟用的模板
AUDIT_EXPLAIN_QUALITY_THRESHOLD = "NORMAL"  # 解釋品質閾值
```

### 日誌配置
```python
AUDIT_LOG_DIR = "data/audit"     # 稽核日誌目錄
AUDIT_BATCH_SECONDS = 2          # 批次寫入間隔(秒)
AUDIT_BATCH_SIZE = 100           # 批次寫入大小
```

## 使用方法

### 1. 自動整合
稽核層已自動整合到現有交易流程中，無需額外配置：

```python
# 啟動機器人（包含稽核層）
python manage.py runbot
```

### 2. 手動使用
```python
from core.audit_integration import AuditIntegration

# 創建稽核整合器
integration = AuditIntegration(trader)

# 處理交易信號
result = integration.process_trading_signal(signal, symbol, df, strategy_name)
if result['approved']:
    # 信號通過稽核，可以下單
    pass
else:
    # 信號被拒絕，原因在result['reason']中
    pass
```

### 3. 查看稽核報告
```python
# 獲取今日稽核報告
report = integration.get_audit_report()

# 獲取指定日期報告
report = integration.get_audit_report("20241201")
```

## API端點

### 稽核儀表板
```
GET /api/audit/dashboard/
```

### 稽核報告
```
GET /api/audit/report/?date=20241201
```

### 稽核事件
```
GET /api/audit/events/?date=20241201&event_type=signal_generated&symbol=BTCUSDT
```

### 稽核配置
```
GET /api/audit/config/
POST /api/audit/config/
```

## 測試

運行稽核層測試：

```bash
python test_audit_system.py
```

測試覆蓋：
- 事件模型創建和序列化
- 風控規則檢查邏輯
- 解釋模板生成
- 稽核日誌記錄
- 稽核管道執行
- 系統整合功能

## 監控和調試

### 1. 日誌文件
- **JSONL日誌**: `data/audit/YYYYMMDD.jsonl`
- **SQLite資料庫**: `data/audit/audit.db`
- **系統日誌**: `logs/trading.log`

### 2. 稽核儀表板
訪問 `templates/audit_dashboard.html` 查看實時稽核狀態

### 3. 關鍵指標
- **風控通過率**: 通過風控檢查的比例
- **訂單成交率**: 提交訂單的成交比例
- **解釋品質**: 生成解釋的品質評分
- **事件處理延遲**: 稽核處理的平均延遲

## 故障排除

### 常見問題

1. **稽核層未啟用**
   - 檢查 `AUDIT_ENABLED` 配置
   - 查看系統日誌中的錯誤信息

2. **風控規則過於嚴格**
   - 調整風控規則閾值
   - 檢查現有風控和稽核風控的衝突

3. **解釋生成失敗**
   - 檢查技術指標數據完整性
   - 查看解釋模板配置

4. **日誌記錄問題**
   - 檢查 `data/audit` 目錄權限
   - 查看批次寫入線程狀態

### 調試模式

啟用詳細日誌：

```python
import logging
logging.getLogger('core').setLevel(logging.DEBUG)
```

## 性能優化

### 1. 批次寫入
- 調整 `AUDIT_BATCH_SECONDS` 和 `AUDIT_BATCH_SIZE`
- 平衡寫入頻率和內存使用

### 2. 佇列管理
- 監控記憶體佇列使用率
- 調整 `AUDIT_MAX_QUEUE_SIZE`

### 3. 資料庫優化
- 定期清理歷史稽核數據
- 為常用查詢添加索引

## 未來擴展

### 1. 高級功能
- 模擬vs實盤對比分析
- 機器學習風控規則
- 自適應解釋模板

### 2. 監控增強
- 實時告警系統
- 性能指標監控
- 自動化報告生成

### 3. 集成擴展
- 外部風控系統集成
- 第三方監控工具
- 雲端日誌存儲

## 貢獻指南

1. 遵循現有的代碼風格
2. 添加適當的測試用例
3. 更新相關文檔
4. 確保向後兼容性

## 授權

本稽核層組件遵循MIT授權條款。
