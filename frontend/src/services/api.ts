// API 服務配置
import axios from 'axios';
import type { 
  TradingPair, 
  Position, 
  Trade, 
  DailyStats, 
  StrategyCombo, 
  TraderStatus,
  SystemHealth,
  ApiResponse,
  PaginatedResponse
} from '../types';

// 創建 axios 實例
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 請求攔截器 - 添加認證 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 響應攔截器 - 處理錯誤
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token 過期，清除本地存儲並跳轉到登入頁
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 交易對相關 API
export const tradingPairApi = {
  // 獲取所有交易對
  getAll: (): Promise<ApiResponse<TradingPair[]>> =>
    api.get('/trading-pairs/').then(res => res.data),
  
  // 創建交易對
  create: (data: Partial<TradingPair>): Promise<ApiResponse<TradingPair>> =>
    api.post('/trading-pairs/', data).then(res => res.data),
  
  // 更新交易對
  update: (symbol: string, data: Partial<TradingPair>): Promise<ApiResponse<TradingPair>> =>
    api.put(`/trading-pairs/${symbol}/`, data).then(res => res.data),
  
  // 刪除交易對
  delete: (symbol: string): Promise<ApiResponse<void>> =>
    api.delete(`/trading-pairs/${symbol}/`).then(res => res.data),
};

// 持倉相關 API
export const positionApi = {
  // 獲取所有持倉
  getAll: (): Promise<ApiResponse<Position[]>> =>
    api.get('/positions/').then(res => res.data),
  
  // 獲取特定持倉
  getBySymbol: (symbol: string): Promise<ApiResponse<Position>> =>
    api.get(`/positions/${symbol}/`).then(res => res.data),
};

// 交易記錄相關 API
export const tradeApi = {
  // 獲取交易記錄（分頁）
  getTrades: (params?: {
    page?: number;
    page_size?: number;
    symbol?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<PaginatedResponse<Trade>> =>
    api.get('/trades/', { params }).then(res => res.data),
  
  // 獲取交易統計
  getStats: (): Promise<ApiResponse<any>> =>
    api.get('/trades/stats/').then(res => res.data),
};

// 每日統計相關 API
export const dailyStatsApi = {
  // 獲取每日統計
  getDailyStats: (date?: string): Promise<ApiResponse<DailyStats[]>> =>
    api.get('/daily-stats/', { params: { date } }).then(res => res.data),
  
  // 獲取特定交易對的每日統計
  getBySymbol: (symbol: string, date?: string): Promise<ApiResponse<DailyStats>> =>
    api.get(`/daily-stats/${symbol}/`, { params: { date } }).then(res => res.data),
};

// 策略組合相關 API
export const strategyComboApi = {
  // 獲取所有策略組合
  getAll: (): Promise<ApiResponse<StrategyCombo[]>> =>
    api.get('/strategy-combos/').then(res => res.data),
  
  // 創建策略組合
  create: (data: Partial<StrategyCombo>): Promise<ApiResponse<StrategyCombo>> =>
    api.post('/strategy-combos/', data).then(res => res.data),
  
  // 更新策略組合
  update: (id: number, data: Partial<StrategyCombo>): Promise<ApiResponse<StrategyCombo>> =>
    api.put(`/strategy-combos/${id}/`, data).then(res => res.data),
  
  // 刪除策略組合
  delete: (id: number): Promise<ApiResponse<void>> =>
    api.delete(`/strategy-combos/${id}/`).then(res => res.data),
  
  // 啟用策略組合
  activate: (id: number): Promise<ApiResponse<StrategyCombo>> =>
    api.post(`/strategy-combos/${id}/activate/`).then(res => res.data),
};

// 交易員狀態相關 API
export const traderStatusApi = {
  // 獲取交易員狀態
  getStatus: (): Promise<ApiResponse<TraderStatus>> =>
    api.get('/trader-status/').then(res => res.data),
  
  // 更新交易員狀態
  updateStatus: (data: Partial<TraderStatus>): Promise<ApiResponse<TraderStatus>> =>
    api.put('/trader-status/', data).then(res => res.data),
  
  // 啟用/禁用交易
  toggleTrading: (enabled: boolean): Promise<ApiResponse<TraderStatus>> =>
    api.post('/trader-status/toggle/', { is_trading_enabled: enabled }).then(res => res.data),
};

// 系統監控相關 API
export const systemApi = {
  // 獲取系統健康狀態
  getHealth: (): Promise<ApiResponse<SystemHealth>> =>
    api.get('/monitoring/system-health/').then(res => res.data),
  
  // 獲取監控儀表板數據
  getDashboard: (): Promise<ApiResponse<any>> =>
    api.get('/monitoring/dashboard/').then(res => res.data),
  
  // 獲取告警列表
  getAlerts: (): Promise<ApiResponse<any[]>> =>
    api.get('/monitoring/alerts/').then(res => res.data),
};

// 認證相關 API
export const authApi = {
  // 登入
  login: (username: string, password: string): Promise<{ access: string; refresh: string }> =>
    api.post('/accounts/token/', { username, password }).then(res => res.data),
  
  // 註冊
  register: (data: { username: string; email: string; password: string }): Promise<ApiResponse<any>> =>
    api.post('/accounts/auth/users/', data).then(res => res.data),
  
  // 刷新 token
  refreshToken: (refresh: string): Promise<ApiResponse<{ access: string }>> =>
    api.post('/accounts/token/refresh/', { refresh }).then(res => res.data),
  
  // 登出
  logout: (): Promise<ApiResponse<void>> =>
    api.post('/accounts/logout/').then(res => res.data),
};

// API金鑰管理相關 API
export const apiKeyApi = {
  // 獲取API金鑰列表
  getApiKeys: (): Promise<ApiResponse<any[]>> =>
    api.get('/api-keys/').then(res => res.data),
  
  // 創建API金鑰
  createApiKey: (data: any): Promise<ApiResponse<any>> =>
    api.post('/api-keys/', data).then(res => res.data),
  
  // 更新API金鑰
  updateApiKey: (id: string, data: any): Promise<ApiResponse<any>> =>
    api.put(`/api-keys/${id}/`, data).then(res => res.data),
  
  // 刪除API金鑰
  deleteApiKey: (id: string): Promise<ApiResponse<void>> =>
    api.delete(`/api-keys/${id}/`).then(res => res.data),
  
  // 驗證API金鑰
  verifyApiKey: (id: string): Promise<ApiResponse<any>> =>
    api.post(`/api-keys/${id}/verify/`).then(res => res.data),
  
  // 測試API連接
  testApiConnection: (id: string): Promise<ApiResponse<any>> =>
    api.post(`/api-keys/${id}/test/`).then(res => res.data),
  
  // 獲取API金鑰摘要
  getApiKeySummary: (): Promise<ApiResponse<any>> =>
    api.get('/api-key-summary/').then(res => res.data),
};

// 交易配置相關 API
export const tradingConfigApi = {
  // 獲取交易配置
  getTradingConfig: (): Promise<ApiResponse<any>> =>
    api.get('/trading-config/').then(res => res.data),
  
  // 更新交易配置
  updateTradingConfig: (data: any): Promise<ApiResponse<any>> =>
    api.put('/trading-config/', data).then(res => res.data),
};

export default api;
