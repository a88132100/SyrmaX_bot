import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, theme } from 'antd';
import zhTW from 'antd/locale/zh_TW';

// 頁面組件
import LoginPage from './pages/LoginPage';
import TestPage from './pages/TestPage';
import DashboardPage from './pages/DashboardPage';
import ApiKeysPage from './pages/ApiKeysPage';

// 創建 React Query 客戶端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5分鐘
      retry: 1,
    },
  },
});

// 檢查是否已登入
const isAuthenticated = () => {
  const token = localStorage.getItem('access_token');
  if (!token) return false;
  
  // 檢查token是否過期（簡單檢查）
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    return payload.exp > currentTime;
  } catch {
    // 如果token格式錯誤，清除它
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    return false;
  }
};

// 受保護的路由組件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return isAuthenticated() ? <>{children}</> : <Navigate to="/login" replace />;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        locale={zhTW}
        theme={{
          algorithm: theme.defaultAlgorithm,
          token: {
            colorPrimary: '#1890ff',
            colorSuccess: '#52c41a',
            colorWarning: '#faad14',
            colorError: '#ff4d4f',
          },
        }}
      >
        <Router>
          <div className="App">
            <Routes>
              {/* 公開路由 */}
              <Route 
                path="/login" 
                element={
                  isAuthenticated() ? <Navigate to="/dashboard" replace /> : <LoginPage />
                } 
              />
              
              {/* 測試路由 */}
              <Route path="/test" element={<TestPage />} />
              
              {/* 受保護的路由 */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/api-keys"
                element={
                  <ProtectedRoute>
                    <ApiKeysPage />
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                }
              />
              
              {/* 404 路由 */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </div>
        </Router>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;