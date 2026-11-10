'use client';

import React, { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import {
  api,
  ReportItem,
  BiomarkerTrendSeries,
  ReportComparisonResponse,
  BiomarkerComparisonItem,
} from '@/lib/api';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import {
  TrendingUp,
  GitCompare,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Sparkles,
  Calendar,
  Layers,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Search,
  SlidersHorizontal,
  Bot,
  Globe,
  FileText,
  ShieldAlert,
  UploadCloud,
  BarChart2,
} from 'lucide-react';

function TrendsAndCompareContent() {
  const { token } = useAuth();
  const searchParams = useSearchParams();
  const initialMode = searchParams.get('mode') === 'compare' ? 'compare' : 'trends';
  const [activeMode, setActiveMode] = useState<'trends' | 'compare'>(initialMode);

  // Trends state
  const [allTrends, setAllTrends] = useState<BiomarkerTrendSeries[]>([]);
  const [availableNames, setAvailableNames] = useState<string[]>([]);
  const [selectedBiomarker, setSelectedBiomarker] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loadingTrends, setLoadingTrends] = useState<boolean>(true);

  // Compare state
  const [reportsList, setReportsList] = useState<ReportItem[]>([]);
  const [reportAId, setReportAId] = useState<string>('');
  const [reportBId, setReportBId] = useState<string>('');
  const [comparisonResult, setComparisonResult] = useState<ReportComparisonResponse | null>(null);
  const [comparing, setComparing] = useState<boolean>(false);
  const [compareLanguage, setCompareLanguage] = useState<'en' | 'ta' | 'hi'>('en');
  const [filterShift, setFilterShift] = useState<'ALL' | 'IMPROVED' | 'DETERIORATED' | 'STABLE'>('ALL');

  const [error, setError] = useState<string | null>(null);

  // Load initial data
  useEffect(() => {
    fetchInitialData();
  }, [token]);

  const fetchInitialData = async () => {
    setLoadingTrends(true);
    setError(null);
    try {
      const activeToken = token || 'dev-user-token';

      // 1. Fetch available biomarker names and all trends
      const [names, trends, reports] = await Promise.all([
        api.getAvailableBiomarkerNames(activeToken).catch(() => []),
        api.getBiomarkerTrends(activeToken).catch(() => []),
        api.getReports(activeToken).catch(() => []),
      ]);

      const labReports = (reports || []).filter((r: ReportItem) => r.report_type !== 'prescription');
      setAvailableNames(names);
      setAllTrends(trends);
      setReportsList(labReports);

      if (names.length > 0) {
        setSelectedBiomarker(names[0]);
      } else if (trends.length > 0) {
        setSelectedBiomarker(trends[0].normalized_name);
      }

      // Default compare selection if >= 2 diagnostic reports exist
      if (labReports.length >= 2) {
        setReportAId(labReports[labReports.length - 1].id); // Older report (Baseline)
        setReportBId(labReports[0].id); // Newer report (Follow-up)
      } else {
        setReportAId('');
        setReportBId('');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load longitudinal data.');
    } finally {
      setLoadingTrends(false);
    }
  };

  const handleRunComparison = async () => {
    if (reportsList.length < 2) {
      alert('You must have at least 2 uploaded reports to perform a comparison.');
      return;
    }
    if (!reportAId || !reportBId) {
      alert('Please select both Baseline Report (A) and Follow-up Report (B).');
      return;
    }
    if (reportAId === reportBId) {
      alert('Please select two distinct reports (e.g. baseline vs follow-up) to compute shifts.');
      return;
    }
    setComparing(true);
    setError(null);
    try {
      const activeToken = token || 'dev-user-token';
      const result = await api.compareReports(activeToken, {
        report_a_id: reportAId,
        report_b_id: reportBId,
        language: compareLanguage,
      });
      setComparisonResult(result);
    } catch (err: any) {
      alert(err.message || 'Failed to generate report comparison.');
    } finally {
      setComparing(false);
    }
  };

  // Active trend series for visualizer
  const activeSeries = allTrends.find(
    (t) => t.normalized_name.toLowerCase() === selectedBiomarker.toLowerCase()
  ) || (allTrends.length > 0 ? allTrends[0] : null);

  // Filtered biomarker list
  const filteredNames = availableNames.filter((n) =>
    n.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Filtered comparison items
  const filteredComparisonItems = (comparisonResult?.items || []).filter((it) => {
    if (filterShift === 'IMPROVED') return it.status_shift === 'IMPROVED_TO_NORMAL';
    if (filterShift === 'DETERIORATED') return it.status_shift.includes('DETERIORATED') || it.status_shift === 'INVERTED_ABNORMAL';
    if (filterShift === 'STABLE') return it.status_shift.includes('STABLE');
    return true;
  });

  // Helper formatting for chart data
  const chartData = (activeSeries?.data_points || []).map((pt, idx) => ({
    name: pt.report_date || `Report ${idx + 1}`,
    value: pt.value_numeric,
    unit: pt.unit || activeSeries?.unit || '',
    flag: pt.flag,
    title: pt.report_title,
    ref_min: activeSeries?.ref_min ?? pt.ref_min,
    ref_max: activeSeries?.ref_max ?? pt.ref_max,
  }));

  const getShiftBadge = (shift: string) => {
    switch (shift) {
      case 'IMPROVED_TO_NORMAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            <ArrowDownRight className="w-3 h-3" /> Improved to Normal
          </span>
        );
      case 'DETERIORATED_TO_ABNORMAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
            <ArrowUpRight className="w-3 h-3" /> Shifted to Out-of-Range
          </span>
        );
      case 'INVERTED_ABNORMAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
            <AlertTriangle className="w-3 h-3" /> Inverted Out-of-Range
          </span>
        );
      case 'NEW_IN_FOLLOWUP':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-teal-500/15 text-teal-400 border border-teal-500/30">
            <Sparkles className="w-3 h-3" /> New in Follow-up
          </span>
        );
      case 'NOT_IN_FOLLOWUP':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-slate-500/15 text-slate-400 border border-slate-500/30">
            Baseline Only
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-slate-500/10 text-slate-300 border border-slate-700/50">
            <Minus className="w-3 h-3" /> Stable ({shift.replace('_', ' ')})
          </span>
        );
    }
  };

  return (
    <div className="p-6 sm:p-10 max-w-7xl mx-auto space-y-8 animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-teal-500/20 text-teal-300 border border-teal-500/30">
              Phase 10 Feature
            </span>
            <span className="text-xs text-slate-400">Longitudinal Analytics & Diff Engine</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-3">
            <TrendingUp className="h-8 w-8 text-teal-400" />
            <span>Biomarker Trends & Report Comparison</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Track historical trajectories of clinical biomarkers over time and generate precision side-by-side AI comparisons.
          </p>
        </div>

        {/* Mode Switcher */}
        <div className="flex items-center bg-slate-900/90 p-1.5 rounded-2xl border border-slate-800 shadow-lg">
          <button
            onClick={() => setActiveMode('trends')}
            className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
              activeMode === 'trends'
                ? 'bg-gradient-to-r from-teal-500 to-emerald-500 text-slate-950 shadow-md shadow-teal-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            <span>Time-Series Visualizer</span>
          </button>
          <button
            onClick={() => {
              setActiveMode('compare');
              if (!comparisonResult && reportsList.length >= 2 && reportAId && reportBId && reportAId !== reportBId) {
                handleRunComparison();
              }
            }}
            className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
              activeMode === 'compare'
                ? 'bg-gradient-to-r from-teal-500 to-emerald-500 text-slate-950 shadow-md shadow-teal-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <GitCompare className="w-4 h-4" />
            <span>Report Comparison Diff</span>
            {reportsList.length > 0 && (
              <span
                className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                  reportsList.length >= 2
                    ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30'
                    : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                }`}
              >
                {reportsList.length >= 2 ? `${reportsList.length} reports` : 'Requires 2+'}
              </span>
            )}
          </button>
        </div>
      </div>

      {loadingTrends ? (
        <div className="py-24 text-center space-y-4">
          <RefreshCw className="w-8 h-8 text-teal-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading historical biomarker telemetry...</p>
        </div>
      ) : (
        <>
          {/* ========================================== */}
          {/* MODE 1: Longitudinal Time-Series Visualizer */}
          {/* ========================================== */}
          {activeMode === 'trends' && (
            reportsList.length < 2 ? (
              <div className="glass-card p-8 sm:p-12 rounded-3xl border border-teal-500/20 bg-slate-900/90 text-center space-y-5 max-w-xl mx-auto shadow-2xl my-8">
                <div className="w-16 h-16 rounded-2xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center mx-auto text-teal-400">
                  <TrendingUp className="w-8 h-8" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-bold text-white">Trend Graphs Require 2 or More Reports</h3>
                  <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                    {reportsList.length === 1
                      ? 'You currently have 1 medical report uploaded. A biomarker trend graph tracks how values change across multiple test dates. Please upload a second report (such as an earlier or follow-up health check) to generate longitudinal trajectory graphs.'
                      : 'You do not have any medical reports uploaded yet. Upload at least 2 diagnostic lab reports to unlock automated historical trend graphs, delta analytics, and comparative diffs.'}
                  </p>
                </div>
                <div className="pt-2">
                  <Link
                    href="/dashboard/upload"
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-emerald-500 text-slate-950 font-bold text-xs hover:from-teal-400 hover:to-emerald-400 transition shadow-lg shadow-teal-500/20"
                  >
                    <UploadCloud className="w-4 h-4" />
                    <span>Upload {reportsList.length === 1 ? 'Second' : 'A'} Report</span>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Left Sidebar: Biomarker Selector */}
              <div className="lg:col-span-1 glass-card p-4 rounded-3xl border border-slate-800 bg-slate-900/80 space-y-4">
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                    Select Biomarker ({availableNames.length})
                  </span>
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      placeholder="Search tested markers..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-slate-950/80 border border-slate-700/60 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                </div>

                <div className="max-h-[500px] overflow-y-auto space-y-1 pr-1 custom-scrollbar">
                  {filteredNames.length === 0 ? (
                    <p className="text-xs text-slate-500 text-center py-6">No matching biomarkers found</p>
                  ) : (
                    filteredNames.map((name) => {
                      const series = allTrends.find((t) => t.normalized_name.toLowerCase() === name.toLowerCase());
                      const isSelected = selectedBiomarker.toLowerCase() === name.toLowerCase();
                      const ptsCount = series?.data_points.length || 0;

                      return (
                        <button
                          key={name}
                          onClick={() => setSelectedBiomarker(name)}
                          className={`w-full text-left px-3 py-2.5 rounded-xl text-xs transition flex items-center justify-between group ${
                            isSelected
                              ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40 font-semibold'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                          }`}
                        >
                          <span className="truncate max-w-[170px]">{name}</span>
                          <span
                            className={`text-[10px] px-1.5 py-0.5 rounded-md font-mono ${
                              isSelected
                                ? 'bg-teal-500/30 text-teal-200'
                                : 'bg-slate-800 text-slate-500 group-hover:text-slate-400'
                            }`}
                          >
                            {ptsCount} pts
                          </span>
                        </button>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Right Content: Chart and Metrics */}
              <div className="lg:col-span-3 space-y-6">
                {activeSeries ? (
                  <>
                    {/* Key Metric KPI Cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                      <div className="glass-card p-4 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-1">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Latest Reading</span>
                        <div className="flex items-baseline gap-2">
                          <span className="text-2xl font-black text-white font-mono">
                            {activeSeries.latest_value ?? 'N/A'}
                          </span>
                          <span className="text-xs text-slate-400">{activeSeries.unit || ''}</span>
                        </div>
                        <span className="text-[11px] text-slate-500 block">
                          Status: <strong className="text-slate-300">{activeSeries.latest_flag}</strong>
                        </span>
                      </div>

                      <div className="glass-card p-4 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-1">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Initial Baseline</span>
                        <div className="flex items-baseline gap-2">
                          <span className="text-2xl font-black text-slate-300 font-mono">
                            {activeSeries.earliest_value ?? 'N/A'}
                          </span>
                          <span className="text-xs text-slate-400">{activeSeries.unit || ''}</span>
                        </div>
                        <span className="text-[11px] text-slate-500 block">
                          First test in record
                        </span>
                      </div>

                      <div className="glass-card p-4 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-1">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Net Change (Δ)</span>
                        <div className="flex items-baseline gap-2">
                          <span
                            className={`text-2xl font-black font-mono ${
                              (activeSeries.overall_change || 0) > 0
                                ? 'text-amber-400'
                                : (activeSeries.overall_change || 0) < 0
                                ? 'text-teal-400'
                                : 'text-slate-300'
                            }`}
                          >
                            {(activeSeries.overall_change || 0) > 0 ? '+' : ''}
                            {activeSeries.overall_change ?? 0}
                          </span>
                          <span className="text-xs text-slate-400">
                            ({activeSeries.overall_change_pct ? `${activeSeries.overall_change_pct}%` : '0%'})
                          </span>
                        </div>
                        <span className="text-[11px] text-slate-500 block">
                          Trajectory: <strong className="capitalize text-teal-400">{activeSeries.trend_direction}</strong>
                        </span>
                      </div>

                      <div className="glass-card p-4 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-1">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Reference Range</span>
                        <div className="flex items-baseline gap-1 pt-1">
                          <span className="text-sm font-bold text-emerald-400 font-mono">
                            {activeSeries.ref_min !== null && activeSeries.ref_max !== null
                              ? `${activeSeries.ref_min} - ${activeSeries.ref_max}`
                              : 'Standard'}
                          </span>
                          <span className="text-xs text-slate-400">{activeSeries.unit || ''}</span>
                        </div>
                        <span className="text-[11px] text-slate-500 block">Normal physiological bounds</span>
                      </div>
                    </div>

                    {/* Chart Container */}
                    <div className="glass-card p-6 rounded-3xl border border-slate-800 bg-slate-900/90 space-y-4">
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div>
                          <h3 className="text-base font-bold text-white flex items-center gap-2">
                            <span>{activeSeries.normalized_name}</span>
                            <span className="text-xs font-normal text-slate-400">
                              ({activeSeries.unit || 'unitless'})
                            </span>
                          </h3>
                          <p className="text-xs text-slate-400">
                            Time-series trajectory with standard clinical reference bounds.
                          </p>
                        </div>
                        <span className="text-xs text-slate-400 flex items-center gap-1.5 bg-slate-800/80 px-3 py-1 rounded-lg border border-slate-700">
                          <Activity className="w-3.5 h-3.5 text-teal-400" />
                          <span>{activeSeries.data_points.length} measurements recorded</span>
                        </span>
                      </div>

                      <div className="h-72 w-full pt-4">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                            <defs>
                              <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="#14b8a6" stopOpacity={0.0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                            <XAxis
                              dataKey="name"
                              stroke="#64748b"
                              fontSize={11}
                              tickLine={false}
                              axisLine={{ stroke: '#334155' }}
                            />
                            <YAxis
                              stroke="#64748b"
                              fontSize={11}
                              tickLine={false}
                              axisLine={{ stroke: '#334155' }}
                            />
                            <Tooltip
                              contentStyle={{
                                backgroundColor: '#0f172a',
                                borderColor: '#334155',
                                borderRadius: '12px',
                                fontSize: '12px',
                              }}
                              itemStyle={{ color: '#2dd4bf' }}
                              labelStyle={{ color: '#94a3b8', fontWeight: 'bold' }}
                            />
                            <Area
                              type="monotone"
                              dataKey="value"
                              stroke="#14b8a6"
                              strokeWidth={3}
                              fillOpacity={1}
                              fill="url(#colorVal)"
                              dot={{ stroke: '#2dd4bf', strokeWidth: 2, r: 5, fill: '#0f172a' }}
                              activeDot={{ r: 7, stroke: '#5eead4', strokeWidth: 2 }}
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Historical Records Table for this biomarker */}
                    <div className="glass-card rounded-3xl overflow-hidden border border-slate-800 bg-slate-900/80">
                      <div className="p-4 border-b border-slate-800 bg-slate-900 flex items-center justify-between">
                        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                          Historical Measurement Log
                        </h4>
                        <span className="text-xs text-slate-500">
                          Sorted chronologically
                        </span>
                      </div>

                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs text-slate-300">
                          <thead className="bg-slate-950/60 text-[11px] text-slate-400 font-semibold border-b border-slate-800">
                            <tr>
                              <th className="p-3.5">Report Date</th>
                              <th className="p-3.5">Report Title</th>
                              <th className="p-3.5">Measured Value</th>
                              <th className="p-3.5">Reference Range</th>
                              <th className="p-3.5">Status Flag</th>
                              <th className="p-3.5 text-right">Action</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60 font-medium">
                            {activeSeries.data_points.map((pt, idx) => (
                              <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                                <td className="p-3.5 font-mono text-slate-400">
                                  {pt.report_date || 'N/A'}
                                </td>
                                <td className="p-3.5 font-semibold text-slate-200">
                                  {pt.report_title}
                                </td>
                                <td className="p-3.5 font-mono font-bold text-teal-400">
                                  {pt.value_numeric ?? pt.value_text ?? 'N/A'} {pt.unit || ''}
                                </td>
                                <td className="p-3.5 text-slate-400">
                                  {pt.reference_range_raw || (pt.ref_min !== null ? `${pt.ref_min} - ${pt.ref_max}` : 'N/A')}
                                </td>
                                <td className="p-3.5">
                                  <span
                                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                      pt.flag === 'NORMAL'
                                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                        : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                                    }`}
                                  >
                                    {pt.flag}
                                  </span>
                                </td>
                                <td className="p-3.5 text-right">
                                  <Link
                                    href={`/dashboard/reports/${pt.report_id}`}
                                    className="text-teal-400 hover:text-teal-300 font-semibold transition"
                                  >
                                    View Report →
                                  </Link>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="glass-card p-12 rounded-3xl border border-slate-800 text-center space-y-3">
                    <TrendingUp className="w-10 h-10 text-slate-500 mx-auto" />
                    <p className="text-sm font-semibold text-white">No biomarker trend series available</p>
                    <p className="text-xs text-slate-400 max-w-sm mx-auto">
                      Upload and extract lab reports to automatically track your historical clinical trajectories.
                    </p>
                  </div>
                )}
              </div>
            </div>
            )
          )}

          {/* ========================================== */}
          {/* MODE 2: Multi-Report Comparative Diff Engine */}
          {/* ========================================== */}
          {activeMode === 'compare' && (
            <div className="space-y-6">
              {reportsList.length < 2 ? (
                <div className="glass-card p-8 sm:p-12 rounded-3xl border border-teal-500/20 bg-slate-900/90 text-center space-y-4 max-w-xl mx-auto shadow-2xl">
                  <div className="w-16 h-16 rounded-2xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center mx-auto text-teal-400">
                    <GitCompare className="w-8 h-8" />
                  </div>
                  <h3 className="text-xl font-bold text-white">Compare Requires 2 or More Reports</h3>
                  <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                    {reportsList.length === 1
                      ? 'You currently have 1 medical report uploaded. To perform automated side-by-side comparison, calculate percentage shifts, and track health improvements, please upload a second report.'
                      : 'You do not have any medical reports uploaded yet. Upload your diagnostic lab reports to unlock automated comparative diffs and clinical trend tracking.'}
                  </p>
                  <div className="pt-2">
                    <Link
                      href="/dashboard/upload"
                      className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-emerald-500 text-slate-950 font-bold text-xs hover:from-teal-400 hover:to-emerald-400 transition shadow-lg shadow-teal-500/20"
                    >
                      <UploadCloud className="w-4 h-4" />
                      <span>Upload {reportsList.length === 1 ? 'Second' : 'A'} Report</span>
                    </Link>
                  </div>
                </div>
              ) : (
                <>
                  {/* Report Selectors Card */}
                  <div className="glass-card p-6 rounded-3xl border border-slate-800 bg-slate-900/90 space-y-4">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <GitCompare className="w-4 h-4 text-teal-400" />
                    <span>Select Reports to Compare</span>
                  </h3>

                  {/* Language Selector */}
                  <div className="flex items-center gap-1.5 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
                    <Globe className="w-3.5 h-3.5 text-teal-400" />
                    <select
                      value={compareLanguage}
                      onChange={(e) => setCompareLanguage(e.target.value as any)}
                      className="bg-transparent border-none text-slate-200 focus:outline-none cursor-pointer text-xs"
                    >
                      <option value="en" className="bg-slate-900 text-slate-200">English (EN)</option>
                      <option value="ta" className="bg-slate-900 text-slate-200">தமிழ் (TA)</option>
                      <option value="hi" className="bg-slate-900 text-slate-200">हिंदी (HI)</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Report A: Baseline */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                      Report A (Baseline / Earlier)
                    </label>
                    <select
                      value={reportAId}
                      onChange={(e) => setReportAId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700/80 rounded-2xl p-3 text-xs text-slate-200 focus:outline-none focus:border-teal-500"
                    >
                      {reportsList.map((r) => (
                        <option key={r.id} value={r.id} className="bg-slate-900 text-slate-200">
                          {r.title} ({r.report_date || 'No Date'})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Report B: Follow-up */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                      Report B (Follow-up / Recent)
                    </label>
                    <select
                      value={reportBId}
                      onChange={(e) => setReportBId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700/80 rounded-2xl p-3 text-xs text-slate-200 focus:outline-none focus:border-teal-500"
                    >
                      {reportsList.map((r) => (
                        <option key={r.id} value={r.id} className="bg-slate-900 text-slate-200">
                          {r.title} ({r.report_date || 'No Date'})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {reportAId && reportBId && reportAId === reportBId && (
                  <p className="text-xs text-amber-400 flex items-center gap-1.5 pt-1">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Please select two different reports to calculate shifts.
                  </p>
                )}

                <div className="flex justify-end pt-2">
                  <button
                    onClick={handleRunComparison}
                    disabled={comparing || !reportAId || !reportBId || reportAId === reportBId || reportsList.length < 2}
                    className="px-6 py-3 rounded-2xl bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-slate-950 font-bold text-xs shadow-lg shadow-teal-500/20 flex items-center gap-2 transition disabled:opacity-50"
                  >
                    {comparing ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Computing Deltas & AI Summary...</span>
                      </>
                    ) : (
                      <>
                        <GitCompare className="w-4 h-4" />
                        <span>Execute Comparative Diff</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Comparison Results */}
              {comparisonResult && (
                <div className="space-y-6">
                  {/* Summary Metric Badges */}
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                    <div className="glass-card p-4 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-1">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Total Compared</span>
                      <span className="text-2xl font-black text-white font-mono">
                        {comparisonResult.total_compared}
                      </span>
                      <span className="text-[11px] text-slate-500 block">Aligned diagnostic biomarkers</span>
                    </div>

                    <div className="glass-card p-4 rounded-2xl border border-emerald-500/20 bg-emerald-950/10 space-y-1">
                      <span className="text-[10px] uppercase font-bold text-emerald-400 block">Improved to Normal</span>
                      <span className="text-2xl font-black text-emerald-400 font-mono">
                        {comparisonResult.improved_count}
                      </span>
                      <span className="text-[11px] text-slate-500 block">Positive health normalizations</span>
                    </div>

                    <div className="glass-card p-4 rounded-2xl border border-amber-500/20 bg-amber-950/10 space-y-1">
                      <span className="text-[10px] uppercase font-bold text-amber-400 block">Shifted / Out-of-Range</span>
                      <span className="text-2xl font-black text-amber-400 font-mono">
                        {comparisonResult.deteriorated_count}
                      </span>
                      <span className="text-[11px] text-slate-500 block">Deviations requiring clinical review</span>
                    </div>

                    <div className="glass-card p-4 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-1">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Stable Biomarkers</span>
                      <span className="text-2xl font-black text-slate-300 font-mono">
                        {comparisonResult.stable_count}
                      </span>
                      <span className="text-[11px] text-slate-500 block">Consistent baseline parameters</span>
                    </div>
                  </div>

                  {/* Side-by-Side Comparison Graph */}
                  {comparisonResult.items.some((it) => it.report_a_value !== undefined && it.report_b_value !== undefined && typeof it.report_a_value === 'number' && typeof it.report_b_value === 'number') && (
                    <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate-800 bg-slate-900/90 space-y-4">
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-2xl bg-teal-500/10 text-teal-400 flex items-center justify-center border border-teal-500/20">
                            <BarChart2 className="w-5 h-5" />
                          </div>
                          <div>
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                              <span>Biomarker Shift Comparison Graph</span>
                            </h3>
                            <p className="text-xs text-slate-400">
                              Visual delta comparison between Baseline (Report A) and Follow-up (Report B).
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-xs font-medium">
                          <div className="flex items-center gap-1.5">
                            <span className="w-3 h-3 rounded-md bg-cyan-500" />
                            <span className="text-slate-300">Baseline (Report A)</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="w-3 h-3 rounded-md bg-emerald-400" />
                            <span className="text-slate-300">Follow-up (Report B)</span>
                          </div>
                        </div>
                      </div>

                      <div className="h-72 w-full pt-4">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={comparisonResult.items
                              .filter((it) => it.report_a_value !== undefined && it.report_b_value !== undefined && typeof it.report_a_value === 'number' && typeof it.report_b_value === 'number')
                              .slice(0, 10)
                              .map((it) => ({
                                name: it.normalized_name,
                                'Baseline (Report A)': it.report_a_value,
                                'Follow-up (Report B)': it.report_b_value,
                                unit: it.unit || '',
                                delta_pct: it.delta_pct,
                              }))}
                            margin={{ top: 10, right: 10, left: 0, bottom: 25 }}
                          >
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis
                              dataKey="name"
                              stroke="#64748b"
                              tick={{ fill: '#94a3b8', fontSize: 11 }}
                              interval={0}
                              angle={-15}
                              textAnchor="end"
                            />
                            <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                            <Tooltip
                              content={({ active, payload, label }) => {
                                if (active && payload && payload.length) {
                                  const d = payload[0].payload;
                                  return (
                                    <div className="bg-slate-900/95 border border-slate-700/80 p-3 rounded-xl shadow-xl text-xs space-y-1">
                                      <p className="font-bold text-white">{label}</p>
                                      <p className="text-cyan-400 font-mono">
                                        Baseline: {payload[0].value} {d.unit}
                                      </p>
                                      {payload[1] && (
                                        <p className="text-emerald-400 font-mono">
                                          Follow-up: {payload[1].value} {d.unit}
                                        </p>
                                      )}
                                      {d.delta_pct !== null && d.delta_pct !== undefined && (
                                        <p
                                          className={`text-[10px] font-bold ${
                                            d.delta_pct > 0
                                              ? 'text-amber-400'
                                              : d.delta_pct < 0
                                              ? 'text-cyan-400'
                                              : 'text-slate-400'
                                          }`}
                                        >
                                          Shift: {d.delta_pct > 0 ? `+${d.delta_pct}%` : `${d.delta_pct}%`}
                                        </p>
                                      )}
                                    </div>
                                  );
                                }
                                return null;
                              }}
                            />
                            <Bar dataKey="Baseline (Report A)" fill="#06b6d4" radius={[6, 6, 0, 0]} />
                            <Bar dataKey="Follow-up (Report B)" fill="#10b981" radius={[6, 6, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  {/* AI Comparative Summary Card */}
                  <div className="glass-card p-6 sm:p-8 rounded-3xl border border-teal-500/30 bg-gradient-to-r from-teal-950/20 via-slate-900/90 to-cyan-950/20 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-2xl bg-teal-500/10 text-teal-400 flex items-center justify-center border border-teal-500/20">
                          <Bot className="w-5 h-5" />
                        </div>
                        <div>
                          <h3 className="text-sm font-bold text-white flex items-center gap-2">
                            <span>Grounded AI Trajectory Analysis</span>
                            <span className="text-[9px] px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-300 font-mono border border-teal-500/20">
                              {comparisonResult.model_used}
                            </span>
                          </h3>
                          <p className="text-xs text-slate-400">
                            Synthesis of progress, physiological changes, and questions for your doctor.
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-800/80 text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">
                      {comparisonResult.ai_summary}
                    </div>

                    <div className="flex items-center gap-1.5 text-[10px] text-slate-500 pt-1">
                      <ShieldAlert className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                      <p>
                        Comparative analysis is for health-literacy tracking only. Please consult your physician before making any clinical decisions.
                      </p>
                    </div>
                  </div>

                  {/* Comparative Diff Table */}
                  <div className="glass-card rounded-3xl overflow-hidden border border-slate-800 bg-slate-900/80 space-y-4">
                    <div className="p-4 border-b border-slate-800 bg-slate-900 flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-2">
                        <SlidersHorizontal className="w-4 h-4 text-slate-400" />
                        <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                          Biomarker Diff Table ({comparisonResult.items.length})
                        </span>
                      </div>

                      {/* Filter Buttons */}
                      <div className="flex items-center gap-1.5 text-xs">
                        <button
                          onClick={() => setFilterShift('ALL')}
                          className={`px-3 py-1 rounded-lg transition font-medium ${
                            filterShift === 'ALL'
                              ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          All ({comparisonResult.items.length})
                        </button>
                        <button
                          onClick={() => setFilterShift('IMPROVED')}
                          className={`px-3 py-1 rounded-lg transition font-medium ${
                            filterShift === 'IMPROVED'
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          Improved ({comparisonResult.improved_count})
                        </button>
                        <button
                          onClick={() => setFilterShift('DETERIORATED')}
                          className={`px-3 py-1 rounded-lg transition font-medium ${
                            filterShift === 'DETERIORATED'
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          Shifted ({comparisonResult.deteriorated_count})
                        </button>
                        <button
                          onClick={() => setFilterShift('STABLE')}
                          className={`px-3 py-1 rounded-lg transition font-medium ${
                            filterShift === 'STABLE'
                              ? 'bg-slate-700/50 text-slate-200 border border-slate-600'
                              : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          Stable ({comparisonResult.stable_count})
                        </button>
                      </div>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs text-slate-300">
                        <thead className="bg-slate-950/60 text-[11px] text-slate-400 font-semibold border-b border-slate-800">
                          <tr>
                            <th className="p-3.5">Biomarker</th>
                            <th className="p-3.5">Baseline (A)</th>
                            <th className="p-3.5">Follow-up (B)</th>
                            <th className="p-3.5">Delta (Δ)</th>
                            <th className="p-3.5">% Change</th>
                            <th className="p-3.5">Status Transition</th>
                            <th className="p-3.5">Clinical Note</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 font-medium">
                          {filteredComparisonItems.map((it, idx) => (
                            <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                              <td className="p-3.5 font-semibold text-slate-200">
                                {it.normalized_name}
                              </td>
                              <td className="p-3.5 font-mono text-slate-300">
                                {it.report_a_value !== null ? `${it.report_a_value} ${it.unit || ''}` : 'N/A'}{' '}
                                {it.report_a_flag && (
                                  <span className="text-[10px] text-slate-500">({it.report_a_flag})</span>
                                )}
                              </td>
                              <td className="p-3.5 font-mono font-bold text-white">
                                {it.report_b_value !== null ? `${it.report_b_value} ${it.unit || ''}` : 'N/A'}{' '}
                                {it.report_b_flag && (
                                  <span className="text-[10px] text-teal-400">({it.report_b_flag})</span>
                                )}
                              </td>
                              <td className="p-3.5 font-mono">
                                {typeof it.delta_numeric === 'number' ? (
                                  <span
                                    className={
                                      it.delta_numeric > 0
                                        ? 'text-amber-400'
                                        : it.delta_numeric < 0
                                        ? 'text-teal-400'
                                        : 'text-slate-400'
                                    }
                                  >
                                    {it.delta_numeric > 0 ? '+' : ''}
                                    {it.delta_numeric} {it.unit || ''}
                                  </span>
                                ) : (
                                  '—'
                                )}
                              </td>
                              <td className="p-3.5 font-mono">
                                {typeof it.delta_pct === 'number' ? (
                                  <span
                                    className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                                      it.delta_pct > 0
                                        ? 'bg-amber-500/10 text-amber-400'
                                        : it.delta_pct < 0
                                        ? 'bg-teal-500/10 text-teal-400'
                                        : 'bg-slate-800 text-slate-400'
                                    }`}
                                  >
                                    {it.delta_pct > 0 ? '+' : ''}
                                    {it.delta_pct}%
                                  </span>
                                ) : (
                                  '—'
                                )}
                              </td>
                              <td className="p-3.5">{getShiftBadge(it.status_shift)}</td>
                              <td className="p-3.5 text-slate-400 max-w-xs truncate" title={it.clinical_interpretation}>
                                {it.clinical_interpretation}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function TrendsAndComparePage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center space-y-4">
          <RefreshCw className="h-8 w-8 text-teal-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading Biomarker Trends & Comparison...</p>
        </div>
      }
    >
      <TrendsAndCompareContent />
    </Suspense>
  );
}
