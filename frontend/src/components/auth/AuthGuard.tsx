'use client';

import React, { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Activity } from 'lucide-react';

const PUBLIC_PATHS = ['/', '/login', '/register'];

export const AuthGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    const isPublic = PUBLIC_PATHS.includes(pathname);

    // If unauthenticated and attempting to visit a protected route
    if (!user && !isPublic) {
      router.replace('/login');
      return;
    }

    // If authenticated and visiting login or register
    if (user && (pathname === '/login' || pathname === '/register')) {
      if (user.role === 'admin') {
        router.replace('/admin');
      } else {
        router.replace('/dashboard');
      }
      return;
    }

    // If regular user attempts to visit admin route
    if (user && user.role !== 'admin' && pathname.startsWith('/admin')) {
      router.replace('/dashboard');
      return;
    }

    // If admin attempts to visit patient dashboard routes
    if (user && user.role === 'admin' && pathname.startsWith('/dashboard')) {
      router.replace('/admin');
      return;
    }
  }, [user, isLoading, pathname, router]);

  // If loading session state, show a clean loading spinner for protected routes
  const isPublic = PUBLIC_PATHS.includes(pathname);
  if (isLoading && !isPublic) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center space-y-4">
        <div className="h-12 w-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center animate-pulse">
          <Activity className="h-6 w-6 text-cyan-400 animate-spin" />
        </div>
        <p className="text-xs text-slate-400 font-medium">Verifying secure session...</p>
      </div>
    );
  }

  // Block rendering protected pages if unauthenticated
  if (!user && !isPublic) {
    return null;
  }

  return <>{children}</>;
};
