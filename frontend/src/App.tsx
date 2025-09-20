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

// 簡單的登入頁面
const LoginPage: React.FC = () => {
  const handleLogin = () => {
    // 暫時的登入邏輯 - 直接跳轉到儀表板
    window.location.href = '/dashboard'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-purple-800 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-cyan-400 to-purple-500 rounded-2xl flex items-center justify-center">
            <span className="text-white font-bold text-2xl">SX</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            SyrmaX
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            智能交易機器人平台
          </p>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              用戶名
            </label>
            <input 
              type="text" 
              placeholder="請輸入用戶名" 
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              密碼
            </label>
            <input 
              type="password" 
              placeholder="請輸入密碼" 
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <button 
            onClick={handleLogin}
            className="w-full bg-gradient-to-r from-cyan-400 to-purple-500 text-white font-semibold py-3 px-4 rounded-lg hover:from-cyan-500 hover:to-purple-600 transition-all duration-200 transform hover:scale-105 active:scale-95"
          >
            登入系統
          </button>
          
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">
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