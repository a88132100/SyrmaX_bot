import { useLocation, useNavigate } from 'react-router-dom'
import { SxButton } from '@/components/ui/sx-button'
import { Menu, X } from 'lucide-react'
import { useState } from 'react'

const items = [
  { href: "/dashboard", label: "儀表板", icon: "📊" },
  { href: "/api-keys", label: "API 金鑰", icon: "🔑" },
  { href: "/pairs", label: "交易對", icon: "📈" },
  { href: "/positions", label: "持倉", icon: "📥" },
  { href: "/history", label: "記錄", icon: "🗂️" },
  { href: "/strategies", label: "策略", icon: "🧪" },
  { href: "/system", label: "系統", icon: "🖥️" },
]

export function SideNav() {
  const location = useLocation()
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)

  const handleNavClick = (href: string) => {
    navigate(href)
    setIsOpen(false)
  }

  return (
    <>
      {/* 桌機固定側欄 */}
      <aside className="hidden lg:flex w-72 shrink-0 sticky top-0 h-screen flex-col bg-sx-surface/80 backdrop-blur-md border-r border-sx-border z-30">
        <div className="p-4 text-sm text-sx-sub">選單</div>
        <nav className="px-3 space-y-1">
          {items.map(item => (
            <button
              key={item.href}
              onClick={() => handleNavClick(item.href)}
              className={`flex items-center gap-3 px-3 h-10 rounded-lg border w-full text-left ${
                location.pathname === item.href
                  ? 'border-gold-600/40 bg-gold-600/10 text-gold-400'
                  : 'border-transparent hover:bg-white/5 text-sx-text'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      {/* 手機 Drawer：按鈕放在 TopNav */}
      <div className="lg:hidden">
        <SxButton 
          variant="outline" 
          size="sm" 
          aria-label="開啟選單" 
          className="mx-2 mt-2"
          leftIcon={<Menu size={16} />}
          onClick={() => setIsOpen(true)}
        >
          選單
        </SxButton>

        {/* 手機版側欄 Drawer */}
        {isOpen && (
          <>
            <div 
              className="fixed inset-0 z-50 bg-black/50 lg:hidden"
              onClick={() => setIsOpen(false)}
            />
            <aside className="fixed left-0 top-0 z-50 h-screen w-72 bg-sx-surface text-sx-text lg:hidden">
              <div className="flex items-center justify-between p-4">
                <div className="text-sm text-sx-sub">選單</div>
                <SxButton 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setIsOpen(false)}
                  leftIcon={<X size={16} />}
                >
                  關閉
                </SxButton>
              </div>
              <nav className="px-3 space-y-1">
                {items.map(item => (
                  <button
                    key={item.href}
                    onClick={() => handleNavClick(item.href)}
                    className="flex items-center gap-3 px-3 h-10 rounded-lg hover:bg-white/5 w-full text-left text-sx-text"
                  >
                    <span>{item.icon}</span>
                    <span>{item.label}</span>
                  </button>
                ))}
              </nav>
            </aside>
          </>
        )}
      </div>
    </>
  )
}