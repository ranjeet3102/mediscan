'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { api, AdminUserSessionRecord } from '@/lib/api';
import { AdminPageShell } from '@/components/admin/AdminPageShell';
import { LogIn, LogOut, RefreshCw, ShieldCheck, Search } from 'lucide-react';

function fmtTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export default function AdminSessionsPage() {
  const { token } = useAuth();
  const [sessions, setSessions] = useState<AdminUserSessionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [eventFilter, setEventFilter] = useState<'ALL' | 'user_login' | 'user_logout'>('ALL');
  const [emailSearch, setEmailSearch] = useState('');

  const fetchSessions = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAdminUserSessions(token, 100);
      setSessions(data);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (e: any) {
      setError(e.message || 'Failed to fetch sessions');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const filteredSessions = sessions.filter((s) => {
    const matchesType = eventFilter === 'ALL' || s.event_type === eventFilter;
    const q = emailSearch.trim().toLowerCase();
    const matchesEmail =
      !q ||
      (s.user_email || '').toLowerCase().includes(q) ||
      (s.user_id_ref || '').toLowerCase().includes(q);
    return matchesType && matchesEmail;
  });

  const loginCount = sessions.filter((s) => s.event_type === 'user_login').length;
  const logoutCount = sessions.filter((s) => s.event_type === 'user_logout').length;

  return (
    <AdminPageShell
      title="User Login & Logout Activity Log"
      breadcrumb="Session Log"
      description="Chronological audit trail of user authentication login and logout events across the platform."
      badgeText="Authentication Audit Trail"
      lastRefreshed={lastRefreshed}
      error={error}
      actions={
        <button
          onClick={fetchSessions}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold flex items-center gap-2 transition disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Log
        </button>
      }
    >
      {/* Summary Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <div className="glass-card p-4 rounded-2xl border border-white/10 space-y-1">
          <p className="text-[11px] text-slate-400">Total Session Events</p>
          <p className="text-2xl font-extrabold text-white">{sessions.length}</p>
        </div>
        <div className="glass-card p-4 rounded-2xl border border-white/10 space-y-1">
          <p className="text-[11px] text-slate-400">Login Events</p>
          <p className="text-2xl font-extrabold text-emerald-400">{loginCount}</p>
        </div>
        <div className="glass-card p-4 rounded-2xl border border-white/10 space-y-1">
          <p className="text-[11px] text-slate-400">Logout Events</p>
          <p className="text-2xl font-extrabold text-blue-400">{logoutCount}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <span className="text-xs text-slate-400">
          Showing {filteredSessions.length} of {sessions.length} recorded authentication events
        </span>
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="h-3.5 w-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={emailSearch}
              onChange={(e) => setEmailSearch(e.target.value)}
              placeholder="Filter by email or ID..."
              className="bg-slate-900 border border-white/10 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-400"
            />
          </div>
          <select
            value={eventFilter}
            onChange={(e) => setEventFilter(e.target.value as 'ALL' | 'user_login' | 'user_logout')}
            className="bg-slate-900 border border-white/10 text-xs text-white rounded-xl px-3 py-1.5 focus:outline-none focus:border-purple-400"
          >
            <option value="ALL">All Events</option>
            <option value="user_login">Logins Only</option>
            <option value="user_logout">Logouts Only</option>
          </select>
        </div>
      </div>

      {/* Sessions Table */}
      <div className="glass-card rounded-2xl border border-white/10 overflow-hidden">
        <div className="overflow-x-auto max-h-[560px] overflow-y-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="sticky top-0 bg-slate-950/95 backdrop-blur-md z-10">
              <tr className="bg-white/5 text-[10px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Event</th>
                <th className="py-3 px-4">User (Email)</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Privacy</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono text-[11px]">
              {loading && sessions.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-10 text-center text-slate-400 text-xs">
                    <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-purple-400" />
                    Loading session log...
                  </td>
                </tr>
              ) : filteredSessions.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-10 text-center text-slate-400 text-xs">
                    No session events recorded yet. Events appear after users log in or out.
                  </td>
                </tr>
              ) : (
                filteredSessions.map((s, idx) => (
                  <tr key={s.id || idx} className="hover:bg-white/[0.02] transition">
                    <td className="py-3 px-4 text-slate-400">{fmtTime(s.created_at)}</td>
                    <td className="py-3 px-4">
                      {s.event_type === 'user_login' ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold">
                          <LogIn className="h-3 w-3" /> LOGIN
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-300 border border-blue-500/20 text-[10px] font-bold">
                          <LogOut className="h-3 w-3" /> LOGOUT
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      {s.user_email
                        ? s.user_email
                        : s.user_id_ref
                        ? `ID: ${s.user_id_ref.slice(0, 8)}…`
                        : '—'}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                          s.status === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                            : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                        }`}
                      >
                        {s.status?.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-purple-400 flex items-center gap-1 text-[10px]">
                        <ShieldCheck className="h-3.5 w-3.5" /> AUDIT LOG
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <p className="text-[11px] text-slate-500 text-center">
        <ShieldCheck className="h-3 w-3 inline mr-1 text-emerald-500" />
        Session log stores authentication timestamps and email only. No medical data, lab values, or clinical notes are stored here.
      </p>
    </AdminPageShell>
  );
}

