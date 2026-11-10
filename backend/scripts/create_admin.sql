-- ============================================================================
-- Medical OCR & Health Literacy Platform
-- Single Administrator Provisioning SQL Script
-- ============================================================================
-- Description:
-- In accordance with medical privacy & zero-PHI compliance requirements,
-- administrator accounts CANNOT be created via the public frontend/API.
-- Admins must be provisioned directly in Supabase using the queries below.
--
-- How to run:
-- 1. Open your Supabase Dashboard: https://supabase.com/dashboard/project/yifyjtejxrqlexuupgal
-- 2. Go to SQL Editor -> New Query
-- 3. Paste and run this script.
-- ============================================================================

-- Ensure pgcrypto extension is available for secure password hashing
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- OPTION 1: Create a Brand New Administrator Account Directly in SQL
-- ============================================================================
DO $$
DECLARE
    v_admin_id UUID := '18c60302-1240-4bee-a9d8-b9b487777789'::UUID;
    v_admin_email TEXT := 'admin@medicalocr.com';
    v_admin_password TEXT := 'AdminSecurePass123!';
    v_encrypted_pw TEXT;
BEGIN
    -- Hash the password using Blowfish crypt (compatible with Supabase Auth / GoTrue)
    v_encrypted_pw := crypt(v_admin_password, gen_salt('bf'));

    -- 1. Insert or update in auth.users
    IF NOT EXISTS (SELECT 1 FROM auth.users WHERE email = v_admin_email) THEN
        INSERT INTO auth.users (
            instance_id,
            id,
            aud,
            role,
            email,
            encrypted_password,
            email_confirmed_at,
            raw_app_meta_data,
            raw_user_meta_data,
            created_at,
            updated_at
        ) VALUES (
            '00000000-0000-0000-0000-000000000000',
            v_admin_id,
            'authenticated',
            'authenticated',
            v_admin_email,
            v_encrypted_pw,
            now(),
            '{"provider": "email", "providers": ["email"], "role": "admin"}'::jsonb,
            '{"role": "admin", "preferred_language": "en", "full_name": "System Administrator"}'::jsonb,
            now(),
            now()
        );
        RAISE NOTICE 'Admin user % created in auth.users with ID %', v_admin_email, v_admin_id;
    ELSE
        UPDATE auth.users
        SET encrypted_password = v_encrypted_pw,
            email_confirmed_at = COALESCE(email_confirmed_at, now()),
            raw_user_meta_data = raw_user_meta_data || '{"role": "admin", "full_name": "System Administrator"}'::jsonb,
            raw_app_meta_data = raw_app_meta_data || '{"role": "admin"}'::jsonb,
            updated_at = now()
        WHERE email = v_admin_email;
        RAISE NOTICE 'Admin user % updated in auth.users', v_admin_email;
    END IF;

    -- 2. Upsert into public.profiles
    INSERT INTO public.profiles (id, email, role, preferred_language, updated_at)
    VALUES (
        (SELECT id FROM auth.users WHERE email = v_admin_email),
        v_admin_email,
        'admin',
        'en',
        now()
    )
    ON CONFLICT (id) DO UPDATE
    SET role = 'admin',
        email = EXCLUDED.email,
        updated_at = now();

    RAISE NOTICE 'Admin profile synchronized in public.profiles for %', v_admin_email;
END $$;

-- ============================================================================
-- OPTION 2: Promote Any Existing User to Administrator by Email
-- ============================================================================
-- To promote an existing user who registered as a patient:
--
-- UPDATE public.profiles
-- SET role = 'admin', updated_at = now()
-- WHERE email = 'target_email@medicalocr.com';
--
-- UPDATE auth.users
-- SET raw_user_meta_data = raw_user_meta_data || '{"role": "admin"}'::jsonb,
--     raw_app_meta_data = raw_app_meta_data || '{"role": "admin"}'::jsonb,
--     updated_at = now()
-- WHERE email = 'target_email@medicalocr.com';
-- ============================================================================

-- Verification query: inspect all current administrators
SELECT 
    p.id,
    p.email,
    p.role,
    p.preferred_language,
    u.email_confirmed_at,
    p.created_at
FROM public.profiles p
LEFT JOIN auth.users u ON u.id = p.id
WHERE p.role = 'admin';
