import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { MainLayout } from '@/components/layout/MainLayout'
import { DashboardPage } from '@/pages/DashboardPage'
import { ApiKeysPage } from '@/pages/ApiKeysPage'
import { PairsPage } from '@/pages/PairsPage'
import { PositionsPage } from '@/pages/PositionsPage'
import { HistoryPage } from '@/pages/HistoryPage'
import { StrategiesPage } from '@/pages/StrategiesPage'
import { SystemPage } from '@/pages/SystemPage'

// 現代化登入頁面
const LoginPage: React.FC = () => {
  const handleLogin = () => {
    // 暫時的登入邏輯 - 直接跳轉到儀表板
    window.location.href = '/dashboard'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4 relative overflow-hidden">
      {/* 背景裝飾 */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%239C92AC%22%20fill-opacity%3D%220.1%22%3E%3Ccircle%20cx%3D%2230%22%20cy%3D%2230%22%20r%3D%222%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] opacity-20"></div>
      
      <div className="relative z-10 bg-white/10 backdrop-blur-xl rounded-3xl shadow-2xl w-full max-w-md p-8 border border-white/20">
        <div className="text-center mb-8">
          <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-blue-500 to-purple-600 rounded-3xl flex items-center justify-center shadow-2xl">
            <span className="text-white font-bold text-3xl">SX</span>
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-3">
            SyrmaX
          </h1>
          <p className="text-white/80 text-lg">
            智能交易平台
          </p>
        </div>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-white/90 mb-3">
              用戶名
            </label>
            <input 
              type="text" 
              placeholder="請輸入用戶名" 
              className="w-full px-4 py-4 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent backdrop-blur-sm transition-all duration-200"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-white/90 mb-3">
              密碼
            </label>
            <input 
              type="password" 
              placeholder="請輸入密碼" 
              className="w-full px-4 py-4 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent backdrop-blur-sm transition-all duration-200"
            />
          </div>
          
          <button 
            onClick={handleLogin}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-4 px-6 rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl hover:shadow-blue-500/25"
          >
            登入系統
          </button>
          
          <div className="text-center p-4 bg-white/5 rounded-xl border border-white/10">
            <p className="text-sm text-white/70">
              💡 登入功能正在開發中，敬請期待！
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background text-foreground">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={
            <MainLayout>
              <DashboardPage />
            </MainLayout>
          } />
          <Route path="/api-keys" element={
            <MainLayout>
              <ApiKeysPage />
            </MainLayout>
          } />
          <Route path="/pairs" element={
            <MainLayout>
              <PairsPage />
            </MainLayout>
          } />
          <Route path="/positions" element={
            <MainLayout>
              <PositionsPage />
            </MainLayout>
          } />
          <Route path="/history" element={
            <MainLayout>
              <HistoryPage />
            </MainLayout>
          } />
          <Route path="/strategies" element={
            <MainLayout>
              <StrategiesPage />
            </MainLayout>
          } />
          <Route path="/system" element={
            <MainLayout>
              <SystemPage />
            </MainLayout>
          } />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App