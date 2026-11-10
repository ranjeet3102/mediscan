'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { api, TelemetryModuleBreakdownItem } from '@/lib/api';
import { AdminPageShell } from '@/components/admin/AdminPageShell';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { Layers, RefreshCw, Activity, Zap, CheckCircle2 } from 'lucide-react';

export default function AdminWorkloadPage() {
  const { token } = useAuth();
  const [breakdown, setBreakdown] = useState<TelemetryModuleBreakdownItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const fetchBreakdown = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAdminBreakdown(token);
      setBreakdown(data);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err: any) {
      setError(err.message || 'Failed to load workload breakdown');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchBreakdown();
  }, [fetchBreakdown]);

  const totalExecutions = breakdown.reduce((acc, m) => acc + (m.event_count || 0), 0);
  const avgLatency = breakdown.length
    ? Math.round(breakdown.reduce((acc, m) => acc + (m.avg_latency_ms || 0), 0) / breakdown.length)
    : 0;
  const topModule = breakdown.reduce<TelemetryModuleBreakdownItem | null>(
    (best, cur) => (!best || cur.event_count > best.event_count ? cur : best),
    null
  );

  return (
    <AdminPageShell
      title="Workload Breakdown"
      breadcrumb="Workload Breakdown"
      description="Module-level throughput, percentage share, average processing latency, and execution success rates across all platform pipelines."
      badgeText="Subsystem Workload & Latency Distribution"
      lastRefreshed={lastRefreshed}
      error={error}
      actions={
        <button
          onClick={fetchBreakdown}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold flex items-center gap-2 transition disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      }
    >
      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card p-5 rounded-2xl border border-white/10 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Active Platform Pipelines</span>
            <Layers className="h-4 w-4 text-purple-400" />
          </div>
          <p className="text-3xl font-extrabold text-white">{breakdown.length}</p>
          <p className="text-[11px] text-slate-400">Instrumented processing subsystems</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-white/10 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Total Tracked Executions</span>
            <Activity className="h-4 w-4 text-teal-400" />
          </div>
          <p className="text-3xl font-extrabold text-white">{totalExecutions}</p>
          <p className="text-[11px] text-slate-400">
            Top module: {topModule?.module_name || '—'}
          </p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-white/10 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Mean Subsystem Latency</span>
            <Zap className="h-4 w-4 text-cyan-400" />
          </div>
          <p className="text-3xl font-extrabold text-white">
            {avgLatency} <span className="text-sm font-normal text-slate-400">ms</span>
          </p>
          <p className="text-[11px] text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3" /> All pipelines monitored
          </p>
        </div>
      </div>

      {/* BarChart Visualization */}
      <div className="glass-card p-6 sm:p-7 rounded-3xl border border-white/10 space-y-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="h-5 w-5 text-purple-400" />
            <span>Executions vs. Average Latency by Module</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Side-by-side comparison of job counts and response time across OCR, RAG, Prescription, and Chat subsystems.
          </p>
        </div>

        <div className="h-72 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={breakdown} margin={{ top: 10, right: 15, left: -10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
              <XAxis
                dataKey="module_name"
                stroke="#94a3b8"
                tick={{ fontSize: 10 }}
                interval={0}
                angle={-12}
                textAnchor="end"
              />
              <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              <Bar dataKey="event_count" name="Event Count" fill="#a855f7" radius={[6, 6, 0, 0]} />
              <Bar dataKey="avg_latency_ms" name="Avg Latency (ms)" fill="#14b8a6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Table */}
      <div className="glass-card p-6 sm:p-7 rounded-3xl border border-white/10 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="h-5 w-5 text-purple-400" />
            <span>Subsystem Workload & Latency Distribution</span>
          </h3>
          <span className="text-xs text-slate-400 font-mono">
            {breakdown.length} Platform Pipelines
          </span>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-white/10">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-white/5 text-[10px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                <th className="py-3 px-4">Subsystem / Module</th>
                <th className="py-3 px-4">Event Count</th>
                <th className="py-3 px-4">Workload Distribution</th>
                <th className="py-3 px-4">Avg Latency</th>
                <th className="py-3 px-4">Success Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading && breakdown.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-10 text-center text-slate-400 text-xs">
                    <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-purple-400" />
                    Loading workload metrics...
                  </td>
                </tr>
              ) : breakdown.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-10 text-center text-slate-400 text-xs">
                    No workload breakdown data available yet.
                  </td>
                </tr>
              ) : (
                breakdown.map((m, idx) => (
                  <tr key={idx} className="hover:bg-white/[0.02] transition">
                    <td className="py-3 px-4 font-semibold text-white">{m.module_name}</td>
                    <td className="py-3 px-4 font-mono text-purple-300 font-bold">{m.event_count}</td>
                    <td className="py-3 px-4 w-56">
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-purple-500 to-indigo-500 h-full rounded-full"
                            style={{ width: `${Math.max(m.percentage, 5)}%` }}
                          ></div>
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono">{m.percentage}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-cyan-300">{m.avg_latency_ms} ms</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                        {m.success_rate}%
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

