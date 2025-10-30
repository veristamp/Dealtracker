// src/api/index.ts

import { Product } from "@/lib/types";

const API_BASE = '';

let authToken: string | null = null;
export function setAuthToken(token: string | null) {
  authToken = token;
}

export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchAPI<T>(url: string, options: RequestInit = {}): Promise<T> {
  if (!options.method || options.method.toUpperCase() === 'GET') {
    const separator = url.includes('?') ? '&' : '?';
    url += `${separator}_=${new Date().getTime()}`;
  }

  const headers = new Headers(options.headers || {});
  if (authToken) {
    headers.set('Authorization', `Bearer ${authToken}`);
  }

  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  try {
    const response = await fetch(`${API_BASE}${url}`, {
      credentials: 'include',
      ...options,
      headers,
    });
    if (!response.ok) {
      let errorMessage = `Server error: ${response.status}`;
      let status = response.status;
      if (status === 401) {
        errorMessage = 'Not authenticated. Please log in again.';
      } else if (status === 403) {
        errorMessage = 'Access forbidden. Insufficient permissions.';
      }
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch (parseError) {
        try {
          const errorText = await response.text();
          errorMessage = errorText || errorMessage;
        } catch {}
        console.error('Error parsing response:', parseError);
      }
      throw new ApiError(errorMessage, status);
    }
    
    if (response.status === 204) {
      return { success: true } as T;
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Network error occurred');
  }
}

export const api = {
  setAuthToken,

  // Authentication
  login: async (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    return fetchAPI<{ success: boolean; message?: string }>('/api/auth/login', {
      method: 'POST',
      body: formData,
    });
  },
  register: async (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    return fetchAPI<{ success: boolean; message?: string }>('/api/auth/register', {
      method: 'POST',
      body: formData,
    });
  },
  logout: async () => {
    return fetchAPI<{ success: boolean }>('/api/auth/logout', { method: 'POST' });
  },

  // User info
  getUserInfo: async () => {
    return fetchAPI<{ success: boolean; username?: string; tier?: string }>('/api/userinfo');
  },
  
  // Dashboard & Settings
  getDashboardStats: async () => {
    return fetchAPI<{ success: boolean; data: any }>('/api/dashboard-stats');
  },
  getSchedulerStatus: async () => {
    return fetchAPI<{ success: boolean; data: { running: boolean } }>('/api/scheduler/status');
  },
  getSchedulerInterval: async () => {
    return fetchAPI<{ success: boolean; data: { interval: number } }>('/api/scheduler/interval');
  },
  startScheduler: async () => {
    return fetchAPI<{ success: boolean; message: string }>('/api/scheduler/start', { method: 'POST' });
  },
  stopScheduler: async () => {
    return fetchAPI<{ success: boolean; message: string }>('/api/scheduler/stop', { method: 'POST' });
  },
  rescheduleScheduler: async (interval: number) => {
    return fetchAPI<{ success: boolean; message: string }>('/api/scheduler/reschedule', {
      method: 'POST',
      body: JSON.stringify({ interval }),
    });
  },

  // Products
  getProducts: async () => {
    return fetchAPI<Product[]>('/api/products/'); // Use the corrected Product type
  },
  addProduct: async (url: string, priceThreshold: number) => {
    return fetchAPI<{ success: boolean; message?: string }>('/api/products/', {
      method: 'POST',
      body: JSON.stringify({ url, price_threshold: priceThreshold }),
    });
  },
  deleteProduct: async (id: number) => {
    return fetchAPI<{ success: boolean; message?: string }>(`/api/products/${id}`, { method: 'DELETE' });
  },
  bulkDeleteProducts: async (productIds: number[]) => {
    return fetchAPI<{ success: boolean; message?: string }>('/api/products/bulk-delete', {
      method: 'POST',
      body: JSON.stringify({ product_ids: productIds }),
    });
  },
  syncProducts: async () => {
    return fetchAPI<{ success: boolean; message?: string }>('/api/products/sync', { method: 'POST' });
  },
  getProductHistory: async (id: number) => {
    return fetchAPI<{ success: boolean; data: any[] }>(`/api/products/${id}/history`);
  },
  
  // **CORRECTED**: Moved updateProductStatus inside the exported 'api' object
  updateProductStatus: async (productId: number, active: boolean): Promise<{ success: boolean; message: string }> => {
    return fetchAPI(`/api/products/${productId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active }),
    });
  },

  // Alerts & Activity
  getAlerts: async () => {
    return fetchAPI<{ success: boolean; data: any[] }>('/api/alerts/');
  },
  getActivity: async () => {
    return fetchAPI<{ success: boolean; data: any[] }>('/api/activity/');
  },
};