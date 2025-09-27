export function QuickActions() {
  const actions = [
    { href: "/api-keys", title: "API 金鑰管理", desc: "管理交易所金鑰與權限", icon: "🔑" },
    { href: "/pairs", title: "交易對管理", desc: "配置交易對與參數", icon: "📈" },
    { href: "/positions", title: "持倉監控", desc: "查看即時持倉與風控", icon: "📥" },
    { href: "/history", title: "交易記錄", desc: "檢視歷史訂單與損益", icon: "🗂️" },
    { href: "/strategies", title: "策略配置", desc: "建立與啟用策略", icon: "🧪" },
    { href: "/system", title: "系統監控", desc: "服務狀態與日誌", icon: "🖥️" },
  ]

  const handleClick = (href: string) => {
    window.location.href = href
  }

  return (
    <section className="mt-6">
      <h2 className="text-xl font-semibold mb-2 text-sx-text">工作台</h2>
      <p className="text-sx-sub text-sm mb-4">從這裡快速進入常用功能</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {actions.map(action => (
          <div
            key={action.href}
            onClick={() => handleClick(action.href)}
            className="sx-card p-5 block group cursor-pointer"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-white/5">{action.icon}</div>
              <div>
                <div className="text-base font-medium group-hover:text-gold-400 text-sx-text">
                  {action.title}
                </div>
                <div className="text-sx-sub text-sm mt-0.5">{action.desc}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
