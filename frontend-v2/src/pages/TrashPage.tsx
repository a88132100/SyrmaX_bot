import React, { useEffect, useMemo, useState } from 'react'
import { RefreshCw, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { mockStore, type ListTrashParams } from '@/lib/mockStore'
import { useTrashCount } from '@/hooks/useTrashCount'
import { TrashToolbar } from './bots/components/TrashToolbar'
import { TrashTable } from './bots/components/TrashTable'
import { Pager } from '@/components/ui/Pager'
import { Toast } from '@/components/ui/Toast'
import { PurgeBotDialog } from '@/components/bot/PurgeBotDialog'
import type { Bot } from '@/lib/mockStore'

type Sort = { field: 'deletedAt' | 'name'; dir: 'asc' | 'desc' } | null

/**
 * 回收桶頁面
 * - 顯示軟刪除的機器人列表
 * - 支援搜尋、篩選、排序、分頁
 * - 單筆還原/永久刪除功能
 */
export default function TrashPage() {
  const trashCount = useTrashCount()

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [query, setQuery] = useState('')
  const [exchange, setExchange] = useState<string | undefined>(undefined)
  const [strategy, setStrategy] = useState<string | undefined>(undefined)
  // 預設排序：刪除時間降序（最新刪除在最上面）
  const [sort, setSort] = useState<Sort>({ field: 'deletedAt', dir: 'desc' })
  // 儲存所有符合條件的資料（不包含排序和分頁）
  const [allRows, setAllRows] = useState<Bot[]>([])
  const [total, setTotal] = useState(0)
  const [toast, setToast] = useState<{
    message: string
    type: 'success' | 'error' | 'info'
  } | null>(null)
  // 永久刪除 Dialog 狀態
  const [purgeDialogOpen, setPurgeDialogOpen] = useState(false)
  const [botToPurge, setBotToPurge] = useState<Bot | null>(null)

  // 組合查詢參數
  const params = useMemo<ListTrashParams>(
    () => ({
      page,
      size: pageSize,
      query,
      exchange,
      strategy,
      sort: sort ?? undefined, // 將 null 轉為 undefined
    }),
    [page, pageSize, query, exchange, strategy, sort]
  )

  // 載入資料（不包含排序和分頁，這些在客戶端處理）
  async function fetchData(showSuccessToast = false) {
    console.log('fetchData 開始執行')
    setLoading(true)
    setError(null)
    try {
      // 使用最新的參數重新載入（不包含 sort，因為排序在客戶端處理）
      // 使用一個很大的 pageSize 來取得所有符合條件的資料
      const currentParams: ListTrashParams = {
        page: 1,
        size: 10000, // 足夠大的數字以取得所有項目
        query,
        exchange,
        strategy,
        // 不傳入 sort，讓客戶端處理排序
      }
      console.log('載入參數:', currentParams)
      
      // 先等待一小段時間確保 loading 狀態可見
      await new Promise(resolve => setTimeout(resolve, 100))
      
      const result = await mockStore.listTrash(currentParams)
      // 儲存所有符合條件的資料（不包含排序和分頁）
      setAllRows(result.items)
      setTotal(result.total)
      console.log('載入完成，共', result.total, '筆')
      
      // 如果是手動重新整理，顯示成功 toast
      if (showSuccessToast) {
        setToast({ message: '已重新整理', type: 'success' })
      }
    } catch (e: any) {
      console.error('載入失敗:', e)
      setError(e?.message ?? '載入失敗')
      setToast({ 
        message: '操作失敗：系統暫時發生問題，請稍後再試。', 
        type: 'error' 
      })
    } finally {
      setLoading(false)
      console.log('fetchData 完成')
    }
  }

  // 當查詢參數改變時重新載入（不包含 sort，因為排序在客戶端處理）
  useEffect(() => {
    fetchData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, exchange, strategy])

  // 客戶端排序和分頁處理
  const rows = useMemo(() => {
    // 先進行排序
    let sortedRows = [...allRows]
    
    // 如果 sort 為 null，恢復到預設的刪除時間降序
    const effectiveSort = sort || { field: 'deletedAt' as const, dir: 'desc' as const }
    
    sortedRows.sort((a, b) => {
      const getValue = (x: Bot) => {
        if (effectiveSort.field === 'deletedAt') {
          return typeof x.deletedAt === 'number' ? x.deletedAt : 0
        }
        return x.name.toLowerCase()
      }
      const av = getValue(a)
      const bv = getValue(b)
      if (effectiveSort.dir === 'asc') {
        return av > bv ? 1 : av < bv ? -1 : 0
      } else {
        return av < bv ? 1 : av > bv ? -1 : 0
      }
    })
    
    // 再進行分頁
    const start = (page - 1) * pageSize
    const end = start + pageSize
    return sortedRows.slice(start, end)
  }, [allRows, sort, page, pageSize])

  // 單筆還原
  async function handleRestore(id: string) {
    try {
      const bot = rows.find(r => r.id === id)
      const botName = bot?.name || '機器人'
      
      await mockStore.restoreBots([id])
      // 重新載入列表
      await fetchData()
      // 回收桶計數會透過訂閱機制自動更新（restoreBots 會觸發 _notifyBotsChanged）
      setToast({ 
        message: `已還原 1 個機器人「${botName}」`, 
        type: 'success' 
      })
    } catch (e: any) {
      console.error('還原失敗:', e)
      setToast({
        message: '操作失敗：系統暫時發生問題，請稍後再試。',
        type: 'error',
      })
    }
  }

  // 打開永久刪除確認 Dialog
  function handlePurgeClick(id: string) {
    const bot = rows.find(r => r.id === id)
    if (bot) {
      setBotToPurge(bot)
      setPurgeDialogOpen(true)
    }
  }

  // 確認永久刪除
  async function handlePurgeConfirm() {
    if (!botToPurge) return
    
    try {
      await mockStore.purgeBots([botToPurge.id])
      const botName = botToPurge.name
      // 重新載入列表
      await fetchData()
      // 回收桶計數會透過訂閱機制自動更新（purgeBots 會觸發 _notifyBotsChanged）
      setToast({ 
        message: `已永久刪除 1 個機器人「${botName}」`, 
        type: 'success' 
      })
      setBotToPurge(null)
    } catch (e: any) {
      console.error('永久刪除失敗:', e)
      setToast({
        message: '操作失敗：系統暫時發生問題，請稍後再試。',
        type: 'error',
      })
      // 失敗時不關閉 Dialog，讓用戶重試
    }
  }

  // 當 pageSize 改變時，重置到第一頁
  useEffect(() => {
    setPage(1)
  }, [pageSize, query, exchange, strategy])
  
  // 當排序改變時，重置到第一頁（因為排序會改變資料順序）
  useEffect(() => {
    setPage(1)
  }, [sort])

  return (
    <div className="p-6">
      {/* 頁面標題 */}
      <header className="mb-4">
        <h1 className="text-2xl font-semibold tracking-tight text-text-primary">回收桶</h1>
        <div className="mt-3 h-px bg-border/60" />
      </header>

      {/* 工具列：搜尋 + 篩選 + 重新整理 */}
      <div className="mt-6 mb-6 flex flex-col">
        {/* 第一行：只有搜尋欄 */}
        <div className="w-full" style={{ marginBottom: '16px' }}>
          <div className="flex items-center w-full rounded-full border border-border bg-background-secondary px-3 py-1.5 text-sm focus-within:border-border/80 transition-colors">
            <Search className="w-4 h-4 text-text-tertiary flex-shrink-0 mr-2" />
            <input
              type="text"
              placeholder="搜尋名稱 / 幣對 / 策略"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 bg-transparent outline-none border-none shadow-none ring-0 placeholder:text-text-tertiary/60 text-text-primary"
              style={{
                boxShadow: 'none',
                WebkitAppearance: 'none',
                appearance: 'none',
              }}
            />
          </div>
        </div>

        {/* 第二行：篩選 dropdown + 重新整理 */}
        <div className="flex items-center gap-2">
          <TrashToolbar
            exchange={exchange}
            onExchange={setExchange}
            strategy={strategy}
            onStrategy={setStrategy}
          />
          <Button
            variant="ghost"
            size="icon"
            onClick={() => {
              console.log('重新整理按鈕被點擊')
              fetchData(true) // 傳入 true 表示手動重新整理，需要顯示成功 toast
            }}
            className="h-9 w-9 hover:bg-background-secondary/50 cursor-pointer relative z-10"
            aria-label="重新整理"
            disabled={loading}
            title="重新整理"
            type="button"
          >
            <RefreshCw 
              className={`w-4 h-4 transition-transform ${loading ? 'animate-spin' : ''}`}
              style={loading ? { animation: 'spin 1s linear infinite' } : {}}
            />
          </Button>
        </div>
      </div>

      {/* 統計文字 */}
      <div 
        className="text-sm text-text-secondary"
        style={{ 
          marginTop: '16px',  // 與下拉選單按鈕之間的間距（使用明確的像素值）
          marginBottom: '24px' // 與下方表格之間的間距
        }}
      >
        目前共 {trashCount} 個可復原項目
      </div>

      {/* 表格 */}
      <TrashTable
        loading={loading}
        error={error}
        rows={rows}
        total={total}
        trashCount={trashCount}
        sort={sort}
        onSort={setSort}
        onRestore={handleRestore}
        onPurge={handlePurgeClick}
      />

      {/* 分頁 */}
      {total > 0 && (
        <div className="mt-2">
          <Pager
            page={page}
            pageSize={pageSize}
            total={total}
            onPage={setPage}
            onPageSize={setPageSize}
          />
        </div>
      )}

      {/* Toast 通知 */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={3000}
          onClose={() => setToast(null)}
        />
      )}

      {/* 永久刪除確認 Dialog */}
      <PurgeBotDialog
        isOpen={purgeDialogOpen}
        onClose={() => {
          setPurgeDialogOpen(false)
          setBotToPurge(null)
        }}
        onConfirm={handlePurgeConfirm}
        bot={botToPurge}
      />
    </div>
  )
}

