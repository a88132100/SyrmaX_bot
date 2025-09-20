import React from 'react'
import { 
  DollarSign, 
  TrendingUp, 
  Activity, 
  Wallet,
  KeyRound,
  BarChart3,
  Settings2,
  Monitor,
  History,
  Plus
} from 'lucide-react'
import { SxButton } from '@/components/ui/sx-button'
import { formatCurrency, formatPercentage } from '@/lib/utils'

const kpiData = [
  {
    title: '總資產',
    value: '$0.00',
    change: '+0.00%',
    changeType: 'positive' as const,
    icon: DollarSign,
    description: '今日無變化'
  },
  {
    title: '今日收益',
    value: '+0.00%',
    change: '較昨日持平',
    changeType: 'neutral' as const,
    icon: TrendingUp,
    description: '較昨日持平'
  },
  {
    title: '活躍交易',
    value: '0',
    change: '等待啟動',
    changeType: 'neutral' as const,
    icon: Activity,
    description: '等待啟動'
  },
  {
    title: '持倉數量',
    value: '0',
    change: '無持倉',
    changeType: 'neutral' as const,
    icon: Wallet,
    description: '無持倉'
  }
]

const quickActions = [
  {
    title: 'API 金鑰管理',
    description: '管理交易所API金鑰',
    icon: KeyRound,
    href: '/api-keys',
    variant: 'primary' as const
  },
  {
    title: '交易對管理',
    description: '配置交易對參數',
    icon: BarChart3,
    href: '/pairs',
    variant: 'secondary' as const
  },
  {
    title: '持倉監控',
    description: '實時監控持倉狀況',
    icon: Wallet,
    href: '/positions',
    variant: 'secondary' as const
  },
  {
    title: '交易記錄',
    description: '查看歷史交易記錄',
    icon: History,
    href: '/history',
    variant: 'secondary' as const
  },
  {
    title: '策略配置',
    description: '設置交易策略參數',
    icon: Settings2,
    href: '/strategies',
    variant: 'secondary' as const
  },
  {
    title: '系統監控',
    description: '監控系統運行狀態',
    icon: Monitor,
    href: '/system',
    variant: 'secondary' as const
  }
]

export function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-foreground">
          歡迎回來！ 👋
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          查看您的交易表現和系統狀態，開始您的智能交易之旅
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        {kpiData.map((kpi, index) => {
          const Icon = kpi.icon
          return (
            <div 
              key={index}
              className="sx-hover-lift bg-card border border-border rounded-2xl p-6 space-y-4"
            >
              <div className="flex items-center justify-between">
                <div className="p-3 rounded-xl bg-primary/10">
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-muted-foreground">
                    {kpi.title}
                  </p>
                  <p className="text-2xl font-bold text-foreground">
                    {kpi.value}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`text-sm font-medium ${
                  kpi.changeType === 'positive' ? 'text-success' :
                  kpi.changeType === 'negative' ? 'text-danger' :
                  'text-muted-foreground'
                }`}>
                  {kpi.change}
                </span>
                <span className="text-xs text-muted-foreground">
                  {kpi.description}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-foreground">🚀 快速功能</h2>
          <p className="text-muted-foreground">選擇您需要的功能模組</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action, index) => {
            const Icon = action.icon
            return (
              <div 
                key={index}
                className="sx-hover-lift bg-card border border-border rounded-2xl p-6 space-y-4 group cursor-pointer"
                onClick={() => window.location.href = action.href}
              >
                <div className="flex items-center space-x-4">
                  <div className={`p-3 rounded-xl ${
                    action.variant === 'primary' 
                      ? 'sx-gradient-primary' 
                      : 'bg-secondary'
                  }`}>
                    <Icon className={`h-6 w-6 ${
                      action.variant === 'primary' 
                        ? 'text-white' 
                        : 'text-secondary-foreground'
                    }`} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                      {action.title}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {action.description}
                    </p>
                  </div>
                </div>
                
                <div className="flex justify-end">
                  <SxButton 
                    variant={action.variant}
                    size="sm"
                    rightIcon={<Plus className="h-4 w-4" />}
                  >
                    進入
                  </SxButton>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}