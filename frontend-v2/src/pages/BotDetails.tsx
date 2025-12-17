import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { getSeverityBadgeStyle } from '@/lib/subtleBadgeStyles'
import { mockStore, type Bot } from '@/lib/mockStore'
import { formatCurrency, formatPosition } from '@/lib/utils'
import { cn } from '@/lib/utils'
import { BotStatusBadge } from '@/components/bots/BotStatusBadge'
import { BotDetailActions } from '@/components/bots/BotDetailActions'
import { DetailSection } from '@/components/bots/DetailSection'
import { DeleteBotDialog } from '@/components/bot/DeleteBotDialog'
import { RenameBotDialog } from '@/components/bots/RenameBotDialog'
import { Toast } from '@/components/ui/Toast'
import { getBotById, updateBot, addBot, removeBot } from '@/lib/botsStorage'

/**
 * 機器人詳細頁
 * Phase 4: 狀態 Banner × Skeleton × RWD × 結構重整
 * 
 * 功能：
 * - 顯示機器人基本資訊、策略設定、風控設定、績效摘要
 * - 頂部卡片顯示狀態徽章與操作按鈕（啟動/暫停、複製、刪除）
 * - 狀態 Banner：顯示非 running 狀態的提示訊息
 * - Skeleton Loading：300ms 延遲，避免閃爍
 * - RWD 響應式設計：Header 支援 flex-wrap，窄螢幕時按鈕自動換行
 * - 使用 DetailSection 統一四個區塊樣式
 * - 操作按鈕具備 loading 狀態、錯誤提示、與列表頁狀態一致的顏色邏輯
 */
export default function BotDetails() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  
  // bot 狀態：undefined = 載入中, null = 找不到, Bot = 找到機器人
  const [bot, setBot] = useState<Bot | null | undefined>(undefined)
  const [isActionLoading, setIsActionLoading] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null)
  const [isDeleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [isRenameDialogOpen, setRenameDialogOpen] = useState(false)

  // 載入機器人資料
  useEffect(() => {
    if (!id) {
      setBot(null)
      return
    }

    // Phase 4: 使用 300ms 延遲，避免 Skeleton 一閃而過
    const timer = setTimeout(() => {
      // 使用 botsStorage 的 getBotById 從 localStorage 查找
      const foundBot = getBotById(id)
      setBot(foundBot ?? null)
    }, 300)

    return () => clearTimeout(timer)
  }, [id])

  // 訂閱 mockStore 變更，即時更新 bot 狀態
  useEffect(() => {
    if (!id) return

    const unsubscribe = mockStore.subscribeBots(() => {
      // 使用 botsStorage 的 getBotById 從 localStorage 查找
      const updatedBot = getBotById(id)
      if (updatedBot) {
        setBot(updatedBot)
      } else {
        // 如果找不到，設為 null（可能已被刪除）
        setBot(null)
      }
    })

    return unsubscribe
  }, [id])

  // Phase 4: Skeleton Loading 元件
  function BotDetailSkeleton() {
    return (
      <div className="animate-pulse">
        {/* Header skeleton */}
        <div className="rounded-2xl border border-border/60 bg-background-secondary/80 px-6 py-4">
          <div className="h-6 w-64 bg-white/10 rounded mb-4" />
          <div className="h-4 w-40 bg-white/5 rounded" />
        </div>
        {/* Sections skeleton */}
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="mt-6 rounded-2xl border border-border/60 bg-background-secondary/80 px-6 py-6"
          >
            <div className="h-5 w-32 bg-white/10 rounded mb-3" />
            <div className="space-y-2">
              <div className="h-3 w-3/4 bg-white/5 rounded" />
              <div className="h-3 w-2/3 bg-white/5 rounded" />
              <div className="h-3 w-1/2 bg-white/5 rounded" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  // Loading 狀態（bot === undefined）
  if (bot === undefined) {
    return (
      <div className="p-6">
        {/* 返回按鈕 */}
        <div className="mb-4">
          <Link
            to="/bots"
            className="inline-flex items-center text-sm text-text-secondary hover:text-text-primary transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            返回機器人管理
          </Link>
        </div>
        {/* 外層容器 */}
        <div className="mx-auto max-w-6xl px-6 py-6">
          <BotDetailSkeleton />
        </div>
      </div>
    )
  }

  // NotFound 狀態
  if (!bot) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <h1 className="text-2xl font-semibold text-text-primary mb-4">找不到機器人</h1>
          <p className="text-text-secondary mb-6">此機器人可能已被刪除或不存在。</p>
          <Button onClick={() => navigate('/bots')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回機器人管理
          </Button>
        </div>
      </div>
    )
  }

  // 操作處理函數：啟動機器人
  const handleStart = async () => {
    if (!bot) return
    
    setIsActionLoading(true)
    setActionError(null)
    
    try {
      // 使用 botsStorage 更新 localStorage
      updateBot(bot.id, {
        status: 'running',
        lastActiveAt: new Date().toISOString(),
      })
      
      // 重新從 localStorage 讀取最新 bot 狀態
      const updated = getBotById(bot.id)
      if (updated) {
        setBot(updated)
      }
      
      setToast({
        type: 'success',
        message: `已啟動機器人「${bot.name}」`,
      })
    } catch (error) {
      setToast({
        type: 'error',
        message: '啟動機器人失敗，請稍後再試',
      })
    } finally {
      setIsActionLoading(false)
    }
  }

  // 操作處理函數：暫停機器人
  const handleStop = async () => {
    if (!bot) return
    
    setIsActionLoading(true)
    setActionError(null)
    
    try {
      // 使用 botsStorage 更新 localStorage
      updateBot(bot.id, {
        status: 'paused',
      })
      
      // 重新從 localStorage 讀取最新 bot 狀態
      const updated = getBotById(bot.id)
      if (updated) {
        setBot(updated)
      }
      
      setToast({
        type: 'success',
        message: `已暫停機器人「${bot.name}」`,
      })
    } catch (error) {
      setToast({
        type: 'error',
        message: '暫停機器人失敗，請稍後再試',
      })
    } finally {
      setIsActionLoading(false)
    }
  }

  // 操作處理函數：複製機器人
  const handleDuplicate = async () => {
    if (!bot) return
    
    setIsActionLoading(true)
    setActionError(null)
    
    try {
      // 建立新機器人（複製）
      const newBot: Bot = {
        ...bot,
        id: crypto.randomUUID(),
        name: `${bot.name} (複製)`,
        status: 'stopped',
        pnlToday: 0,
        pnlMtd: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isDeleted: false,
      }
      
      // 使用 botsStorage 新增到 localStorage
      addBot(newBot)
      
      // ⚠️ 這裡「不要」 setBot(newBot)，也不要 navigate
      // 畫面仍停留在原本的機器人
      
      setToast({
        type: 'success',
        message: `已建立副本「${newBot.name}」`,
      })
    } catch (error) {
      setToast({
        type: 'error',
        message: '建立副本失敗，請稍後再試',
      })
    } finally {
      setIsActionLoading(false)
    }
  }

  // 操作處理函數：開啟重新命名對話框
  const handleRename = () => {
    setRenameDialogOpen(true)
  }

  // 操作處理函數：開啟刪除對話框
  const handleDelete = () => {
    setDeleteDialogOpen(true)
  }

  // 操作處理函數：確認刪除
  const handleDeleteConfirm = async () => {
    if (!bot) return
    
    setIsActionLoading(true)
    setActionError(null)
    
    try {
      // 先從 localStorage 讀取機器人，確保存在
      const currentBot = getBotById(bot.id)
      if (!currentBot) {
        throw new Error('找不到機器人')
      }
      
      // 使用 mockStore.deleteBot 進行軟刪除（包含回收桶邏輯）
      // 傳入 userId 參數（這裡先用 'system'，之後可從 context 取得）
      await mockStore.deleteBot(bot.id, 'system')
      
      // 同步到 localStorage：標記為已刪除
      const now = Date.now()
      const DAY = 24 * 60 * 60 * 1000
      const GRACE_DAYS = 7
      updateBot(bot.id, {
        isDeleted: true,
        deletedAt: now,
        purgeAt: now + GRACE_DAYS * DAY,
        deletedBy: 'system',
        updatedAt: new Date().toISOString(),
      })
      
      setToast({ message: '機器人已刪除（可於回收桶還原）', type: 'success' })
      // 導回列表頁
      navigate('/bots')
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '刪除失敗，請稍後再試'
      setActionError(errorMsg)
      setToast({ message: errorMsg, type: 'error' })
      setIsActionLoading(false)
    }
  }

  // 策略類型映射
  const strategyUseMap = {
    trend: '趨勢跟隨',
    range: '網格',
    defense: '防守型',
  }

  // 風險等級映射
  const riskMap = {
    low: '低',
    mid: '中',
    high: '高',
  }

  // 格式化日期時間
  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="p-6">
      {/* 返回按鈕 */}
      <div className="mb-4">
        <Link
          to="/bots"
          className="inline-flex items-center text-sm text-text-secondary hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          返回機器人管理
        </Link>
      </div>

      {/* 外層容器 - 限制最大寬度並置中 */}
      <div className="mx-auto max-w-6xl px-6 py-6 space-y-6">
        {/* Header 卡片 - Phase 4 RWD 更新版 */}
        <section 
          className="rounded-2xl border border-border px-6 py-4"
          style={{ 
            backgroundColor: 'rgba(31, 35, 41, 0.6)', // bg-background-tertiary with 60% opacity
            borderRadius: '16px' // 確保圓角生效
          }}
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            {/* 左側：名稱 + meta + 狀態 */}
            <div className="flex flex-col gap-2 flex-1 min-w-[220px]">
              {/* 上：機器人名稱 + 狀態徽章 */}
              <div className="flex items-center">
                <h1 className="text-2xl font-semibold text-text-primary">{bot.name}</h1>
                <div className="ml-9" style={{ marginLeft: '36px' }}>
                  <BotStatusBadge status={bot.status} />
                </div>
              </div>
              {/* 下：交易所 / 交易對 / 倍數 / 策略包 */}
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-text-secondary">
                {bot.exchange} · {bot.symbol} · {bot.leverage}x · {bot.strategyPackName}
              </div>
              {/* 錯誤訊息列 */}
              {actionError && (
                <div className="text-xs text-red-400 mt-1">
                  {actionError}
                </div>
              )}
              {/* 錯誤狀態的額外 Badge */}
              {bot.status === 'error' && bot.lastError && (
                <span style={{ ...getSeverityBadgeStyle('danger'), marginTop: '4px', width: 'fit-content' }}>
                  {bot.lastError}
                </span>
              )}
            </div>

            {/* 右側：操作按鈕群組 */}
            {bot && (
              <BotDetailActions
                bot={bot}
                isLoading={isActionLoading}
                onStart={handleStart}
                onStop={handleStop}
                onRename={handleRename}
                onDuplicate={handleDuplicate}
                onDelete={handleDelete}
              />
            )}
          </div>
        </section>

        {/* Phase 4: 使用 DetailSection 統一四個區塊 */}
        <div className="space-y-6">
          {/* 基本資訊 */}
          <DetailSection title="基本資訊">
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-2 text-sm leading-relaxed pr-6">
              <div className="py-1.5">
                <dt className="text-text-secondary">機器人名稱</dt>
                <dd className="text-text-primary mt-0.5">{bot.name}</dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">建立時間</dt>
                <dd className="text-text-primary mt-0.5">{formatDateTime(bot.createdAt)}</dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">最後更新時間</dt>
                <dd className="text-text-primary mt-0.5">{formatDateTime(bot.updatedAt)}</dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">交易所</dt>
                <dd className="text-text-primary mt-0.5">{bot.exchange}</dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">幣對</dt>
                <dd className="text-text-primary mt-0.5 font-mono">{bot.symbol}</dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">槓桿</dt>
                <dd className="text-text-primary mt-0.5">{bot.leverage}x</dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">策略包名稱</dt>
                <dd className="text-text-primary mt-0.5">{bot.strategyPackName}</dd>
              </div>
            </dl>
          </DetailSection>

          {/* 風控設定摘要 */}
          <DetailSection title="風控設定摘要">
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-2 text-sm leading-relaxed pr-6">
              <div className="py-1.5">
                <dt className="text-text-secondary">單筆下單金額</dt>
                <dd className="text-text-primary mt-0.5">{formatPosition(bot.positionMode, bot.positionValue, mockStore.accountEquity)}</dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">最大倉位</dt>
                <dd className="text-text-secondary mt-0.5 italic">—</dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">停利 / 停損比</dt>
                <dd className="text-text-secondary mt-0.5 italic">—</dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">每日最大虧損</dt>
                <dd className="text-text-secondary mt-0.5 italic">—</dd>
              </div>
            </dl>
          </DetailSection>

          {/* 策略設定摘要 */}
          <DetailSection title="策略設定摘要">
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-2 text-sm leading-relaxed pr-6">
              <div className="py-1.5">
                <dt className="text-text-secondary">策略類型</dt>
                <dd className="text-text-primary mt-0.5">{strategyUseMap[bot.strategyUse]}</dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">風險等級</dt>
                <dd className="text-text-primary mt-0.5">{riskMap[bot.strategyRisk]}</dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">指標組合</dt>
                <dd className="text-text-primary mt-0.5">使用 EMA + RSI 濾網</dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">下單頻率</dt>
                <dd className="text-text-primary mt-0.5">每 1 分鐘掃描一次訊號</dd>
              </div>
            </dl>
          </DetailSection>

          {/* 績效摘要 */}
          <DetailSection title="績效摘要">
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-2 text-sm leading-relaxed pr-6">
              <div className="py-1.5">
                <dt className="text-text-secondary">今日 PnL</dt>
                <dd className={cn(
                  'mt-0.5 font-semibold tabular-nums',
                  bot.pnlToday > 0
                    ? 'text-success'
                    : bot.pnlToday < 0
                      ? 'text-danger'
                      : 'text-text-tertiary'
                )}>
                  {formatCurrency(bot.pnlToday)}
                </dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">本月 PnL</dt>
                <dd className={cn(
                  'mt-0.5 font-semibold tabular-nums',
                  bot.pnlMtd > 0
                    ? 'text-success'
                    : bot.pnlMtd < 0
                      ? 'text-danger'
                      : 'text-text-tertiary'
                )}>
                  {formatCurrency(bot.pnlMtd)}
                </dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">30 日勝率</dt>
                <dd className="text-text-secondary mt-0.5 italic">尚無資料</dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">30 日 Sharpe</dt>
                <dd className="text-text-secondary mt-0.5 italic">尚無資料</dd>
              </div>
              <div className="py-1.5">
                <dt className="text-text-secondary">最大回撤</dt>
                <dd className="text-text-secondary mt-0.5 italic">尚無資料</dd>
              </div>
            </dl>
          </DetailSection>
        </div>
      </div>

      {/* 重新命名對話框 */}
      {bot && (
        <RenameBotDialog
          bot={bot}
          isOpen={isRenameDialogOpen}
          onClose={() => setRenameDialogOpen(false)}
          onRenamed={(newName) => {
            // 重新從 localStorage 讀取最新 bot 狀態
            const updated = getBotById(bot.id)
            if (updated) {
              setBot(updated)
            }
            // 顯示成功 Toast
            setToast({
              type: 'success',
              message: `已將機器人名稱更新為「${newName}」`,
            })
          }}
        />
      )}

      {/* 刪除確認對話框 */}
      {bot && (
        <DeleteBotDialog
          isOpen={isDeleteDialogOpen}
          onClose={() => setDeleteDialogOpen(false)}
          onConfirm={handleDeleteConfirm}
          bot={bot}
        />
      )}

      {/* Toast 提示 */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={3000}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  )
}
