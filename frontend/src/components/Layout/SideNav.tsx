import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { 
  LayoutDashboard, 
  KeyRound, 
  BarChart3, 
  Wallet, 
  History, 
  Settings2, 
  Monitor,
  Menu,
  X
} from 'lucide-react'
import { SxButton } from '@/components/ui/sx-button'
import { cn } from '@/lib/utils'

interface SideNavProps {
  isOpen?: boolean
  onToggle?: () => void
  className?: string
}

const navItems = [
  { id: 'dashboard', label: '儀表板', icon: LayoutDashboard, path: '/dashboard' },
  { id: 'api-keys', label: 'API 金鑰', icon: KeyRound, path: '/api-keys' },
  { id: 'pairs', label: '交易對', icon: BarChart3, path: '/pairs' },
  { id: 'positions', label: '持倉', icon: Wallet, path: '/positions' },
  { id: 'history', label: '記錄', icon: History, path: '/history' },
  { id: 'strategies', label: '策略', icon: Settings2, path: '/strategies' },
  { id: 'system', label: '系統', icon: Monitor, path: '/system' },
]

export function SideNav({ isOpen = false, onToggle, className }: SideNavProps) {
  const location = useLocation()
  const navigate = useNavigate()

  const handleNavClick = (path: string) => {
    navigate(path)
    onToggle?.()
  }

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        "fixed left-0 top-16 z-50 h-[calc(100vh-4rem)] w-64 transform border-r border-border/40 bg-background/95 backdrop-blur transition-transform duration-300 ease-in-out lg:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full",
        className
      )}>
        <div className="flex h-full flex-col">
          {/* Mobile close button */}
          <div className="flex items-center justify-between p-4 lg:hidden">
            <h2 className="text-lg font-semibold">選單</h2>
            <SxButton variant="ghost" size="icon" onClick={onToggle}>
              <X className="h-5 w-5" />
            </SxButton>
          </div>

          {/* Navigation items */}
          <nav className="flex-1 space-y-1 p-4">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path
              const Icon = item.icon

              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.path)}
                  className={cn(
                    "w-full flex items-center space-x-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </button>
              )
            })}
          </nav>

          {/* Footer */}
          <div className="border-t border-border/40 p-4">
            <div className="text-xs text-muted-foreground">
              <p>快捷鍵：</p>
              <p>G + A → API 金鑰</p>
              <p>G + P → 交易對</p>
              <p>G + S → 策略</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
