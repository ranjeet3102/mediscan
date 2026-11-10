import sys
import os

# Add backend directory to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.supabase_client import get_supabase_admin_client, get_supabase_client, is_supabase_configured

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin@123"
ADMIN_ROLE = "admin"
ADMIN_LANG = "en"

USER_EMAIL = "ranjeet@gmail.com"
USER_PASSWORD = "Ranjeet@123"
USER_ROLE = "user"
USER_LANG = "en"

def seed_account(admin_client, email, password, role, lang, full_name):
    print(f"\nSetting up account: {email} (role: {role})...")
    user_id = None
    try:
        users_list = admin_client.auth.admin.list_users()
        for u in users_list:
            if getattr(u, "email", "") == email:
                user_id = u.id
                print(f"[INFO] Found existing Supabase Auth user: {email} (ID: {user_id})")
                break
    except Exception as e:
        print(f"[WARN] Error listing users: {e}")

    if not user_id:
        try:
            res = admin_client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "role": role,
                    "preferred_language": lang,
                    "full_name": full_name,
                }
            })
            if res and res.user:
                user_id = res.user.id
                print(f"[SUCCESS] Created Supabase Auth user: {email} (ID: {user_id})")
        except Exception as e:
            print(f"[ERROR] Failed to create user {email}: {e}")
    else:
        try:
            admin_client.auth.admin.update_user_by_id(
                user_id,
                {
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {
                        "role": role,
                        "preferred_language": lang,
                        "full_name": full_name,
                    }
                }
            )
            print(f"[SUCCESS] Synced/updated credentials and metadata for user ID {user_id}")
        except Exception as e:
            print(f"[WARN] Error updating user attributes: {e}")

    if user_id:
        try:
            profile_data = {
                "id": user_id,
                "email": email,
                "role": role,
                "preferred_language": lang,
            }
            admin_client.table("profiles").upsert(profile_data).execute()
            print(f"[SUCCESS] Stored/updated profile in 'public.profiles': {email}")
        except Exception as e:
            print(f"[ERROR] Failed to upsert profile in 'public.profiles': {e}")

    return user_id

def setup_admin():
    print("=" * 60)
    print("Supabase Auth & Profiles Seed Script (Admin & Primary User)")
    print("=" * 60)
    
    print(f"Supabase Configured: {is_supabase_configured()}")
    print(f"Supabase URL: {settings.SUPABASE_URL}")
    
    admin_client = get_supabase_admin_client()
    if not admin_client:
        print("[ERROR] Could not initialize Supabase Admin Client (Service Role Key).")
        return False

    # 1. Admin Account
    admin_id = seed_account(
        admin_client,
        ADMIN_EMAIL,
        ADMIN_PASSWORD,
        ADMIN_ROLE,
        ADMIN_LANG,
        "Primary Platform Administrator"
    )

    # 2. Primary Patient Account
    user_id = seed_account(
        admin_client,
        USER_EMAIL,
        USER_PASSWORD,
        USER_ROLE,
        USER_LANG,
        "Demo Patient Account"
    )

    # 3. Verify Live Sign-Ins
    print("\nVerifying Live Supabase Auth Logins...")
    supabase_client = get_supabase_client()
    for em, pw, r in [(ADMIN_EMAIL, ADMIN_PASSWORD, "Admin"), (USER_EMAIL, USER_PASSWORD, "Patient")]:
        try:
            login_res = supabase_client.auth.sign_in_with_password({"email": em, "password": pw})
            if login_res.session:
                print(f"[SUCCESS] {r} login verified! Token length: {len(login_res.session.access_token)}")
        except Exception as e:
            print(f"[WARN] Verification login note for {em}: {e}")

    print("\n" + "=" * 60)
    print("LIVE SUPABASE CREDENTIALS FOR APPLICATION:")
    print("1. SYSTEM ADMINISTRATOR:")
    print(f"   Email:    {ADMIN_EMAIL}")
    print(f"   Password: {ADMIN_PASSWORD}")
    print(f"   Role:     {ADMIN_ROLE}")
    print("2. PATIENT USER:")
    print(f"   Email:    {USER_EMAIL}")
    print(f"   Password: {USER_PASSWORD}")
    print(f"   Role:     {USER_ROLE}")
    print("=" * 60)
    return True

if __name__ == "__main__":
    setup_admin()
