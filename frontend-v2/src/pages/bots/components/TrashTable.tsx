import React from 'react'
import { RotateCcw, Trash2, Inbox, SearchX } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { Bot } from '@/lib/mockStore'

interface TrashTableProps {
  loading: boolean
  error: string | null
  rows: Bot[]
  total: number // 當前查詢結果總數（考慮 filter）
  trashCount: number // 回收桶實際總數（不考慮 filter）
  sort: { field: 'deletedAt' | 'name'; dir: 'asc' | 'desc' } | null
  onSort: (s: TrashTableProps['sort']) => void
  onRestore: (id: string) => void
  onPurge: (id: string) => void
}

/**
 * 回收桶表格
 * - 顯示軟刪除的機器人列表
 * - 支援排序（名稱、刪除時間）
 * - 單筆還原/永久刪除操作
 * - 顯示距離清除倒數
 */
export function TrashTable({
  loading,
  error,
  rows,
  total,
  trashCount,
  sort,
  onSort,
  onRestore,
  onPurge,
}: TrashTableProps) {
  const navigate = useNavigate()

  // 載入狀態
  if (loading) {
    return (
      <div
        className="h-40 grid place-items-center opacity-70 rounded-xl border border-border"
        role="status"
        aria-live="polite"
      >
        讀取中…
      </div>
    )
  }

  // 錯誤狀態
  if (error) {
    return (
      <div
        className="h-40 grid place-items-center text-danger rounded-xl border border-border"
        role="alert"
        aria-live="assertive"
      >
        {error}
      </div>
    )
  }

  // 空狀態處理：區分「回收桶完全空」與「filter 無結果」
  if (!rows.length) {
    // 如果 total === 0 且 trashCount > 0，表示是 filter 無結果
    const isFilterEmpty = total === 0 && trashCount > 0
    
    if (isFilterEmpty) {
      // Filter 無結果的 empty state
      return (
        <div
          className="h-64 grid place-items-center rounded-lg border border-border bg-background-secondary overflow-hidden"
          style={{ borderRadius: '8px' }}
          role="status"
          aria-live="polite"
        >
          <div className="flex flex-col items-center gap-4 text-center">
            <SearchX className="h-12 w-12 text-text-tertiary" aria-hidden="true" />
            <div>
              <p className="text-text-primary font-medium mb-1">找不到符合條件的機器人</p>
              <p className="text-sm text-text-secondary">
                試試調整搜尋關鍵字或篩選條件
              </p>
            </div>
          </div>
        </div>
      )
    } else {
      // 回收桶完全空的 empty state
      return (
        <div
          className="h-64 grid place-items-center rounded-lg border border-border bg-background-secondary overflow-hidden"
          style={{ borderRadius: '8px' }}
          role="status"
          aria-live="polite"
        >
          <div className="flex flex-col items-center gap-4 text-center">
            <Inbox className="h-12 w-12 text-text-tertiary" aria-hidden="true" />
            <div>
              <p className="text-text-primary font-medium mb-1">回收桶是空的</p>
              <p className="text-sm text-text-secondary">
                沒有可復原的機器人
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/bots')}
            >
              前往機器人管理
            </Button>
          </div>
        </div>
      )
    }
  }

  // 排序表頭元件
  function SortHeader({
    field,
    label,
  }: {
    field: 'deletedAt' | 'name'
    label: string
  }) {
    const active = sort?.field === field
    const arrow = !active ? '' : sort?.dir === 'asc' ? '↑' : '↓'

    // 排序邏輯：兩個欄位都支援三次點擊循環
    // 無排序 -> 升序 -> 降序 -> 無排序
    const handleSort = () => {
      if (!active) {
        // 當前欄位未排序，設為升序
        onSort({ field, dir: 'asc' })
      } else if (sort?.dir === 'asc') {
        // 當前是升序，改為降序
        onSort({ field, dir: 'desc' })
      } else {
        // 當前是降序，取消排序（第三次點擊）
        onSort(null)
      }
    }

    return (
      <button
        type="button"
        className="text-left w-full flex items-center gap-1 text-text-secondary transition-colors hover:text-text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 bg-transparent border border-border rounded-md px-2 py-1 [background-image:none] [box-shadow:none]"
        onClick={handleSort}
        aria-label={`依${label}排序`}
        aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}
        style={{
          backgroundColor: 'transparent',
          border: '1px solid rgb(42, 47, 58)',
          boxShadow: 'none',
          WebkitAppearance: 'none',
          appearance: 'none',
          backgroundImage: 'none',
          textShadow: 'none',
          outline: 'none',
        }}
      >
        <span>{label}</span>
        {arrow && <span className="text-xs text-text-primary">{arrow}</span>}
      </button>
    )
  }

  const now = Date.now()

  return (
    <div className="rounded-lg border border-border bg-background-secondary overflow-hidden" style={{ borderRadius: '8px' }}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-background-tertiary/40">
            <tr>
              <th className="px-4 py-3 w-[32%] text-left font-medium text-text-primary bg-transparent">
                <SortHeader field="name" label="名稱" />
              </th>
              <th className="px-4 py-3 w-[20%] text-left font-medium text-text-primary">
                策略包
              </th>
              <th className="px-4 py-3 w-[18%] text-left font-medium text-text-primary bg-transparent">
                <SortHeader field="deletedAt" label="刪除時間" />
              </th>
              <th className="px-4 py-3 w-[18%] text-left font-medium text-text-primary">
                距離清除
              </th>
              <th className="px-4 py-3 w-[12%] text-right font-medium text-text-primary">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((r, index) => {
              // 計算距離清除時間（使用 deletedAt + 7天）
              const deletedAt = typeof r.deletedAt === 'number' ? r.deletedAt : 0
              const purgeAt = deletedAt + 7 * 24 * 60 * 60 * 1000 // deletedAt + 7天
              const leftMs = Math.max(0, purgeAt - now)
              const leftDays = Math.floor(leftMs / (24 * 60 * 60 * 1000))
              const leftHours = Math.ceil(leftMs / (60 * 60 * 1000))
              const leftStr =
                leftDays > 0
                  ? `${leftDays} 天`
                  : `${Math.max(1, leftHours)} 小時`

              // 距離清除警示色邏輯
              const getExpireColorClass = () => {
                if (leftDays > 2) {
                  return 'text-text-secondary' // 3天以上：一般文字顏色
                } else if (leftDays >= 1) {
                  return 'text-warning font-medium' // 1-2天：黃色
                } else {
                  return 'text-orange-500 font-medium' // 小於24小時：橘紅色
                }
              }

              const deletedAtStr = deletedAt
                ? new Date(deletedAt).toLocaleString('zh-TW', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                : '-'

              return (
                <tr
                  key={r.id}
                  className="hover:bg-background-tertiary/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-text-primary">{r.name}</div>
                    <div className="text-xs text-text-secondary mt-1.5">
                      {r.symbol} · {r.exchange}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-text-secondary">
                    {r.strategyPackName ?? '-'}
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-text-secondary text-xs">
                      {deletedAtStr}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn('trash-expire-countdown', getExpireColorClass())}>
                      {leftStr}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => onRestore(r.id)}
                        className="h-8 min-w-[80px]"
                        aria-label={`還原機器人 ${r.name}`}
                      >
                        <RotateCcw className="h-3.5 w-3.5 mr-1.5" />
                        還原
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => onPurge(r.id)}
                        className="h-8 min-w-[80px]"
                        aria-label={`永久刪除機器人 ${r.name}`}
                      >
                        <Trash2 className="h-3.5 w-3.5 mr-1.5" />
                        永久刪除
                      </Button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

