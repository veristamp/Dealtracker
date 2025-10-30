// src/lib/types.ts

export interface Product {
  id: number;
  product_id: number;
  url: string;
  name: string;
  current_price: number | null;
  threshold_price: number;
  timestamp: string;
  active: boolean;
  last_scrape_status: 'success' | 'failed' | 'pending';
  tag: string | null;
}

export interface Alert {
  id: number;
  product_id: number;
  product_name: string;
  scraped_price: number;
  threshold_price: number;
  currency: string;
  timestamp: string;
}

export interface ActivityLog {
  id: number;
  timestamp: string;
  action_type: string;
  details: Record<string, any>;
}

export interface PriceHistory {
  id: number;
  product_id: number;
  timestamp: string;
  price: number;
}

export interface DashboardStats {
  total_products: number;
  active_deals: number;
}

export interface User {
  username: string;
  tier: string;
  is_active: boolean;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
}

export interface SchedulerStatus {
  running: boolean;
}

export interface SchedulerInterval {
  interval: number;
}