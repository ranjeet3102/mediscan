'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import {
  Activity,
  FileCheck2,
  BrainCircuit,
  MessageSquareCode,
  TrendingUp,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  Lock,
  Stethoscope,
  Globe2,
  CheckCircle,
} from 'lucide-react';

export default function HomePage() {
  const { user } = useAuth();

  return (
    <div className="relative overflow-hidden">
      {/* Background Glows */}
      <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[700px] h-[450px] bg-gradient-to-tr from-cyan-600/20 via-teal-500/10 to-transparent blur-[120px] pointer-events-none rounded-full" />
      <div className="absolute bottom-10 right-10 w-[400px] h-[400px] bg-purple-600/10 blur-[130px] pointer-events-none rounded-full" />

      {/* Hero Section */}
      <section className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-20 text-center">
        <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-300 text-xs font-semibold mb-6 animate-pulse-glow">
          <Sparkles className="h-3.5 w-3.5 text-teal-400" />
          <span>Medical Report Simplifier 2.0 • Free & Open-Source First</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-tight sm:leading-tight">
          AI-Powered, <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 via-cyan-300 to-sky-400">Confidence-Aware</span> Health Literacy
        </h1>

        <p className="mt-6 text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Upload medical lab reports and prescriptions to extract, verify, simplify, converse, and track trends over time—with zero patient data exposed to administrators.
        </p>

        {/* Action CTAs */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/dashboard"
            className="px-6 py-3.5 rounded-2xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold text-sm shadow-xl shadow-cyan-500/25 transition-all transform hover:-translate-y-0.5 flex items-center space-x-2"
          >
            <span>Launch Patient Portal</span>
            <ArrowRight className="h-4 w-4" />
          </Link>

          <Link
            href="/admin"
            className="px-6 py-3.5 rounded-2xl bg-slate-900/80 hover:bg-slate-800 text-slate-200 border border-purple-500/30 hover:border-purple-500/60 font-semibold text-sm shadow-lg shadow-purple-500/10 transition-all transform hover:-translate-y-0.5 flex items-center space-x-2"
          >
            <ShieldCheck className="h-4 w-4 text-purple-400" />
            <span>Open Admin Telemetry (Zero PHI)</span>
          </Link>
        </div>

        {/* Pipeline Badge Flow */}
        <div className="mt-16 flex flex-wrap items-center justify-center gap-2 sm:gap-4 max-w-4xl mx-auto">
          {['1. Extract', '2. Verify', '3. Explain', '4. Ask', '5. Compare', '6. Track'].map((step, idx) => (
            <div
              key={step}
              className="px-3.5 py-1.5 rounded-xl bg-slate-900/70 border border-white/10 text-xs font-mono text-cyan-300 flex items-center space-x-1.5"
            >
              <CheckCircle className="h-3 w-3 text-teal-400" />
              <span>{step}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Feature Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Card 1: OCR & Verification */}
          <div className="glass-card p-6 rounded-3xl glass-card-hover space-y-4">
            <div className="h-12 w-12 rounded-2xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400">
              <FileCheck2 className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Confidence-Aware OCR</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              OpenCV preprocessing coupled with Tesseract OCR extracts lab parameters and assigns a multi-factor confidence rating, never guessing ambiguous values.
            </p>
          </div>

          {/* Card 2: Grounded Explanations */}
          <div className="glass-card p-6 rounded-3xl glass-card-hover space-y-4">
            <div className="h-12 w-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <BrainCircuit className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Grounded Medical RAG</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Local Ollama LLM grounded in a curated medical knowledge base with pgvector indexing, ensuring patient-safe, plain-English explanations.
            </p>
          </div>

          {/* Card 3: Ask My Report */}
          <div className="glass-card p-6 rounded-3xl glass-card-hover space-y-4">
            <div className="h-12 w-12 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
              <MessageSquareCode className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Conversational Q&A</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Interact with your specific report results in real-time. Ask follow-up queries with automatic context recall of previous historical tests.
            </p>
          </div>

          {/* Card 4: Longitudinal Trends */}
          <div className="glass-card p-6 rounded-3xl glass-card-hover space-y-4">
            <div className="h-12 w-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <TrendingUp className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Historical Biomarker Trends</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Visualize longitudinal charts for HbA1c, TSH, Lipid profiles, and Kidney markers across dates with shaded reference boundary bands.
            </p>
          </div>

          {/* Card 5: Doctor Support */}
          <div className="glass-card p-6 rounded-3xl glass-card-hover space-y-4">
            <div className="h-12 w-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Stethoscope className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Doctor Discussion Summary</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Generate print-ready 1-page clinical visit summaries and informed, neutral questions to discuss with your consulting physician.
            </p>
          </div>

          {/* Card 6: Privacy Guarantee */}
          <div className="glass-card p-6 rounded-3xl glass-card-hover space-y-4 border-purple-500/30">
            <div className="h-12 w-12 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <Lock className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Strict Privacy Separation</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Users manage their medical data; Admins see strictly aggregated system telemetry. Zero patient names, files, OCR text, or chats are visible to admins.
            </p>
          </div>
        </div>
      </section>

      {/* Multilingual Footer Banner */}
      <footer className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 border-t border-white/10 mt-12 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
        <div className="flex items-center space-x-2">
          <Globe2 className="h-4 w-4 text-teal-400" />
          <span>Multilingual Ready: English • தமிழ் • हिन्दी</span>
        </div>
        <p className="text-slate-500">
          Medical Report Simplifier 2.0 • Academic & Health-Literacy Research Initiative
        </p>
      </footer>
    </div>
  );
}
