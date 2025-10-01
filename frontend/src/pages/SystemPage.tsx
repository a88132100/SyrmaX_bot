import React from 'react'
import { RefreshCw, Download, Monitor, Activity, Database, Wifi } from 'lucide-react'
import { SxButton } from '@/components/ui/sx-button'
import { BackBar } from '@/components/ui/BackBar'

const systemStatus = [
  { name: '撮合服務', status: '良好', latency: '12ms', icon: Activity },
  { name: '風控服務', status: '良好', latency: '8ms', icon: Monitor },
  { name: '執行器', status: '良好', latency: '15ms', icon: RefreshCw },
  { name: 'WebSocket', status: '良好', latency: '5ms', icon: Wifi },
  { name: '資料庫', status: '良好', latency: '3ms', icon: Database },
]

export function SystemPage() {
  return (
    <div className="space-y-6">
      <BackBar />
      
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-sx-text">系統監控</h1>
          <p className="text-sx-sub">監控系統運行狀態和性能指標</p>
        </div>
        <div className="flex space-x-2">
          <SxButton variant="outline" leftIcon={<RefreshCw className="h-4 w-4" />}>
            重新啟動服務
          </SxButton>
          <SxButton variant="outline" leftIcon={<Download className="h-4 w-4" />}>
            下載診斷包
          </SxButton>
        </div>
      </div>

      {/* System Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
        {systemStatus.map((service, index) => {
          const Icon = service.icon
          return (
            <div key={index} className="bg-card border border-gray-200 rounded-2xl p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 rounded-lg bg-success/10">
                  <Icon className="h-5 w-5 text-success" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">{service.name}</h3>
                  <p className="text-sm text-success">{service.status}</p>
                </div>
              </div>
              <div className="text-2xl font-bold text-foreground mb-1">
                {service.latency}
              </div>
              <p className="text-xs text-muted-foreground">延遲時間</p>
            </div>
          )
        })}
      </div>

      {/* Logs Section */}
      <div className="bg-card border border-gray-200 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-foreground">系統日誌</h3>
          <SxButton variant="outline" size="sm">
            檢視日誌
          </SxButton>
        </div>
        <div className="bg-muted rounded-lg p-4 font-mono text-sm">
          <div className="text-success">[2024-01-20 14:30:15] INFO: 系統運行正常</div>
          <div className="text-success">[2024-01-20 14:30:10] INFO: 風控服務已啟動</div>
          <div className="text-success">[2024-01-20 14:30:05] INFO: 撮合服務已連接</div>
        </div>
      </div>
    </div>
  )
}
