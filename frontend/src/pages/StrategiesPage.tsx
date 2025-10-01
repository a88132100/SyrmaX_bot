import React from 'react'
import { Plus, TestTube, FilePlus, Settings2, Play, Pause } from 'lucide-react'
import { SxButton } from '@/components/ui/sx-button'
import { BackBar } from '@/components/ui/BackBar'

export function StrategiesPage() {
  return (
    <div className="space-y-6">
      <BackBar />
      
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-sx-text">策略配置</h1>
          <p className="text-sx-sub">設置交易策略參數和回測</p>
        </div>
        <div className="flex space-x-2">
          <SxButton variant="outline" leftIcon={<TestTube className="h-4 w-4" />}>
            回測
          </SxButton>
          <SxButton variant="outline" leftIcon={<FilePlus className="h-4 w-4" />}>
            建立範本
          </SxButton>
          <SxButton 
            variant="primary" 
            size="lg"
            leftIcon={<Plus className="h-5 w-5" />}
          >
            新增策略
          </SxButton>
        </div>
      </div>

      <div className="bg-card border border-gray-200 rounded-2xl p-12 text-center">
        <Settings2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-foreground mb-2">
          策略配置功能開發中
        </h3>
        <p className="text-muted-foreground mb-6">
          此功能將包含策略創建、回測和模板管理
        </p>
        <div className="flex justify-center space-x-2">
          <SxButton variant="success" leftIcon={<Play className="h-4 w-4" />}>
            啟用策略
          </SxButton>
          <SxButton variant="warning" leftIcon={<Pause className="h-4 w-4" />}>
            停用策略
          </SxButton>
          <SxButton variant="outline" leftIcon={<TestTube className="h-4 w-4" />}>
            回測策略
          </SxButton>
        </div>
      </div>
    </div>
  )
}
