import logging
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger("medical_ocr.supabase")

_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None

def is_supabase_configured() -> bool:
    """Check if Supabase URL and Key have been supplied with actual values."""
    url = settings.SUPABASE_URL
    key = settings.get_supabase_anon_key or settings.SUPABASE_SERVICE_ROLE_KEY
    return bool(
        url 
        and key 
        and not url.startswith("https://your-supabase") 
        and not key.startswith("your-supabase")
    )

def get_supabase_client() -> Client:
    """Get or initialize standard Supabase client for backend operations."""
    global _supabase_client
    if _supabase_client is None:
        try:
            key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.get_supabase_anon_key
            if key and settings.SUPABASE_URL:
                _supabase_client = create_client(settings.SUPABASE_URL, key)
        except Exception as e:
            logger.warning(f"Supabase client initialization warning: {e}. Running in local mock/unconnected mode.")
            _supabase_client = None
    return _supabase_client

def get_supabase_admin_client() -> Client:
    """Get or initialize Supabase Service Role client for elevated tasks (bypassing RLS)."""
    global _supabase_admin_client
    if _supabase_admin_client is None:
        try:
            key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.get_supabase_anon_key
            if key and settings.SUPABASE_URL:
                _supabase_admin_client = create_client(settings.SUPABASE_URL, key)
        except Exception as e:
            logger.warning(f"Supabase admin client initialization warning: {e}")
            _supabase_admin_client = None
    return _supabase_admin_client
