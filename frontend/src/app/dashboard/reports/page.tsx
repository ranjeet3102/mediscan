'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { api, ReportItem } from '@/lib/api';
import {
  FileText,
  UploadCloud,
  Search,
  Filter,
  Trash2,
  ExternalLink,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileCheck,
  Pill,
  Sparkles,
  RefreshCw,
  ScanLine,
} from 'lucide-react';

export default function MyReportsPage() {
  const { token } = useAuth();
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getReports(token || 'dev-user-token');
      setReports(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch reports.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [token]);

  const handleDelete = async (id: string, title: string) => {
    if (!confirm(`Are you sure you want to permanently delete "${title}"? This will remove all associated clinical values.`)) {
      return;
    }
    setDeletingId(id);
    try {
      await api.deleteReport(token || 'dev-user-token', id);
      setReports((prev) => prev.filter((r) => r.id !== id));
    } catch (err: any) {
      alert(err.message || 'Failed to delete report.');
    } finally {
      setDeletingId(null);
    }
  };

  // Filter reports by search keyword and category tab
  const filteredReports = reports.filter((r) => {
    const matchesSearch = r.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter =
      selectedFilter === 'all' ||
      (selectedFilter === 'lab_report' && r.report_type !== 'prescription') ||
      (selectedFilter === 'prescription' && r.report_type === 'prescription');
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="glass-card p-6 sm:p-8 rounded-3xl border border-cyan-500/30 bg-gradient-to-r from-slate-900/90 via-cyan-950/20 to-slate-900/90 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/20 border border-teal-500/40 text-teal-300 text-xs font-semibold">
            <FileCheck className="h-3 w-3 text-teal-400" />
            <span>Document Repository</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            My Medical Reports &amp; Prescriptions
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 max-w-xl">
            Access your verified medical records, check confidence scores, download originals via private signed URLs, or launch conversational Q&amp;A.
          </p>
        </div>

        <Link
          href="/dashboard/upload"
          className="self-start sm:self-auto px-5 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 flex items-center space-x-2 transition"
        >
          <UploadCloud className="h-4 w-4" />
          <span>Upload Report</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by report title..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900/80 border border-white/10 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-cyan-400 transition"
          />
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center bg-slate-900/90 border border-white/10 rounded-xl p-1 w-full sm:w-auto">
          {[
            { id: 'all', label: 'All Documents' },
            { id: 'lab_report', label: 'Lab Reports' },
            { id: 'prescription', label: 'Prescriptions' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedFilter(tab.id)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition ${
                selectedFilter === tab.id
                  ? 'bg-teal-500/20 text-cyan-300 border border-teal-500/40'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Reports Content */}
      {loading ? (
        <div className="glass-card p-12 rounded-3xl text-center space-y-3">
          <RefreshCw className="h-8 w-8 text-cyan-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading your medical records...</p>
        </div>
      ) : error ? (
        <div className="glass-card p-8 rounded-3xl text-center space-y-4 border-rose-500/30">
          <AlertCircle className="h-8 w-8 text-rose-400 mx-auto" />
          <p className="text-xs text-rose-300">{error}</p>
          <button
            onClick={fetchReports}
            className="px-4 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs font-semibold text-white hover:bg-slate-800"
          >
            Retry
          </button>
        </div>
      ) : filteredReports.length === 0 ? (
        /* Empty State */
        <div className="glass-card p-12 rounded-3xl text-center space-y-4 border border-white/10">
          <div className="h-16 w-16 rounded-3xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mx-auto text-cyan-400">
            <FileText className="h-8 w-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white">No Documents Found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              {searchQuery
                ? 'No documents match your search query. Try adjusting your keywords.'
                : 'You have not uploaded any medical records yet. Upload your first document to start.'}
            </p>
          </div>
          <Link
            href="/dashboard/upload"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 hover:scale-105 transition"
          >
            <UploadCloud className="h-4 w-4" />
            <span>Upload Document</span>
          </Link>
        </div>
      ) : (
        /* Reports Grid / Cards */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredReports.map((report) => (
            <div
              key={report.id}
              className="glass-card p-6 rounded-3xl glass-card-hover border flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div
                    className={`p-3 rounded-2xl border ${
                      report.report_type === 'prescription'
                        ? 'bg-purple-500/10 border-purple-500/20 text-purple-400'
                        : 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400'
                    }`}
                  >
                    {report.report_type === 'prescription' ? (
                      <Pill className="h-5 w-5 text-purple-400" />
                    ) : (
                      <FileText className="h-5 w-5 text-cyan-400" />
                    )}
                  </div>
                  <span
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-full border uppercase ${
                      report.ocr_status === 'completed'
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                        : report.ocr_status === 'processing'
                        ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                        : 'bg-teal-500/10 border-teal-500/30 text-teal-400'
                    }`}
                  >
                    {report.ocr_status}
                  </span>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-white line-clamp-1">{report.title}</h3>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {report.report_date || 'Date not specified'} • {report.report_type === 'prescription' ? 'prescription' : 'lab report'}
                  </p>
                </div>

                <div className="flex items-center space-x-2 text-[11px] text-slate-300">
                  <CheckCircle2 className="h-3.5 w-3.5 text-teal-400" />
                  <span>Private Storage Locked</span>
                </div>
              </div>

              {/* Card Footer Actions - If prescription, NEVER show View OCR */}
              <div className="pt-3 border-t border-white/10 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {report.report_type === 'prescription' ? (
                    <Link
                      href={`/dashboard/prescriptions?reportId=${report.id}`}
                      className="p-2 px-3 rounded-xl bg-purple-950/40 border border-purple-500/30 hover:border-purple-400 text-purple-300 text-xs font-semibold flex items-center space-x-1.5 transition hover:scale-105"
                      title="View prescription in Prescriptions section"
                    >
                      <Pill className="h-3.5 w-3.5 text-purple-400" />
                      <span>View Prescription</span>
                    </Link>
                  ) : (
                    <Link
                      href={`/dashboard/reports/${report.id}`}
                      className="p-2 px-3 rounded-xl bg-cyan-950/40 border border-cyan-500/30 hover:border-cyan-400 text-cyan-300 text-xs font-semibold flex items-center space-x-1.5 transition"
                      title="View OCR & diagnostic findings"
                    >
                      <ScanLine className="h-3.5 w-3.5" />
                      <span>View OCR</span>
                    </Link>
                  )}

                  {report.signed_url && (
                    <a
                      href={report.signed_url}
                      target="_blank"
                      rel="noreferrer"
                      className="p-2 rounded-xl bg-slate-900 border border-white/10 text-slate-300 hover:text-cyan-400 text-xs flex items-center space-x-1 transition"
                      title="Download original file via signed URL"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      <span className="text-[10px]">Original</span>
                    </a>
                  )}
                </div>

                <button
                  onClick={() => handleDelete(report.id, report.title)}
                  disabled={deletingId === report.id}
                  className="p-2 rounded-xl bg-slate-900 border border-white/10 text-slate-400 hover:text-rose-400 hover:border-rose-500/30 text-xs transition"
                  title="Delete report"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
