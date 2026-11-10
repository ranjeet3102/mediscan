import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.supabase_client import get_supabase_admin_client, get_supabase_client, is_supabase_configured

def audit_supabase():
    print("=" * 70)
    print("SUPABASE LIVE DATABASE & AUTH AUDIT")
    print("=" * 70)
    print(f"Supabase Configured: {is_supabase_configured()}")
    print(f"Supabase URL:        {settings.SUPABASE_URL}")
    print("=" * 70)

    admin_client = get_supabase_admin_client()
    supabase = get_supabase_client()

    if not admin_client:
        print("[ERROR] Cannot connect to Supabase Admin Client. Check SERVICE_ROLE_KEY.")
        return

    # 1. Audit Auth Users
    print("\n--- 1. SUPABASE AUTH USERS (auth.users) ---")
    try:
        users = admin_client.auth.admin.list_users()
        print(f"Total Registered Auth Users: {len(users)}")
        for u in users:
            meta = getattr(u, "user_metadata", {}) or {}
            print(f"  • User ID: {u.id}")
            print(f"    Email:     {u.email}")
            print(f"    Confirmed: {getattr(u, 'email_confirmed_at', None) is not None}")
            print(f"    Metadata:  {meta}")
    except Exception as e:
        print(f"[ERROR] Listing auth users failed: {e}")

    # 2. Audit public.profiles Table
    print("\n--- 2. DATABASE PROFILES TABLE (public.profiles) ---")
    try:
        profiles_res = admin_client.table("profiles").select("*").execute()
        profiles = profiles_res.data or []
        print(f"Total Profiles in DB: {len(profiles)}")
        for p in profiles:
            print(f"  • Profile ID: {p.get('id')}")
            print(f"    Email:      {p.get('email')}")
            print(f"    Full Name:  {p.get('full_name')}")
            print(f"    Role:       {p.get('role')}")
            print(f"    Language:   {p.get('preferred_language')}")
            print(f"    Created At: {p.get('created_at')}")
    except Exception as e:
        print(f"[ERROR] Querying public.profiles failed: {e}")

    # 3. Audit Other Tables
    tables_to_check = ["reports", "test_results", "glossary_items", "system_events"]
    print("\n--- 3. DATABASE TABLES INTEGRITY & ROW COUNTS ---")
    for tbl in tables_to_check:
        try:
            res = admin_client.table(tbl).select("id", count="exact").limit(1).execute()
            count = res.count if hasattr(res, "count") and res.count is not None else len(res.data or [])
            print(f"  [OK] Table '{tbl}': Accessible (Rows: {count})")
        except Exception as e:
            print(f"  [WARN] Table '{tbl}': {e}")

    # 4. Audit Storage Buckets
    print("\n--- 4. SUPABASE STORAGE BUCKETS ---")
    try:
        buckets = admin_client.storage.list_buckets()
        print(f"Total Storage Buckets: {len(buckets)}")
        for b in buckets:
            print(f"  • Bucket: {b.name} (Public: {b.public})")
    except Exception as e:
        print(f"[ERROR] Listing storage buckets failed: {e}")

    # 5. Live Authentication Verification
    print("\n--- 5. LIVE END-TO-END AUTHENTICATION TEST ---")
    test_creds = [
        ("admin@medicalocr.com", "AdminSecurePass123!", "Admin"),
        ("patient@medicalocr.com", "PatientSecurePass123!", "Patient"),
    ]
    for email, password, label in test_creds:
        try:
            auth_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if auth_res and auth_res.session:
                token = auth_res.session.access_token
                user = auth_res.user
                print(f"  [SUCCESS] {label} ({email}) Logged In!")
                print(f"    - Access Token Length: {len(token)} chars")
                print(f"    - Supabase User ID:    {user.id}")
            else:
                print(f"  [FAIL] {label} ({email}) Sign in returned no session")
        except Exception as e:
            print(f"  [FAIL] {label} ({email}) Sign in error: {e}")

    print("\n" + "=" * 70)
    print("AUDIT COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    audit_supabase()
