# 基於波動率的風險調整功能

## 功能概述

「基於波動率的風險調整」功能是SyrmaX交易系統的重要風控模組，旨在通過監控市場波動率（ATR）的異常變化，自動調整交易行為以降低風險。

## 核心功能

### 1. 波動率監控
- **ATR比率計算**：實時計算當前ATR與歷史平均ATR的比率
- **異常檢測**：當ATR比率超過設定閾值時觸發風險控制
- **自動恢復**：當波動率恢復正常時自動恢復交易

### 2. 交易暫停機制
- **自動暫停**：當ATR比率 ≥ 3.0時自動暫停交易
- **最小暫停時間**：確保暫停持續至少30分鐘，避免頻繁切換
- **狀態持久化**：暫停狀態存儲在數據庫中，重啟後保持

### 3. 倉位大小動態調整
- **高波動率減倉**：當ATR比率 > 2.0時減少倉位大小
- **低波動率增倉**：當ATR比率 < 0.5時適當增加倉位
- **調整係數計算**：根據波動率比例動態計算調整係數

## 配置參數

| 參數名稱 | 預設值 | 說明 |
|---------|--------|------|
| `ENABLE_VOLATILITY_RISK_ADJUSTMENT` | `true` | 是否啟用波動率風險調整 |
| `VOLATILITY_THRESHOLD_MULTIPLIER` | `2.0` | 倉位調整閾值倍數 |
| `VOLATILITY_PAUSE_THRESHOLD` | `3.0` | 交易暫停閾值（ATR比率） |
| `VOLATILITY_RECOVERY_THRESHOLD` | `1.5` | 交易恢復閾值（ATR比率） |
| `VOLATILITY_PAUSE_DURATION_MINUTES` | `30` | 最小暫停時間（分鐘） |

## 實現邏輯

### 波動率檢查流程
```python
def check_volatility_risk_adjustment(self, symbol: str, df: pd.DataFrame) -> bool:
    # 1. 獲取歷史平均ATR
    avg_atr = self.average_atrs.get(symbol)
    
    # 2. 計算當前ATR比率
    current_atr = df['atr'].iloc[-1]
    atr_ratio = current_atr / avg_atr
    
    # 3. 檢查是否應該暫停交易
    if atr_ratio >= self.volatility_pause_threshold:
        # 開始暫停交易
        return False
    
    # 4. 檢查是否可以恢復交易
    elif atr_ratio <= self.volatility_recovery_threshold:
        # 檢查最小暫停時間
        if elapsed_time >= min_pause_duration:
            # 恢復交易
            return True
    
    return True
```

### 倉位調整邏輯
```python
def adjust_position_size_by_volatility(self, symbol: str, base_quantity: float, df: pd.DataFrame) -> float:
    # 1. 計算ATR比率
    atr_ratio = current_atr / avg_atr
    
    # 2. 根據波動率調整倉位
    if atr_ratio > self.volatility_threshold_multiplier:
        # 高波動率：減少倉位
        adjustment_factor = self.volatility_threshold_multiplier / atr_ratio
        return base_quantity * adjustment_factor
    elif atr_ratio < 0.5:
        # 低波動率：適當增加倉位
        adjustment_factor = min(1.5, 1.0 / atr_ratio)
        return base_quantity * adjustment_factor
    else:
        # 正常波動率：不調整
        return base_quantity
```

## 數據庫模型

### VolatilityPauseStatus
```python
class VolatilityPauseStatus(models.Model):
    trading_pair = models.OneToOneField(TradingPair, primary_key=True)
    is_paused = models.BooleanField(default=False)
    pause_start_time = models.DateTimeField(null=True, blank=True)
    pause_reason = models.CharField(max_length=255, blank=True, null=True)
    current_atr_ratio = models.FloatField(default=1.0)
    last_updated = models.DateTimeField(auto_now=True)
```

## 管理界面

### Django Admin 功能
- **狀態監控**：查看每個交易對的波動率暫停狀態
- **ATR比率顯示**：實時顯示當前ATR比率
- **暫停原因記錄**：記錄暫停的具體原因
- **自動管理**：系統自動創建和管理暫停狀態

## 使用場景

### 1. 極端市場條件
- **重大新聞事件**：如央行政策變更、重大經濟數據發布
- **市場恐慌**：如黑天鵝事件、系統性風險
- **流動性不足**：如假期期間、低交易量時段

### 2. 技術性波動
- **突破失敗**：價格突破後快速回撤
- **假突破**：技術指標出現虛假信號
- **過度擴張**：價格偏離均值過遠

## 優勢特點

### 1. 自動化風險控制
- **無需人工干預**：系統自動監控和調整
- **實時響應**：毫秒級波動率檢測
- **智能恢復**：條件滿足時自動恢復交易

### 2. 數據驅動決策
- **歷史基準**：基於歷史平均ATR進行比較
- **動態調整**：根據市場條件動態調整參數
- **風險量化**：將波動率風險轉化為具體數值

### 3. 靈活配置
- **可調參數**：所有閾值都可以根據需要調整
- **開關控制**：可以完全啟用或禁用此功能
- **個性化設置**：不同交易對可以設置不同參數

## 測試驗證

### 單元測試
- **正常波動率測試**：驗證正常市場條件下的功能
- **高波動率測試**：驗證異常市場條件下的暫停機制
- **倉位調整測試**：驗證倉位大小的動態調整

### 回測驗證
- **歷史數據測試**：使用歷史數據驗證功能有效性
- **極端情況測試**：模擬極端市場條件下的表現
- **性能測試**：驗證對系統性能的影響

## 注意事項

### 1. 參數設置
- **閾值設置**：需要根據具體市場和交易對調整閾值
- **時間設置**：最小暫停時間要平衡風險控制和交易機會
- **監控頻率**：需要定期檢查和調整參數

### 2. 系統集成
- **與其他風控模組協調**：避免與其他風控功能衝突
- **日誌記錄**：確保所有操作都有詳細日誌記錄
- **監控告警**：設置適當的監控和告警機制

### 3. 持續優化
- **參數調優**：根據實際交易結果持續優化參數
- **功能擴展**：考慮添加更多波動率指標
- **用戶反饋**：收集用戶反饋並改進功能

## 總結

「基於波動率的風險調整」功能是SyrmaX交易系統的重要組成部分，通過智能監控市場波動率，自動調整交易行為，有效降低極端市場條件下的風險。該功能具有高度的自動化、靈活性和可配置性，能夠適應不同的市場環境和交易需求。
