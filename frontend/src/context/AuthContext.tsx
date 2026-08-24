'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { useAuthStore } from '@/store/auth';

interface AuthContextType {
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
  role: 'customer' | 'agent' | 'admin';
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isLoading, setIsLoading] = useState(true);
  const { setAuth, clearAuth, isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    // Check if we have a valid token on mount
    const token = localStorage.getItem('access_token');
    if (token) {
      // Token exists, consider authenticated
      setIsLoading(false);
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    const { access_token, refresh_token } = response.data;
    // Get user info
    const userResponse = await api.get('/auth/me');
    setAuth(userResponse.data, access_token, refresh_token);
    // Also store in localStorage for axios interceptor
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    router.push('/dashboard');
  };

  const register = async (data: RegisterData) => {
    const response = await api.post('/auth/register', data);
    // Auto-login after registration
    const loginResponse = await api.post('/auth/login', { 
      email: data.email, 
      password: data.password 
    });
    const { access_token, refresh_token } = loginResponse.data;
    setAuth(response.data, access_token, refresh_token);
    // Also store in localStorage for axios interceptor
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    router.push('/dashboard');
  };

  const logout = () => {
    clearAuth();
    // Also clear localStorage for axios interceptor
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ login, register, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}