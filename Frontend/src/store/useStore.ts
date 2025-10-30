import { create } from 'zustand';
import { Product, Alert, ActivityLog, User, DashboardStats } from '@/lib/types';

interface AppState {
  // Auth
  user: User | null;
  isAuthenticated: boolean;
  
  // Data
  products: Product[];
  alerts: Alert[];
  activity: ActivityLog[];
  dashboardStats: DashboardStats | null;
  
  // UI State
  isLoading: boolean;
  isSoundEnabled: boolean; // Add sound setting state

  // Actions
  setUser: (user: User | null) => void;
  setProducts: (products: Product[]) => void;
  setAlerts: (alerts: Alert[]) => void;
  setActivity: (activity: ActivityLog[]) => void;
  setDashboardStats: (stats: DashboardStats) => void;
  setLoading: (loading: boolean) => void;
  setIsSoundEnabled: (enabled: boolean) => void; // Add action for sound
  logout: () => void;
  login: () => void;
}

export const useStore = create<AppState>((set) => ({
  // Initial state
  user: null,
  isAuthenticated: false,
  products: [],
  alerts: [],
  activity: [],
  dashboardStats: null,
  isLoading: false,
  // Initialize sound setting from localStorage, default to true
  isSoundEnabled: JSON.parse(localStorage.getItem('soundEnabled') || 'true'),

  // Actions
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  login: () => set({ isAuthenticated: true }),
  setProducts: (products) => set({ products }),
  setAlerts: (alerts) => set({ alerts }),
  setActivity: (activity) => set({ activity }),
  setDashboardStats: (dashboardStats) => set({ dashboardStats }),
  setLoading: (isLoading) => set({ isLoading }),
  
  // Update sound setting and persist to localStorage
  setIsSoundEnabled: (enabled) => {
    set({ isSoundEnabled: enabled });
    localStorage.setItem('soundEnabled', JSON.stringify(enabled));
  },

  logout: () => {
    // Clear all state on logout
    set({
      user: null,
      isAuthenticated: false,
      products: [],
      alerts: [],
      activity: [],
      dashboardStats: null,
    });
  },
}));