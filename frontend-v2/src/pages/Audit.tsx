/**
 * 稽核與風險日誌頁面
 * 
 * 功能：
 * - 顯示系統的策略事件、風險控管與 API 狀態記錄
 * - 支援多種篩選條件（時間區間、事件類型、風險等級、機器人）
 * - 點擊列表項目可查看詳細資訊（Drawer）
 * - 目前使用模擬資料，未連接真實交易所
 */

import React, { useState, useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Drawer } from '@/components/ui/drawer'
import { Dropdown, DropdownItem } from '@/components/ui/Dropdown'
import { loadBots } from '@/lib/botsStorage'
import { cn } from '@/lib/utils'
import { getSeverityBadgeStyle as getSeverityStyle, getNeutralBadgeStyle, getSecondaryBadgeStyle } from '@/lib/subtleBadgeStyles'
import { STRATEGY_BUNDLES } from '@/components/strategies/strategyBundles'

// 型別定義
type AuditSeverity = 'info' | 'warning' | 'danger'
type AuditEventType = 'strategy' | 'risk' | 'system' | 'api'

interface AuditLogItem {
  id: string
  timestamp: string // ISO 字串
  botId?: string
  botName?: string
  exchange?: string
  symbol?: string
  eventType: AuditEventType
  severity: AuditSeverity
  title: string
  message: string
  suggestion?: string
  strategyBundleId?: string
}

// 工具函式：判斷時間是否在指定區間內
function matchTimeRange(timestamp: string, range: '1d' | '7d' | '30d'): boolean {
  const t = new Date(timestamp).getTime()
  const now = Date.now()
  const oneDay = 24 * 60 * 60 * 1000

  if (range === '1d') return now - t <= oneDay
  if (range === '7d') return now - t <= 7 * oneDay
  return now - t <= 30 * oneDay
}

// 取得事件類型顯示文字
function getEventTypeLabel(type: AuditEventType): string {
  switch (type) {
    case 'strategy':
      return '策略事件'
    case 'risk':
      return '風險控管'
    case 'system':
      return '系統'
    case 'api':
      return 'API'
  }
}

// 取得風險等級顯示文字
function getSeverityLabel(severity: AuditSeverity): string {
  switch (severity) {
    case 'info':
      return '資訊'
    case 'warning':
      return '警告'
    case 'danger':
      return '危險'
  }
}

// 取得風險等級 Badge 顏色樣式（尺寸由 className 控制）
function getSeverityColorStyle(severity: AuditSeverity): React.CSSProperties {
  const fullStyle = getSeverityStyle(severity)
  // 只返回顏色相關的樣式，明確排除尺寸相關屬性
  return {
    backgroundColor: fullStyle.backgroundColor,
    borderColor: fullStyle.borderColor,
    color: fullStyle.color,
    // 明確不包含：height, paddingLeft, paddingRight, fontSize, fontWeight 等
  }
}

// 取得事件類型 Badge 完整樣式（用於表格）
function getEventTypeBadgeStyle(type: AuditEventType): React.CSSProperties {
  // 事件類型使用中性樣式：bg-white/5 border-white/10 text-text-secondary
  return {
    display: 'inline-flex',
    alignItems: 'center',
    height: '24px',
    borderRadius: '9999px',
    borderWidth: '1px',
    paddingLeft: '10px',
    paddingRight: '10px',
    fontSize: '12px',
    fontWeight: 500,
    whiteSpace: 'nowrap',
    backgroundColor: 'rgba(255, 255, 255, 0.05)', // white/5
    borderColor: 'rgba(255, 255, 255, 0.1)', // white/10
    color: '#A6AEC3', // text-text-secondary
  }
}

// 取得事件類型 Badge 顏色樣式（用於 Drawer，尺寸由 className 控制）
function getEventTypeColorStyle(type: AuditEventType): React.CSSProperties {
  return {
    backgroundColor: 'rgba(255, 255, 255, 0.05)', // white/5
    borderColor: 'rgba(255, 255, 255, 0.1)', // white/10
    color: '#A6AEC3', // text-text-secondary
  }
}

// 格式化時間顯示（表格用，到分鐘）
function formatTimestampShort(timestamp: string): string {
  const date = new Date(timestamp)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

// 格式化時間顯示（Drawer 用，包含秒數）
function formatTimestampFull(timestamp: string): string {
  const date = new Date(timestamp)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

// 正規化事件標題：移除幣種前綴、機器人字樣，統一格式
function normalizeEventTitle(raw: string): string {
  if (!raw) return "事件詳情"

  let t = raw.trim()

  // 1) 移除開頭幣種代碼（BTC/ETH…）
  t = t.replace(/^([A-Z0-9]{2,12})\s+/, "")

  // 2) 去掉「機器人」字樣避免跟 meta 重複
  t = t.replace(/機器人/g, "").replace(/\s+/g, " ").trim()

  // 3) 特例：連續停損自動暫停
  const m = t.match(/連續\s*(\d+)\s*筆停損.*已自動暫停/)
  if (m?.[1]) return `已自動暫停：連續 ${m[1]} 筆停損`

  // 4) 有逗號就取第一段（更像標題）
  if (t.includes("，")) t = t.split("，")[0].trim()

  // 5) 最後保險：太長就截斷
  const max = 18
  if (t.length > max) t = t.slice(0, max) + "…"

  return t || "事件詳情"
}

export default function AuditPage() {
  const navigate = useNavigate()
  const [selectedSeverity, setSelectedSeverity] = useState<AuditSeverity | 'all'>('all')
  const [selectedEventType, setSelectedEventType] = useState<AuditEventType | 'all'>('all')
  const [selectedBotId, setSelectedBotId] = useState<string | 'all'>('all')
  const [selectedRange, setSelectedRange] = useState<'1d' | '7d' | '30d'>('7d')
  const [selectedLog, setSelectedLog] = useState<AuditLogItem | null>(null)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [bots, setBots] = useState<ReturnType<typeof loadBots>>([])

  // 開發模式：確認組件已載入最新版本
  useEffect(() => {
    if (import.meta.env.DEV) {
      console.log('[AuditPage] 組件已載入 - v1.1 (已優化)')
    }
  }, [])

  // 載入機器人列表
  useEffect(() => {
    const loadedBots = loadBots()
    setBots(loadedBots)
  }, [])

  // 建立假資料（部分對應真實 botId，部分留空）
  const MOCK_AUDIT_LOGS: AuditLogItem[] = useMemo(() => {
    const now = Date.now()
    const botIds = bots.length > 0 ? bots.map(b => b.id) : []
    const bot1Id = botIds[0] || undefined
    const bot2Id = botIds[1] || undefined
    const bot3Id = botIds[2] || undefined

    return [
      {
        id: 'audit-1',
        timestamp: new Date(now - 2 * 60 * 60 * 1000).toISOString(), // 2小時前
        botId: bot1Id,
        botName: bot1Id ? bots.find(b => b.id === bot1Id)?.name : undefined,
        exchange: 'BINANCE',
        symbol: 'BTC/USDT',
        eventType: 'strategy',
        severity: 'danger',
        title: 'BTC 趨勢跟隨機器人連續 3 筆停損，已自動暫停',
        message: '機器人在過去 1 小時內連續觸發 3 次停損，系統已自動暫停交易以避免進一步損失。建議檢查市場趨勢是否發生變化，或調整策略參數。',
        suggestion: '建議檢查 BTC/USDT 的市場趨勢是否發生變化，考慮調整停損點位或降低倉位大小。',
        strategyBundleId: bot1Id ? bots.find(b => b.id === bot1Id)?.strategyPackId : undefined,
      },
      {
        id: 'audit-2',
        timestamp: new Date(now - 5 * 60 * 60 * 1000).toISOString(), // 5小時前
        botId: undefined, // 未知機器人
        exchange: 'BINANCE',
        symbol: undefined,
        eventType: 'api',
        severity: 'warning',
        title: 'Binance API 連線異常，已重新連線',
        message: '檢測到 Binance API 連線中斷，系統已自動嘗試重新連線並成功恢復。中斷時間約 30 秒，期間未執行任何交易。',
        suggestion: '建議持續監控 API 連線狀態，如頻繁出現連線問題，請檢查網路環境或 API 金鑰設定。',
      },
      {
        id: 'audit-3',
        timestamp: new Date(now - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1天前
        botId: bot2Id,
        botName: bot2Id ? bots.find(b => b.id === bot2Id)?.name : undefined,
        exchange: 'OKX',
        symbol: 'ETH/USDT',
        eventType: 'risk',
        severity: 'danger',
        title: '風控層觸發：單日損失超過 5%，建議檢查策略參數',
        message: 'ETH 網格交易機器人今日累計損失已達 5.2%，超過系統設定的 5% 風險閾值。系統已自動降低倉位並發出警告。',
        suggestion: '建議檢查策略參數設定，考慮降低槓桿倍數或調整網格間距。如市場波動持續加大，可考慮暫時停止交易。',
        strategyBundleId: bot2Id ? bots.find(b => b.id === bot2Id)?.strategyPackId : undefined,
      },
      {
        id: 'audit-4',
        timestamp: new Date(now - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2天前
        botId: bot3Id,
        botName: bot3Id ? bots.find(b => b.id === bot3Id)?.name : undefined,
        exchange: 'BYBIT',
        symbol: 'SOL/USDT',
        eventType: 'system',
        severity: 'info',
        title: '系統自動備份完成',
        message: '系統已自動完成今日的配置與交易記錄備份，備份檔案已儲存至雲端儲存空間。',
        suggestion: undefined,
      },
      {
        id: 'audit-5',
        timestamp: new Date(now - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3天前
        botId: bot1Id,
        botName: bot1Id ? bots.find(b => b.id === bot1Id)?.name : undefined,
        exchange: 'BINANCE',
        symbol: 'BTC/USDT',
        eventType: 'strategy',
        severity: 'warning',
        title: '策略參數自動調整建議',
        message: '根據近期市場波動分析，建議調整 BTC 趨勢跟隨策略的移動平均線週期，以提升策略適應性。',
        suggestion: '可考慮將 EMA 週期從 20 調整為 15，以更快反應市場變化。',
        strategyBundleId: bot1Id ? bots.find(b => b.id === bot1Id)?.strategyPackId : undefined,
      },
      {
        id: 'audit-6',
        timestamp: new Date(now - 4 * 24 * 60 * 60 * 1000).toISOString(), // 4天前
        botId: undefined,
        exchange: 'OKX',
        symbol: undefined,
        eventType: 'api',
        severity: 'warning',
        title: 'OKX API 請求速率接近限制',
        message: 'OKX API 請求速率已達到每分鐘 120 次，接近系統限制（每分鐘 150 次）。建議優化請求頻率以避免觸發限流。',
        suggestion: '建議檢查是否有不必要的重複請求，或考慮增加請求間隔時間。',
      },
      {
        id: 'audit-7',
        timestamp: new Date(now - 5 * 24 * 60 * 60 * 1000).toISOString(), // 5天前
        botId: bot2Id,
        botName: bot2Id ? bots.find(b => b.id === bot2Id)?.name : undefined,
        exchange: 'OKX',
        symbol: 'ETH/USDT',
        eventType: 'risk',
        severity: 'info',
        title: '風險評估：市場波動率正常',
        message: 'ETH/USDT 的市場波動率處於正常範圍內，當前策略參數設定適宜，無需調整。',
        suggestion: undefined,
      },
      {
        id: 'audit-8',
        timestamp: new Date(now - 6 * 24 * 60 * 60 * 1000).toISOString(), // 6天前
        botId: bot3Id,
        botName: bot3Id ? bots.find(b => b.id === bot3Id)?.name : undefined,
        exchange: 'BYBIT',
        symbol: 'SOL/USDT',
        eventType: 'strategy',
        severity: 'info',
        title: '策略執行正常，無異常狀況',
        message: 'SOL 套利機器人運行正常，所有策略指標均在預期範圍內。',
        suggestion: undefined,
      },
      {
        id: 'audit-9',
        timestamp: new Date(now - 8 * 24 * 60 * 60 * 1000).toISOString(), // 8天前
        botId: bot1Id,
        botName: bot1Id ? bots.find(b => b.id === bot1Id)?.name : undefined,
        exchange: 'BINANCE',
        symbol: 'BTC/USDT',
        eventType: 'risk',
        severity: 'warning',
        title: '倉位集中度提醒',
        message: 'BTC 趨勢跟隨機器人的倉位集中度較高，建議分散風險或降低單一倉位大小。',
        suggestion: '建議將單一倉位從 1000 USDT 降低至 800 USDT，或考慮增加其他交易對的配置。',
        strategyBundleId: bot1Id ? bots.find(b => b.id === bot1Id)?.strategyPackId : undefined,
      },
      {
        id: 'audit-10',
        timestamp: new Date(now - 10 * 24 * 60 * 60 * 1000).toISOString(), // 10天前
        botId: undefined,
        exchange: 'BINANCE',
        symbol: undefined,
        eventType: 'system',
        severity: 'info',
        title: '系統維護完成',
        message: '系統已完成例行維護，所有服務已恢復正常運作。維護期間未影響正在運行的交易機器人。',
        suggestion: undefined,
      },
      {
        id: 'audit-11',
        timestamp: new Date(now - 12 * 24 * 60 * 60 * 1000).toISOString(), // 12天前
        botId: bot2Id,
        botName: bot2Id ? bots.find(b => b.id === bot2Id)?.name : undefined,
        exchange: 'OKX',
        symbol: 'ETH/USDT',
        eventType: 'strategy',
        severity: 'danger',
        title: '策略執行錯誤，已自動恢復',
        message: 'ETH 網格交易機器人執行過程中發生錯誤，系統已自動重試並恢復正常運作。錯誤原因：網路延遲導致訂單狀態查詢失敗。',
        suggestion: '建議檢查網路連線穩定性，如問題持續發生，可考慮增加重試次數或調整超時設定。',
        strategyBundleId: bot2Id ? bots.find(b => b.id === bot2Id)?.strategyPackId : undefined,
      },
      {
        id: 'audit-12',
        timestamp: new Date(now - 15 * 24 * 60 * 60 * 1000).toISOString(), // 15天前
        botId: bot3Id,
        botName: bot3Id ? bots.find(b => b.id === bot3Id)?.name : undefined,
        exchange: 'BYBIT',
        symbol: 'SOL/USDT',
        eventType: 'api',
        severity: 'warning',
        title: 'BYBIT API 金鑰即將過期',
        message: 'BYBIT API 金鑰將於 7 天後過期，請及時更新以避免影響交易機器人運作。',
        suggestion: '請前往「設定」頁面更新 API 金鑰，建議在過期前 3 天完成更新。',
      },
    ]
  }, [bots])

  // 篩選與排序後的日誌
  const filteredAndSortedLogs = useMemo(() => {
    // 1. 篩選
    const filtered = MOCK_AUDIT_LOGS.filter((log) => {
      // 依時間區間粗略過濾
      if (!matchTimeRange(log.timestamp, selectedRange)) return false

      // 依事件類型
      if (selectedEventType !== 'all' && log.eventType !== selectedEventType) {
        return false
      }

      // 依風險等級
      if (selectedSeverity !== 'all' && log.severity !== selectedSeverity) {
        return false
      }

      // 依機器人
      if (selectedBotId !== 'all' && log.botId !== selectedBotId) {
        return false
      }

      return true
    })

    // 2. 排序（時間 desc，最新的在前）
    return filtered.sort((a, b) => {
      const timeA = new Date(a.timestamp).getTime()
      const timeB = new Date(b.timestamp).getTime()
      return timeB - timeA
    })
  }, [MOCK_AUDIT_LOGS, selectedRange, selectedEventType, selectedSeverity, selectedBotId])

  // 處理查看詳情
  const handleViewDetail = (log: AuditLogItem) => {
    setSelectedLog(log)
    setIsDrawerOpen(true)
  }

  // 處理關閉 Drawer
  const handleCloseDrawer = () => {
    setIsDrawerOpen(false)
    setSelectedLog(null)
  }

  // 處理策略組合連結
  const handleStrategyBundleLink = (bundleId: string) => {
    // 從 STRATEGY_BUNDLES 中找到對應的 bundle，獲取 style
    const bundle = STRATEGY_BUNDLES.find(b => b.id === bundleId)
    if (bundle) {
      navigate(`/strategies?style=${bundle.style}&bundle=${encodeURIComponent(bundleId)}`)
    } else {
      // 如果找不到，嘗試從 bundleId 推斷 style（例如 aggressive-A1A2）
      const styleMatch = bundleId.match(/^(aggressive|balanced|conservative)-/)
      if (styleMatch) {
        navigate(`/strategies?style=${styleMatch[1]}&bundle=${encodeURIComponent(bundleId)}`)
      } else {
        // 最後備案：只帶 bundle 參數
        navigate(`/strategies?bundle=${encodeURIComponent(bundleId)}`)
      }
    }
    handleCloseDrawer()
  }

  // 取得機器人顯示名稱
  const getBotDisplayName = (log: AuditLogItem): string => {
    if (log.botName) return log.botName
    if (log.botId) {
      const bot = bots.find(b => b.id === log.botId)
      if (bot) return bot.name
    }
    return '未知機器人'
  }

  return (
    <div className="p-6 space-y-6">
      {/* 1. 頂部標題區 */}
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-text-primary">稽核與風險日誌</h1>
        <p className="text-sm text-text-secondary">
          檢視 SyrmaX 系統的策略事件、風險控管與 API 狀態記錄。本頁目前使用模擬資料，未連接真實交易所。
        </p>
      </div>

      {/* 2. 篩選列 */}
      <div className="flex flex-wrap items-center gap-2">
        {/* 左側：時間區間 + 事件類型 + 等級 */}
        <div className="flex flex-wrap items-center gap-2">
          {/* 時間區間 Segmented-like 按鈕 */}
          <div className="flex items-center gap-1 border border-border/60 rounded-lg p-1 bg-background-secondary/80">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedRange('1d')}
              className={cn(
                'h-8 px-3 text-sm',
                selectedRange === '1d'
                  ? 'bg-background-tertiary text-text-primary'
                  : 'text-text-secondary hover:text-text-primary'
              )}
              aria-pressed={selectedRange === '1d'}
            >
              今天
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedRange('7d')}
              className={cn(
                'h-8 px-3 text-sm',
                selectedRange === '7d'
                  ? 'bg-background-tertiary text-text-primary'
                  : 'text-text-secondary hover:text-text-primary'
              )}
              aria-pressed={selectedRange === '7d'}
            >
              近 7 天
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedRange('30d')}
              className={cn(
                'h-8 px-3 text-sm',
                selectedRange === '30d'
                  ? 'bg-background-tertiary text-text-primary'
                  : 'text-text-secondary hover:text-text-primary'
              )}
              aria-pressed={selectedRange === '30d'}
            >
              近 30 天
            </Button>
          </div>

          {/* 事件類型 Dropdown */}
          <Dropdown
            trigger={
              <Button variant="outline" size="sm" className="h-8 text-sm">
                {selectedEventType === 'all' ? '事件類型' : getEventTypeLabel(selectedEventType)}
                <ChevronDown className="h-4 w-4 ml-1" />
              </Button>
            }
          >
            <DropdownItem onClick={() => setSelectedEventType('all')}>
              全部
            </DropdownItem>
            <DropdownItem onClick={() => setSelectedEventType('strategy')}>
              策略事件
            </DropdownItem>
            <DropdownItem onClick={() => setSelectedEventType('risk')}>
              風險控管
            </DropdownItem>
            <DropdownItem onClick={() => setSelectedEventType('system')}>
              系統
            </DropdownItem>
            <DropdownItem onClick={() => setSelectedEventType('api')}>
              API
            </DropdownItem>
          </Dropdown>

          {/* 風險等級 Segmented-like 按鈕 */}
          <div className="flex items-center gap-1 border border-border/60 rounded-lg p-1 bg-background-secondary/80">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedSeverity('all')}
              className={cn(
                'h-8 px-3 text-sm',
                selectedSeverity === 'all'
                  ? 'bg-background-tertiary text-text-primary'
                  : 'text-text-secondary hover:text-text-primary'
              )}
              aria-pressed={selectedSeverity === 'all'}
            >
              全部
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedSeverity('info')}
              className={cn(
                'h-8 px-3 text-sm',
                selectedSeverity === 'info'
                  ? 'bg-background-tertiary text-text-primary'
                  : 'text-text-secondary hover:text-text-primary'
              )}
              aria-pressed={selectedSeverity === 'info'}
            >
              資訊
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedSeverity('warning')}
              className={cn(
                'h-8 px-3 text-sm',
                selectedSeverity === 'warning'
                  ? 'bg-background-tertiary text-text-primary'
                  : 'text-text-secondary hover:text-text-primary'
              )}
              aria-pressed={selectedSeverity === 'warning'}
            >
              警告
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedSeverity('danger')}
              className={cn(
                'h-8 px-3 text-sm',
                selectedSeverity === 'danger'
                  ? 'bg-background-tertiary text-text-primary'
                  : 'text-text-secondary hover:text-text-primary'
              )}
              aria-pressed={selectedSeverity === 'danger'}
            >
              危險
            </Button>
          </div>
        </div>

        {/* 右側：機器人下拉（固定右側） */}
        <div className="ml-auto">
          <Dropdown
            trigger={
              <Button variant="outline" size="sm" className="h-8 text-sm">
                {selectedBotId === 'all'
                  ? '所有機器人'
                  : bots.find(b => b.id === selectedBotId)?.name || '未知機器人'}
                <ChevronDown className="h-4 w-4 ml-1" />
              </Button>
            }
          >
            <DropdownItem onClick={() => setSelectedBotId('all')}>
              所有機器人
            </DropdownItem>
            {bots.map((bot) => (
              <DropdownItem key={bot.id} onClick={() => setSelectedBotId(bot.id)}>
                {bot.name}
              </DropdownItem>
            ))}
          </Dropdown>
        </div>
      </div>

      {/* 3. 主表格 */}
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="min-w-[160px]">時間</TableHead>
              <TableHead className="min-w-[200px]">機器人</TableHead>
              <TableHead className="min-w-[100px]">事件類型</TableHead>
              <TableHead className="min-w-[100px]">風險等級</TableHead>
              <TableHead className="w-[520px]">標題</TableHead>
              <TableHead className="min-w-[100px]">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredAndSortedLogs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-text-secondary py-8">
                  沒有符合條件的稽核記錄
                </TableCell>
              </TableRow>
            ) : (
              filteredAndSortedLogs.map((log) => (
                <TableRow
                  key={log.id}
                  className="cursor-pointer hover:bg-background-tertiary/30 transition-colors"
                  onClick={() => handleViewDetail(log)}
                >
                  <TableCell className="text-sm text-text-secondary">
                    {formatTimestampShort(log.timestamp)}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1.5">
                      <div className="text-sm font-semibold text-text-primary leading-tight truncate max-w-[240px]">
                        {getBotDisplayName(log)}
                      </div>
                      {(log.exchange || log.symbol) && (
                        <div className="text-xs text-text-secondary leading-tight truncate max-w-[240px]">
                          {[log.exchange, log.symbol].filter(Boolean).join(' / ')}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-left">
                    <div style={getEventTypeBadgeStyle(log.eventType)}>
                      {getEventTypeLabel(log.eventType)}
                    </div>
                  </TableCell>
                  <TableCell className="text-left">
                    <div style={getSeverityStyle(log.severity)}>
                      {getSeverityLabel(log.severity)}
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-text-primary">
                    <div
                      className="max-w-[520px] leading-snug text-text-primary line-clamp-2"
                      title={log.title}
                    >
                      {log.title}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleViewDetail(log)
                      }}
                      className="h-8 text-xs hover:bg-background-tertiary/50"
                    >
                      查看詳情
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* 4. 詳細 Drawer */}
      <Drawer isOpen={isDrawerOpen && !!selectedLog} onClose={handleCloseDrawer}>
        {selectedLog && (
          <div className="h-full flex flex-col">
            {/* 標題欄 - Sticky Header */}
            <div className="sticky top-0 z-10 bg-background-secondary/95 backdrop-blur border-b border-border/60 flex-shrink-0">
              <div className="flex items-start justify-between px-4 py-3 gap-3">
                <div className="flex-1 min-w-0">
                  {/* 第一行：主標題 */}
                  <h2 className="text-base font-semibold text-text-primary line-clamp-2">
                    {normalizeEventTitle(selectedLog.title)}
                  </h2>
                  {/* 第二行：meta 資訊 */}
                  <div className="mt-1 flex items-center gap-2 text-xs text-text-secondary min-w-0">
                    <span className="truncate">
                      {formatTimestampFull(selectedLog.timestamp)}｜{getBotDisplayName(selectedLog)}｜{selectedLog.symbol ?? '-'}
                    </span>
                    <span className="shrink-0">｜</span>
                    <div 
                      className="shrink-0 inline-flex items-center h-6 rounded-full border px-2.5 text-xs font-semibold"
                      style={getSeverityStyle(selectedLog.severity)}
                    >
                      {getSeverityLabel(selectedLog.severity)}
                    </div>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleCloseDrawer}
                  className="h-8 w-8 flex-shrink-0 text-text-tertiary hover:text-text-primary"
                  aria-label="關閉"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* 內容區域 - 分段資訊面板 */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* 機器人資訊 Section */}
              <div className="rounded-xl border border-border/60 bg-background-secondary/60 p-4">
                <h3 className="text-sm font-medium text-text-primary mb-3">機器人資訊</h3>
                <dl className="grid grid-cols-2 gap-x-6 gap-y-3">
                  <div>
                    <dt className="text-xs text-text-tertiary">名稱</dt>
                    <dd className="text-sm mt-0.5">
                      <div style={getNeutralBadgeStyle()}>
                        {getBotDisplayName(selectedLog)}
                      </div>
                    </dd>
                  </div>
                  {selectedLog.exchange && (
                    <div>
                      <dt className="text-xs text-text-tertiary">交易所</dt>
                      <dd className="text-sm mt-0.5">
                        <div style={getSecondaryBadgeStyle()}>
                          {selectedLog.exchange}
                        </div>
                      </dd>
                    </div>
                  )}
                  {selectedLog.symbol && (
                    <div>
                      <dt className="text-xs text-text-tertiary">交易對</dt>
                      <dd className="text-sm mt-0.5">
                        <div style={getSecondaryBadgeStyle()}>
                          {selectedLog.symbol}
                        </div>
                      </dd>
                    </div>
                  )}
                  {selectedLog.strategyBundleId && (
                    <div>
                      <dt className="text-xs text-text-tertiary">策略組合</dt>
                      <dd className="text-sm mt-0.5">
                        <button
                          onClick={() => handleStrategyBundleLink(selectedLog.strategyBundleId!)}
                          style={getSecondaryBadgeStyle()}
                          className="hover:bg-background-secondary/80 hover:border-border transition-colors cursor-pointer"
                        >
                          {(() => {
                            const bundleName = bots.find(b => b.strategyPackId === selectedLog.strategyBundleId)?.strategyPackName
                            const bundle = STRATEGY_BUNDLES.find(b => b.id === selectedLog.strategyBundleId)
                            const displayName = bundleName || bundle?.name || `策略組合 ID: ${selectedLog.strategyBundleId}`
                            return `查看 ${displayName} 詳情`
                          })()}
                        </button>
                      </dd>
                    </div>
                  )}
                </dl>
              </div>

              {/* 事件類型 / 風險等級 Section */}
              <div className="rounded-xl border border-border/60 bg-background-secondary/60 p-4">
                <h3 className="text-sm font-medium text-text-primary mb-2">事件類型 / 風險等級</h3>
                <div className="flex items-center gap-2">
                  <div style={getEventTypeBadgeStyle(selectedLog.eventType)}>
                    {getEventTypeLabel(selectedLog.eventType)}
                  </div>
                  <div style={getSeverityStyle(selectedLog.severity)}>
                    {getSeverityLabel(selectedLog.severity)}
                  </div>
                </div>
              </div>

              {/* 詳細訊息 Section */}
              <div className="rounded-xl border border-border/60 bg-background-secondary/60 p-4">
                <h3 className="text-sm font-medium text-text-primary mb-3">詳細訊息</h3>
                <div className="text-sm leading-6 text-text-secondary whitespace-pre-line">
                  {selectedLog.message}
                </div>
              </div>

              {/* 建議處理方式 Section */}
              {selectedLog.suggestion && (
                <div className="rounded-xl border border-border/60 bg-background-secondary/60 p-4">
                  <h3 className="text-sm font-medium text-text-primary mb-3">建議處理方式</h3>
                  {Array.isArray(selectedLog.suggestion) ? (
                    <ul className="list-disc pl-5 space-y-2 text-sm leading-6 text-text-secondary">
                      {selectedLog.suggestion.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <div className="text-sm leading-6 text-text-secondary whitespace-pre-line">
                      {selectedLog.suggestion}
                    </div>
                  )}
                </div>
              )}

            </div>

            {/* 底部固定文案 - Footer */}
            <div className="mt-6 border-t border-border/60 pt-4 text-xs text-text-tertiary leading-relaxed px-4 pb-4 flex-shrink-0">
              本頁僅提供策略與風險事件記錄（示意資料）。機器人建立、啟動與參數調整請至「機器人管理」進行。
            </div>
          </div>
        )}
      </Drawer>
    </div>
  )
}
