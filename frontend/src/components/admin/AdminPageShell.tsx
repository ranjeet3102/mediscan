'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import {
  ShieldAlert,
  ChevronRight,
  Lock,
  AlertTriangle,
  Server,
  Layers,
  Clock,
  Users,
  LogIn,
} from 'lucide-react';

interface AdminPageShellProps {
  title: string;
  breadcrumb: string;
  description: string;
  badgeText?: string;
  lastRefreshed?: string;
  error?: string | null;
  actions?: React.ReactNode;
  children: React.ReactNode;
}

const ADMIN_NAV_TABS = [
  { href: '/admin/health', label: 'System Health', icon: Server },
  { href: '/admin/workload', label: 'Workload Breakdown', icon: Layers },
  { href: '/admin/events', label: 'Live Event Logs', icon: Clock },
  { href: '/admin/users', label: 'User Management', icon: Users },
  { href: '/admin/sessions', label: 'Session Log', icon: LogIn },
];

export const AdminPageShell: React.FC<AdminPageShellProps> = ({
  title,
  breadcrumb,
  description,
  badgeText = 'Zero-PHI Infrastructure Control',
  lastRefreshed,
  error,
  actions,
  children,
}) => {
  const pathname = usePathname();
  const { user } = useAuth();

  if (user && user.role !== 'admin') {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-center space-y-4 max-w-lg mx-auto p-6">
        <div className="p-4 rounded-3xl bg-rose-500/10 border border-rose-500/30 text-rose-400">
          <ShieldAlert className="h-10 w-10 mx-auto mb-2 text-rose-400" />
          <h2 className="text-lg font-bold text-white">Administrator Access Restricted</h2>
          <p className="text-xs text-slate-300 max-w-sm mt-1 leading-relaxed">
            The telemetry and infrastructure control room is strictly restricted to administrative personnel. Medical data protection safeguards prevent unauthorized access.
          </p>
          <div className="mt-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs text-white hover:bg-slate-800 transition"
            >
              <span>Return to Patient Dashboard</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Top Breadcrumb & Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <Link href="/admin/health" className="hover:text-purple-400 transition">
            Admin
          </Link>
          <ChevronRight className="h-3 w-3" />
          <span className="text-purple-400 font-medium">{breadcrumb}</span>
        </div>
        <div className="flex items-center space-x-2.5">
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 flex items-center space-x-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Zero-PHI Isolation Active</span>
          </span>
          {lastRefreshed && (
            <span className="text-[11px] text-slate-500 font-mono hidden sm:inline">
              Refreshed: {lastRefreshed}
            </span>
          )}
        </div>
      </div>

      {/* Main Page Header */}
      <div className="glass-card p-6 sm:p-7 rounded-3xl border border-purple-500/30 bg-gradient-to-r from-slate-900/90 via-purple-950/20 to-slate-900/90 flex flex-col md:flex-row md:items-center md:justify-between gap-5">
        <div className="space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-purple-500/20 border border-purple-500/40 text-purple-300 text-xs font-semibold">
            <Lock className="h-3 w-3 text-purple-400" />
            <span>{badgeText}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            {title}
          </h1>
          <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
            {description}
          </p>
        </div>
        {actions && <div className="flex flex-wrap items-center gap-2.5">{actions}</div>}
      </div>

      {/* Section Navigation Strip */}
      <nav className="flex flex-wrap gap-2 border-b border-white/10 pb-3">
        {ADMIN_NAV_TABS.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-xl border transition ${
                isActive
                  ? 'bg-purple-500/20 text-purple-200 border-purple-500/40 shadow-sm shadow-purple-500/10'
                  : 'bg-slate-900/50 text-slate-400 border-white/10 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className={`h-3.5 w-3.5 ${isActive ? 'text-purple-400' : 'text-slate-400'}`} />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Error Banner */}
      {error && (
        <div className="glass-card p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-3">
          <AlertTriangle className="h-5 w-5 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {children}
    </div>
  );
};

