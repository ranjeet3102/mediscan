import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.supabase_client import get_supabase_admin_client, is_supabase_configured

def remove_all_users():
    print("=" * 60)
    print("Supabase User Deletion Utility: Removing All Users")
    print("=" * 60)

    if not is_supabase_configured():
        print("[ERROR] Supabase is not configured.")
        return False

    admin_client = get_supabase_admin_client()
    if not admin_client:
        print("[ERROR] Could not initialize Supabase Admin Client (Service Role Key required).")
        return False

    # 1. Fetch all users from auth.users
    try:
        users = admin_client.auth.admin.list_users()
    except Exception as e:
        print(f"[ERROR] Failed to list auth users: {e}")
        return False

    total_users = len(users)
    print(f"[INFO] Found {total_users} user(s) in auth.users.")

    deleted_count = 0
    failed_count = 0

    for idx, u in enumerate(users, 1):
        uid = u.id
        email = getattr(u, "email", "No Email")
        try:
            admin_client.auth.admin.delete_user(uid)
            deleted_count += 1
            print(f"[{idx}/{total_users}] Deleted: {email} (ID: {uid})")
        except Exception as e:
            failed_count += 1
            print(f"[{idx}/{total_users}] Failed to delete {email} (ID: {uid}): {e}")

    # 2. Clean any orphaned profiles in public.profiles
    try:
        admin_client.table("profiles").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("[INFO] Cleaned public.profiles table.")
    except Exception as e:
        print(f"[WARN] Error cleaning public.profiles: {e}")

    # 3. Verify final count
    remaining_users = admin_client.auth.admin.list_users()
    remaining_profiles = admin_client.table("profiles").select("id", count="exact").execute()

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f" - Successfully deleted: {deleted_count} user(s)")
    print(f" - Failed deletions:     {failed_count} user(s)")
    print(f" - Remaining in auth.users:     {len(remaining_users)}")
    print(f" - Remaining in public.profiles: {len(remaining_profiles.data)}")
    print("=" * 60)
    return True

if __name__ == "__main__":
    remove_all_users()
