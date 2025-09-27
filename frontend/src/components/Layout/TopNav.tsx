import { Bell, User, Settings, LogOut, ChevronDown } from 'lucide-react'
import { SxButton } from '@/components/ui/sx-button'

interface TopNavProps {
  onApiKeysClick?: () => void
  onLogout?: () => void
}

export function TopNav({ onApiKeysClick, onLogout }: TopNavProps) {
  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border bg-card/60 backdrop-blur-md">
      <div className="max-w-[1280px] mx-auto px-6 md:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="h-10 w-10 bg-gradient-to-br from-primary to-secondary rounded-xl flex items-center justify-center shadow-lg">
              <span className="text-white font-bold text-lg">SX</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                SyrmaX
              </h1>
              <p className="text-sm text-gray-400">智能交易平台</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <SxButton 
              variant="ghost" 
              size="sm"
              leftIcon={<Bell className="h-4 w-4" />}
              className="text-gray-300 hover:text-white hover:bg-white/10"
            >
              通知
            </SxButton>

            <SxButton 
              variant="gold" 
              size="md"
              leftIcon={<Settings className="h-4 w-4" />}
              onClick={onApiKeysClick}
            >
              API 金鑰管理
            </SxButton>

            <div className="flex items-center space-x-2">
              <SxButton 
                variant="ghost" 
                size="sm"
                leftIcon={<User className="h-4 w-4" />}
                rightIcon={<ChevronDown className="h-3 w-3" />}
                className="text-gray-300 hover:text-white hover:bg-white/10"
              >
                用戶
              </SxButton>
              <SxButton 
                variant="ghost" 
                size="sm"
                leftIcon={<LogOut className="h-4 w-4" />}
                onClick={onLogout}
                className="text-gray-300 hover:text-danger hover:bg-danger/10"
              >
                登出
              </SxButton>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}