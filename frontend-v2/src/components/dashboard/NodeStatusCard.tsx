import React from 'react'
import { Activity, Wifi, Clock, Database } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { applyCardStyles } from '@/lib/cardStyles'
import { cn } from '@/lib/utils'
import type { NodeMetric } from '@/lib/types/dashboard'

import { getNodeStatusBadgeStyle } from '@/lib/subtleBadgeStyles'

export function NodeStatusCard({ metrics }: { metrics: NodeMetric }) {
  // 延遲狀態判斷：良好 / 偏高 / 異常
  const getLatencyStatus = (ms: number) => {
    if (ms < 100) {
      // 良好：綠色
      return { label: '良好', status: 'good' as const }
    } else if (ms < 200) {
      // 偏高：橘色
      return { label: '偏高', status: 'warning' as const }
    } else {
      // 異常：紅色
      return { label: '異常', status: 'error' as const }
    }
  }

  // 隊列長度狀態判斷：正常 / 偏高 / 擁擠
  const getQueueStatus = (len: number) => {
    if (len < 5) {
      // 正常：綠色
      return { label: '正常', status: 'good' as const }
    } else if (len < 15) {
      // 偏高：橘色
      return { label: '偏高', status: 'warning' as const }
    } else {
      // 擁擠：紅色
      return { label: '擁擠', status: 'error' as const }
    }
  }

  // WS 掛線率狀態判斷：穩定 / 偶發中斷 / 頻繁斷線
  const getWsStatus = (r: number) => {
    if (r < 0.01) {
      // 穩定：綠色
      return { label: '穩定', status: 'good' as const }
    } else if (r < 0.05) {
      // 偶發中斷：橘色
      return { label: '偶發中斷', status: 'warning' as const }
    } else {
      // 頻繁斷線：紅色
      return { label: '頻繁斷線', status: 'error' as const }
    }
  }

  const latencyStatus = getLatencyStatus(metrics.latencyMs)
  const queueStatus = getQueueStatus(metrics.queueLength)
  const wsStatus = getWsStatus(metrics.wsDropRate)

  // 格式化更新時間
  const lastUpdatedTime = new Date(metrics.ts).toLocaleTimeString('zh-TW', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit',
    hour12: false 
  })

  return (
    <Card style={applyCardStyles()}>
      <CardHeader className="pb-1">
        {/* Header 區塊：左側標題，右側更新時間 */}
        <div className="flex items-center justify-between mb-3">
          <CardTitle className="flex items-center gap-xs text-sm font-semibold">
            <Activity className="h-5 w-5 text-primary" />
            節點狀態
          </CardTitle>
          <span className="text-xs text-slate-400">
            更新於 {lastUpdatedTime}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {/* Body 區塊：三條指標列，使用 space-y-3 增加垂直間距 */}
        <div className="mt-2 space-y-3 max-w-sm mx-auto">
          {/* 延遲指標列 */}
          <div className="grid grid-cols-[auto_1fr] items-center gap-3 py-2.5">
            {/* 左側：icon + 指標名稱 */}
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-slate-400" />
              <span className="text-xs text-slate-200">延遲</span>
            </div>
            {/* 右側：數值（粗體）+ 狀態 chip（同一行，向左移動 148 單位 */}
            <div className="flex items-center justify-end" style={{ transform: 'translateX(-592px)' }}>
              <span className="text-sm font-semibold text-slate-50">
                {metrics.latencyMs} ms
              </span>
              <span 
                style={{ ...getNodeStatusBadgeStyle(latencyStatus.status), marginLeft: '24px' }}
              >
                {latencyStatus.label}
              </span>
            </div>
          </div>

          {/* 隊列長度指標列 */}
          <div className="grid grid-cols-[auto_1fr] items-center gap-3 py-2.5">
            {/* 左側：icon + 指標名稱 */}
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-slate-400" />
              <span className="text-xs text-slate-200">隊列長度</span>
            </div>
            {/* 右側：數值（粗體）+ 狀態 chip（同一行，chip 右對齊），向左移動 148 單位 */}
            <div className="flex items-center justify-end" style={{ transform: 'translateX(-592px)' }}>
              <span className="text-sm font-semibold text-slate-50">
                {metrics.queueLength}
              </span>
              <span 
                style={{ ...getNodeStatusBadgeStyle(queueStatus.status), marginLeft: '24px' }}
              >
                {queueStatus.label}
              </span>
            </div>
          </div>

          {/* WS 掛線率指標列 */}
          <div className="grid grid-cols-[auto_1fr] items-center gap-3 py-2.5">
            {/* 左側：icon + 指標名稱 */}
            <div className="flex items-center gap-2">
              <Wifi className="h-4 w-4 text-slate-400" />
              <span className="text-xs text-slate-200">WS 掛線率</span>
            </div>
            {/* 右側：數值（粗體）+ 狀態 chip（同一行，chip 右對齊），向左移動 148 單位 */}
            <div className="flex items-center justify-end" style={{ transform: 'translateX(-592px)' }}>
              <span className="text-sm font-semibold text-slate-50">
                {(metrics.wsDropRate * 100).toFixed(2)}%
              </span>
              <span 
                style={{ ...getNodeStatusBadgeStyle(wsStatus.status), marginLeft: '24px' }}
              >
                {wsStatus.label}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}


