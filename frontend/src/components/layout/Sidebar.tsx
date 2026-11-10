'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import {
  LayoutDashboard,
  UploadCloud,
  FileText,
  MessageSquareQuote,
  TrendingUp,
  Pill,
  Stethoscope,
  Settings,
  Info,
} from 'lucide-react';

const userNavItems = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Upload Report', href: '/dashboard/upload', icon: UploadCloud },
  { name: 'My Reports', href: '/dashboard/reports', icon: FileText },
  { name: 'Ask My Report', href: '/dashboard/chat', icon: MessageSquareQuote, badge: 'AI' },
  { name: 'Trends & Comparison', href: '/dashboard/trends', icon: TrendingUp },
  { name: 'Prescriptions', href: '/dashboard/prescriptions', icon: Pill },
  { name: 'Doctor Summary', href: '/dashboard/doctor-summary', icon: Stethoscope },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  if (isAdmin) {
    return null;
  }

  return (
    <aside className="w-64 flex-shrink-0 border-r border-white/10 bg-[#0a0f1d]/90 flex flex-col justify-between min-h-[calc(100vh-4rem)] p-4">
      <div className="space-y-6">
        {/* User Profile Card */}
        <div className="glass-card p-3 rounded-2xl flex items-center space-x-3 border border-cyan-500/20 bg-cyan-950/20">
          <div className="h-9 w-9 rounded-xl flex items-center justify-center font-bold text-sm bg-gradient-to-tr from-teal-500 to-cyan-400 text-slate-950">
            {user?.email?.charAt(0).toUpperCase() || 'P'}
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-semibold text-white truncate">{user?.email}</p>
            <div className="flex items-center space-x-1.5 mt-0.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">
                Patient Mode
              </span>
            </div>
          </div>
        </div>

        {/* Regular Patient Features */}
        <div className="space-y-1">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-3 mb-2">
            Patient Features
          </p>
          {userNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition ${
                  isActive
                    ? 'bg-gradient-to-r from-teal-500/20 to-cyan-500/10 text-cyan-300 border border-cyan-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-md bg-teal-500/20 text-teal-300 border border-teal-500/30">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </div>

      {/* Footer Info Notice */}
      <div className="glass-card p-3 rounded-2xl bg-amber-500/5 border border-amber-500/20 text-[11px] text-amber-200/90 flex items-start space-x-2">
        <Info className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
        <p className="leading-tight">
          <strong className="text-amber-300 font-semibold">Educational Tool:</strong> Not a substitute for professional clinical medical advice or diagnosis.
        </p>
      </div>
    </aside>
  );
};
