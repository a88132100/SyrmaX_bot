import React from 'react'
import { FileSpreadsheet, ShieldCheck, History } from 'lucide-react'
import { SxButton } from '@/components/ui/sx-button'

export function HistoryPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">交易記錄</h1>
          <p className="text-muted-foreground">查看歷史交易記錄和分析</p>
        </div>
        <div className="flex space-x-2">
          <SxButton variant="outline" leftIcon={<FileSpreadsheet className="h-4 w-4" />}>
            匯出 CSV
          </SxButton>
          <SxButton variant="outline" leftIcon={<ShieldCheck className="h-4 w-4" />}>
            對帳
          </SxButton>
        </div>
      </div>

      <div className="bg-card border border-border rounded-2xl p-12 text-center">
        <History className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-foreground mb-2">
          交易記錄功能開發中
        </h3>
        <p className="text-muted-foreground mb-6">
          此功能將包含交易歷史、分析報告和數據匯出
        </p>
        <div className="flex justify-center space-x-2">
          <SxButton variant="outline" leftIcon={<FileSpreadsheet className="h-4 w-4" />}>
            匯出記錄
          </SxButton>
          <SxButton variant="outline" leftIcon={<ShieldCheck className="h-4 w-4" />}>
            對帳報告
          </SxButton>
        </div>
      </div>
    </div>
  )
}
