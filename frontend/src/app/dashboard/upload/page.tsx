'use client';

import React, { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import {
  UploadCloud,
  FileText,
  FileCheck2,
  AlertCircle,
  CheckCircle2,
  Lock,
  ArrowRight,
  Sparkles,
  RefreshCw,
  X,
  File,
  ShieldCheck,
} from 'lucide-react';

const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25 MB
const ALLOWED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.webp'];

export default function UploadReportPage() {
  const { token } = useAuth();
  const router = useRouter();

  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [reportType, setReportType] = useState<'lab_report' | 'prescription' | 'radiology' | 'other'>('lab_report');
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStep, setUploadStep] = useState<number>(0);
  const [uploadSuccess, setUploadSuccess] = useState<boolean>(false);
  const [uploadedReportId, setUploadedReportId] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileValidation = (selectedFile: File) => {
    setError(null);
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(`File is too large (${(selectedFile.size / (1024 * 1024)).toFixed(1)}MB). Maximum allowed size is 25MB.`);
      return false;
    }
    const ext = '.' + selectedFile.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setError(`Unsupported file type '${ext}'. Please upload a PDF, PNG, JPG, or TIFF document.`);
      return false;
    }
    setFile(selectedFile);
    if (!title) {
      // Auto-populate title from file name
      const cleanTitle = selectedFile.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
      setTitle(cleanTitle.charAt(0).toUpperCase() + cleanTitle.slice(1));
    }
    return true;
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileValidation(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileValidation(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select or drop a medical report file.');
      return;
    }
    if (!title.trim()) {
      setError('Please provide a descriptive title for this document.');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadStep(1); // Step 1: Validating file

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title.trim());
      formData.append('report_type', reportType);
      formData.append('report_date', reportDate);

      // Simulate smooth step animation
      setTimeout(() => setUploadStep(2), 400); // Step 2: Encrypting & Uploading to Private Bucket
      
      const resp = await api.uploadReport(token || 'dev-user-token', formData);

      setUploadStep(3); // Step 3: Registered in PostgreSQL
      setUploadedReportId(resp.data.id);
      setUploadSuccess(true);
    } catch (err: any) {
      setError(err.message || 'Failed to upload report. Please check backend connection.');
    } finally {
      setUploading(false);
    }
  };

  const resetUpload = () => {
    setFile(null);
    setTitle('');
    setError(null);
    setUploadSuccess(false);
    setUploadStep(0);
    setUploadedReportId(null);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="glass-card p-6 sm:p-8 rounded-3xl border border-cyan-500/30 bg-gradient-to-r from-slate-900/90 via-cyan-950/20 to-slate-900/90">
        <div className="space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/20 border border-teal-500/40 text-teal-300 text-xs font-semibold">
            <Lock className="h-3 w-3 text-teal-400" />
            <span>Encrypted Private Storage Bucket</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            Upload Medical Report or Prescription
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 max-w-2xl">
            Securely upload diagnostic reports (PDF, PNG, JPG, TIFF). Your files are stored in isolated tenant storage with private signed URLs and prepared for confidence verification.
          </p>
        </div>
      </div>

      {uploadSuccess ? (
        /* Upload Success View */
        <div className="glass-card p-8 rounded-3xl border border-emerald-500/30 bg-emerald-950/10 text-center space-y-6 animate-fade-in">
          <div className="h-16 w-16 rounded-3xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center mx-auto text-emerald-400">
            <CheckCircle2 className="h-8 w-8" />
          </div>
          <div className="space-y-2 max-w-md mx-auto">
            <h2 className="text-xl font-bold text-white">Document Ingested Successfully!</h2>
            <p className="text-xs text-slate-300">
              <strong className="text-white">{title}</strong> has been encrypted and stored in your private storage. Ready for OCR preprocessing and structured extraction.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <button
              onClick={() =>
                router.push(
                  reportType === 'prescription'
                    ? `/dashboard/prescriptions?reportId=${uploadedReportId}`
                    : '/dashboard/reports'
                )
              }
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 flex items-center space-x-2 transition hover:scale-105"
            >
              <span>{reportType === 'prescription' ? 'View in Prescriptions' : 'View in My Reports'}</span>
              <ArrowRight className="h-4 w-4" />
            </button>
            <button
              onClick={resetUpload}
              className="px-6 py-3 rounded-xl bg-slate-900 border border-white/10 hover:border-white/20 text-slate-300 font-semibold text-xs flex items-center space-x-2 transition"
            >
              <RefreshCw className="h-4 w-4" />
              <span>{reportType === 'prescription' ? 'Upload Another Prescription' : 'Upload Another Report'}</span>
            </button>
          </div>
        </div>
      ) : (
        /* Upload Form */
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-3">
              <AlertCircle className="h-5 w-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Drag & Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`glass-card p-8 rounded-3xl border-2 border-dashed transition-all cursor-pointer text-center space-y-4 ${
              isDragging
                ? 'border-cyan-400 bg-cyan-950/30 scale-[1.01]'
                : file
                ? 'border-teal-500/50 bg-teal-950/20'
                : 'border-white/20 hover:border-cyan-400/60 hover:bg-slate-900/50'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,.png,.jpg,.jpeg,.tiff,.webp"
              className="hidden"
            />

            {file ? (
              <div className="flex flex-col items-center space-y-3">
                <div className="h-14 w-14 rounded-2xl bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-400">
                  <FileCheck2 className="h-7 w-7" />
                </div>
                <div>
                  <p className="text-sm font-bold text-white">{file.name}</p>
                  <p className="text-xs text-teal-400 font-mono mt-0.5">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB • Ready for ingestion
                  </p>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                  className="px-3 py-1 rounded-lg bg-slate-900 border border-white/10 text-slate-400 hover:text-rose-400 text-xs flex items-center space-x-1"
                >
                  <X className="h-3 w-3" />
                  <span>Remove file</span>
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center space-y-3">
                <div className="h-14 w-14 rounded-2xl bg-slate-900 border border-white/10 flex items-center justify-center text-cyan-400 shadow-inner">
                  <UploadCloud className="h-7 w-7" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">
                    Click to browse or drag and drop your report here
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Supports high-resolution PDF, PNG, JPG, JPEG, TIFF (Up to 25MB)
                  </p>
                </div>
                <div className="flex items-center space-x-2 pt-2">
                  {['PDF', 'PNG', 'JPG', 'TIFF'].map((fmt) => (
                    <span
                      key={fmt}
                      className="px-2 py-0.5 rounded-md bg-slate-900 border border-white/10 text-[10px] font-mono font-bold text-slate-400"
                    >
                      {fmt}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Document Metadata Form */}
          <div className="glass-card p-6 rounded-3xl space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">
              Document Metadata
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Title */}
              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Report Title *
                </label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Complete Blood Count (CBC) or Thyroid Profile"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-900/80 border border-white/10 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-cyan-400 transition"
                />
              </div>

              {/* Category */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Document Category
                </label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value as any)}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-900/80 border border-white/10 text-white text-xs focus:outline-none focus:border-cyan-400 transition"
                >
                  <option value="lab_report">Lab Diagnostic Report (Blood, Urine, etc.)</option>
                  <option value="prescription">Doctor Prescription / Medication</option>
                  <option value="radiology">Radiology / Scan Summary</option>
                  <option value="other">Other Medical Document</option>
                </select>
              </div>

              {/* Date */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Report Test Date
                </label>
                <input
                  type="date"
                  value={reportDate}
                  onChange={(e) => setReportDate(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-900/80 border border-white/10 text-white text-xs focus:outline-none focus:border-cyan-400 transition"
                />
              </div>
            </div>

            {/* Ingestion Steps Progress */}
            {uploading && (
              <div className="pt-4 space-y-2">
                <div className="flex items-center justify-between text-xs text-cyan-300 font-semibold">
                  <span>Ingestion Pipeline:</span>
                  <span>
                    {uploadStep === 1 && 'Validating file format & signatures...'}
                    {uploadStep === 2 && 'Encrypting & storing in private bucket...'}
                    {uploadStep === 3 && 'Recording metadata & generating signed URL...'}
                  </span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-white/10">
                  <div
                    className="bg-gradient-to-r from-teal-500 to-cyan-400 h-full transition-all duration-300"
                    style={{ width: `${(uploadStep / 3) * 100}%` }}
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={uploading || !file}
              className="w-full mt-2 py-3.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <ShieldCheck className="h-4 w-4" />
              <span>{uploading ? 'Processing Document Ingestion...' : 'Ingest Document & Securely Store'}</span>
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
