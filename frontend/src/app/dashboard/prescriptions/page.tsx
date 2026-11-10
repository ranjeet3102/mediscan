'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import {
  api,
  ReportItem,
  PrescriptionResponse,
  MedicationItem,
  MedicationCreateRequest,
} from '@/lib/api';
import {
  Pill,
  Clock,
  Calendar,
  Sun,
  Sunrise,
  Moon,
  Bed,
  Plus,
  Trash2,
  Printer,
  FileText,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  ChevronRight,
  ShieldCheck,
  Stethoscope,
  Info,
  X,
  Edit3,
  ListChecks,
} from 'lucide-react';

function PrescriptionsContent() {
  const { token } = useAuth();
  const searchParams = useSearchParams();
  const initialReportId = searchParams.get('reportId') || '';

  // State
  const [reportsList, setReportsList] = useState<ReportItem[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>(initialReportId);
  const [prescription, setPrescription] = useState<PrescriptionResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingReports, setLoadingReports] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Custom text parse mode
  const [customTextMode, setCustomTextMode] = useState<boolean>(false);
  const [customText, setCustomText] = useState<string>('');
  const [parsingText, setParsingText] = useState<boolean>(false);

  // Add Medication Modal
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [addForm, setAddForm] = useState<MedicationCreateRequest>({
    medicine_name: '',
    generic_name: '',
    form: 'Tablet',
    strength: '',
    dosage: '1 Tablet',
    frequency: '1-0-1',
    timing: 'After Food',
    duration: '7 days',
    instructions: '',
  });

  // Fetch reports list
  useEffect(() => {
    if (!token) return;
    const fetchReports = async () => {
      setLoadingReports(true);
      try {
        const reps = await api.getReports(token);
        // Exclusively show prescriptions here - user specified prescriptions only belong here
        const rxReports = reps.filter((r) => r.report_type === 'prescription');
        setReportsList(rxReports);
        if (initialReportId && rxReports.some((r) => r.id === initialReportId)) {
          setSelectedReportId(initialReportId);
        } else if (rxReports.length > 0) {
          setSelectedReportId(rxReports[0].id);
        } else {
          setSelectedReportId('');
        }
      } catch (err) {
        console.error('Failed to fetch reports:', err);
      } finally {
        setLoadingReports(false);
      }
    };
    fetchReports();
  }, [token]);

  // Fetch prescription for selected report
  useEffect(() => {
    if (!token || !selectedReportId) return;

    const fetchRx = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getPrescription(token, selectedReportId);
        setPrescription(data);
      } catch (err: any) {
        console.error('Failed to fetch prescription:', err);
        setError(err.message || 'Failed to retrieve prescription');
      } finally {
        setLoading(false);
      }
    };

    fetchRx();
  }, [token, selectedReportId]);

  // Handle custom text parsing
  const handleParseCustomText = async () => {
    if (!token || !customText.trim()) return;
    setParsingText(true);
    setError(null);
    try {
      const data = await api.parsePrescriptionText(token, customText, selectedReportId || 'custom-prescription');
      setPrescription(data);
      setCustomTextMode(false);
    } catch (err: any) {
      setError(err.message || 'Failed to parse prescription text');
    } finally {
      setParsingText(false);
    }
  };

  // Handle Add Medication
  const handleAddMedication = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !addForm.medicine_name.trim()) return;

    try {
      const repId = selectedReportId || prescription?.report_id || 'adhoc-prescription';
      const newMed = await api.addMedicationItem(token, repId, addForm);
      if (prescription) {
        setPrescription({
          ...prescription,
          medications: [...prescription.medications, newMed],
          total_medications_count: prescription.total_medications_count + 1,
        });
      } else {
        setPrescription({
          id: 'rx-new',
          report_id: repId,
          medications: [newMed],
          total_medications_count: 1,
          parsed_at: new Date().toISOString(),
        });
      }
      setIsAddModalOpen(false);
      setAddForm({
        medicine_name: '',
        generic_name: '',
        form: 'Tablet',
        strength: '',
        dosage: '1 Tablet',
        frequency: '1-0-1',
        timing: 'After Food',
        duration: '7 days',
        instructions: '',
      });
    } catch (err: any) {
      alert(err.message || 'Failed to add medication');
    }
  };

  // Handle Delete Medication
  const handleDeleteMedication = async (medId?: string) => {
    if (!token || !medId) return;
    if (!confirm('Remove this medication from the schedule?')) return;

    try {
      const repId = selectedReportId || prescription?.report_id || 'adhoc-prescription';
      await api.deleteMedicationItem(token, repId, medId);
      if (prescription) {
        setPrescription({
          ...prescription,
          medications: prescription.medications.filter((m) => m.id !== medId),
          total_medications_count: Math.max(0, prescription.total_medications_count - 1),
        });
      }
    } catch (err: any) {
      alert(err.message || 'Failed to delete medication');
    }
  };

  // Filter medications into daily slots
  const morningMeds = prescription?.medications.filter((m) => m.morning) || [];
  const afternoonMeds = prescription?.medications.filter((m) => m.afternoon) || [];
  const nightMeds = prescription?.medications.filter((m) => m.night) || [];
  const bedtimeMeds = prescription?.medications.filter((m) => m.bedtime) || [];

  return (
    <div className="space-y-6 pb-16">
      {/* Screen Controls Header (Hidden in Print Mode) */}
      <div className="print:hidden space-y-4">
        {/* Top Breadcrumb & Phase Badge */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <Link href="/dashboard" className="hover:text-cyan-400 transition">
              Dashboard
            </Link>
            <ChevronRight className="h-3 w-3" />
            <span className="text-cyan-400 font-medium">Prescription & Medication Planner</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 flex items-center space-x-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Phase 11 Complete</span>
            </span>
          </div>
        </div>

        {/* Page Title & Intro */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold tracking-tight bg-gradient-to-r from-white via-cyan-100 to-teal-200 bg-clip-text text-transparent flex items-center gap-3">
              <Pill className="h-7 w-7 text-cyan-400" />
              Prescription Parsing & Daily Medication Schedule
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Extracts medicine names, dosage strengths, intake frequencies, and meal timings to generate an interactive daily medication schedule and printable pill planner.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-cyan-500/40 hover:bg-slate-800 text-cyan-300 font-bold text-xs flex items-center space-x-2 transition cursor-pointer"
            >
              <Plus className="h-4 w-4" />
              <span>Add Medication</span>
            </button>

            <button
              onClick={() => setCustomTextMode(!customTextMode)}
              className="px-3.5 py-2.5 rounded-xl glass-card hover:bg-white/10 text-slate-200 font-medium text-xs flex items-center space-x-2 border border-white/10 transition cursor-pointer"
            >
              <Edit3 className="h-4 w-4 text-slate-400" />
              <span>{customTextMode ? 'Close Text Parser' : 'Paste Rx Text'}</span>
            </button>

            <button
              onClick={() => window.print()}
              disabled={!prescription || prescription.medications.length === 0}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold text-xs flex items-center space-x-2 shadow-lg shadow-cyan-500/20 transition disabled:opacity-50 cursor-pointer"
            >
              <Printer className="h-4 w-4" />
              <span>Print Pill Planner</span>
            </button>
          </div>
        </div>

        {/* Custom Text Parsing Drawer */}
        {customTextMode && (
          <div className="glass-card p-5 rounded-2xl border border-cyan-500/30 bg-slate-950/90 space-y-3 animate-fade-in">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-cyan-400" />
                <span>Paste Doctor Prescription Transcript or Handwritten OCR Text</span>
              </span>
              <button onClick={() => setCustomTextMode(false)} className="text-slate-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>
            <textarea
              rows={4}
              value={customText}
              onChange={(e) => setCustomText(e.target.value)}
              placeholder="e.g.&#10;Dr. Rajesh Sharma, MD&#10;Rx:&#10;1. Tab. Metformin 500mg 1-0-1 After Food for 1 month&#10;2. Tab. Telmisartan 40mg 1-0-0 (OD) Before Food&#10;3. Tab. Pantoprazole 40mg 1-0-0 Empty stomach for 14 days"
              className="w-full bg-slate-900 border border-white/10 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 font-mono"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={handleParseCustomText}
                disabled={parsingText || !customText.trim()}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 font-bold text-xs flex items-center space-x-2 disabled:opacity-50"
              >
                <Sparkles className={`h-3.5 w-3.5 ${parsingText ? 'animate-spin' : ''}`} />
                <span>{parsingText ? 'Parsing...' : 'Extract Medications'}</span>
              </button>
            </div>
          </div>
        )}

        {/* Document Selector Bar */}
        <div className="glass-card p-4 rounded-2xl border border-cyan-500/20 bg-gradient-to-r from-slate-950/80 to-cyan-950/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex-1 flex flex-col sm:flex-row sm:items-center gap-2.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5 whitespace-nowrap">
              <Pill className="h-4 w-4 text-cyan-400" />
              <span>Select Prescription:</span>
            </label>
            <select
              value={selectedReportId}
              onChange={(e) => setSelectedReportId(e.target.value)}
              disabled={loadingReports || reportsList.length === 0}
              className="w-full sm:max-w-md bg-slate-900/90 text-white text-xs border border-white/10 rounded-xl px-3 py-2.5 focus:outline-none focus:border-cyan-400 transition"
            >
              {loadingReports ? (
                <option value="">Loading prescriptions...</option>
              ) : reportsList.length === 0 ? (
                <option value="">No prescriptions found. Please upload a prescription or paste text.</option>
              ) : (
                reportsList.map((rep) => (
                  <option key={rep.id} value={rep.id}>
                    {rep.title} ({rep.report_date || rep.created_at?.slice(0, 10) || 'Recent'})
                  </option>
                ))
              )}
            </select>
          </div>

          <div className="text-xs text-slate-400 flex items-center space-x-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
            <span>{prescription?.total_medications_count || 0} active medication(s)</span>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="print:hidden glass-card p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-3">
          <AlertTriangle className="h-5 w-5 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="glass-card p-12 rounded-3xl border border-white/10 text-center space-y-4">
          <RefreshCw className="h-8 w-8 text-cyan-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Parsing prescription & structuring medication schedule...</p>
        </div>
      )}

      {/* ========================================================================= */}
      {/* PRESCRIPTION SCHEDULE & PILL PLANNER CONTAINER */}
      {/* ========================================================================= */}
      {!loading && prescription && (
        <div className="space-y-6">
          {/* Prescription Metadata Card */}
          <div className="glass-card p-5 sm:p-6 rounded-3xl border border-white/10 bg-[#0a0f1d]/90 flex flex-col md:flex-row md:items-center justify-between gap-4 print:bg-white print:text-slate-900 print:border-slate-300">
            <div className="space-y-1.5">
              <div className="flex items-center space-x-2">
                <Stethoscope className="h-5 w-5 text-teal-400 print:text-slate-800" />
                <h2 className="text-base font-bold text-white print:text-slate-900">
                  {prescription.doctor_name || 'Prescribing Physician'}
                </h2>
                {prescription.clinic_name && (
                  <span className="text-xs text-slate-400 print:text-slate-600 font-normal">
                    • {prescription.clinic_name}
                  </span>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 print:text-slate-600">
                {prescription.patient_name && (
                  <span>Patient: <strong className="text-white print:text-slate-900">{prescription.patient_name}</strong>
                    {prescription.patient_age && ` (${prescription.patient_age} yrs${prescription.patient_gender ? `, ${prescription.patient_gender}` : ''})`}
                  </span>
                )}
                <span>Date: <strong className="text-slate-300 print:text-slate-800">{prescription.prescription_date || 'Recent Visit'}</strong></span>
                {prescription.diagnosis && (
                  <span>Diagnosis: <strong className="text-teal-300 print:text-slate-800">{prescription.diagnosis}</strong></span>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <span className="px-3 py-1 rounded-xl bg-teal-500/10 print:bg-slate-100 text-teal-300 print:text-slate-800 font-mono text-xs border border-teal-500/30 print:border-slate-300">
                {prescription.total_medications_count} Prescribed Medicines
              </span>
            </div>
          </div>

          {/* Section 1: Daily Time-of-Day Schedule Visualizer (Interactive) */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-xs font-bold text-cyan-300 print:text-slate-900 uppercase tracking-wider">
              <Clock className="h-4 w-4 text-cyan-400 print:text-slate-700" />
              <span>Daily Medication Time Slots</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Morning Slot */}
              <div className="glass-card p-4 rounded-2xl border border-amber-500/20 bg-amber-950/10 space-y-3 print:bg-white print:border-slate-300">
                <div className="flex items-center justify-between border-b border-white/5 print:border-slate-200 pb-2">
                  <div className="flex items-center space-x-2">
                    <Sunrise className="h-5 w-5 text-amber-400 print:text-amber-600" />
                    <span className="text-xs font-bold text-white print:text-slate-900">Morning</span>
                  </div>
                  <span className="text-[10px] font-mono text-amber-300 print:text-amber-800">8:00 AM</span>
                </div>

                {morningMeds.length === 0 ? (
                  <p className="text-[11px] text-slate-500 py-3 text-center">No morning doses</p>
                ) : (
                  <div className="space-y-2.5">
                    {morningMeds.map((m, idx) => (
                      <div key={idx} className="p-2.5 rounded-xl bg-white/[0.02] print:bg-slate-50 border border-white/5 print:border-slate-200 space-y-1">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-white print:text-slate-900">{m.medicine_name}</p>
                          <span className="text-[10px] font-mono text-amber-300 print:text-slate-800">{m.strength}</span>
                        </div>
                        <p className="text-[10px] text-slate-400 print:text-slate-600">{m.dosage}</p>
                        <div className="flex items-center justify-between text-[9px] pt-1">
                          <span className={`px-1.5 py-0.5 rounded font-bold ${
                            m.timing === 'Before Food' ? 'bg-amber-500/20 text-amber-300' : 'bg-teal-500/20 text-teal-300'
                          }`}>
                            {m.timing}
                          </span>
                          <span className="text-slate-400">{m.duration}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Afternoon Slot */}
              <div className="glass-card p-4 rounded-2xl border border-yellow-500/20 bg-yellow-950/10 space-y-3 print:bg-white print:border-slate-300">
                <div className="flex items-center justify-between border-b border-white/5 print:border-slate-200 pb-2">
                  <div className="flex items-center space-x-2">
                    <Sun className="h-5 w-5 text-yellow-400 print:text-yellow-600" />
                    <span className="text-xs font-bold text-white print:text-slate-900">Afternoon</span>
                  </div>
                  <span className="text-[10px] font-mono text-yellow-300 print:text-yellow-800">1:00 PM</span>
                </div>

                {afternoonMeds.length === 0 ? (
                  <p className="text-[11px] text-slate-500 py-3 text-center">No afternoon doses</p>
                ) : (
                  <div className="space-y-2.5">
                    {afternoonMeds.map((m, idx) => (
                      <div key={idx} className="p-2.5 rounded-xl bg-white/[0.02] print:bg-slate-50 border border-white/5 print:border-slate-200 space-y-1">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-white print:text-slate-900">{m.medicine_name}</p>
                          <span className="text-[10px] font-mono text-yellow-300 print:text-slate-800">{m.strength}</span>
                        </div>
                        <p className="text-[10px] text-slate-400 print:text-slate-600">{m.dosage}</p>
                        <div className="flex items-center justify-between text-[9px] pt-1">
                          <span className="px-1.5 py-0.5 rounded font-bold bg-teal-500/20 text-teal-300">
                            {m.timing}
                          </span>
                          <span className="text-slate-400">{m.duration}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Night Slot */}
              <div className="glass-card p-4 rounded-2xl border border-indigo-500/20 bg-indigo-950/10 space-y-3 print:bg-white print:border-slate-300">
                <div className="flex items-center justify-between border-b border-white/5 print:border-slate-200 pb-2">
                  <div className="flex items-center space-x-2">
                    <Moon className="h-5 w-5 text-indigo-400 print:text-indigo-600" />
                    <span className="text-xs font-bold text-white print:text-slate-900">Night / Dinner</span>
                  </div>
                  <span className="text-[10px] font-mono text-indigo-300 print:text-indigo-800">8:00 PM</span>
                </div>

                {nightMeds.length === 0 ? (
                  <p className="text-[11px] text-slate-500 py-3 text-center">No night doses</p>
                ) : (
                  <div className="space-y-2.5">
                    {nightMeds.map((m, idx) => (
                      <div key={idx} className="p-2.5 rounded-xl bg-white/[0.02] print:bg-slate-50 border border-white/5 print:border-slate-200 space-y-1">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-white print:text-slate-900">{m.medicine_name}</p>
                          <span className="text-[10px] font-mono text-indigo-300 print:text-slate-800">{m.strength}</span>
                        </div>
                        <p className="text-[10px] text-slate-400 print:text-slate-600">{m.dosage}</p>
                        <div className="flex items-center justify-between text-[9px] pt-1">
                          <span className="px-1.5 py-0.5 rounded font-bold bg-teal-500/20 text-teal-300">
                            {m.timing}
                          </span>
                          <span className="text-slate-400">{m.duration}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Bedtime Slot */}
              <div className="glass-card p-4 rounded-2xl border border-purple-500/20 bg-purple-950/10 space-y-3 print:bg-white print:border-slate-300">
                <div className="flex items-center justify-between border-b border-white/5 print:border-slate-200 pb-2">
                  <div className="flex items-center space-x-2">
                    <Bed className="h-5 w-5 text-purple-400 print:text-purple-600" />
                    <span className="text-xs font-bold text-white print:text-slate-900">Bedtime</span>
                  </div>
                  <span className="text-[10px] font-mono text-purple-300 print:text-purple-800">10:00 PM</span>
                </div>

                {bedtimeMeds.length === 0 ? (
                  <p className="text-[11px] text-slate-500 py-3 text-center">No bedtime doses</p>
                ) : (
                  <div className="space-y-2.5">
                    {bedtimeMeds.map((m, idx) => (
                      <div key={idx} className="p-2.5 rounded-xl bg-white/[0.02] print:bg-slate-50 border border-white/5 print:border-slate-200 space-y-1">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-white print:text-slate-900">{m.medicine_name}</p>
                          <span className="text-[10px] font-mono text-purple-300 print:text-slate-800">{m.strength}</span>
                        </div>
                        <p className="text-[10px] text-slate-400 print:text-slate-600">{m.dosage}</p>
                        <div className="flex items-center justify-between text-[9px] pt-1">
                          <span className="px-1.5 py-0.5 rounded font-bold bg-purple-500/20 text-purple-300">
                            {m.timing}
                          </span>
                          <span className="text-slate-400">{m.duration}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Section 2: Detailed Medication Directory Table */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-xs font-bold text-teal-300 print:text-slate-900 uppercase tracking-wider">
                <ListChecks className="h-4 w-4 text-teal-400 print:text-slate-700" />
                <span>Prescription Directory & Administration Rules</span>
              </div>
            </div>

            <div className="overflow-x-auto rounded-2xl border border-white/10 print:border-slate-300">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-white/5 print:bg-slate-100 text-[10px] uppercase tracking-wider text-slate-400 print:text-slate-700 border-b border-white/10 print:border-slate-300">
                    <th className="py-3 px-4">Medicine & Formulation</th>
                    <th className="py-3 px-4">Dosage / Strength</th>
                    <th className="py-3 px-4">Frequency</th>
                    <th className="py-3 px-4">Food Timing</th>
                    <th className="py-3 px-4">Duration</th>
                    <th className="py-3 px-4">Instructions</th>
                    <th className="py-3 px-4 print:hidden">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 print:divide-slate-200">
                  {prescription.medications.map((item, idx) => (
                    <tr key={idx} className="hover:bg-white/[0.02]">
                      <td className="py-3 px-4">
                        <p className="font-bold text-white print:text-slate-900">{item.medicine_name}</p>
                        {item.generic_name && (
                          <p className="text-[10px] text-slate-400 print:text-slate-600">{item.generic_name}</p>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-cyan-300 print:text-slate-800">
                        {item.strength} <span className="text-slate-400">({item.form})</span>
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-teal-300 print:text-slate-800">
                        {item.frequency}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white/5 print:bg-slate-100 border border-white/10 print:border-slate-300 text-slate-300 print:text-slate-800">
                          {item.timing}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-300 print:text-slate-700">{item.duration || 'N/A'}</td>
                      <td className="py-3 px-4 text-slate-400 print:text-slate-600 text-[11px]">
                        {item.instructions || 'Take as directed'}
                      </td>
                      <td className="py-3 px-4 print:hidden">
                        <button
                          onClick={() => handleDeleteMedication(item.id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
                          title="Remove Medication"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 3: Printable Weekly Pill Planner Card (Hidden on Screen, Crisp on Print) */}
          <div className="hidden print:block space-y-3 pt-4">
            <h3 className="text-xs font-bold text-slate-900 uppercase">Weekly Patient Intake Tracker (Mon - Sun)</h3>
            <table className="w-full text-left text-[10px] border-collapse border border-slate-300">
              <thead>
                <tr className="bg-slate-100 text-slate-700">
                  <th className="border border-slate-300 p-1.5">Medicine</th>
                  <th className="border border-slate-300 p-1.5">Dose & Timing</th>
                  <th className="border border-slate-300 p-1 text-center">Mon</th>
                  <th className="border border-slate-300 p-1 text-center">Tue</th>
                  <th className="border border-slate-300 p-1 text-center">Wed</th>
                  <th className="border border-slate-300 p-1 text-center">Thu</th>
                  <th className="border border-slate-300 p-1 text-center">Fri</th>
                  <th className="border border-slate-300 p-1 text-center">Sat</th>
                  <th className="border border-slate-300 p-1 text-center">Sun</th>
                </tr>
              </thead>
              <tbody>
                {prescription.medications.map((m, idx) => (
                  <tr key={idx}>
                    <td className="border border-slate-300 p-1.5 font-bold">{m.medicine_name} ({m.strength})</td>
                    <td className="border border-slate-300 p-1.5">{m.frequency} • {m.timing}</td>
                    {[0, 1, 2, 3, 4, 5, 6].map((day) => (
                      <td key={day} className="border border-slate-300 p-1 text-center">
                        <div className="h-3.5 w-3.5 border border-slate-400 mx-auto rounded-sm"></div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Section 4: Safety & Adherence Notice */}
          <div className="p-4 rounded-2xl bg-amber-500/5 print:bg-slate-50 border border-amber-500/20 print:border-slate-300 text-xs text-amber-200/90 print:text-slate-800 flex items-start space-x-3">
            <Info className="h-4 w-4 text-amber-400 print:text-slate-700 flex-shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              <strong className="text-amber-300 print:text-slate-900 font-semibold">Medication Safety Notice:</strong> Always confirm dosage and instructions with the original physical prescription or consulting pharmacist. Do not alter doses without physician guidance.
            </p>
          </div>
        </div>
      )}

      {/* Empty State when no prescription loaded */}
      {!loading && !prescription && (
        <div className="glass-card p-12 rounded-3xl border border-white/10 text-center space-y-4">
          <div className="h-16 w-16 rounded-3xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mx-auto text-purple-400">
            <Pill className="h-8 w-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white">No Prescriptions Selected</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Upload a doctor&apos;s prescription slip or paste handwritten Rx text above to view structured medicine names, dosages, meal timings, and daily pill schedules.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link
              href="/dashboard/upload"
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 hover:scale-105 transition"
            >
              <Plus className="h-4 w-4" />
              <span>Upload Prescription</span>
            </Link>
            <button
              onClick={() => setCustomTextMode(true)}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-white font-semibold text-xs hover:border-cyan-400 transition"
            >
              <Edit3 className="h-4 w-4 text-cyan-400" />
              <span>Paste Rx Text</span>
            </button>
          </div>
        </div>
      )}

      {/* Add Medication Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="glass-card p-6 rounded-3xl border border-cyan-500/30 max-w-md w-full space-y-4 bg-slate-950">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Pill className="h-4 w-4 text-cyan-400" />
                <span>Add Medication to Schedule</span>
              </h3>
              <button onClick={() => setIsAddModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleAddMedication} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-300 font-semibold block mb-1">Medicine Brand Name *</label>
                <input
                  type="text"
                  required
                  value={addForm.medicine_name}
                  onChange={(e) => setAddForm({ ...addForm, medicine_name: e.target.value })}
                  placeholder="e.g. Metformin / Dolo"
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-semibold block mb-1">Form</label>
                  <select
                    value={addForm.form}
                    onChange={(e) => setAddForm({ ...addForm, form: e.target.value })}
                    className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
                  >
                    <option value="Tablet">Tablet</option>
                    <option value="Capsule">Capsule</option>
                    <option value="Syrup">Syrup</option>
                    <option value="Injection">Injection</option>
                    <option value="Drops">Drops</option>
                    <option value="Inhaler">Inhaler</option>
                    <option value="Ointment">Ointment</option>
                  </select>
                </div>

                <div>
                  <label className="text-slate-300 font-semibold block mb-1">Strength</label>
                  <input
                    type="text"
                    value={addForm.strength}
                    onChange={(e) => setAddForm({ ...addForm, strength: e.target.value })}
                    placeholder="e.g. 500 mg, 40 mg"
                    className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-semibold block mb-1">Frequency</label>
                  <select
                    value={addForm.frequency}
                    onChange={(e) => setAddForm({ ...addForm, frequency: e.target.value })}
                    className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
                  >
                    <option value="1-0-1">1-0-1 (Twice Daily - BD)</option>
                    <option value="1-0-0">1-0-0 (Morning Only - OD)</option>
                    <option value="0-0-1">0-0-1 (Night Only)</option>
                    <option value="1-1-1">1-1-1 (Thrice Daily - TDS)</option>
                    <option value="1-1-1-1">1-1-1-1 (Four Times - QID)</option>
                    <option value="SOS">SOS (As Needed / Fever)</option>
                  </select>
                </div>

                <div>
                  <label className="text-slate-300 font-semibold block mb-1">Meal Timing</label>
                  <select
                    value={addForm.timing}
                    onChange={(e) => setAddForm({ ...addForm, timing: e.target.value })}
                    className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
                  >
                    <option value="After Food">After Food</option>
                    <option value="Before Food">Before Food</option>
                    <option value="Empty Stomach">Empty Stomach</option>
                    <option value="With Food">With Food</option>
                    <option value="At Bedtime">At Bedtime</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-semibold block mb-1">Duration</label>
                  <input
                    type="text"
                    value={addForm.duration}
                    onChange={(e) => setAddForm({ ...addForm, duration: e.target.value })}
                    placeholder="e.g. 5 days, 1 month"
                    className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
                  />
                </div>

                <div>
                  <label className="text-slate-300 font-semibold block mb-1">Generic Name</label>
                  <input
                    type="text"
                    value={addForm.generic_name}
                    onChange={(e) => setAddForm({ ...addForm, generic_name: e.target.value })}
                    placeholder="e.g. Paracetamol"
                    className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Special Instructions</label>
                <input
                  type="text"
                  value={addForm.instructions}
                  onChange={(e) => setAddForm({ ...addForm, instructions: e.target.value })}
                  placeholder="e.g. Take with warm water, avoid dairy"
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-white/10 text-slate-300 hover:bg-white/5"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20"
                >
                  Add to Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function PrescriptionsPage() {
  return (
    <Suspense
      fallback={
        <div className="glass-card p-12 rounded-3xl border border-white/10 text-center space-y-4">
          <RefreshCw className="h-8 w-8 text-cyan-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading Prescription & Pill Planner...</p>
        </div>
      }
    >
      <PrescriptionsContent />
    </Suspense>
  );
}
