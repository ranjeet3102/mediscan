'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api, UserProfile } from '@/lib/api';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName?: string, preferred_language?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();

  useEffect(() => {
    // Load session from localStorage on initial render
    const storedToken = localStorage.getItem('med_ocr_token');
    const storedUser = localStorage.getItem('med_ocr_user');

    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error('Failed to parse cached user session:', e);
        localStorage.removeItem('med_ocr_token');
        localStorage.removeItem('med_ocr_user');
        setToken(null);
        setUser(null);
      }
    } else {
      // Unauthenticated state
      setToken(null);
      setUser(null);
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const resp = await api.login(email, password);
      setToken(resp.access_token);
      setUser(resp.user);
      localStorage.setItem('med_ocr_token', resp.access_token);
      localStorage.setItem('med_ocr_user', JSON.stringify(resp.user));

      if (resp.user.role === 'admin') {
        router.push('/admin');
      } else {
        router.push('/dashboard');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (email: string, password: string, fullName = '', preferred_language = 'en') => {
    setIsLoading(true);
    try {
      await api.signup({ email, password, full_name: fullName, preferred_language });
      // Automatically log in after registration
      await login(email, password);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('med_ocr_token');
    localStorage.removeItem('med_ocr_user');
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
