'use client';

import React from 'react';
import Link from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { 
  Activity, 
  Shield, 
  User, 
  LogOut, 
  Globe, 
  Sparkles,
  CheckCircle2
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-white/10 bg-[#080c14]/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <a href="/" className="flex items-center space-x-2 group">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-400 p-0.5 shadow-lg shadow-teal-500/20 group-hover:shadow-teal-500/40 transition">
                <div className="h-full w-full bg-[#080c14] rounded-[10px] flex items-center justify-center">
                  <Activity className="h-5 w-5 text-cyan-400 animate-pulse" />
                </div>
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-lg text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-cyan-400">
                  Medical Report Simplifier
                </span>
                <span className="text-[10px] font-semibold tracking-wider text-teal-400 uppercase">
                  Version 2.0 • AI Health Literacy
                </span>
              </div>
            </a>
          </div>

          {/* Right Navigation Elements */}
          <div className="flex items-center space-x-4">
            {/* Language Preference Badge (When logged in) */}
            {user && (
              <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-white/10 text-xs text-slate-300">
                <Globe className="h-3.5 w-3.5 text-cyan-400" />
                <span>Language:</span>
                <span className="font-medium text-white uppercase">{user.preferred_language || 'EN'}</span>
              </div>
            )}

            {/* Portal Navigation Link */}
            {user && (
              <a
                href={user.role === 'admin' ? '/admin' : '/dashboard'}
                className={`px-3 py-1.5 text-xs font-medium rounded-xl border flex items-center space-x-1.5 transition ${
                  user.role === 'admin'
                    ? 'bg-purple-950/40 border-purple-500/30 text-purple-300 hover:border-purple-400'
                    : 'bg-teal-950/40 border-teal-500/30 text-teal-300 hover:border-teal-400'
                }`}
              >
                {user.role === 'admin' ? (
                  <>
                    <Shield className="h-3.5 w-3.5" />
                    <span>Admin Telemetry</span>
                  </>
                ) : (
                  <>
                    <User className="h-3.5 w-3.5" />
                    <span>Patient Portal</span>
                  </>
                )}
              </a>
            )}

            {/* User Profile / Auth State */}
            {user ? (
              <div className="flex items-center space-x-3 pl-2 border-l border-white/10">
                <div className="hidden md:flex flex-col text-right">
                  <span className="text-xs font-semibold text-white truncate max-w-[160px]">
                    {user.full_name || user.email}
                  </span>
                  <span className="text-[10px] text-teal-400 flex items-center justify-end space-x-1">
                    <CheckCircle2 className="h-2.5 w-2.5" />
                    <span>{user.role === 'admin' ? 'Administrator' : 'Patient Session'}</span>
                  </span>
                </div>
                <button
                  onClick={logout}
                  title="Sign Out"
                  className="p-2 rounded-lg bg-slate-900 border border-white/10 text-slate-400 hover:text-rose-400 hover:border-rose-500/30 transition flex items-center space-x-1 text-xs"
                >
                  <LogOut className="h-4 w-4" />
                  <span className="hidden sm:inline">Sign Out</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <a
                  href="/login"
                  className="px-3.5 py-1.5 rounded-xl bg-slate-900 border border-white/10 hover:border-white/20 text-slate-200 font-medium text-xs transition"
                >
                  Sign In
                </a>
                <a
                  href="/register"
                  className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold text-xs shadow-md shadow-cyan-500/20 transition"
                >
                  Create Account
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
