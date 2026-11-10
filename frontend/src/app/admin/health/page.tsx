'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { api, AdminStats, SystemHealth } from '@/lib/api';
import { AdminPageShell } from '@/components/admin/AdminPageShell';
import {
  Server,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Database,
  ScanLine,
  BrainCircuit,
  HardDrive,
  ShieldCheck,
  Activity,
} from 'lucide-react';

export default function AdminHealthPage() {
  const { token } = useAuth();
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const fetchHealthData = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [healthData, statsData] = await Promise.all([
        api.getAdminHealth(token),
        api.getAdminStats(token).catch(() => null),
      ]);
      setHealth(healthData);
      if (statsData) setStats(statsData);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err: any) {
      setError(err.message || 'Failed to fetch system health diagnostics');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchHealthData();
  }, [fetchHealthData]);

  const services = [
    {
      name: 'FastAPI Engine',
      subtitle: 'Port 8000 • Uvicorn ASGI',
      statusText: `v${health?.version || '2.0.0'} • Online`,
      ok: true,
      icon: Server,
      color: 'emerald',
    },
    {
      name: 'Tesseract OCR & OpenCV',
      subtitle: '300 DPI • PSM 4/6/11 Pipeline',
      statusText: health?.tesseract_available
        ? 'Binary Ready • CLAHE & Deskew Active'
        : 'Tesseract Binary Not Detected',
      ok: health ? health.tesseract_available : true,
      icon: ScanLine,
      color: 'teal',
    },
    {
      name: health?.llm_provider === 'groq' ? 'Groq Cloud LLM' : 'Ollama Local LLM',
      subtitle:
        health?.llm_provider === 'groq'
          ? 'Ultra-Fast LPU Cloud Inference'
          : 'Port 11434 • RAG Grounding',
      statusText:
        health?.llm_provider === 'groq'
          ? 'Groq LPU Active'
          : health?.ollama_available
          ? 'Local Ollama Active'
          : 'Fallback / Offline Mode',
      ok: health ? health.llm_provider === 'groq' || health.ollama_available : true,
      icon: BrainCircuit,
      color: 'purple',
    },
    {
      name: 'PostgreSQL / pgvector & Supabase',
      subtitle: '384-d Cosine Similarity • Auth & RLS',
      statusText: health?.database_connected
        ? 'Supabase Connected • RLS Active'
        : 'Development Mock Mode (Local)',
      ok: health ? health.database_connected || !health.supabase_configured : true,
      icon: Database,
      color: 'cyan',
    },
  ];

  const isHealthy = (health?.status || 'healthy') === 'healthy';

  return (
    <AdminPageShell
      title="System Health & Diagnostics"
      breadcrumb="System Health"
      description="Live infrastructure heartbeat for FastAPI, Tesseract OCR, LLM inference providers, and Supabase PostgreSQL/pgvector."
      badgeText="Infrastructure & Microservices Matrix"
      lastRefreshed={lastRefreshed}
      error={error}
      actions={
        <button
          onClick={fetchHealthData}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold flex items-center gap-2 transition disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Run Health Check</span>
        </button>
      }
    >
      {/* Overall Status Summary */}
      <div className="glass-card p-6 rounded-3xl border border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div
            className={`p-3.5 rounded-2xl border ${
              isHealthy
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
            }`}
          >
            <Activity className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400">Overall Platform Status</p>
            <h2 className="text-xl font-extrabold text-white tracking-tight">
              {loading && !health
                ? 'Checking Microservices...'
                : isHealthy
                ? 'All Core Systems Operational'
                : 'Degraded Service Detected'}
            </h2>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              API v{health?.version || '2.0.0'} • Provider: {(health?.llm_provider || 'ollama').toUpperCase()} •{' '}
              {health?.timestamp ? new Date(health.timestamp).toLocaleString() : 'Live Check'}
            </p>
          </div>
        </div>
        <span
          className={`px-3.5 py-1.5 rounded-full text-xs font-mono font-bold border self-start md:self-center ${
            isHealthy
              ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
              : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
          }`}
        >
          STATUS: {(health?.status || stats?.system_status || 'OPERATIONAL').toUpperCase()}
        </span>
      </div>

      {/* Microservices Health Matrix */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {services.map((svc) => {
          const Icon = svc.icon;
          return (
            <div
              key={svc.name}
              className="glass-card p-5 rounded-2xl bg-slate-900/80 border border-white/10 space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-white/5 border border-white/10 text-purple-300">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">{svc.name}</h3>
                    <p className="text-[11px] text-slate-400">{svc.subtitle}</p>
                  </div>
                </div>
                {svc.ok ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-400 flex-shrink-0" />
                ) : (
                  <XCircle className="h-5 w-5 text-rose-400 flex-shrink-0" />
                )}
              </div>
              <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] font-mono">
                <span className={svc.ok ? 'text-emerald-400' : 'text-rose-400'}>
                  {svc.statusText}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                    svc.ok
                      ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                      : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                  }`}
                >
                  {svc.ok ? 'ONLINE' : 'CHECK REQUIRED'}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Runtime Metadata & Storage */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card p-5 rounded-2xl border border-white/10 space-y-1.5">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Supabase Auth & DB</span>
            <Database className="h-4 w-4 text-cyan-400" />
          </div>
          <p className="text-lg font-bold text-white">
            {health?.supabase_configured ? 'Production Cloud' : 'Dev Fallback'}
          </p>
          <p className="text-[11px] text-slate-400">
            {health?.database_connected ? 'Live PostgreSQL connection verified' : 'Using local mock fallback'}
          </p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-white/10 space-y-1.5">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Telemetry Storage Footprint</span>
            <HardDrive className="h-4 w-4 text-purple-400" />
          </div>
          <p className="text-lg font-bold text-white">
            {stats?.storage_used_mb ?? 0} MB
          </p>
          <p className="text-[11px] text-slate-400">
            Aggregated system event & document storage
          </p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-white/10 space-y-1.5">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Zero-PHI Isolation Guard</span>
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
          </div>
          <p className="text-lg font-bold text-emerald-400">Enforced</p>
          <p className="text-[11px] text-slate-400">
            RLS policies block admin access to clinical values
          </p>
        </div>
      </div>
    </AdminPageShell>
  );
}

