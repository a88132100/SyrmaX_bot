import React from 'react'
import { Bell, User, Settings, LogOut } from 'lucide-react'
import { SxButton } from '@/components/ui/sx-button'

interface TopNavProps {
  onApiKeysClick?: () => void
  onLogout?: () => void
}

export function TopNav({ onApiKeysClick, onLogout }: TopNavProps) {
  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="max-w-[1280px] mx-auto px-6 md:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="h-8 w-8 rounded-lg sx-gradient-primary flex items-center justify-center">
              <span className="text-white font-bold text-sm">SX</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">SyrmaX</h1>
              <p className="text-xs text-muted-foreground">智能交易平台</p>
            </div>
          </div>

          {/* Right side actions */}
          <div className="flex items-center space-x-3">
            {/* Notifications */}
            <SxButton variant="ghost" size="icon">
              <Bell className="h-5 w-5" />
            </SxButton>

            {/* API Keys CTA */}
            <SxButton 
              variant="primary" 
              size="md"
              leftIcon={<Settings className="h-4 w-4" />}
              onClick={onApiKeysClick}
            >
              API 金鑰管理
            </SxButton>

            {/* User menu */}
            <div className="flex items-center space-x-2">
              <SxButton variant="ghost" size="icon">
                <User className="h-5 w-5" />
              </SxButton>
              <SxButton 
                variant="ghost" 
                size="sm"
                leftIcon={<LogOut className="h-4 w-4" />}
                onClick={onLogout}
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
