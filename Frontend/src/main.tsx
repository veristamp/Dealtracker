// src/main.tsx (updated to disable Strict Mode for stability)

import { createRoot } from 'react-dom/client';
import { Toaster } from 'sonner';
import App from './App.tsx';
import './index.css';
const userTheme = localStorage.getItem('theme');
if (userTheme === 'dark' || (!userTheme && !('theme' in localStorage))) {
  document.documentElement.classList.add('dark');
  localStorage.setItem('theme', 'dark');
} else {
  document.documentElement.classList.remove('dark');
}
// Strict Mode disabled to avoid double renders and SSE bursts
createRoot(document.getElementById('root')!).render(
  <>
    <App />
    <Toaster 
      position="top-right" 
      richColors 
      expand={false}
      duration={4000}
    />
  </>
);
