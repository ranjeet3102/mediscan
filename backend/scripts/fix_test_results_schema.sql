-- ============================================================================
-- Medical OCR Platform - test_results Table Schema Fix
-- Run this in Supabase Dashboard > SQL Editor > New Query
-- ============================================================================
-- Adds missing columns to test_results that are required for confidence
-- verification and normalization features to store results correctly.
-- Safe to run multiple times (uses IF NOT EXISTS pattern).
-- ============================================================================

-- Add composite_confidence column (stores multi-factor confidence score 0-100)
ALTER TABLE public.test_results
ADD COLUMN IF NOT EXISTS composite_confidence FLOAT DEFAULT 95.0;

-- Add verification_status column
ALTER TABLE public.test_results
ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'verified';

-- Add verification_reason column
ALTER TABLE public.test_results
ADD COLUMN IF NOT EXISTS verification_reason TEXT;

-- Add is_outlier flag column
ALTER TABLE public.test_results
ADD COLUMN IF NOT EXISTS is_outlier BOOLEAN DEFAULT FALSE;

-- Add normalized_name column (canonical biomarker name after normalization)
ALTER TABLE public.test_results
ADD COLUMN IF NOT EXISTS normalized_name TEXT;

-- Add ref_min / ref_max numeric columns for reference interval bounds
ALTER TABLE public.test_results
ADD COLUMN IF NOT EXISTS ref_min FLOAT;

ALTER TABLE public.test_results
ADD COLUMN IF NOT EXISTS ref_max FLOAT;

-- Add reference_range_raw column (raw text of reference range from the report)
ALTER TABLE public.test_results
ADD COLUMN IF NOT EXISTS reference_range_raw TEXT;

-- Add flag column (NORMAL, LOW, HIGH, CRITICAL, UNCERTAIN)
ALTER TABLE public.test_results
ADD COLUMN IF NOT EXISTS flag TEXT DEFAULT 'NORMAL';

-- Add ocr_confidence column (Tesseract word-level confidence for this result)
ALTER TABLE public.test_results
ADD COLUMN IF NOT EXISTS ocr_confidence FLOAT DEFAULT 95.0;

-- Add value_text column (for qualitative results like NEGATIVE, POSITIVE)
ALTER TABLE public.test_results
ADD COLUMN IF NOT EXISTS value_text TEXT;

-- Add value_numeric column (for quantitative numeric result values)
ALTER TABLE public.test_results
ADD COLUMN IF NOT EXISTS value_numeric FLOAT;

-- Add unit column (measurement unit like g/dL, mg/dL, %)
ALTER TABLE public.test_results
ADD COLUMN IF NOT EXISTS unit TEXT;

-- Verify the final schema
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'test_results'
ORDER BY ordinal_position;
