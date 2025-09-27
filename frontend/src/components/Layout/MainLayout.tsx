import React, { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { TopNav } from '../layout/TopNav'
import { SideNav } from '../layout/SideNav'
import { Menu } from 'lucide-react'
import { SxButton } from '@/components/ui/sx-button'

interface MainLayoutProps {
  children?: React.ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleApiKeysClick = () => {
    window.location.href = '/api-keys'
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    window.location.href = '/login'
  }

  return (
    <div className="min-h-screen bg-background">
      <TopNav 
        onApiKeysClick={handleApiKeysClick}
        onLogout={handleLogout}
      />
      
      <div className="flex">
        <div className="hidden lg:block">
          <SideNav />
        </div>

        <SideNav 
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
        />

        <main className="flex-1 lg:ml-64">
          <div className="lg:hidden p-4">
            <SxButton 
              variant="ghost" 
              size="sm"
              leftIcon={<Menu className="h-4 w-4" />}
              onClick={() => setSidebarOpen(true)}
            >
              選單
            </SxButton>
          </div>

          <div className="max-w-[1280px] mx-auto px-6 md:px-8 py-8">
            {children || <Outlet />}
          </div>
        </main>
      </div>
    </div>
  )
}