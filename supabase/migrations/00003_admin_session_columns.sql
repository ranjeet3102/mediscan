-- Add optional user_email and user_id_ref columns to system_events for Admin login/logout session log
ALTER TABLE public.system_events
    ADD COLUMN IF NOT EXISTS user_email TEXT,
    ADD COLUMN IF NOT EXISTS user_id_ref TEXT;

