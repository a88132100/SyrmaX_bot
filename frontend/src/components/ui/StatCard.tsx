export function StatCard({ 
  icon, 
  title, 
  value, 
  subtitle, 
  trend = 'flat', 
  loading = false 
}: {
  icon: React.ReactNode
  title: string
  value: string
  subtitle?: string
  trend?: 'up' | 'down' | 'flat'
  loading?: boolean
}) {
  if (loading) return <div className="sx-card h-28 animate-pulse" />
  
  return (
    <div className="sx-card p-5 flex items-center gap-4">
      <div className="p-3 rounded-xl bg-white/5">{icon}</div>
      <div className="flex-1 min-w-0">
        <div className="text-sm text-sx-sub">{title}</div>
        <div className="mt-1 text-3xl sx-mono text-sx-text font-semibold">{value}</div>
        {subtitle && <div className="text-xs text-sx-sub mt-1">{subtitle}</div>}
      </div>
      <span className={
        'px-2 py-1 rounded-full text-xs border ' + (
          trend === 'up' ? 'text-success border-success/30' :
          trend === 'down' ? 'text-danger border-danger/30' : 'text-sx-subtext border-white/10'
        )
      }>
        {trend.toUpperCase()}
      </span>
    </div>
  )
}