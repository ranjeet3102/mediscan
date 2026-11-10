-- ==============================================================================
-- Medical Report Simplifier 2.0 - Storage Bucket & Storage RLS Configuration
-- File: supabase/migrations/00002_storage_setup.sql
-- ==============================================================================

-- 1. Create Private Storage Bucket for Medical Reports
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'medical-reports',
    'medical-reports',
    false, -- STRICT PRIVACY: Private bucket requiring authenticated signed URLs
    26214400, -- 25 MB in bytes
    ARRAY[
        'application/pdf',
        'image/png',
        'image/jpeg',
        'image/jpg',
        'image/tiff',
        'image/webp'
    ]
)
ON CONFLICT (id) DO UPDATE SET
    public = false,
    file_size_limit = 26214400,
    allowed_mime_types = ARRAY[
        'application/pdf',
        'image/png',
        'image/jpeg',
        'image/jpg',
        'image/tiff',
        'image/webp'
    ];

-- ==============================================================================
-- 2. Storage Row-Level Security (RLS) Policies
-- Enforces that patients can only read, upload, and delete objects stored in
-- their own user directory: medical-reports/{user_id}/*
-- ==============================================================================

-- Policy: Users can view/download only their own uploaded medical files
DROP POLICY IF EXISTS "Users can read own medical reports" ON storage.objects;
CREATE POLICY "Users can read own medical reports"
    ON storage.objects FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'medical-reports'
        AND (auth.uid()::text = (storage.foldername(name))[1])
    );

-- Policy: Users can upload files only into their own user folder
DROP POLICY IF EXISTS "Users can upload own medical reports" ON storage.objects;
CREATE POLICY "Users can upload own medical reports"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'medical-reports'
        AND (auth.uid()::text = (storage.foldername(name))[1])
    );

-- Policy: Users can update/replace files only in their own user folder
DROP POLICY IF EXISTS "Users can update own medical reports" ON storage.objects;
CREATE POLICY "Users can update own medical reports"
    ON storage.objects FOR UPDATE
    TO authenticated
    USING (
        bucket_id = 'medical-reports'
        AND (auth.uid()::text = (storage.foldername(name))[1])
    );

-- Policy: Users can delete files only in their own user folder
DROP POLICY IF EXISTS "Users can delete own medical reports" ON storage.objects;
CREATE POLICY "Users can delete own medical reports"
    ON storage.objects FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'medical-reports'
        AND (auth.uid()::text = (storage.foldername(name))[1])
    );
