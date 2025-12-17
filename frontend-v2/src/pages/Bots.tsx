import React, { useState, useMemo, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { 
  Plus, 
  Play, 
  Pause, 
  RotateCw, 
  Copy,
  AlertTriangle,
  Trash2,
  MoreVertical,
  Check
} from 'lucide-react'
import { 
  useReactTable, 
  getCoreRowModel, 
  getSortedRowModel,
  flexRender,
  createColumnHelper,
  type ColumnDef,
  type SortingState,
  type Column
} from '@tanstack/react-table'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { getSecondaryBadgeStyle, getBotStatusBadgeStyle } from '@/lib/subtleBadgeStyles'
import { BOT_STATUS_STYLES } from '@/lib/botStatusStyles'
import { mockStore, type Bot } from '@/lib/mockStore'
import { formatCurrency, formatTimeAgo, formatPosition } from '@/lib/utils'
import { CreateBotWizard } from '@/components/bot/CreateBotWizard'
import { BotErrorDrawer } from '@/components/bot/BotErrorDrawer'
import { DeleteBotDialog } from '@/components/bot/DeleteBotDialog'
import { DeleteBotsDialog } from '@/components/bot/DeleteBotsDialog'
import { Toast } from '@/components/ui/Toast'
import { Dropdown, DropdownItem } from '@/components/ui/Dropdown'
import { cn } from '@/lib/utils'
import { STRATEGY_BUNDLES } from '@/components/strategies/strategyBundles'
import type { StrategyBundleTemplate } from '@/components/strategies/types'
import { loadBots, addBot, removeBot, updateBot, updateBots, restoreBots } from '@/lib/botsStorage'

const SORT_KEY = 'syrmax.bots.table.sort.v1'
const DEFAULT_SORT: SortingState = [{ id: 'name', desc: false }]

function SortIcon({ state }: { state: false | 'asc' | 'desc' }) {
  if (!state) {
    return <span className="text-xs text-text-tertiary opacity-70">↕</span>
  }
  const symbol = state === 'asc' ? '↑' : '↓'
  return <span className="text-xs text-text-primary">{symbol}</span>
}

/**
 * 根據機器人的 strategyPackId 找到對應的策略組合
 * @param bot 機器人資料
 * @returns 對應的策略組合，如果找不到則返回 undefined
 */
function findBundleForBot(bot: Bot): StrategyBundleTemplate | undefined {
  // 如果有 strategyPackId，直接從 STRATEGY_BUNDLES 中查找
  if (bot.strategyPackId) {
    return STRATEGY_BUNDLES.find((b) => b.id === bot.strategyPackId)
  }

  // 如果還沒有 bundleId，嘗試用舊欄位粗略對應（暫時 fallback）
  // 注意：這個 fallback 邏輯可能不夠精確，因為舊資料可能無法完全對應到新的 bundle
  // 如果找不到對應的 bundle，就回傳 undefined，讓 UI 顯示舊文案
  return undefined
}

function SortableColumnHeader<T>({
  column,
  label,
  align = 'left',
}: {
  column: Column<T, unknown>
  label: React.ReactNode
  align?: 'left' | 'right'
}) {
  const sortState = column.getIsSorted()

  const handleToggle = (event: { shiftKey: boolean; metaKey?: boolean; ctrlKey?: boolean; preventDefault: () => void }) => {
    if (event.metaKey || event.ctrlKey) {
      event.preventDefault()
      column.clearSorting()
      return
    }
    column.toggleSorting(undefined, event.shiftKey)
  }

  return (
    <div
      role="button"
      tabIndex={0}
      className={cn(
        'group inline-flex w-full select-none items-center gap-2 text-text-secondary transition-colors hover:text-text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50',
        align === 'right' ? 'justify-end text-right' : 'justify-start text-left'
      )}
      onClick={(event) => handleToggle(event)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          handleToggle(event)
        }
      }}
    >
      <span>{label}</span>
      <SortIcon state={sortState} />
      {sortState && (
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation()
            column.clearSorting()
          }}
          className="ml-2 inline-flex items-center justify-center rounded-full border border-transparent bg-transparent text-xs leading-none text-text-tertiary opacity-0 transition-all duration-150 hover:border-border hover:bg-background-tertiary hover:text-text-primary focus-visible:opacity-100 focus-visible:ring-1 focus-visible:ring-primary group-hover:opacity-100"
          style={{ width: '16px', height: '16px' }}
          aria-label="清除此欄排序"
          title="清除此欄排序"
        >
          ×
        </button>
      )}
    </div>
  )
}

/**
 * 機器人管理頁（表格樣式）
 * - TanStack Table v8 表格
 * - 可排序、Zebra 樣式、hover 顯示操作
 * - 三步建立向導
 * - 錯誤排查 Drawer
 */
export default function Bots() {
  const navigate = useNavigate()
  // 從 localStorage 載入機器人列表（第一次使用時會使用 DEMO 資料）
  const [bots, setBots] = useState<Bot[]>([])
  // 回收桶計數 hook（使用訂閱機制自動更新，無需手動 refresh）
  // 注意：此處不需要 refresh，因為訂閱機制會自動更新
  const [wizardOpen, setWizardOpen] = useState(false)
  const [errorDrawerOpen, setErrorDrawerOpen] = useState(false)
  const [selectedBot, setSelectedBot] = useState<Bot | null>(null)
  const [hoveredRowId, setHoveredRowId] = useState<string | null>(null)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info'; onUndo?: () => void } | null>(null)
  
  // 刪除相關狀態
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteBotsDialogOpen, setDeleteBotsDialogOpen] = useState(false)
  const [botToDelete, setBotToDelete] = useState<Bot | null>(null)
  const [lastDeletedBotId, setLastDeletedBotId] = useState<string | null>(null)
  
  // 批次選擇相關狀態
  const [selectedBotIds, setSelectedBotIds] = useState<Set<string>>(new Set())
  const [isMobileViewport, setIsMobileViewport] = useState(() => 
    typeof window !== 'undefined' ? window.matchMedia('(max-width: 767.98px)').matches : false
  )
  
  // 監聽視窗大小變化
  useEffect(() => {
    const mediaQuery = window.matchMedia('(max-width: 767.98px)')
    const handleChange = (event: MediaQueryListEvent | MediaQueryList) => {
      setIsMobileViewport(event.matches)
    }
    handleChange(mediaQuery)
    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  // 排序狀態（從 localStorage 讀取）
  const [sorting, setSorting] = useState<SortingState>(() => {
    try {
      const saved = localStorage.getItem(SORT_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed)) {
          return parsed as SortingState
        }
        if (parsed && typeof parsed === 'object' && 'column' in parsed) {
          return [{ id: parsed.column, desc: Boolean(parsed.desc) }]
        }
      }
    } catch (error) {
      console.warn('[Bots] 無法讀取排序設定：', error)
    }
    return DEFAULT_SORT
  })

  // 保存排序狀態
  useEffect(() => {
    try {
      if (sorting.length > 0) {
        localStorage.setItem(SORT_KEY, JSON.stringify(sorting))
      } else {
        localStorage.removeItem(SORT_KEY)
      }
    } catch (error) {
      console.warn('[Bots] 無法保存排序設定：', error)
    }
  }, [sorting])

  const columnHelper = createColumnHelper<Bot>()

  // 批次選擇處理
  const toggleBotSelection = (botId: string) => {
    setSelectedBotIds(prev => {
      const next = new Set(prev)
      if (next.has(botId)) {
        next.delete(botId)
      } else {
        next.add(botId)
      }
      return next
    })
  }

  const toggleSelectAll = () => {
    if (selectedBotIds.size === bots.length) {
      setSelectedBotIds(new Set())
    } else {
      setSelectedBotIds(new Set(bots.map(b => b.id)))
    }
  }

  // 表格欄位定義
  const columns = useMemo(() => [
    // 勾選框欄（批次選擇）
    {
      id: 'select',
      header: () => (
        <div className="flex items-center justify-center">
          <button
            type="button"
            onClick={toggleSelectAll}
            className="h-4 w-4 rounded border border-white bg-transparent flex items-center justify-center hover:bg-white/10 transition-colors"
            aria-label={selectedBotIds.size === bots.length ? '取消全選' : '全選'}
          >
            {selectedBotIds.size === bots.length && bots.length > 0 && (
              <Check className="h-3 w-3 text-white" />
            )}
          </button>
        </div>
      ),
      cell: ({ row }: { row: any }) => {
        const bot = row.original
        const isSelected = selectedBotIds.has(bot.id)
        return (
          <div className="flex items-center justify-center">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                toggleBotSelection(bot.id)
              }}
              className="h-4 w-4 rounded border border-white bg-transparent flex items-center justify-center hover:bg-white/10 transition-colors"
              aria-label={isSelected ? '取消選擇' : '選擇'}
            >
              {isSelected && (
                <Check className="h-3 w-3 text-white" />
              )}
            </button>
          </div>
        )
      },
      size: 48,
      enableSorting: false
    },
    
    // 名稱欄
    columnHelper.accessor('name', {
      header: ({ column }) => <SortableColumnHeader column={column} label="名稱" align="left" />,
      cell: ({ row }) => {
        const bot = row.original
        return (
          <Link
            to={`/bots/${bot.id}`}
            className="flex flex-col gap-[18px] cursor-pointer hover:text-text-primary transition-colors"
          >
            <div className="text-text-primary font-medium hover:underline">{bot.name}</div>
            {bot.lastActiveAt ? (
              <div className="text-xs text-text-secondary">
                {formatTimeAgo(bot.lastActiveAt)}
              </div>
            ) : (
              <div className="text-xs text-text-tertiary">{bot.id}</div>
            )}
          </Link>
        )
      },
      size: 240
    }),

    // 交易所/連線
    columnHelper.accessor('exchange', {
      header: '交易所/連線',
      cell: ({ row }) => {
        const bot = row.original
        // 根據連線狀態決定小色點顏色
        const getStatusDotColor = (status: string) => {
          if (status === 'connected') return '#3FBF7F' // 綠色（成功）
          if (status === 'down') return '#F05B61' // 紅色（失敗）
          // 短暫斷線重試顯示黃色（預留，目前類型只有 connected/down）
          return '#E9A73A' // 黃色（重試）
        }
        // 根據 pingMs 決定延遲顏色
        const getPingColor = (ms: number) => {
          if (ms <= 100) return '#6B7385' // 灰色（良好）
          if (ms <= 500) return '#E9A73A' // 黃色（警告）
          return '#F05B61' // 紅色（危險）
        }
        const statusDotColor = getStatusDotColor(bot.connectionStatus)
        const pingColor = getPingColor(bot.pingMs)
        
        return (
          <div className="flex flex-col gap-3">
            {/* 第 1 行：交易所徽章 + 小色點 */}
            <div className="flex items-center">
              <span style={getSecondaryBadgeStyle()}>{bot.exchange}</span>
              {/* 小色點（6px）與徽章間距 16px */}
              <div
                className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                style={{ 
                  backgroundColor: statusDotColor,
                  marginLeft: '16px',
                  minWidth: '6px',
                  minHeight: '6px'
                }}
              />
            </div>
            {/* 第 2 行：延遲顯示 */}
            {bot.pingMs > 0 && (
              <div className="text-xs font-mono tabular-nums" style={{ color: pingColor }}>
                {bot.pingMs}ms
              </div>
            )}
          </div>
        )
      },
      size: 160
    }),

    // 幣對
    columnHelper.accessor('symbol', {
      header: '幣對',
      cell: ({ getValue }) => (
        <div className="font-mono tabular-nums text-text-primary">{getValue()}</div>
      ),
      size: 120
    }),

    // 策略包
    columnHelper.accessor('strategyPackName', {
      header: '策略包',
      cell: ({ row }) => {
        const bot = row.original
        const bundle = findBundleForBot(bot)

        // 如果找到對應的 bundle，使用 bundle 的資料顯示
        if (bundle) {
          // 風險等級對應表（bundle 使用 'low' | 'medium' | 'high'，顯示時轉換為中文）
          const riskLabelMap: Record<'low' | 'medium' | 'high', string> = {
            low: '低風險',
            medium: '中風險',
            high: '高風險',
          }

          return (
            <div className="flex flex-col gap-[18px]">
              <div className="text-text-primary">{bundle.name}</div>
              <div className="text-xs text-text-secondary">
                {bundle.styleLabel}・{riskLabelMap[bundle.riskLevel]}
              </div>
            </div>
          )
        }

        // 找不到 bundle（舊資料或尚未遷移完成），沿用原本顯示方式
        const useMap: Record<'trend' | 'range' | 'defense', string> = {
          trend: '趨勢',
          range: '震盪',
          defense: '防守',
        }
        const riskMap: Record<'low' | 'mid' | 'high', string> = {
          low: '低',
          mid: '中',
          high: '高',
        }

        return (
          <div className="flex flex-col gap-[18px]">
            <div className="text-text-primary">
              {bot.strategyPackName ?? '未分類策略'}
            </div>
            {bot.strategyUse && bot.strategyRisk && (
              <div className="text-xs text-text-secondary">
                {useMap[bot.strategyUse]}・風險{riskMap[bot.strategyRisk]}
              </div>
            )}
          </div>
        )
      },
      size: 160
    }),

    // 倉位
    columnHelper.accessor('positionValue', {
      header: () => <div className="text-left">倉位</div>,
      cell: ({ row }) => {
        const bot = row.original
        return (
          <div className="text-left font-mono tabular-nums text-text-primary">
            {formatPosition(bot.positionMode, bot.positionValue, mockStore.accountEquity)}
          </div>
        )
      },
      size: 160
    }),

    // 槓桿
    columnHelper.accessor('leverage', {
      header: ({ column }) => <SortableColumnHeader column={column} label="槓桿" align="right" />,
      cell: ({ getValue }) => (
        <div className="text-right font-mono tabular-nums text-text-primary" style={{ paddingRight: '32px' }}>
          {getValue()}x
        </div>
      ),
      size: 120
    }),

    // 狀態
    columnHelper.accessor('status', {
      header: ({ column }) => <SortableColumnHeader column={column} label="狀態" align="right" />,
      cell: ({ row }) => {
        const status = row.original.status
        const style = BOT_STATUS_STYLES[status]
        const badgeStyle = getBotStatusBadgeStyle(status)
        
        return (
          <div className="flex items-center justify-end pr-4">
            {/* 小圓點 (6px) - 在膠囊外面 */}
            <div
              className="w-1.5 h-1.5 rounded-full flex-shrink-0"
              style={{ 
                backgroundColor: style.dotColor,
                minWidth: '6px',
                minHeight: '6px',
                marginRight: '16px' // 維持 16px 間距
              }}
            />
            {/* Subtle Badge 風格 */}
            <span style={badgeStyle}>
              {style.label}
            </span>
          </div>
        )
      },
      size: 160
    }),

    // 今日 PnL
    columnHelper.accessor('pnlToday', {
      header: ({ column }) => <SortableColumnHeader column={column} label="今日 PnL" align="right" />,
      cell: ({ getValue }) => {
        const value = getValue()
        // 確定顏色：>0 綠色、<0 紅色、=0 灰色
        let textColor: string
        if (value > 0) {
          textColor = '#3FBF7F' // success - 綠色
        } else if (value < 0) {
          textColor = '#F05B61' // danger - 紅色
        } else {
          textColor = '#6B7385' // text-tertiary - 灰色
        }
        return (
          <div 
            className="text-right font-mono tabular-nums font-semibold"
            style={{ color: textColor }}
          >
            {formatCurrency(value)}
          </div>
        )
      },
      size: 120
    }),

    // 本月 PnL
    columnHelper.accessor('pnlMtd', {
      header: ({ column }) => <SortableColumnHeader column={column} label="本月 PnL" align="right" />,
      cell: ({ getValue }) => {
        const value = getValue()
        // 確定顏色：>0 綠色、<0 紅色、=0 灰色
        let textColor: string
        if (value > 0) {
          textColor = '#3FBF7F' // success - 綠色
        } else if (value < 0) {
          textColor = '#F05B61' // danger - 紅色
        } else {
          textColor = '#6B7385' // text-tertiary - 灰色
        }
        return (
          <div 
            className="text-right font-mono tabular-nums font-semibold"
            style={{ color: textColor }}
          >
            {formatCurrency(value)}
          </div>
        )
      },
      size: 120
    }),

    // 操作欄
    {
      id: 'actions',
      header: '操作',
      cell: ({ row }) => {
        const bot = row.original
        const isHovered = hoveredRowId === bot.id
        const canShowActions = isHovered || bot.status === 'error'
        
        // 判斷是否可以刪除（只有 stopped/paused/error 可以刪除）
        const canDelete = bot.status === 'stopped' || bot.status === 'paused' || bot.status === 'error'
        const isRunningOrCooling = bot.status === 'running' || bot.status === 'cooling'

        // 行動版：使用 kebab menu
        if (isMobileViewport) {
          return (
            <div className="flex items-center justify-end" style={{ width: '140px' }}>
              <Dropdown
                trigger={
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-8 w-8 rounded-lg p-0"
                    aria-label="更多操作"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                }
                align="right"
              >
                {bot.status === 'error' && (
                  <>
                    <DropdownItem
                      onClick={() => {
                        setSelectedBot(bot)
                        setErrorDrawerOpen(true)
                      }}
                    >
                      <AlertTriangle className="h-4 w-4 mr-2 inline" />
                      錯誤排查
                    </DropdownItem>
                    <DropdownItem onClick={() => handleBotAction(bot.id, 'restart')}>
                      <RotateCw className="h-4 w-4 mr-2 inline" />
                      重啟
                    </DropdownItem>
                  </>
                )}
                {bot.status !== 'error' && (
                  <>
                    {bot.status === 'running' ? (
                      <DropdownItem onClick={() => handleBotAction(bot.id, 'pause')}>
                        <Pause className="h-4 w-4 mr-2 inline" />
                        暫停
                      </DropdownItem>
                    ) : (
                      <DropdownItem onClick={() => handleBotAction(bot.id, 'start')}>
                        <Play className="h-4 w-4 mr-2 inline" />
                        啟動
                      </DropdownItem>
                    )}
                    {bot.status !== 'stopped' && bot.status !== 'running' && (
                      <DropdownItem onClick={() => handleBotAction(bot.id, 'restart')}>
                        <RotateCw className="h-4 w-4 mr-2 inline" />
                        重啟
                      </DropdownItem>
                    )}
                    <DropdownItem onClick={() => handleBotAction(bot.id, 'copy')}>
                      <Copy className="h-4 w-4 mr-2 inline" />
                      複製
                    </DropdownItem>
                  </>
                )}
                <DropdownItem
                  variant="danger"
                  onClick={() => {
                    setBotToDelete(bot)
                    setDeleteDialogOpen(true)
                  }}
                  disabled={!canDelete}
                >
                  <Trash2 className="h-4 w-4 mr-2 inline" />
                  刪除
                </DropdownItem>
              </Dropdown>
            </div>
          )
        }

        // 桌機版：顯示所有按鈕
        return (
          <div className="flex items-center justify-end gap-2 pl-6" style={{ width: '200px' }}>
            {canShowActions && (
              <>
                {bot.status === 'error' ? (
                  <>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 rounded-lg"
                      onClick={() => {
                        setSelectedBot(bot)
                        setErrorDrawerOpen(true)
                      }}
                      aria-label="錯誤排查"
                      title="錯誤排查"
                    >
                      <AlertTriangle className="h-4 w-4 text-danger" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 rounded-lg"
                      onClick={() => handleBotAction(bot.id, 'restart')}
                      aria-label="重啟"
                      title="重啟"
                    >
                      <RotateCw className="h-4 w-4" />
                    </Button>
                  </>
                ) : (
                  <>
                    {bot.status === 'running' ? (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 rounded-lg"
                        onClick={() => handleBotAction(bot.id, 'pause')}
                        aria-label="暫停"
                        title="暫停"
                      >
                        <Pause className="h-4 w-4" />
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 rounded-lg"
                        onClick={() => handleBotAction(bot.id, 'start')}
                        aria-label="啟動"
                        title="啟動"
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                    )}
                    {bot.status !== 'stopped' && bot.status !== 'running' && (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 rounded-lg"
                        onClick={() => handleBotAction(bot.id, 'restart')}
                        aria-label="重啟"
                        title="重啟"
                      >
                        <RotateCw className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 rounded-lg"
                      onClick={() => handleBotAction(bot.id, 'copy')}
                      aria-label="複製"
                      title="複製"
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </>
                )}
                {/* 刪除按鈕 */}
                <Button
                  size="sm"
                  variant="ghost"
                  className={cn(
                    "h-8 rounded-lg bg-transparent",
                    canDelete 
                      ? "text-muted hover:text-danger hover:bg-transparent" 
                      : "text-muted-foreground cursor-not-allowed opacity-50 hover:bg-transparent"
                  )}
                  onClick={() => {
                    if (canDelete) {
                      setBotToDelete(bot)
                      setDeleteDialogOpen(true)
                    }
                  }}
                  disabled={!canDelete}
                  aria-label={isRunningOrCooling ? "需先停止機器人才能刪除" : "刪除機器人"}
                  title={isRunningOrCooling ? "需先停止機器人才能刪除" : "刪除機器人"}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </>
            )}
          </div>
        )
      },
      size: 200,
      enableSorting: false
    }
  ] as ColumnDef<Bot>[], [hoveredRowId, navigate, isMobileViewport, selectedBotIds, bots.length])

  // 表格實例
  const table = useReactTable({
    data: bots,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    state: {
      sorting
    },
    onSortingChange: setSorting,
    columnResizeMode: 'onChange',
    enableSortingRemoval: true,
    enableMultiSort: true
  })

  // 處理機器人操作
  const handleBotAction = (botId: string, action: 'start' | 'pause' | 'restart' | 'copy' | 'paperTrade') => {
    if (action === 'copy') {
      // 複製機器人：先找到要複製的機器人
      const botToCopy = bots.find(b => b.id === botId)
      if (!botToCopy) return
      
      const newBot: Bot = {
        ...botToCopy,
        id: crypto.randomUUID(),
        name: `${botToCopy.name} (複製)`,
        status: 'stopped',
        pnlToday: 0,
        pnlMtd: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isDeleted: false
      }
      
      // 同步到 localStorage
      const updated = addBot(newBot)
      setBots(updated)
      setToast({ message: '已複製機器人', type: 'success' })
      return
    }
    
    if (action === 'paperTrade') {
      // Mock: 切換紙上交易
      setToast({ message: '已切換為紙上交易', type: 'info' })
      return
    }
    
    // 更新狀態：啟動、暫停、重啟
    let patch: Partial<Bot> = {}
    switch (action) {
      case 'start':
        patch = { status: 'running', lastActiveAt: new Date().toISOString() }
        break
      case 'pause':
        patch = { status: 'paused' }
        break
      case 'restart':
        patch = { status: 'running', lastActiveAt: new Date().toISOString(), connectionStatus: 'connected' }
        break
    }
    
    // 同步到 localStorage
    const updated = updateBot(botId, patch)
    setBots(updated)
    setToast({ message: `已${action === 'start' ? '啟動' : action === 'pause' ? '暫停' : '重啟'}機器人`, type: 'success' })
  }

  // 處理建立成功
  // 注意：CreateBotWizard 已經會將新機器人寫入 localStorage
  // 這裡只需要從 localStorage 重新載入列表即可
  const handleCreateSuccess = (newBot: Bot) => {
    // 從 localStorage 重新載入列表（確保資料一致性）
    const updated = loadBots()
    setBots(updated)
    setToast({ message: '已建立機器人', type: 'success' })
  }

  // 處理單筆刪除
  const handleDeleteBot = async () => {
    if (!botToDelete) return
    
    const botId = botToDelete.id
    const botName = botToDelete.name
    
    try {
      // 使用軟刪除，標記為已刪除（而不是完全移除）
      const now = Date.now()
      const DAY = 24 * 60 * 60 * 1000
      const GRACE_DAYS = 7
      
      // 同步到 localStorage：標記為已刪除
      updateBot(botId, {
        isDeleted: true,
        deletedAt: now,
        purgeAt: now + GRACE_DAYS * DAY,
        deletedBy: 'system',
        updatedAt: new Date().toISOString(),
      })
      
      // 重新載入列表（過濾已刪除的）
      const updated = loadBots().filter(bot => !bot.isDeleted)
      setBots(updated)
      setLastDeletedBotId(botId)
      
      // 通知 mockStore 更新（觸發訂閱機制）
      mockStore._notifyBotsChanged()
      
      // 回收桶計數會透過訂閱機制自動更新，無需手動 refresh
      setToast({
        message: `已刪除「${botName}」`,
        type: 'success',
        onUndo: () => {
          handleRestoreBot(botId)
        }
      })
      setBotToDelete(null)
    } catch (error) {
      setToast({ message: '刪除失敗', type: 'error' })
    }
  }

  // 處理批次刪除
  const handleDeleteBots = async () => {
    const selectedBots = bots.filter(b => selectedBotIds.has(b.id))
    const canDeleteBots = selectedBots.filter(b => 
      b.status === 'stopped' || b.status === 'paused' || b.status === 'error'
    )
    
    if (canDeleteBots.length === 0) return
    
    try {
      const ids = canDeleteBots.map(b => b.id)
      const now = Date.now()
      const DAY = 24 * 60 * 60 * 1000
      const GRACE_DAYS = 7
      
      // 同步到 localStorage：批次標記為已刪除
      updateBots((currentBots) => 
        currentBots.map(b => 
          ids.includes(b.id)
            ? {
                ...b,
                isDeleted: true,
                deletedAt: now,
                purgeAt: now + GRACE_DAYS * DAY,
                deletedBy: 'system',
                updatedAt: new Date().toISOString(),
              }
            : b
        )
      )
      
      // 重新載入列表（過濾已刪除的）
      const updated = loadBots().filter(bot => !bot.isDeleted)
      setBots(updated)
      setSelectedBotIds(new Set())
      
      // 通知 mockStore 更新（觸發訂閱機制）
      mockStore._notifyBotsChanged()
      
      // 回收桶計數會透過訂閱機制自動更新，無需手動 refresh
      setToast({ message: `已刪除 ${canDeleteBots.length} 個機器人`, type: 'success' })
    } catch (error) {
      setToast({ message: '批次刪除失敗', type: 'error' })
    }
  }

  // 復原機器人
  const handleRestoreBot = async (botId: string) => {
    try {
      // 使用 botsStorage 還原機器人
      restoreBots([botId])
      
      // 重新從 localStorage 載入列表（過濾已刪除的）
      const updated = loadBots().filter(bot => !bot.isDeleted)
      setBots(updated)
      setLastDeletedBotId(null)
      
      // 通知 mockStore 更新（觸發訂閱機制）
      mockStore._notifyBotsChanged()
      
      // 回收桶計數會透過訂閱機制自動更新，無需手動 refresh
    } catch (error) {
      setToast({ message: '復原失敗', type: 'error' })
    }
  }

  // 從 localStorage 載入機器人列表（頁面載入時），過濾掉已刪除的機器人
  useEffect(() => {
    const loaded = loadBots()
    // 過濾掉已刪除的機器人（只顯示未刪除的）
    const activeBots = loaded.filter(bot => !bot.isDeleted)
    setBots(activeBots)
  }, [])

  const handleClearSorting = () => {
    setSorting([])
  }

  const handleRestoreDefaultSorting = () => {
    setSorting(DEFAULT_SORT.map((item) => ({ ...item })))
  }

  return (
    <div className="p-6 space-y-6">
      {/* 頁面標題 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-text-primary">機器人管理</h1>
          <p className="text-text-secondary mt-1">管理您的交易機器人</p>
        </div>
        <Button 
          onClick={() => {
            console.log('[Bots] 建立機器人按鈕被點擊，設置 wizardOpen 為 true')
            setWizardOpen(true)
          }}
        >
          <Plus className="h-4 w-4 mr-2" />
          建立機器人
        </Button>
      </div>

      {/* 排序工具列 */}
      <div className="flex items-center justify-end gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleClearSorting}
          title="清除目前所有排序"
        >
          清除排序
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRestoreDefaultSorting}
          title="恢復系統預設排序"
        >
          恢復預設
        </Button>
      </div>

      {/* 批次刪除工具列 */}
      {selectedBotIds.size > 0 && (
        <div className="sticky top-0 z-10 flex items-center justify-between px-4 py-3 bg-background-secondary border border-border rounded-lg shadow-sm">
          <span className="text-sm text-text-primary">
            已選 <strong>{selectedBotIds.size}</strong> 個機器人
          </span>
          <Button
            variant="destructive"
            size="sm"
            className="bg-danger hover:bg-danger/90"
            style={{
              backgroundColor: '#F05B61',
            }}
            onClick={() => {
              const selectedBots = bots.filter(b => selectedBotIds.has(b.id))
              setDeleteBotsDialogOpen(true)
            }}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            刪除
          </Button>
        </div>
      )}

      {/* 表格 */}
      <div 
        className="rounded-xl border border-border overflow-hidden bg-background-secondary"
        style={{
          borderRadius: '12px',
          border: '1px solid #2A2F3A',
          overflow: 'hidden'
        }}
      >
        <div className="overflow-auto">
          <table 
            className="w-full"
            style={{
              borderCollapse: 'separate',
              borderSpacing: 0,
              width: '100%'
            }}
          >
            <thead>
              {table.getHeaderGroups().map(headerGroup => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header, headerIndex) => {
                    // 判斷欄位是否需要右對齊
                    const columnId = header.column.id
                    const isRightAligned = ['positionValue', 'leverage', 'status', 'pnlToday', 'pnlMtd', 'actions'].includes(columnId)
                    const isSelectColumn = columnId === 'select'
                    
                    return (
                      <th
                        key={header.id}
                        style={{ 
                          width: header.getSize() !== 150 ? header.getSize() : undefined,
                          ...(headerIndex === 0 && { borderTopLeftRadius: '12px' }),
                          ...(headerIndex === headerGroup.headers.length - 1 && { borderTopRightRadius: '12px' })
                        }}
                        className={cn(
                          "h-16 px-4 align-middle font-medium text-text-secondary leading-relaxed bg-background-secondary border-b border-border",
                          isRightAligned ? "text-right" : "text-left",
                          isSelectColumn && "text-center"
                        )}
                      >
                        {header.isPlaceholder
                          ? null
                          : flexRender(header.column.columnDef.header, header.getContext())}
                      </th>
                    )
                  })}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row, index) => {
                const bot = row.original
                const isError = bot.status === 'error'
                const isOdd = index % 2 === 0
                const isLastRow = index === table.getRowModel().rows.length - 1

                return (
                  <tr
                    key={row.id}
                    className={cn(
                      "transition-colors",
                      // Hover 樣式（最優先）
                      "hover:bg-background-tertiary",
                      // Zebra 樣式（基礎層）
                      !isError && isOdd && "bg-[#141820]",
                      !isError && !isOdd && "bg-[#191E26]",
                      // 錯誤列樣式（疊加在 zebra 上）
                      isError && "bg-[rgba(240,91,97,0.12)]",
                      // 行高
                      bot.lastActiveAt ? "min-h-[80px]" : "min-h-[72px]"
                    )}
                    style={{
                      ...(isError && { borderLeftWidth: '3px', borderLeftColor: '#F05B61', borderLeftStyle: 'solid' })
                    }}
                    onMouseEnter={() => setHoveredRowId(bot.id)}
                    onMouseLeave={() => setHoveredRowId(null)}
                  >
                    {row.getVisibleCells().map((cell, cellIndex) => {
                      // 判斷欄位是否需要右對齊
                      const columnId = cell.column.id
                      const isRightAligned = ['positionValue', 'leverage', 'status', 'pnlToday', 'pnlMtd', 'actions'].includes(columnId)
                      const isSelectColumn = columnId === 'select'
                      
                      return (
                        <td
                          key={cell.id}
                          style={{
                            ...(isLastRow && cellIndex === 0 && { borderBottomLeftRadius: '12px' }),
                            ...(isLastRow && cellIndex === row.getVisibleCells().length - 1 && { borderBottomRightRadius: '12px' })
                          }}
                          className={cn(
                            "px-4 align-middle leading-relaxed py-6 border-b border-border",
                            // 最後一行移除底部邊框
                            isLastRow && "border-b-0",
                            // 根據欄位設置對齊方式
                            isRightAligned ? "text-right" : isSelectColumn ? "text-center" : "text-left"
                          )}
                        >
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </td>
                      )
                    })}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 建立機器人向導 */}
      <CreateBotWizard
        isOpen={wizardOpen}
        onClose={() => setWizardOpen(false)}
        onSuccess={handleCreateSuccess}
      />

      {/* 錯誤排查 Drawer */}
      <BotErrorDrawer
        isOpen={errorDrawerOpen}
        onClose={() => {
          setErrorDrawerOpen(false)
          setSelectedBot(null)
        }}
        bot={selectedBot}
        onAction={handleBotAction}
      />

      {/* 單筆刪除對話框 */}
      <DeleteBotDialog
        isOpen={deleteDialogOpen}
        onClose={() => {
          setDeleteDialogOpen(false)
          setBotToDelete(null)
        }}
        onConfirm={handleDeleteBot}
        bot={botToDelete}
      />

      {/* 批次刪除對話框 */}
      <DeleteBotsDialog
        isOpen={deleteBotsDialogOpen}
        onClose={() => setDeleteBotsDialogOpen(false)}
        onConfirm={handleDeleteBots}
        bots={bots.filter(b => selectedBotIds.has(b.id))}
      />

      {/* Toast 提示 */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={toast.onUndo ? 0 : 3000}
          onClose={() => setToast(null)}
          onUndo={toast.onUndo}
        />
      )}
    </div>
  )
}