// 交易機器人前端類型定義

// 用戶相關類型
export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

// 交易對類型
export interface TradingPair {
  symbol: string;
  interval: string;
  precision: number;
  average_atr?: number;
  consecutive_stop_loss: number;
  last_trade_time?: string;
}

// 持倉類型
export interface Position {
  trading_pair: string;
  active: boolean;
  side: 'BUY' | 'SELL';
  entry_price: number;
  quantity: number;
  open_time: string;
}

// 交易記錄類型
export interface Trade {
  id: number;
  trading_pair: string;
  trade_time: string;
  side: 'BUY' | 'SELL';
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  reason: string;
}

// 每日統計類型
export interface DailyStats {
  trading_pair: string;
  date: string;
  pnl: number;
  start_balance: number;
  max_daily_loss_pct: number;
}

// 策略組合類型
export interface StrategyCombo {
  id: number;
  name: string;
  description: string;
  combo_mode: 'aggressive' | 'balanced' | 'conservative' | 'auto' | 'custom';
  conditions: any[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// 交易員狀態類型
export interface TraderStatus {
  is_trading_enabled: boolean;
  stop_signal_received: boolean;
  last_daily_reset_date: string;
  hourly_trade_count: number;
  daily_trade_count: number;
  last_hourly_reset: string;
}

// 系統監控類型
export interface SystemHealth {
  status: 'HEALTHY' | 'WARNING' | 'CRITICAL';
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  network_status: 'ONLINE' | 'OFFLINE';
  last_updated: string;
}

// API 響應類型
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

// 分頁類型
export interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

// 分頁響應類型
export interface PaginatedResponse<T> {
  results: T[];
  pagination: Pagination;
}
