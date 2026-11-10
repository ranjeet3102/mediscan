'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { api, ReportItem } from '@/lib/api';
import {
  UploadCloud,
  FileText,
  MessageSquareQuote,
  TrendingUp,
  GitCompare,
  Pill,
  Stethoscope,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowUpRight,
  ShieldCheck,
  Sparkles,
  Inbox,
} from 'lucide-react';

export default function DashboardPage() {
  const { user, token } = useAuth();
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!token) return;
    const fetchUserData = async () => {
      setLoading(true);
      try {
        const userReports = await api.getReports(token);
        setReports(userReports);
      } catch (e) {
        console.error('Failed to load user reports:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchUserData();
  }, [token]);

  const labReportsCount = reports.filter((r) => r.report_type === 'lab_report').length;
  const prescriptionsCount = reports.filter((r) => r.report_type === 'prescription').length;
  const completedCount = reports.filter((r) => r.ocr_status === 'completed').length;

  const stats = [
    { label: 'My Uploaded Reports', value: reports.length.toString(), icon: FileText, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
    { label: 'Lab Reports Processed', value: labReportsCount.toString(), icon: CheckCircle2, color: 'text-teal-400', bg: 'bg-teal-500/10' },
    { label: 'Active Prescriptions', value: prescriptionsCount.toString(), icon: Pill, color: 'text-purple-400', bg: 'bg-purple-500/10' },
    { label: 'Verified Documents', value: completedCount.toString(), icon: ShieldCheck, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  ];

  const quickActions = [
    {
      title: 'Upload New Report',
      description: 'Ingest PDF or image lab report with OpenCV deskew & Tesseract OCR verification.',
      icon: UploadCloud,
      href: '/dashboard/upload',
      color: 'from-teal-500/20 to-cyan-500/20 border-cyan-500/30',
      badge: 'OCR Ingestion',
    },
    {
      title: 'Ask My Report (Q&A)',
      description: 'Conversational chat grounded in your verified report values and clinical findings.',
      icon: MessageSquareQuote,
      href: '/dashboard/chat',
      color: 'from-cyan-500/20 to-blue-500/20 border-blue-500/30',
      badge: 'Ollama AI',
    },
    {
      title: 'Compare Two Reports',
      description: 'Automated delta calculation and change explanation between test dates.',
      icon: GitCompare,
      href: '/dashboard/trends?mode=compare',
      color: 'from-blue-500/20 to-indigo-500/20 border-indigo-500/30',
      badge: 'Delta Engine',
    },
    {
      title: 'Longitudinal Trends',
      description: 'Visual time-series graphs of biomarkers like HbA1c, TSH, and Hemoglobin.',
      icon: TrendingUp,
      href: '/dashboard/trends',
      color: 'from-emerald-500/20 to-teal-500/20 border-emerald-500/30',
      badge: 'Recharts',
    },
    {
      title: 'Prescription Schedule',
      description: 'Structured medicine schedules with dosage, frequency, and timing instructions.',
      icon: Pill,
      href: '/dashboard/prescriptions',
      color: 'from-purple-500/20 to-pink-500/20 border-purple-500/30',
      badge: 'Medications',
    },
    {
      title: 'Doctor Visit Summary',
      description: 'Generate 1-page clinical summary and neutral questions for your physician.',
      icon: Stethoscope,
      href: '/dashboard/doctor-summary',
      color: 'from-amber-500/20 to-orange-500/20 border-amber-500/30',
      badge: 'Doctor Suite',
    },
  ];

  const recentReports = reports.slice(0, 5);

  return (
    <div className="space-y-8">
      {/* Top Welcome Banner */}
      <div className="glass-card p-6 sm:p-8 rounded-3xl relative overflow-hidden border border-cyan-500/30 bg-gradient-to-r from-slate-900/90 via-cyan-950/20 to-slate-900/90">
        <div className="relative z-10 max-w-2xl space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/20 border border-teal-500/40 text-teal-300 text-xs font-semibold">
            <Sparkles className="h-3 w-3 text-teal-400" />
            <span>Health Literacy Assistant Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            Welcome back, <span className="text-cyan-400">{user?.full_name || user?.email?.split('@')[0]}</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Your medical records are stored securely with end-to-end privacy isolation. Review simplified test breakdowns, ask questions, or compare reports.
          </p>
        </div>
      </div>

      {/* Metric Counters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="glass-card p-5 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400 font-medium">{stat.label}</span>
                <div className={`p-2 rounded-xl ${stat.bg}`}>
                  <Icon className={`h-4 w-4 ${stat.color}`} />
                </div>
              </div>
              <p className="text-2xl font-bold text-white">{loading ? '...' : stat.value}</p>
            </div>
          );
        })}
      </div>

      {/* Quick Actions Grid */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">
          Core Workflow Capabilities
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Link
                key={action.title}
                href={action.href}
                className={`glass-card p-5 rounded-2xl glass-card-hover border bg-gradient-to-br ${action.color} flex flex-col justify-between space-y-4 group`}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="p-2.5 rounded-xl bg-slate-900/80 border border-white/10 text-cyan-400 group-hover:scale-110 transition">
                      <Icon className="h-5 w-5" />
                    </div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-900/90 text-slate-300 border border-white/10">
                      {action.badge}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-white group-hover:text-cyan-300 transition">
                    {action.title}
                  </h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {action.description}
                  </p>
                </div>
                <div className="flex items-center text-xs font-semibold text-cyan-400 group-hover:translate-x-1 transition space-x-1">
                  <span>Open Feature</span>
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Recent Uploaded Reports Table Preview */}
      <div className="glass-card p-6 rounded-3xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white">Your Recent Medical Documents</h3>
            <p className="text-xs text-slate-400">Scoped exclusively to your account</p>
          </div>
          <Link
            href="/dashboard/reports"
            className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition"
          >
            View all reports &rarr;
          </Link>
        </div>

        {recentReports.length === 0 ? (
          <div className="text-center py-8 space-y-3">
            <div className="p-3 rounded-2xl bg-slate-900/80 border border-white/10 text-slate-400 inline-block">
              <Inbox className="h-6 w-6" />
            </div>
            <p className="text-xs text-slate-400">No medical reports uploaded yet.</p>
            <Link
              href="/dashboard/upload"
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-teal-500/20 text-teal-300 text-xs font-semibold border border-teal-500/30 hover:bg-teal-500/30 transition"
            >
              <UploadCloud className="h-3.5 w-3.5" />
              <span>Upload your first report</span>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/10 text-slate-400 uppercase tracking-wider">
                  <th className="pb-3 font-semibold">Document Title</th>
                  <th className="pb-3 font-semibold">Date</th>
                  <th className="pb-3 font-semibold">Category</th>
                  <th className="pb-3 font-semibold text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {recentReports.map((report) => (
                  <tr key={report.id} className="hover:bg-white/5 transition">
                    <td className="py-3.5 font-medium text-white flex items-center space-x-2">
                      {report.report_type === 'prescription' ? (
                        <Pill className="h-4 w-4 text-purple-400 flex-shrink-0" />
                      ) : (
                        <FileText className="h-4 w-4 text-cyan-400 flex-shrink-0" />
                      )}
                      <Link
                        href={
                          report.report_type === 'prescription'
                            ? `/dashboard/prescriptions?reportId=${report.id}`
                            : `/dashboard/reports/${report.id}`
                        }
                        className="hover:text-cyan-400 transition"
                      >
                        {report.title}
                      </Link>
                    </td>
                    <td className="py-3.5 text-slate-400">{report.report_date || 'Recent'}</td>
                    <td className="py-3.5 text-slate-300 capitalize">{report.report_type.replace('_', ' ')}</td>
                    <td className="py-3.5 text-right">
                      <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold">
                        <CheckCircle2 className="h-3 w-3" />
                        <span className="capitalize">{report.ocr_status}</span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
