const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface UserProfile {
  id: string;
  email: string;
  full_name?: string;
  role: 'user' | 'admin';
  preferred_language: 'en' | 'ta' | 'hi';
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
  expires_in?: number;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  total_reports_processed: number;
  ocr_requests_count: number;
  ai_requests_count: number;
  average_processing_time_ms: number;
  api_success_rate: number;
  storage_used_mb: number;
  system_status: string;
}

export interface SystemHealth {
  status: string;
  version: string;
  timestamp: string;
  database_connected: boolean;
  supabase_configured: boolean;
  tesseract_available: boolean;
  ollama_available: boolean;
  llm_provider?: string;
}

export interface TelemetryTimeSeriesPoint {
  time: string;
  timestamp: string;
  ocr_requests: number;
  ai_queries: number;
  total_events: number;
  avg_latency_ms: number;
}

export interface TelemetryModuleBreakdownItem {
  module_name: string;
  event_count: number;
  percentage: number;
  avg_latency_ms: number;
  success_rate: number;
}

export interface TelemetryEventItem {
  id: string;
  event_type: string;
  duration_ms: number;
  status: string;
  token_count: number;
  created_at: string;
}

export interface AdminTelemetryOverview {
  stats: AdminStats;
  health: SystemHealth;
  time_series: TelemetryTimeSeriesPoint[];
  breakdown: TelemetryModuleBreakdownItem[];
  recent_events: TelemetryEventItem[];
}

export interface AdminUserRecord {
  id: string;
  email: string;
  full_name: string | null;
  role: 'user' | 'admin';
  preferred_language: string;
  created_at: string | null;
  last_sign_in_at: string | null;
  is_active: boolean;
}

export interface AdminUserSessionRecord {
  id: string;
  event_type: 'user_login' | 'user_logout';
  status: string;
  created_at: string;
  user_email?: string;
  user_id_ref?: string;
  duration_ms?: number;
}

export interface AdminCreateUserPayload {
  email: string;
  password: string;
  full_name?: string;
  role: 'user' | 'admin' | string;
  preferred_language: string;
}

export interface ReportItem {
  id: string;
  user_id: string;
  title: string;
  file_url: string;
  file_type: string;
  report_type: 'lab_report' | 'prescription' | 'radiology' | 'other';
  report_date?: string;
  ocr_status: 'pending' | 'processing' | 'completed' | 'failed';
  summary?: string;
  signed_url?: string;
  created_at?: string;
}

export interface ReportDetail extends ReportItem {
  raw_ocr_text?: string;
  test_results_count: number;
}

export interface TestResultItem {
  id: string;
  report_id: string;
  user_id: string;
  raw_test_name: string;
  normalized_name: string;
  value_numeric?: number;
  value_text?: string;
  unit?: string;
  reference_range_raw?: string;
  ref_min?: number;
  ref_max?: number;
  flag: 'NORMAL' | 'LOW' | 'HIGH' | 'CRITICAL' | 'UNCERTAIN';
  ocr_confidence: number;
  composite_confidence?: number;
  verification_status: 'verified' | 'needs_review' | 'user_corrected';
  verification_reason?: string;
  is_outlier?: boolean;
  created_at?: string;
}

export interface VerificationSummary {
  report_id: string;
  total_biomarkers: number;
  verified_count: number;
  needs_review_count: number;
  outlier_count: number;
  average_composite_confidence: number;
  average_ocr_confidence: number;
  results: TestResultItem[];
}

export interface GlossaryItem {
  canonical_name: string;
  aliases: string[];
  category: string;
  definition: string;
  what_it_measures: string;
  patient_friendly_summary: string;
  organs_involved: string;
  standard_unit: string;
  typical_range_info: string;
  high_value_meaning: string;
  low_value_meaning: string;
  similarity_score?: number;
}

export interface GroundedCitation {
  biomarker_name: string;
  measured_value: string;
  unit?: string;
  reference_interval?: string;
  flag: string;
  clinical_meaning: string;
  organs_involved?: string;
}

export interface ReportExplanation {
  report_id: string;
  title: string;
  language: string;
  executive_summary: string;
  normal_findings_summary: string;
  abnormal_findings_summary: string;
  doctor_questions: string[];
  citations: GroundedCitation[];
  disclaimer: string;
  model_used: string;
  is_mock_fallback: boolean;
  generated_at?: string;
}

export interface AIStatus {
  available: boolean;
  model: string;
  available_models: string[];
  ollama_url: string;
  provider?: 'groq' | 'ollama' | 'fallback' | string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  sources?: string[];
}

export interface ChatRequest {
  message: string;
  language?: string;
  conversation_id?: string;
  preferred_model?: string;
}

export interface ChatResponse {
  conversation_id: string;
  report_id: string;
  reply: ChatMessage;
  messages: ChatMessage[];
  cited_biomarkers: string[];
  suggested_followups: string[];
  model_used: string;
  is_mock_fallback: boolean;
}

export interface ConversationHistory {
  conversation_id: string;
  report_id: string;
  messages: ChatMessage[];
  created_at?: string;
  updated_at?: string;
}

// ==========================================
// Longitudinal Trends & Multi-Report Comparison Interfaces (Phase 10)
// ==========================================

export interface BiomarkerDataPoint {
  report_id: string;
  report_title: string;
  report_date?: string;
  value_numeric?: number;
  value_text?: string;
  unit?: string;
  reference_range_raw?: string;
  ref_min?: number;
  ref_max?: number;
  flag: string;
}

export interface BiomarkerTrendSeries {
  normalized_name: string;
  unit?: string;
  ref_min?: number;
  ref_max?: number;
  data_points: BiomarkerDataPoint[];
  latest_value?: number;
  latest_flag?: string;
  earliest_value?: number;
  overall_change?: number;
  overall_change_pct?: number;
  trend_direction: 'improving' | 'stable' | 'concerning' | 'elevated' | 'declining';
}

export interface BiomarkerComparisonItem {
  normalized_name: string;
  unit?: string;
  ref_min?: number;
  ref_max?: number;
  reference_range_raw?: string;
  report_a_value?: number;
  report_a_text?: string;
  report_a_flag?: string;
  report_b_value?: number;
  report_b_text?: string;
  report_b_flag?: string;
  delta_numeric?: number;
  delta_pct?: number;
  status_shift: string;
  clinical_interpretation: string;
}

export interface ReportComparisonRequest {
  report_a_id: string;
  report_b_id: string;
  language?: string;
  preferred_model?: string;
}

export interface ReportComparisonResponse {
  report_a_id: string;
  report_a_title: string;
  report_a_date?: string;
  report_b_id: string;
  report_b_title: string;
  report_b_date?: string;
  total_compared: number;
  improved_count: number;
  deteriorated_count: number;
  stable_count: number;
  items: BiomarkerComparisonItem[];
  ai_summary: string;
  model_used: string;
  is_mock_fallback: boolean;
}

// ==========================================
// Doctor Support Suite & Multilingual Interfaces (Phase 12)
// ==========================================

export interface DoctorQuestion {
  category: string;
  question: string;
  context: string;
  priority: 'high' | 'medium' | 'general';
}

export interface DoctorSummaryItem {
  name: string;
  value: string;
  unit: string;
  reference_range: string;
  flag: string;
  organs?: string;
  clinical_note?: string;
}

export interface DoctorLongitudinalShift {
  biomarker: string;
  earliest: number;
  latest: number;
  unit: string;
  delta: number;
  delta_pct?: number;
  direction: string;
}

export interface DoctorSummaryResponse {
  report_id: string;
  report_title: string;
  report_date?: string;
  patient_email?: string;
  language: string;
  executive_clinical_summary: string;
  abnormal_findings_count: number;
  total_findings_count: number;
  key_abnormalities: DoctorSummaryItem[];
  key_normal_findings: DoctorSummaryItem[];
  longitudinal_shifts: DoctorLongitudinalShift[];
  doctor_questions: DoctorQuestion[];
  clinical_notes_for_physician: string;
  disclaimer?: string;
  model_used: string;
  is_mock_fallback: boolean;
  generated_at?: string;
}

// ==========================================
// Prescription Parsing & Medication Interfaces (Phase 11)
// ==========================================

export interface MedicationItem {
  id?: string;
  prescription_id?: string;
  report_id?: string;
  medicine_name: string;
  generic_name?: string;
  form?: string;
  strength?: string;
  dosage?: string;
  frequency: string;
  timing: string;
  duration?: string;
  instructions?: string;
  morning: boolean;
  afternoon: boolean;
  night: boolean;
  bedtime: boolean;
  confidence?: number;
  created_at?: string;
}

export interface MedicationCreateRequest {
  medicine_name: string;
  generic_name?: string;
  form?: string;
  strength?: string;
  dosage?: string;
  frequency: string;
  timing: string;
  duration?: string;
  instructions?: string;
}

export interface PrescriptionResponse {
  id: string;
  report_id: string;
  doctor_name?: string;
  clinic_name?: string;
  prescription_date?: string;
  diagnosis?: string;
  patient_name?: string;
  patient_age?: string;
  patient_gender?: string;
  medications: MedicationItem[];
  total_medications_count: number;
  parsed_at: string;
  raw_text?: string;
}

export const api = {
  async getAuthHeaders(token?: string | null): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Login failed');
    }
    return res.json();
  },

  async signup(data: { email: string; password: string; full_name?: string; role?: string; preferred_language?: string }) {
    const res = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(err.detail || 'Registration failed');
    }
    return res.json();
  },

  async getMe(token: string): Promise<UserProfile> {
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: await this.getAuthHeaders(token),
    });
    if (!res.ok) throw new Error('Failed to retrieve user profile');
    return res.json();
  },

  async updateProfile(token: string, data: { preferred_language?: string; role?: string }) {
    const res = await fetch(`${API_BASE_URL}/auth/profile`, {
      method: 'PUT',
      headers: await this.getAuthHeaders(token),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update profile');
    return res.json();
  },

  async getAdminStats(token: string): Promise<AdminStats> {
    const res = await fetch(`${API_BASE_URL}/admin/stats`, {
      headers: await this.getAuthHeaders(token),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Unauthorized admin access' }));
      throw new Error(err.detail || 'Failed to fetch admin stats');
    }
    return res.json();
  },

  async getAdminHealth(token: string): Promise<SystemHealth> {
    const res = await fetch(`${API_BASE_URL}/admin/health`, {
      headers: await this.getAuthHeaders(token),
    });
    if (!res.ok) throw new Error('Failed to fetch system health');
    return res.json();
  },

  async getAdminTelemetryOverview(token: string): Promise<AdminTelemetryOverview> {
    const res = await fetch(`${API_BASE_URL}/admin/telemetry/overview`, {
      headers: await this.getAuthHeaders(token),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch admin telemetry overview' }));
      throw new Error(err.detail || 'Failed to fetch admin telemetry overview');
    }
    const json = await res.json();
    return json.data;
  },

  async getAdminTimeSeries(token: string, hours: number = 24): Promise<TelemetryTimeSeriesPoint[]> {
    const res = await fetch(`${API_BASE_URL}/admin/telemetry/timeseries?hours=${hours}`, {
      headers: await this.getAuthHeaders(token),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch time series telemetry' }));
      throw new Error(err.detail || 'Failed to fetch time series telemetry');
    }
    const json = await res.json();
    return json.data || [];
  },

  async getAdminBreakdown(token: string): Promise<TelemetryModuleBreakdownItem[]> {
    const res = await fetch(`${API_BASE_URL}/admin/telemetry/breakdown`, {
      headers: await this.getAuthHeaders(token),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch telemetry breakdown' }));
      throw new Error(err.detail || 'Failed to fetch telemetry breakdown');
    }
    const json = await res.json();
    return json.data || [];
  },

  async getAdminEvents(token: string, limit: number = 25): Promise<TelemetryEventItem[]> {
    const res = await fetch(`${API_BASE_URL}/admin/telemetry/events?limit=${limit}`, {
      headers: await this.getAuthHeaders(token),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch telemetry events' }));
      throw new Error(err.detail || 'Failed to fetch telemetry events');
    }
    const json = await res.json();
    return json.data || [];
  },

  async getAdminUsers(token: string): Promise<AdminUserRecord[]> {
    const res = await fetch(`${API_BASE_URL}/admin/users`, {
      headers: await this.getAuthHeaders(token),
    });
    const json = await res.json().catch(() => null);
    if (!res.ok || !json?.success) {
      throw new Error(json?.detail || json?.message || `Failed to fetch users (HTTP ${res.status})`);
    }
    return json.data || [];
  },

  async createAdminUser(token: string, payload: AdminCreateUserPayload): Promise<{ id: string; email: string; role: string }> {
    const res = await fetch(`${API_BASE_URL}/admin/users`, {
      method: 'POST',
      headers: await this.getAuthHeaders(token),
      body: JSON.stringify(payload),
    });
    const json = await res.json().catch(() => null);
    if (!res.ok || !json?.success) {
      throw new Error(json?.detail || json?.message || `Failed to create user (HTTP ${res.status})`);
    }
    return json.data;
  },

  async deleteAdminUser(token: string, userId: string): Promise<{ deleted_user_id: string }> {
    const res = await fetch(`${API_BASE_URL}/admin/users/${encodeURIComponent(userId)}`, {
      method: 'DELETE',
      headers: await this.getAuthHeaders(token),
    });
    const json = await res.json().catch(() => null);
    if (!res.ok || !json?.success) {
      throw new Error(json?.detail || json?.message || `Failed to delete user (HTTP ${res.status})`);
    }
    return json.data;
  },

  async updateAdminUserRole(token: string, userId: string, role: 'user' | 'admin'): Promise<{ user_id: string; new_role: string }> {
    const res = await fetch(`${API_BASE_URL}/admin/users/${encodeURIComponent(userId)}/role`, {
      method: 'PATCH',
      headers: await this.getAuthHeaders(token),
      body: JSON.stringify({ role }),
    });
    const json = await res.json().catch(() => null);
    if (!res.ok || !json?.success) {
      throw new Error(json?.detail || json?.message || `Failed to update user role (HTTP ${res.status})`);
    }
    return json.data;
  },

  async getAdminUserSessions(token: string, limit: number = 100): Promise<AdminUserSessionRecord[]> {
    const res = await fetch(`${API_BASE_URL}/admin/users/sessions?limit=${limit}`, {
      headers: await this.getAuthHeaders(token),
    });
    const json = await res.json().catch(() => null);
    if (!res.ok || !json?.success) {
      throw new Error(json?.detail || json?.message || `Failed to fetch session log (HTTP ${res.status})`);
    }
    return json.data || [];
  },

  // ==========================================
  // Report API Methods
  // ==========================================

  async uploadReport(token: string, formData: FormData): Promise<{ success: boolean; message: string; data: ReportItem }> {
    const res = await fetch(`${API_BASE_URL}/reports/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to upload report' }));
      throw new Error(err.detail || 'Failed to upload report');
    }
    return res.json();
  },

  async getReports(token: string): Promise<ReportItem[]> {
    const res = await fetch(`${API_BASE_URL}/reports/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch reports' }));
      throw new Error(err.detail || 'Failed to fetch reports');
    }
    return res.json();
  },

  async getReport(token: string, id: string): Promise<ReportDetail> {
    const res = await fetch(`${API_BASE_URL}/reports/${id}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to retrieve report' }));
      throw new Error(err.detail || 'Failed to retrieve report');
    }
    return res.json();
  },

  async deleteReport(token: string, id: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE_URL}/reports/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to delete report' }));
      throw new Error(err.detail || 'Failed to delete report');
    }
    return res.json();
  },

  // ==========================================
  // OCR & Preprocessing Methods
  // ==========================================

  async processReportOCR(token: string, reportId: string): Promise<{
    success: boolean;
    message: string;
    data: {
      report_id: string;
      raw_ocr_text: string;
      average_confidence: number;
      overall_status: string;
      total_pages: number;
      low_confidence_count: number;
    };
  }> {
    const res = await fetch(`${API_BASE_URL}/ocr/process-report/${reportId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'OCR processing failed' }));
      throw new Error(err.detail || 'OCR processing failed');
    }
    return res.json();
  },

  async previewPreprocess(token: string, formData: FormData): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/ocr/preview-preprocess`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to preview preprocessing' }));
      throw new Error(err.detail || 'Failed to preview preprocessing');
    }
    return res.json();
  },

  // ==========================================
  // Structured Clinical Extraction Methods
  // ==========================================

  async extractStructuredTestResults(token: string, reportId: string): Promise<{
    success: boolean;
    message: string;
    data: {
      report_id: string;
      total_extracted: number;
      results: TestResultItem[];
    };
  }> {
    const res = await fetch(`${API_BASE_URL}/reports/${reportId}/extract-structured`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Structured extraction failed' }));
      throw new Error(err.detail || 'Structured extraction failed');
    }
    return res.json();
  },

  async getReportTestResults(token: string, reportId: string): Promise<TestResultItem[]> {
    const res = await fetch(`${API_BASE_URL}/reports/${reportId}/test-results`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch structured test results' }));
      throw new Error(err.detail || 'Failed to fetch structured test results');
    }
    return res.json();
  },

  async updateTestResult(token: string, resultId: string, updateData: Partial<TestResultItem>): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE_URL}/reports/test-results/${resultId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(updateData),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to update test result' }));
      throw new Error(err.detail || 'Failed to update test result');
    }
    return res.json();
  },

  async getVerificationSummary(token: string, reportId: string): Promise<VerificationSummary> {
    const res = await fetch(`${API_BASE_URL}/reports/${reportId}/verification-summary`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch verification summary' }));
      throw new Error(err.detail || 'Failed to fetch verification summary');
    }
    return res.json();
  },

  // ==========================================
  // Medical Glossary & Knowledge Base Methods
  // ==========================================

  async searchGlossary(token: string, query: string, limit: number = 5): Promise<GlossaryItem[]> {
    const res = await fetch(`${API_BASE_URL}/glossary/search?q=${encodeURIComponent(query)}&limit=${limit}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Glossary search failed' }));
      throw new Error(err.detail || 'Glossary search failed');
    }
    const json = await res.json();
    return json.data?.results || [];
  },

  async getGlossaryItem(token: string, canonicalName: string): Promise<GlossaryItem> {
    const res = await fetch(`${API_BASE_URL}/glossary/item/${encodeURIComponent(canonicalName)}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to load glossary item' }));
      throw new Error(err.detail || 'Failed to load glossary item');
    }
    const json = await res.json();
    return json.data;
  },

  async getGlossaryCategories(token: string): Promise<{ total_categories: number; categories: Record<string, any[]> }> {
    const res = await fetch(`${API_BASE_URL}/glossary/categories/all`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch glossary categories' }));
      throw new Error(err.detail || 'Failed to fetch glossary categories');
    }
    const json = await res.json();
    return json.data;
  },

  // ==========================================
  // Grounded AI Report Explanation Methods (Phase 8)
  // ==========================================

  async getAIStatus(token: string): Promise<AIStatus> {
    const res = await fetch(`${API_BASE_URL}/ai/status`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      return {
        available: false,
        model: 'llama3:latest',
        available_models: [],
        ollama_url: 'http://localhost:11434',
      };
    }
    const json = await res.json();
    return json.data;
  },

  async generateReportExplanation(
    token: string,
    reportId: string,
    language: string = 'en',
    model?: string
  ): Promise<ReportExplanation> {
    const modelParam = model ? `&model=${encodeURIComponent(model)}` : '';
    const res = await fetch(`${API_BASE_URL}/reports/${reportId}/explain?language=${encodeURIComponent(language)}${modelParam}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to generate AI report explanation' }));
      throw new Error(err.detail || 'Failed to generate AI report explanation');
    }
    const json = await res.json();
    return json.data;
  },

  async getReportExplanation(
    token: string,
    reportId: string,
    language: string = 'en'
  ): Promise<ReportExplanation> {
    const res = await fetch(`${API_BASE_URL}/reports/${reportId}/explanation?language=${encodeURIComponent(language)}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to retrieve report explanation' }));
      throw new Error(err.detail || 'Failed to retrieve report explanation');
    }
    const json = await res.json();
    return json.data;
  },

  // ==========================================
  // "Ask My Report" Conversational Q&A Methods (Phase 9)
  // ==========================================

  async sendReportChatMessage(
    token: string,
    reportId: string,
    payload: ChatRequest
  ): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE_URL}/reports/${reportId}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to send chat message' }));
      throw new Error(err.detail || 'Failed to send chat message');
    }
    const json = await res.json();
    return json.data;
  },

  async getReportChatHistory(
    token: string,
    reportId: string
  ): Promise<ConversationHistory> {
    const res = await fetch(`${API_BASE_URL}/reports/${reportId}/chat`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to retrieve chat history' }));
      throw new Error(err.detail || 'Failed to retrieve chat history');
    }
    const json = await res.json();
    return json.data;
  },

  async clearReportChatHistory(
    token: string,
    reportId: string
  ): Promise<{ cleared: boolean; report_id: string }> {
    const res = await fetch(`${API_BASE_URL}/reports/${reportId}/chat`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to clear chat history' }));
      throw new Error(err.detail || 'Failed to clear chat history');
    }
    const json = await res.json();
    return json.data;
  },

  // ==========================================
  // Longitudinal Trends & Comparison Methods (Phase 10)
  // ==========================================

  async getBiomarkerTrends(
    token: string,
    biomarkerName?: string
  ): Promise<BiomarkerTrendSeries[]> {
    const query = biomarkerName ? `?biomarker_name=${encodeURIComponent(biomarkerName)}` : '';
    const res = await fetch(`${API_BASE_URL}/trends/biomarkers${query}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch biomarker trends' }));
      throw new Error(err.detail || 'Failed to fetch biomarker trends');
    }
    const json = await res.json();
    return json.data || [];
  },

  async getAvailableBiomarkerNames(
    token: string
  ): Promise<string[]> {
    const res = await fetch(`${API_BASE_URL}/trends/biomarker-names`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch available biomarker names' }));
      throw new Error(err.detail || 'Failed to fetch available biomarker names');
    }
    const json = await res.json();
    return json.data?.names || [];
  },

  async compareReports(
    token: string,
    payload: ReportComparisonRequest
  ): Promise<ReportComparisonResponse> {
    const res = await fetch(`${API_BASE_URL}/reports/compare`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to compare reports' }));
      throw new Error(err.detail || 'Failed to compare reports');
    }
    const json = await res.json();
    return json.data;
  },

  // ==========================================
  // Doctor Support Suite & Multilingual Methods (Phase 12)
  // ==========================================

  async getDoctorSummary(
    token: string,
    reportId: string,
    language: string = 'en',
    preferredModel?: string
  ): Promise<DoctorSummaryResponse> {
    const query = new URLSearchParams({ language });
    if (preferredModel) query.append('preferred_model', preferredModel);
    const res = await fetch(`${API_BASE_URL}/reports/${reportId}/doctor-summary?${query.toString()}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to retrieve doctor summary' }));
      throw new Error(err.detail || 'Failed to retrieve doctor summary');
    }
    const json = await res.json();
    return json.data;
  },

  async getDoctorQuestions(
    token: string,
    reportId: string,
    language: string = 'en'
  ): Promise<DoctorQuestion[]> {
    const res = await fetch(`${API_BASE_URL}/reports/${reportId}/doctor-questions?language=${encodeURIComponent(language)}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to retrieve doctor questions' }));
      throw new Error(err.detail || 'Failed to retrieve doctor questions');
    }
    const json = await res.json();
    return json.data || [];
  },

  // ==========================================
  // Prescription Parsing & Medication Methods (Phase 11)
  // ==========================================

  async parsePrescriptionText(
    token: string,
    rawText: string,
    reportId: string = 'adhoc-prescription'
  ): Promise<PrescriptionResponse> {
    const res = await fetch(`${API_BASE_URL}/prescriptions/parse-text`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ raw_text: rawText, report_id: reportId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to parse prescription text' }));
      throw new Error(err.detail || 'Failed to parse prescription text');
    }
    const json = await res.json();
    return json.data;
  },

  async parsePrescriptionReport(
    token: string,
    reportId: string
  ): Promise<PrescriptionResponse> {
    const res = await fetch(`${API_BASE_URL}/prescriptions/parse-report/${reportId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to parse prescription report' }));
      throw new Error(err.detail || 'Failed to parse prescription report');
    }
    const json = await res.json();
    return json.data;
  },

  async getPrescription(
    token: string,
    reportId: string
  ): Promise<PrescriptionResponse> {
    const res = await fetch(`${API_BASE_URL}/prescriptions/${reportId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to retrieve prescription' }));
      throw new Error(err.detail || 'Failed to retrieve prescription');
    }
    const json = await res.json();
    return json.data;
  },

  async addMedicationItem(
    token: string,
    reportId: string,
    payload: MedicationCreateRequest
  ): Promise<MedicationItem> {
    const res = await fetch(`${API_BASE_URL}/prescriptions/${reportId}/medications`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to add medication' }));
      throw new Error(err.detail || 'Failed to add medication');
    }
    const json = await res.json();
    return json.data;
  },

  async deleteMedicationItem(
    token: string,
    reportId: string,
    medId: string
  ): Promise<{ deleted: boolean; med_id: string }> {
    const res = await fetch(`${API_BASE_URL}/prescriptions/${reportId}/medications/${medId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to delete medication' }));
      throw new Error(err.detail || 'Failed to delete medication');
    }
    const json = await res.json();
    return json.data;
  },
};




