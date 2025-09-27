import React from 'react'
import { Plus, Upload, Download, BarChart3 } from 'lucide-react'
import { SxButton } from '@/components/ui/sx-button'

export function PairsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">交易對管理</h1>
          <p className="text-muted-foreground">配置交易對參數和策略模板</p>
        </div>
        <SxButton 
          variant="primary" 
          size="lg"
          leftIcon={<Plus className="h-5 w-5" />}
        >
          新增交易對
        </SxButton>
      </div>

      <div className="bg-card border border-gray-200 rounded-2xl p-12 text-center">
        <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-foreground mb-2">
          交易對管理功能開發中
        </h3>
        <p className="text-muted-foreground mb-6">
          此功能將包含交易對配置、策略模板和批量操作
        </p>
        <div className="flex justify-center space-x-2">
          <SxButton variant="outline" leftIcon={<Upload className="h-4 w-4" />}>
            匯入 CSV
          </SxButton>
          <SxButton variant="outline" leftIcon={<Download className="h-4 w-4" />}>
            匯出 CSV
          </SxButton>
        </div>
      </div>
    </div>
  )
}
