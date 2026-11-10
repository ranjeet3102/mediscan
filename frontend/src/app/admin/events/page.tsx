'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { api, TelemetryEventItem } from '@/lib/api';
import { AdminPageShell } from '@/components/admin/AdminPageShell';
import { Clock, RefreshCw, ShieldCheck, Filter } from 'lucide-react';

export default function AdminEventsPage() {
  const { token } = useAuth();
  const [events, setEvents] = useState<TelemetryEventItem[]>([]);
  const [eventFilter, setEventFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [limit, setLimit] = useState<number>(50);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const fetchEvents = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAdminEvents(token, limit);
      setEvents(data);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err: any) {
      setError(err.message || 'Failed to load live system events');
    } finally {
      setLoading(false);
    }
  }, [token, limit]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const filteredEvents = events.filter((e) => {
    const matchesCategory =
      eventFilter === 'ALL' ||
      (eventFilter === 'OCR' && (e.event_type.includes('ocr') || e.event_type.includes('extraction'))) ||
      (eventFilter === 'AI' && (e.event_type.includes('ai') || e.event_type.includes('doctor'))) ||
      (eventFilter === 'VECTOR' && (e.event_type.includes('vector') || e.event_type.includes('glossary'))) ||
      (eventFilter === 'AUTH' && (e.event_type.includes('user_') || e.event_type.includes('admin_')));

    const matchesStatus = statusFilter === 'ALL' || e.status === statusFilter;
    return matchesCategory && matchesStatus;
  });

  const successCount = filteredEvents.filter((e) => e.status === 'success').length;
  const errorCount = filteredEvents.filter((e) => e.status !== 'success').length;

  return (
    <AdminPageShell
      title="Live Event Logs"
      breadcrumb="Live Event Logs"
      description="Real-time sanitized operational telemetry stream capturing pipeline executions, latency, token usage, and completion status without any PHI."
      badgeText="Zero-PHI Sanitized Event Stream"
      lastRefreshed={lastRefreshed}
      error={error}
      actions={
        <div className="flex items-center gap-2">
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="bg-slate-900 border border-white/10 text-xs text-white rounded-xl px-3 py-2 focus:outline-none focus:border-purple-400"
          >
            <option value={25}>Last 25 events</option>
            <option value={50}>Last 50 events</option>
            <option value={100}>Last 100 events</option>
          </select>
          <button
            onClick={fetchEvents}
            disabled={loading}
            className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold flex items-center gap-2 transition disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Stream</span>
          </button>
        </div>
      }
    >
      {/* Summary Badges */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card p-4 rounded-2xl border border-white/10 space-y-1">
          <p className="text-[11px] text-slate-400">Matching Events</p>
          <p className="text-2xl font-extrabold text-white">{filteredEvents.length}</p>
        </div>
        <div className="glass-card p-4 rounded-2xl border border-white/10 space-y-1">
          <p className="text-[11px] text-slate-400">Success Status</p>
          <p className="text-2xl font-extrabold text-emerald-400">{successCount}</p>
        </div>
        <div className="glass-card p-4 rounded-2xl border border-white/10 space-y-1">
          <p className="text-[11px] text-slate-400">Warnings / Errors</p>
          <p className="text-2xl font-extrabold text-rose-400">{errorCount}</p>
        </div>
      </div>

      {/* Events Table */}
      <div className="glass-card p-6 sm:p-7 rounded-3xl border border-white/10 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Clock className="h-5 w-5 text-purple-400" />
            <span>Real-Time Sanitized System Events Stream</span>
          </h2>
          <div className="flex flex-wrap items-center gap-2">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={eventFilter}
              onChange={(e) => setEventFilter(e.target.value)}
              className="bg-slate-900 border border-white/10 text-xs text-white rounded-xl px-3 py-1.5 focus:outline-none focus:border-purple-400"
            >
              <option value="ALL">All Modules</option>
              <option value="OCR">OCR &amp; Extraction</option>
              <option value="AI">AI &amp; Grounding</option>
              <option value="VECTOR">Vector &amp; Glossary</option>
              <option value="AUTH">Auth &amp; Admin</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-900 border border-white/10 text-xs text-white rounded-xl px-3 py-1.5 focus:outline-none focus:border-purple-400"
            >
              <option value="ALL">All Statuses</option>
              <option value="success">Success Only</option>
              <option value="error">Errors Only</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-white/10 max-h-[560px] overflow-y-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="sticky top-0 bg-slate-950/95 backdrop-blur-md z-10">
              <tr className="bg-white/5 text-[10px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                <th className="py-2.5 px-3.5">Timestamp</th>
                <th className="py-2.5 px-3.5">Event Type</th>
                <th className="py-2.5 px-3.5">Duration</th>
                <th className="py-2.5 px-3.5">Tokens</th>
                <th className="py-2.5 px-3.5">Status</th>
                <th className="py-2.5 px-3.5">Privacy Guard</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono text-[11px]">
              {loading && filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-10 text-center text-slate-400 text-xs">
                    <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-purple-400" />
                    Loading event stream...
                  </td>
                </tr>
              ) : filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-10 text-center text-slate-400 text-xs">
                    No events match the selected filter.
                  </td>
                </tr>
              ) : (
                filteredEvents.map((evt, idx) => (
                  <tr key={evt.id || idx} className="hover:bg-white/[0.02]">
                    <td className="py-2.5 px-3.5 text-slate-400">
                      {evt.created_at
                        ? new Date(evt.created_at).toLocaleString([], {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                          })
                        : 'Recent'}
                    </td>
                    <td className="py-2.5 px-3.5 font-semibold text-white">
                      <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10">
                        {evt.event_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3.5 text-cyan-300">{evt.duration_ms} ms</td>
                    <td className="py-2.5 px-3.5 text-slate-300">{evt.token_count ?? 0}</td>
                    <td className="py-2.5 px-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          evt.status === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30'
                            : 'bg-rose-500/10 text-rose-300 border border-rose-500/30'
                        }`}
                      >
                        {evt.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2.5 px-3.5">
                      <span className="text-emerald-400 flex items-center space-x-1 text-[10px]">
                        <ShieldCheck className="h-3.5 w-3.5" />
                        <span>NO PHI</span>
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </AdminPageShell>
  );
}

