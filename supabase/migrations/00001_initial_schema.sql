-- ==============================================================================
-- Medical Report Simplifier 2.0 - Initial Supabase Database Schema & Migrations
-- File: supabase/migrations/00001_initial_schema.sql
-- ==============================================================================

-- 1. Enable Required PostgreSQL Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ==============================================================================
-- 2. Profiles Table (Extends Supabase Auth users)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    preferred_language TEXT NOT NULL DEFAULT 'en' CHECK (preferred_language IN ('en', 'ta', 'hi')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast role & email lookups
CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);

-- Trigger to auto-create profile on auth.user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, role, preferred_language)
    VALUES (NEW.id, NEW.email, 'user', 'en')
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ==============================================================================
-- 3. Reports Table (Uploaded documents & OCR tracking)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    file_url TEXT NOT NULL,
    file_type TEXT NOT NULL,
    report_type TEXT NOT NULL DEFAULT 'lab_report' CHECK (report_type IN ('lab_report', 'prescription', 'radiology', 'other')),
    report_date DATE,
    ocr_status TEXT NOT NULL DEFAULT 'pending' CHECK (ocr_status IN ('pending', 'processing', 'completed', 'failed')),
    raw_ocr_text TEXT,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reports_user_id ON public.reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_date ON public.reports(report_date);
CREATE INDEX IF NOT EXISTS idx_reports_ocr_status ON public.reports(ocr_status);

-- ==============================================================================
-- 4. Test Results Table (Structured clinical lab values)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES public.reports(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    raw_test_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    value_numeric NUMERIC,
    value_text TEXT,
    unit TEXT,
    reference_range_raw TEXT,
    ref_min NUMERIC,
    ref_max NUMERIC,
    flag TEXT NOT NULL DEFAULT 'NORMAL' CHECK (flag IN ('NORMAL', 'LOW', 'HIGH', 'CRITICAL', 'UNCERTAIN')),
    ocr_confidence NUMERIC(5, 2),
    verification_status TEXT NOT NULL DEFAULT 'verified' CHECK (verification_status IN ('verified', 'needs_review', 'user_corrected')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_test_results_report_id ON public.test_results(report_id);
CREATE INDEX IF NOT EXISTS idx_test_results_user_id ON public.test_results(user_id);
CREATE INDEX IF NOT EXISTS idx_test_results_normalized_name ON public.test_results(normalized_name);
CREATE INDEX IF NOT EXISTS idx_test_results_flag ON public.test_results(flag);

-- ==============================================================================
-- 5. Prescriptions Table (Parsed medication schedules)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.prescriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES public.reports(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    medicine_name TEXT NOT NULL,
    strength TEXT,
    dosage TEXT,
    frequency TEXT,
    timing TEXT,
    duration TEXT,
    instructions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prescriptions_report_id ON public.prescriptions(report_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_user_id ON public.prescriptions(user_id);

-- ==============================================================================
-- 6. Medical Glossary Table (Curated clinical dictionary + Vector Embeddings)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.medical_glossary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name TEXT UNIQUE NOT NULL,
    aliases TEXT[] NOT NULL DEFAULT '{}',
    category TEXT NOT NULL,
    definition TEXT NOT NULL,
    what_it_measures TEXT NOT NULL,
    patient_friendly_summary TEXT NOT NULL,
    standard_unit TEXT,
    typical_range_info TEXT,
    embedding vector(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_medical_glossary_canonical ON public.medical_glossary(canonical_name);
CREATE INDEX IF NOT EXISTS idx_medical_glossary_aliases ON public.medical_glossary USING GIN(aliases);

-- ==============================================================================
-- 7. Conversations Table ("Ask My Report" Multi-turn Chat)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES public.reports(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_report_id ON public.conversations(report_id);

-- ==============================================================================
-- 8. System Events Table (Admin Telemetry - STRICT ZERO PHI)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.system_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,  -- 'ocr_processed', 'ai_chat_completed', 'report_uploaded', etc.
    duration_ms INTEGER,
    status TEXT NOT NULL,       -- 'success', 'error'
    token_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_system_events_type ON public.system_events(event_type);
CREATE INDEX IF NOT EXISTS idx_system_events_created_at ON public.system_events(created_at);

-- ==============================================================================
-- 9. Row Level Security (RLS) Policies
-- ==============================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.test_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.prescriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medical_glossary ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_events ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can view and update only their own profile
CREATE POLICY "Users can view own profile" 
    ON public.profiles FOR SELECT 
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
    ON public.profiles FOR UPDATE 
    USING (auth.uid() = id);

-- Reports: Users can CRUD only their own reports
CREATE POLICY "Users can view own reports" 
    ON public.reports FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own reports" 
    ON public.reports FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own reports" 
    ON public.reports FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own reports" 
    ON public.reports FOR DELETE 
    USING (auth.uid() = user_id);

-- Test Results: Users can CRUD only their own test results
CREATE POLICY "Users can view own test results" 
    ON public.test_results FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own test results" 
    ON public.test_results FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own test results" 
    ON public.test_results FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own test results" 
    ON public.test_results FOR DELETE 
    USING (auth.uid() = user_id);

-- Prescriptions: Users can CRUD only their own prescriptions
CREATE POLICY "Users can view own prescriptions" 
    ON public.prescriptions FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own prescriptions" 
    ON public.prescriptions FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own prescriptions" 
    ON public.prescriptions FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own prescriptions" 
    ON public.prescriptions FOR DELETE 
    USING (auth.uid() = user_id);

-- Conversations: Users can CRUD only their own conversations
CREATE POLICY "Users can view own conversations" 
    ON public.conversations FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own conversations" 
    ON public.conversations FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own conversations" 
    ON public.conversations FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own conversations" 
    ON public.conversations FOR DELETE 
    USING (auth.uid() = user_id);

-- Medical Glossary: Read-only for authenticated users
CREATE POLICY "Authenticated users can read medical glossary" 
    ON public.medical_glossary FOR SELECT 
    TO authenticated 
    USING (true);

-- System Events: Admins can read telemetry; System/Server inserts telemetry
CREATE POLICY "Admins can view system telemetry" 
    ON public.system_events FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE public.profiles.id = auth.uid() 
            AND public.profiles.role = 'admin'
        )
    );

CREATE POLICY "Service can insert system events"
    ON public.system_events FOR INSERT
    WITH CHECK (true);
