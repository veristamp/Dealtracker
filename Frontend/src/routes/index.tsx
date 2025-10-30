import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { ProtectedRoute } from './ProtectedRoute';
import Login from '@/app/Login';
import Dashboard from '@/app/Dashboard';
import Products from '@/app/Products';
import Analytics from '@/app/Analytics';
import Settings from '@/app/Settings';
import NotFound from '@/app/NotFound';
import Activity from '@/app/Activity';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <Dashboard />,
      },
      {
        path: 'products',
        element: <Products />,
      },
      {
        path: 'analytics',
        element: <Analytics />,
      },
      {
        path: 'activity',
        element: <Activity />,
      },
      {
        path: 'settings',
        element: <Settings />,
      },
    ],
  },
  {
    path: '*',
    element: <NotFound />,
  },
]);