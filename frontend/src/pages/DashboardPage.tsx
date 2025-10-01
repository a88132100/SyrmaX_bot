import { 
  DollarSign, 
  TrendingUp, 
  Activity, 
  Shield
} from 'lucide-react'
import { StatCard } from '@/components/ui/StatCard'
import { QuickActions } from '@/components/dashboard/QuickActions'
import { BotControl } from '@/components/bot/BotControl'

const kpiData = [
  {
    icon: <DollarSign className="h-6 w-6 text-gold-400" />,
    title: '總資產',
    value: '$0.00',
    subtitle: '今日無變化',
    trend: 'flat' as const
  },
  {
    icon: <TrendingUp className="h-6 w-6 text-success" />,
    title: '今日收益',
    value: '+0.00%',
    subtitle: '較昨日持平',
    trend: 'flat' as const
  },
  {
    icon: <Activity className="h-6 w-6 text-warn" />,
    title: '活躍交易',
    value: '0',
    subtitle: '等待啟動',
    trend: 'flat' as const
  },
  {
    icon: <Shield className="h-6 w-6 text-success" />,
    title: '系統健康',
    value: '100%',
    subtitle: '運行正常',
    trend: 'up' as const
  }
]

export function DashboardPage() {
  return (
    <div className="max-w-[1280px] mx-auto px-6 md:px-8 py-6">
      {/* Hero Section */}
      <div className="text-center py-8">
        <h1 className="text-4xl font-bold sx-gold bg-clip-text text-transparent mb-4">
          SyrmaX 智能交易平台
        </h1>
        <p className="text-lg text-sx-sub max-w-2xl mx-auto">
          專業的量化交易解決方案，讓AI為您的投資保駕護航
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5 mb-6">
        {kpiData.map((kpi, index) => (
          <StatCard
            key={index}
            icon={kpi.icon}
            title={kpi.title}
            value={kpi.value}
            subtitle={kpi.subtitle}
            trend={kpi.trend}
          />
        ))}
      </div>

      {/* Bot Control */}
      <BotControl />

      {/* Quick Actions */}
      <QuickActions />
    </div>
  )
}