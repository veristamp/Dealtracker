// src/routes/ProtectedRoute.tsx

import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useStore } from '@/store/useStore';
import { api } from '@/api';
import { toast } from 'sonner';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { setUser, setLoading } = useStore();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      setIsChecking(true);
      setLoading(true);

      try {
        const response = await api.getUserInfo();
        if (response.success && response.username) {
          setUser({
            username: response.username,
            tier: response.tier || 'bronze',
            is_active: true,
          });
        } else {
          setUser(null);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        setUser(null);
        toast.error('Session expired. Please log in again.');
      } finally {
        setIsChecking(false);
        setLoading(false);
      }
    };

    checkAuth();
  }, [setUser, setLoading]);

  const isAuthenticated = useStore(state => state.isAuthenticated);

  if (isChecking) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}