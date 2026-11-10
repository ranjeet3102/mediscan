from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# ==========================================
# Authentication & User Profile Schemas
# ==========================================

class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    full_name: Optional[str] = Field(None, description="User's full name (e.g. 'John Doe')")
    role: Optional[str] = Field("user", description="'user' or 'admin'")
    preferred_language: Optional[str] = Field("en", description="'en', 'ta', or 'hi'")

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str = "user"
    preferred_language: str = "en"
    created_at: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
    expires_in: Optional[int] = 3600

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, description="User's full name")
    preferred_language: Optional[str] = Field(None, description="'en', 'ta', or 'hi'")
    role: Optional[str] = Field(None, description="'user' or 'admin'")

# ==========================================
# Generic API Responses
# ==========================================

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

# ==========================================
# Admin & Analytics Schemas (Zero-PHI)
# ==========================================

class AdminStatsResponse(BaseModel):
    total_users: int = 0
    active_users: int = 0
    total_reports_processed: int = 0
    ocr_requests_count: int = 0
    ai_requests_count: int = 0
    average_processing_time_ms: float = 0.0
    api_success_rate: float = 100.0
    storage_used_mb: float = 0.0
    system_status: str = "operational"

class SystemHealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "2.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database_connected: bool = False
    supabase_configured: bool = False
    tesseract_available: bool = False
    ollama_available: bool = False
    llm_provider: str = "ollama"  # 'groq' | 'ollama' | 'fallback'

class TelemetryTimeSeriesPoint(BaseModel):
    time: str
    timestamp: str
    ocr_requests: int = 0
    ai_queries: int = 0
    total_events: int = 0
    avg_latency_ms: float = 0.0

class TelemetryModuleBreakdownItem(BaseModel):
    module_name: str
    event_count: int = 0
    percentage: float = 0.0
    avg_latency_ms: float = 0.0
    success_rate: float = 100.0

class TelemetryEventItem(BaseModel):
    id: str
    event_type: str
    duration_ms: float = 0.0
    status: str = "success"
    token_count: int = 0
    created_at: str

class AdminTelemetryOverviewResponse(BaseModel):
    stats: AdminStatsResponse
    health: SystemHealthResponse
    time_series: List[TelemetryTimeSeriesPoint] = []
    breakdown: List[TelemetryModuleBreakdownItem] = []
    recent_events: List[TelemetryEventItem] = []

# ==========================================
# Admin User Management Schemas
# ==========================================

class AdminUserRecord(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str = "user"
    preferred_language: str = "en"
    created_at: Optional[str] = None
    last_sign_in_at: Optional[str] = None
    is_active: bool = True

class AdminUserSessionRecord(BaseModel):
    id: str
    user_id: str
    email: str
    event: str                      # "login" | "logout"
    occurred_at: str
    ip_address: Optional[str] = None

class AdminCreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    role: str = Field("user", description="'user' or 'admin'")
    preferred_language: str = "en"

class AdminUpdateUserRoleRequest(BaseModel):
    role: str = Field(..., description="'user' or 'admin'")

# ==========================================
# Report & Ingestion Schemas
# ==========================================

class ReportBase(BaseModel):
    title: str
    report_type: str = Field("lab_report", description="'lab_report', 'prescription', 'radiology', 'other'")
    report_date: Optional[str] = None

class ReportResponse(BaseModel):
    id: str
    user_id: str
    title: str
    file_url: str
    file_type: str
    report_type: str
    report_date: Optional[str] = None
    ocr_status: str = "pending"
    summary: Optional[str] = None
    signed_url: Optional[str] = None
    created_at: Optional[datetime] = None

class ReportDetailResponse(ReportResponse):
    raw_ocr_text: Optional[str] = None
    test_results_count: int = 0

# ==========================================
# Structured Clinical Test Result Schemas
# ==========================================

class TestResultBase(BaseModel):
    raw_test_name: str
    normalized_name: str
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    reference_range_raw: Optional[str] = None
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    flag: str = Field("NORMAL", description="'NORMAL', 'LOW', 'HIGH', 'CRITICAL', 'UNCERTAIN'")
    ocr_confidence: Optional[float] = 95.0
    composite_confidence: Optional[float] = 95.0
    verification_status: str = Field("verified", description="'verified', 'needs_review', 'user_corrected'")
    verification_reason: Optional[str] = None
    is_outlier: Optional[bool] = False

class TestResultResponse(TestResultBase):
    id: str
    report_id: str
    user_id: str
    created_at: Optional[datetime] = None

class TestResultUpdateRequest(BaseModel):
    normalized_name: Optional[str] = None
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    reference_range_raw: Optional[str] = None
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    flag: Optional[str] = None
    verification_status: Optional[str] = "user_corrected"

class VerificationSummaryResponse(BaseModel):
    report_id: str
    total_biomarkers: int = 0
    verified_count: int = 0
    needs_review_count: int = 0
    outlier_count: int = 0
    average_composite_confidence: float = 0.0
    average_ocr_confidence: float = 0.0
    results: List[TestResultResponse] = []

# ==========================================
# Grounded AI Explanation Schemas (Phase 8)
# ==========================================

class GroundedBiomarkerCitation(BaseModel):
    biomarker_name: str
    measured_value: str
    unit: Optional[str] = None
    reference_interval: Optional[str] = None
    flag: str = "NORMAL"
    clinical_meaning: str
    organs_involved: Optional[str] = None

class ReportExplanationResponse(BaseModel):
    report_id: str
    title: str
    language: str = "en"
    executive_summary: str
    normal_findings_summary: str
    abnormal_findings_summary: str
    doctor_questions: List[str] = []
    citations: List[GroundedBiomarkerCitation] = []
    disclaimer: str
    model_used: str = "llama3:latest"
    is_mock_fallback: bool = False
    generated_at: Optional[str] = None

class OllamaStatusResponse(BaseModel):
    available: bool = False
    model: str = "llama3:latest"
    available_models: List[str] = []
    ollama_url: str = "http://localhost:11434"
    provider: str = "ollama"  # 'groq' | 'ollama' | 'fallback'

# ==========================================
# "Ask My Report" Conversational Q&A Schemas (Phase 9)
# ==========================================

class ChatMessage(BaseModel):
    role: str = "user"  # 'user' | 'assistant' | 'system'
    content: str
    timestamp: Optional[str] = None
    sources: Optional[List[str]] = []

class ChatRequest(BaseModel):
    message: str
    language: str = "en"
    conversation_id: Optional[str] = None
    preferred_model: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    report_id: str
    reply: ChatMessage
    messages: List[ChatMessage] = []
    cited_biomarkers: List[str] = []
    suggested_followups: List[str] = []
    model_used: str = "llama3:latest"
    is_mock_fallback: bool = False

class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    report_id: str
    messages: List[ChatMessage] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# ==========================================
# Longitudinal Trends & Multi-Report Comparison Schemas (Phase 10)
# ==========================================

class BiomarkerDataPoint(BaseModel):
    report_id: str
    report_title: str
    report_date: Optional[str] = None
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    reference_range_raw: Optional[str] = None
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    flag: str = "NORMAL"

class BiomarkerTrendSeries(BaseModel):
    normalized_name: str
    unit: Optional[str] = None
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    data_points: List[BiomarkerDataPoint] = []
    latest_value: Optional[float] = None
    latest_flag: Optional[str] = None
    earliest_value: Optional[float] = None
    overall_change: Optional[float] = None
    overall_change_pct: Optional[float] = None
    trend_direction: str = "stable"  # 'improving', 'stable', 'concerning', 'elevated', 'declining'

class BiomarkerComparisonItem(BaseModel):
    normalized_name: str
    unit: Optional[str] = None
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    reference_range_raw: Optional[str] = None
    report_a_value: Optional[float] = None
    report_a_text: Optional[str] = None
    report_a_flag: Optional[str] = None
    report_b_value: Optional[float] = None
    report_b_text: Optional[str] = None
    report_b_flag: Optional[str] = None
    delta_numeric: Optional[float] = None
    delta_pct: Optional[float] = None
    status_shift: str = "STABLE_NORMAL"
    clinical_interpretation: str = ""

class ReportComparisonRequest(BaseModel):
    report_a_id: str  # Baseline report
    report_b_id: str  # Follow-up report
    language: str = "en"
    preferred_model: Optional[str] = None

class ReportComparisonResponse(BaseModel):
    report_a_id: str
    report_a_title: str
    report_a_date: Optional[str] = None
    report_b_id: str
    report_b_title: str
    report_b_date: Optional[str] = None
    total_compared: int = 0
    improved_count: int = 0
    deteriorated_count: int = 0
    stable_count: int = 0
    items: List[BiomarkerComparisonItem] = []
    ai_summary: str = ""
    model_used: str = "llama3:latest"
    is_mock_fallback: bool = False

# ==========================================
# Doctor Support Suite & Multilingual Schemas (Phase 12)
# ==========================================

class DoctorQuestion(BaseModel):
    category: str
    question: str
    context: str
    priority: str = "general"  # 'high' | 'medium' | 'general'

class DoctorSummaryResponse(BaseModel):
    report_id: str
    report_title: str
    report_date: Optional[str] = None
    patient_email: Optional[str] = None
    language: str = "en"
    executive_clinical_summary: str
    abnormal_findings_count: int = 0
    total_findings_count: int = 0
    key_abnormalities: List[Dict[str, Any]] = []
    key_normal_findings: List[Dict[str, Any]] = []
    longitudinal_shifts: List[Dict[str, Any]] = []
    doctor_questions: List[DoctorQuestion] = []
    clinical_notes_for_physician: str = ""
    disclaimer: str = "Educational health literacy summary. Not a clinical diagnosis."
    model_used: str = "llama3:latest"
    is_mock_fallback: bool = False
    generated_at: Optional[str] = None

# ==========================================
# Prescription Parsing & Medication Schemas (Phase 11)
# ==========================================

class MedicationItem(BaseModel):
    id: Optional[str] = None
    prescription_id: Optional[str] = None
    report_id: Optional[str] = None
    medicine_name: str
    generic_name: Optional[str] = None
    form: Optional[str] = "Tablet"
    strength: Optional[str] = None
    dosage: Optional[str] = "1 Tablet"
    frequency: str = "1-0-1"
    timing: str = "After Food"
    duration: Optional[str] = None
    instructions: Optional[str] = None
    morning: bool = True
    afternoon: bool = False
    night: bool = True
    bedtime: bool = False
    confidence: float = 0.95
    created_at: Optional[str] = None

class MedicationCreateRequest(BaseModel):
    medicine_name: str
    generic_name: Optional[str] = None
    form: Optional[str] = "Tablet"
    strength: Optional[str] = None
    dosage: Optional[str] = "1 Tablet"
    frequency: str = "1-0-1"
    timing: str = "After Food"
    duration: Optional[str] = "7 days"
    instructions: Optional[str] = None

class PrescriptionParseRequest(BaseModel):
    raw_text: Optional[str] = None
    report_id: Optional[str] = None

class PrescriptionResponse(BaseModel):
    id: str
    report_id: str
    doctor_name: Optional[str] = None
    clinic_name: Optional[str] = None
    prescription_date: Optional[str] = None
    diagnosis: Optional[str] = None
    patient_name: Optional[str] = None
    patient_age: Optional[str] = None
    patient_gender: Optional[str] = None
    medications: List[MedicationItem] = []
    total_medications_count: int = 0
    parsed_at: str
    raw_text: Optional[str] = None





