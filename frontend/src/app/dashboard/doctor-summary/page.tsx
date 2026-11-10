'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import {
  api,
  ReportItem,
  DoctorSummaryResponse,
  DoctorQuestion,
  DoctorSummaryItem,
  DoctorLongitudinalShift,
} from '@/lib/api';
import {
  Stethoscope,
  FileText,
  Printer,
  Copy,
  Check,
  RefreshCw,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  Layers,
  ChevronRight,
  Globe,
  HelpCircle,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  Activity,
  ShieldAlert,
  Edit3,
  ListChecks,
  FileDown,
  Info,
  ExternalLink,
} from 'lucide-react';

function DoctorSummaryContent() {
  const { token, user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialReportId = searchParams.get('reportId') || '';

  // State
  const [reportsList, setReportsList] = useState<ReportItem[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>(initialReportId);
  const [language, setLanguage] = useState<'en' | 'ta' | 'hi'>('en');
  const [summaryData, setSummaryData] = useState<DoctorSummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingReports, setLoadingReports] = useState<boolean>(true);
  const [copied, setCopied] = useState<boolean>(false);
  const [checkedQuestions, setCheckedQuestions] = useState<Record<number, boolean>>({});
  const [patientCustomNotes, setPatientCustomNotes] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // 1. Fetch available user reports on mount
  useEffect(() => {
    if (!token) return;
    const fetchReports = async () => {
      setLoadingReports(true);
      try {
        const res = await api.getReports(token);
        const validReports = res.filter((r) => r.ocr_status === 'completed');
        setReportsList(validReports);

        if (!selectedReportId && validReports.length > 0) {
          setSelectedReportId(validReports[0].id);
        }
      } catch (err: any) {
        console.error('Failed to load reports:', err);
      } finally {
        setLoadingReports(false);
      }
    };
    fetchReports();
  }, [token]);

  // 2. Fetch Doctor Summary whenever selectedReportId or language changes
  useEffect(() => {
    if (!token || !selectedReportId) return;

    const fetchSummary = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getDoctorSummary(token, selectedReportId, language);
        setSummaryData(data);
      } catch (err: any) {
        console.error('Failed to generate doctor summary:', err);
        setError(err.message || 'Failed to generate clinical summary');
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [token, selectedReportId, language]);

  // Handle Question Checkbox
  const toggleQuestionCheck = (idx: number) => {
    setCheckedQuestions((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  // Copy Summary to Clipboard
  const handleCopySummary = () => {
    if (!summaryData) return;
    const textToCopy = `
CLINICAL VISIT SUMMARY - ${summaryData.report_title}
Date: ${summaryData.report_date || 'N/A'}
Language: ${language.toUpperCase()}

EXECUTIVE CLINICAL SUMMARY:
${summaryData.executive_clinical_summary}

KEY OUT-OF-RANGE PARAMETERS (${summaryData.abnormal_findings_count}):
${summaryData.key_abnormalities
  .map(
    (a) =>
      `• ${a.name}: ${a.value} ${a.unit} (Ref: ${a.reference_range}) [${a.flag}] - ${a.clinical_note || ''}`
  )
  .join('\n')}

PRIORITIZED DOCTOR QUESTIONS:
${summaryData.doctor_questions.map((q, i) => `${i + 1}. [${q.priority.toUpperCase()}] ${q.question}`).join('\n')}

PHYSICIAN CONSULTATION NOTES:
${summaryData.clinical_notes_for_physician}
    `.trim();

    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  // Handle Print Action
  const handlePrint = () => {
    window.print();
  };

  // Multilingual UI Strings
  const t = {
    en: {
      badge: 'Phase 12 Complete',
      title: 'Doctor Visit Summary & Multilingual Consultation Suite',
      subtitle:
        'Synthesizes multi-page laboratory diagnostics into a concise 1-page clinical briefing with prioritized consultation questions for physician appointments.',
      selectReport: 'Select Laboratory Report',
      noReportsFound: 'No completed reports found. Please upload a report first.',
      printBtn: 'Print / Save PDF (1-Page Brief)',
      copyBtn: 'Copy Brief to Clipboard',
      copied: 'Copied to Clipboard!',
      regenerate: 'Refresh Summary',
      patientInfo: 'Patient & Report Overview',
      patientEmail: 'Patient Identifier',
      reportTitle: 'Report Document',
      testDate: 'Collection / Test Date',
      generatedDate: 'Summary Generated',
      totalBiomarkers: 'Biomarkers Evaluated',
      abnormalBiomarkers: 'Out-of-Range Parameters',
      normalBiomarkers: 'Normal Baseline Parameters',
      execSummaryTitle: 'Executive Clinical Briefing',
      abnormalHeading: 'Flagged Out-of-Range Parameters (Requires Physician Review)',
      normalHeading: 'Stable Normal Physiological Biomarkers',
      longitudinalHeading: 'Longitudinal Biomarker Shifts (Multi-Report Trajectory)',
      questionsHeading: 'Prioritized Doctor Consultation Questions (Interactive Checklist)',
      questionsSubtitle:
        'Mark off the questions you wish to discuss with your doctor during your clinical appointment.',
      physicianNotesHeading: 'Physician Consultation & Prescription Notes (Ruled Area)',
      physicianNotesSubtitle: 'Dedicated space for your doctor to write diagnoses, Rx adjustments, and next retesting schedule.',
      patientNotesHeading: 'Patient Personal Notes & Symptoms',
      disclaimerTitle: 'Medical & Educational Health Literacy Disclaimer',
      disclaimerText:
        'This 1-page summary is generated by Medical OCR Simplifier 2.0 to enhance patient health literacy and doctor-patient communication. It does not constitute an independent medical diagnosis. All clinical decisions must be made in consultation with a qualified medical professional.',
      highPriority: 'HIGH PRIORITY',
      medPriority: 'TREND SHIFT',
      genPriority: 'LIFESTYLE & TIMELINE',
    },
    ta: {
      badge: 'கட்டம் 12 நிறைவுற்றது',
      title: 'மருத்துவர் ஆலோசனை சுருக்கம் & பன்மொழி மருத்துவ அறிக்கை',
      subtitle:
        'சிக்கலான ஆய்வக அறிக்கைகளை சுருக்கமான 1-பக்க மருத்துவ சுருக்கமாகவும், மருத்துவரிடம் கேட்க வேண்டிய முன்னுரிமை கேள்விகளாகவும் மாற்றுகிறது.',
      selectReport: 'மருத்துவ அறிக்கையைத் தேர்ந்தெடுக்கவும்',
      noReportsFound: 'முடிந்த அறிக்கைகள் எதுவும் கிடைக்கவில்லை. முதலில் பதிவேற்றவும்.',
      printBtn: 'அச்சிடுக / PDF ஆக சேமி (1-பக்க அறிக்கை)',
      copyBtn: 'சுருக்கத்தை நகலெடு',
      copied: 'நகலெடுக்கப்பட்டது!',
      regenerate: 'சுருக்கத்தைப் புதுப்பி',
      patientInfo: 'நோயாளி மற்றும் அறிக்கை விவரம்',
      patientEmail: 'நோயாளி அடையாளம்',
      reportTitle: 'அறிக்கை ஆவணம்',
      testDate: 'பரிசோதனை தேதி',
      generatedDate: 'உருவாக்கப்பட்ட தேதி',
      totalBiomarkers: 'மதிப்பாய்வு செய்யப்பட்ட சோதனைகள்',
      abnormalBiomarkers: 'வரம்பிற்கு வெளியே உள்ள சோதனைகள்',
      normalBiomarkers: 'சாதாரண வரம்பில் உள்ள சோதனைகள்',
      execSummaryTitle: 'மருத்துவ நிர்வாக சுருக்கம்',
      abnormalHeading: 'கவனிக்கப்பட வேண்டிய மாறுபட்ட சோதனைகள் (மருத்துவர் மதிப்பாய்வு தேவை)',
      normalHeading: 'சாதாரண ஆரோக்கியமான சோதனைகள்',
      longitudinalHeading: 'நீண்டகால மாற்றங்கள் (முந்தைய அறிக்கைகளுடன் ஒப்பீடு)',
      questionsHeading: 'மருத்துவரிடம் கேட்க வேண்டிய முன்னுரிமை கேள்விகள் (சரிபார்ப்புப் பட்டியல்)',
      questionsSubtitle:
        'உங்கள் மருத்துவ ஆலோசனையின் போது கேட்க விரும்பும் கேள்விகளை குறித்துக்கொள்ளவும்.',
      physicianNotesHeading: 'மருத்துவரின் ஆலோசனைக் குறிப்புகள் (குறிப்பு பகுதி)',
      physicianNotesSubtitle: 'மருத்துவர் மருந்து மாற்றங்கள் மற்றும் அடுத்த பரிசோதனை தேதியை எழுத பிரத்யேக பகுதி.',
      patientNotesHeading: 'நோயாளியின் சொந்தக் குறிப்புகள் மற்றும் அறிகுறிகள்',
      disclaimerTitle: 'மருத்துவ மற்றும் சுகாதார விழிப்புணர்வு மறுப்பு',
      disclaimerText:
        'இந்த சுருக்கம் நோயாளி விழிப்புணர்வுக்காக உருவாக்கப்பட்ட ஒரு கல்வி கருவியாகும். இது நேரடி மருத்துவ நோயறிதல் அல்ல. அனைத்து மருத்துவ முடிவுகளும் தகுதிவாய்ந்த மருத்துவருடன் கலந்தாலோசிக்கப்பட வேண்டும்.',
      highPriority: 'முக்கிய முன்னுரிமை',
      medPriority: 'போக்கு மாற்றம்',
      genPriority: 'வாழ்க்கை முறை & காலம்',
    },
    hi: {
      badge: 'चरण 12 पूर्ण',
      title: 'डॉक्टर परामर्श सारांश और बहुभाषी क्लिनिकल ब्रीफ',
      subtitle:
        'जटिल लैब रिपोर्टों को एक संक्षिप्त 1-पेज क्लिनिकल सारांश और डॉक्टर से पूछने योग्य प्राथमिक प्रश्नों में परिवर्तित करता है।',
      selectReport: 'मेडिकल रिपोर्ट चुनें',
      noReportsFound: 'कोई रिपोर्ट नहीं मिली। कृपया पहले रिपोर्ट अपलोड करें।',
      printBtn: 'प्रिंट करें / PDF सेव करें (1-पेज ब्रीफ)',
      copyBtn: 'सारांश कॉपी करें',
      copied: 'सफलतापूर्वक कॉपी किया गया!',
      regenerate: 'सारांश रीफ्रेश करें',
      patientInfo: 'मरीज एवं रिपोर्ट अवलोकन',
      patientEmail: 'मरीज पहचान',
      reportTitle: 'रिपोर्ट का नाम',
      testDate: 'परीक्षण तिथि',
      generatedDate: 'सारांश निर्माण तिथि',
      totalBiomarkers: 'कुल बायोमार्कर',
      abnormalBiomarkers: 'असामान्य बायोमार्कर',
      normalBiomarkers: 'सामान्य बायोमार्कर',
      execSummaryTitle: 'कार्यकारी क्लिनिकल सारांश',
      abnormalHeading: 'सामान्य सीमा से बाहर बायोमार्कर (डॉक्टर द्वारा समीक्षा आवश्यक)',
      normalHeading: 'सामान्य स्थिर बायोमार्कर',
      longitudinalHeading: 'दीर्घकालिक रुझान एवं बदलाव (पिछली रिपोर्ट से तुलना)',
      questionsHeading: 'डॉक्टर से पूछने योग्य प्राथमिकता वाले प्रश्न (चेकलिस्ट)',
      questionsSubtitle:
        'अपने डॉक्टर परामर्श के दौरान पूछे जाने वाले प्रश्नों को चिह्नित करें।',
      physicianNotesHeading: 'चिकित्सक परामर्श एवं प्रिस्क्रिप्शन नोट्स',
      physicianNotesSubtitle: 'डॉक्टर के लिए निदान, दवाओं में बदलाव और अगली जांच की तारीख लिखने के लिए समर्पित स्थान।',
      patientNotesHeading: 'मरीज के व्यक्तिगत नोट्स एवं लक्षण',
      disclaimerTitle: 'चिकित्सा एवं स्वास्थ्य साक्षरता अस्वीकरण',
      disclaimerText:
        'यह 1-पेज सारांश मरीज की स्वास्थ्य जागरूकता बढ़ाने के लिए तैयार किया गया है। यह प्रत्यक्ष चिकित्सीय निदान नहीं है। सभी निर्णय योग्य डॉक्टर से परामर्श करके ही लें।',
      highPriority: 'उच्च प्राथमिकता',
      medPriority: 'रुझान बदलाव',
      genPriority: 'जीवनशैली एवं समय',
    },
  }[language];

  return (
    <div className="space-y-6 pb-16">
      {/* Screen Controls Header (Hidden in Print Mode) */}
      <div className="print:hidden space-y-4">
        {/* Top Breadcrumb & Badge */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <Link href="/dashboard" className="hover:text-cyan-400 transition">
              Dashboard
            </Link>
            <ChevronRight className="h-3 w-3" />
            <span className="text-cyan-400 font-medium">Doctor Support Suite</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 flex items-center space-x-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>{t.badge}</span>
            </span>
          </div>
        </div>

        {/* Page Title & Intro */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold tracking-tight bg-gradient-to-r from-white via-cyan-100 to-teal-200 bg-clip-text text-transparent flex items-center gap-3">
              <Stethoscope className="h-7 w-7 text-cyan-400" />
              {t.title}
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
              {t.subtitle}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={handlePrint}
              disabled={!summaryData || loading}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold text-xs flex items-center space-x-2 shadow-lg shadow-cyan-500/20 transition disabled:opacity-50 cursor-pointer"
            >
              <Printer className="h-4 w-4" />
              <span>{t.printBtn}</span>
            </button>

            <button
              onClick={handleCopySummary}
              disabled={!summaryData || loading}
              className="px-3.5 py-2.5 rounded-xl glass-card hover:bg-white/10 text-slate-200 font-medium text-xs flex items-center space-x-2 border border-white/10 transition disabled:opacity-50 cursor-pointer"
            >
              {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4 text-slate-400" />}
              <span>{copied ? t.copied : t.copyBtn}</span>
            </button>
          </div>
        </div>

        {/* Control Bar: Report Dropdown & Language Switcher */}
        <div className="glass-card p-4 rounded-2xl border border-cyan-500/20 bg-gradient-to-r from-slate-950/80 to-cyan-950/20 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          {/* Report Selector */}
          <div className="flex-1 flex flex-col sm:flex-row sm:items-center gap-2.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5 whitespace-nowrap">
              <FileText className="h-4 w-4 text-cyan-400" />
              <span>{t.selectReport}:</span>
            </label>
            <select
              value={selectedReportId}
              onChange={(e) => setSelectedReportId(e.target.value)}
              disabled={loadingReports || reportsList.length === 0}
              className="w-full sm:max-w-md bg-slate-900/90 text-white text-xs border border-white/10 rounded-xl px-3 py-2.5 focus:outline-none focus:border-cyan-400 transition"
            >
              {loadingReports ? (
                <option value="">Loading laboratory reports...</option>
              ) : reportsList.length === 0 ? (
                <option value="">{t.noReportsFound}</option>
              ) : (
                reportsList.map((rep) => (
                  <option key={rep.id} value={rep.id}>
                    {rep.title} ({rep.report_date || rep.created_at?.slice(0, 10) || 'Recent'})
                  </option>
                ))
              )}
            </select>
          </div>

          {/* Multilingual Selector */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1 text-xs text-slate-400 mr-1">
              <Globe className="h-3.5 w-3.5 text-cyan-400" />
              <span className="hidden sm:inline">Language:</span>
            </div>
            <div className="inline-flex rounded-xl bg-slate-900/90 p-1 border border-white/10">
              <button
                type="button"
                onClick={() => setLanguage('en')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                  language === 'en'
                    ? 'bg-gradient-to-r from-cyan-500 to-teal-500 text-slate-950 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                English
              </button>
              <button
                type="button"
                onClick={() => setLanguage('ta')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                  language === 'ta'
                    ? 'bg-gradient-to-r from-cyan-500 to-teal-500 text-slate-950 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                தமிழ் (Tamil)
              </button>
              <button
                type="button"
                onClick={() => setLanguage('hi')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                  language === 'hi'
                    ? 'bg-gradient-to-r from-cyan-500 to-teal-500 text-slate-950 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                हिंदी (Hindi)
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="print:hidden glass-card p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-3">
          <AlertTriangle className="h-5 w-5 flex-shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="glass-card p-12 rounded-3xl border border-white/10 text-center space-y-4">
          <div className="inline-flex p-4 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 animate-spin">
            <RefreshCw className="h-8 w-8" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Generating Clinical Doctor Brief...</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
              Analyzing laboratory findings, detecting out-of-range parameters, calculating longitudinal shifts, and preparing prioritized consultation questions in {language.toUpperCase()}.
            </p>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 1-PAGE PRINTABLE CLINICAL CONSULTATION BRIEF */}
      {/* ========================================================================= */}
      {!loading && summaryData && (
        <div
          id="printable-doctor-brief"
          className="print:bg-white print:text-black print:p-0 print:border-none print:shadow-none glass-card p-6 md:p-8 rounded-3xl border border-white/10 space-y-6 bg-[#0a0f1d]/95"
        >
          {/* Header Banner */}
          <div className="border-b border-white/10 print:border-slate-300 pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center space-x-2">
                <span className="p-1.5 rounded-lg bg-teal-500/20 print:bg-slate-100 text-teal-300 print:text-slate-800">
                  <Stethoscope className="h-5 w-5" />
                </span>
                <h2 className="text-lg md:text-xl font-bold text-white print:text-slate-900 tracking-tight">
                  PHYSICIAN CONSULTATION & CLINICAL VISIT BRIEF
                </h2>
              </div>
              <p className="text-xs text-slate-400 print:text-slate-600 mt-1">
                Medical OCR Simplifier 2.0 • Patient Educational Summary & Question Checklist
              </p>
            </div>

            {/* Document Badges */}
            <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
              <span className="px-2.5 py-1 rounded-md bg-white/5 print:bg-slate-100 border border-white/10 print:border-slate-300 text-slate-300 print:text-slate-700">
                Lang: <strong className="uppercase">{summaryData.language}</strong>
              </span>
              <span className="px-2.5 py-1 rounded-md bg-cyan-500/10 print:bg-slate-100 border border-cyan-500/20 print:border-slate-300 text-cyan-300 print:text-slate-800">
                Engine: <strong>{summaryData.is_mock_fallback ? 'Clinical Rules Engine' : summaryData.model_used}</strong>
              </span>
            </div>
          </div>

          {/* Patient & Report Metadata Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-white/[0.02] print:bg-slate-50 p-4 rounded-2xl border border-white/5 print:border-slate-200">
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-400 print:text-slate-500">{t.patientEmail}</p>
              <p className="font-semibold text-white print:text-slate-900 truncate mt-0.5">
                {summaryData.patient_email || user?.email || 'Registered Patient'}
              </p>
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-400 print:text-slate-500">{t.reportTitle}</p>
              <p className="font-semibold text-white print:text-slate-900 truncate mt-0.5">
                {summaryData.report_title}
              </p>
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-400 print:text-slate-500">{t.testDate}</p>
              <p className="font-semibold text-white print:text-slate-900 mt-0.5">
                {summaryData.report_date || 'Current Panel'}
              </p>
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-400 print:text-slate-500">{t.generatedDate}</p>
              <p className="font-semibold text-white print:text-slate-900 mt-0.5">
                {summaryData.generated_at?.slice(0, 10) || new Date().toISOString().slice(0, 10)}
              </p>
            </div>
          </div>

          {/* KPI Snapshot Cards */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3.5 rounded-2xl bg-white/[0.03] print:bg-slate-50 border border-white/10 print:border-slate-300 text-center">
              <p className="text-[10px] font-semibold text-slate-400 print:text-slate-600 uppercase">{t.totalBiomarkers}</p>
              <p className="text-xl font-extrabold text-white print:text-slate-900 mt-0.5">{summaryData.total_findings_count}</p>
            </div>
            <div className="p-3.5 rounded-2xl bg-amber-500/10 print:bg-amber-50 border border-amber-500/20 print:border-amber-300 text-center">
              <p className="text-[10px] font-semibold text-amber-300 print:text-amber-800 uppercase">{t.abnormalBiomarkers}</p>
              <p className="text-xl font-extrabold text-amber-400 print:text-amber-900 mt-0.5">{summaryData.abnormal_findings_count}</p>
            </div>
            <div className="p-3.5 rounded-2xl bg-emerald-500/10 print:bg-emerald-50 border border-emerald-500/20 print:border-emerald-300 text-center">
              <p className="text-[10px] font-semibold text-emerald-300 print:text-emerald-800 uppercase">{t.normalBiomarkers}</p>
              <p className="text-xl font-extrabold text-emerald-400 print:text-emerald-900 mt-0.5">
                {summaryData.total_findings_count - summaryData.abnormal_findings_count}
              </p>
            </div>
          </div>

          {/* Section 1: Executive Clinical Summary */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-xs font-bold text-cyan-300 print:text-slate-900 uppercase tracking-wider">
              <Sparkles className="h-3.5 w-3.5 text-cyan-400 print:text-slate-700" />
              <span>{t.execSummaryTitle}</span>
            </div>
            <div className="p-4 rounded-2xl bg-white/[0.02] print:bg-slate-50 border border-white/10 print:border-slate-300 text-xs text-slate-200 print:text-slate-800 leading-relaxed">
              {summaryData.executive_clinical_summary}
            </div>
          </div>

          {/* Section 2: Flagged Abnormal Parameters Table */}
          {summaryData.key_abnormalities.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center space-x-2 text-xs font-bold text-amber-300 print:text-slate-900 uppercase tracking-wider">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-400 print:text-slate-700" />
                <span>{t.abnormalHeading}</span>
              </div>
              <div className="overflow-x-auto rounded-2xl border border-white/10 print:border-slate-300">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-white/5 print:bg-slate-100 text-[10px] uppercase tracking-wider text-slate-400 print:text-slate-700 border-b border-white/10 print:border-slate-300">
                      <th className="py-2.5 px-3">Biomarker / Test</th>
                      <th className="py-2.5 px-3">Result Value</th>
                      <th className="py-2.5 px-3">Standard Reference</th>
                      <th className="py-2.5 px-3">Clinical Flag</th>
                      <th className="py-2.5 px-3">Physiological System</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 print:divide-slate-200">
                    {summaryData.key_abnormalities.map((item, idx) => (
                      <tr key={idx} className="hover:bg-white/[0.02] print:hover:bg-transparent">
                        <td className="py-2.5 px-3 font-semibold text-white print:text-slate-900">{item.name}</td>
                        <td className="py-2.5 px-3 font-mono font-bold text-amber-300 print:text-slate-900">
                          {item.value} <span className="text-[10px] font-normal text-slate-400 print:text-slate-600">{item.unit}</span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-300 print:text-slate-700">{item.reference_range}</td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              item.flag === 'CRITICAL'
                                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30 print:bg-slate-200 print:text-rose-900'
                                : 'bg-amber-500/20 text-amber-300 border border-amber-500/30 print:bg-slate-200 print:text-amber-900'
                            }`}
                          >
                            {item.flag}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-400 print:text-slate-600 text-[11px]">{item.organs || 'General'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Section 3: Longitudinal Shifts (if any) */}
          {summaryData.longitudinal_shifts.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center space-x-2 text-xs font-bold text-cyan-300 print:text-slate-900 uppercase tracking-wider">
                <TrendingUp className="h-3.5 w-3.5 text-cyan-400 print:text-slate-700" />
                <span>{t.longitudinalHeading}</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {summaryData.longitudinal_shifts.map((shift, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-2xl bg-white/[0.02] print:bg-slate-50 border border-white/10 print:border-slate-300 flex items-center justify-between text-xs"
                  >
                    <div>
                      <p className="font-semibold text-white print:text-slate-900">{shift.biomarker}</p>
                      <p className="text-[10px] text-slate-400 print:text-slate-600 mt-0.5">
                        Baseline: {shift.earliest} {shift.unit} → Current: {shift.latest} {shift.unit}
                      </p>
                    </div>
                    <div className="text-right">
                      <span
                        className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold ${
                          shift.direction === 'improving'
                            ? 'bg-emerald-500/10 text-emerald-300 print:bg-emerald-100 print:text-emerald-900'
                            : shift.direction === 'concerning'
                            ? 'bg-rose-500/10 text-rose-300 print:bg-rose-100 print:text-rose-900'
                            : 'bg-slate-500/10 text-slate-300 print:bg-slate-200 print:text-slate-800'
                        }`}
                      >
                        {shift.direction === 'improving' ? (
                          <ArrowDownRight className="h-3 w-3" />
                        ) : shift.direction === 'concerning' ? (
                          <ArrowUpRight className="h-3 w-3" />
                        ) : null}
                        <span>
                          {shift.delta > 0 ? `+${shift.delta}` : shift.delta} {shift.unit} ({shift.delta_pct}%)
                        </span>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Section 4: Stable Normal Biomarkers */}
          {summaryData.key_normal_findings.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center space-x-2 text-xs font-bold text-emerald-400 print:text-slate-900 uppercase tracking-wider">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 print:text-slate-700" />
                <span>{t.normalHeading}</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {summaryData.key_normal_findings.map((item, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-xl bg-emerald-500/5 print:bg-slate-100 border border-emerald-500/20 print:border-slate-300 text-slate-300 print:text-slate-800 text-[11px] flex items-center space-x-1.5"
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 print:bg-emerald-600"></span>
                    <strong className="font-semibold text-white print:text-slate-900">{item.name}:</strong>
                    <span>
                      {item.value} {item.unit}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Section 5: Prioritized Doctor Consultation Questions (Interactive & Printable Checklist) */}
          <div className="space-y-3 pt-2">
            <div>
              <div className="flex items-center space-x-2 text-xs font-bold text-teal-300 print:text-slate-900 uppercase tracking-wider">
                <ListChecks className="h-4 w-4 text-teal-400 print:text-slate-700" />
                <span>{t.questionsHeading}</span>
              </div>
              <p className="text-[11px] text-slate-400 print:text-slate-600 mt-0.5">
                {t.questionsSubtitle}
              </p>
            </div>

            <div className="space-y-2.5">
              {summaryData.doctor_questions.map((q, idx) => {
                const isChecked = !!checkedQuestions[idx];
                const priorityBadge =
                  q.priority === 'high'
                    ? { text: t.highPriority, style: 'bg-rose-500/20 text-rose-300 border-rose-500/30 print:bg-slate-200 print:text-rose-900' }
                    : q.priority === 'medium'
                    ? { text: t.medPriority, style: 'bg-amber-500/20 text-amber-300 border-amber-500/30 print:bg-slate-200 print:text-amber-900' }
                    : { text: t.genPriority, style: 'bg-teal-500/20 text-teal-300 border-teal-500/30 print:bg-slate-200 print:text-teal-900' };

                return (
                  <div
                    key={idx}
                    onClick={() => toggleQuestionCheck(idx)}
                    className={`p-3.5 rounded-2xl border transition cursor-pointer flex items-start space-x-3.5 ${
                      isChecked
                        ? 'bg-teal-500/10 border-teal-500/30 print:bg-slate-100 print:border-slate-400'
                        : 'bg-white/[0.02] print:bg-white border-white/10 print:border-slate-300 hover:bg-white/5'
                    }`}
                  >
                    {/* Checkbox box */}
                    <div className="mt-0.5 flex-shrink-0">
                      <div
                        className={`h-4 w-4 rounded border flex items-center justify-center transition ${
                          isChecked
                            ? 'bg-teal-400 border-teal-400 text-slate-950 print:bg-slate-900 print:text-white'
                            : 'border-slate-500 print:border-slate-700 bg-transparent'
                        }`}
                      >
                        {isChecked && <Check className="h-3 w-3 stroke-[3]" />}
                      </div>
                    </div>

                    <div className="flex-1 space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold border ${priorityBadge.style}`}>
                          {priorityBadge.text}
                        </span>
                        <span className="text-[10px] text-slate-400 print:text-slate-500 font-mono">
                          {q.category}
                        </span>
                      </div>
                      <p className={`text-xs font-semibold leading-snug ${isChecked ? 'line-through text-slate-400 print:text-slate-500' : 'text-white print:text-slate-900'}`}>
                        {q.question}
                      </p>
                      {q.context && (
                        <p className="text-[11px] text-slate-400 print:text-slate-600">
                          {q.context}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>


          {/* Section 7: Legal Disclaimer */}
          <div className="pt-4 border-t border-white/10 print:border-slate-300 text-[10px] text-slate-400 print:text-slate-600 flex items-start space-x-2.5">
            <ShieldAlert className="h-4 w-4 text-amber-400 print:text-slate-700 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-slate-300 print:text-slate-800">{t.disclaimerTitle}</p>
              <p className="mt-0.5 leading-relaxed">{t.disclaimerText}</p>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !summaryData && !error && (
        <div className="glass-card p-12 rounded-3xl border border-white/10 text-center space-y-3">
          <Stethoscope className="h-10 w-10 text-cyan-400 mx-auto" />
          <h3 className="text-base font-bold text-white">Select a Report to Generate Doctor Brief</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Choose any completed laboratory report from your account to view a 1-page clinical briefing and prioritized consultation questions.
          </p>
        </div>
      )}
    </div>
  );
}

export default function DoctorSummaryPage() {
  return (
    <Suspense
      fallback={
        <div className="glass-card p-12 rounded-3xl border border-white/10 text-center space-y-4">
          <RefreshCw className="h-8 w-8 text-cyan-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading Doctor Visit Suite...</p>
        </div>
      }
    >
      <DoctorSummaryContent />
    </Suspense>
  );
}
