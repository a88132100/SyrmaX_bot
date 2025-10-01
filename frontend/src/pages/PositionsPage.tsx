import React from 'react'
import { Pause, Power, RefreshCw, Wallet, Trash2 } from 'lucide-react'
import { SxButton } from '@/components/ui/sx-button'
import { BackBar } from '@/components/ui/BackBar'

export function PositionsPage() {
  return (
    <div className="space-y-6">
      <BackBar />
      
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-sx-text">持倉監控</h1>
          <p className="text-sx-sub">實時監控持倉狀況和風險控制</p>
        </div>
        <div className="flex space-x-2">
          <SxButton variant="warning" leftIcon={<Pause className="h-4 w-4" />}>
            暫停所有策略
          </SxButton>
          <SxButton variant="destructive" leftIcon={<Power className="h-4 w-4" />}>
            緊急平倉
          </SxButton>
        </div>
      </div>

      <div className="bg-card border border-gray-200 rounded-2xl p-12 text-center">
        <Wallet className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-foreground mb-2">
          持倉監控功能開發中
        </h3>
        <p className="text-muted-foreground mb-6">
          此功能將包含實時持倉監控、風險控制和緊急操作
        </p>
        <div className="flex justify-center space-x-2">
          <SxButton variant="outline" leftIcon={<RefreshCw className="h-4 w-4" />}>
            重新整理
          </SxButton>
          <SxButton variant="danger" leftIcon={<Trash2 className="h-4 w-4" />}>
            平倉
          </SxButton>
        </div>
      </div>
    </div>
  )
}