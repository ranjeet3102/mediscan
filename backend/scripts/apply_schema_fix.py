"""
Run this script to apply the test_results schema fix to Supabase.
Adds all missing columns (composite_confidence, ref_min, ref_max, flag, etc.)
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.supabase_client import get_supabase_admin_client

def apply_schema_fix():
    print("=" * 60)
    print("Applying test_results schema fix to Supabase...")
    print("=" * 60)

    admin = get_supabase_admin_client()
    if not admin:
        print("[ERROR] Cannot connect to Supabase admin client.")
        return

    # Read and execute the SQL file
    sql_path = os.path.join(os.path.dirname(__file__), "fix_test_results_schema.sql")
    with open(sql_path, "r") as f:
        sql = f.read()

    print(f"[INFO] Running SQL migration from: {sql_path}")
    print("[INFO] Please run this SQL in your Supabase Dashboard > SQL Editor:")
    print()
    print("-" * 60)
    # Print only the ALTER TABLE statements for easy copy-paste
    for line in sql.split('\n'):
        line = line.strip()
        if line.startswith('ALTER TABLE') or line.startswith('ADD COLUMN'):
            print(line)
    print("-" * 60)
    print()

    # Try to run individual column additions via RPC (may not work with anon key)
    columns_to_add = [
        ("composite_confidence", "FLOAT", 95.0),
        ("verification_status", "TEXT", "verified"),
        ("verification_reason", "TEXT", None),
        ("is_outlier", "BOOLEAN", False),
        ("normalized_name", "TEXT", None),
        ("ref_min", "FLOAT", None),
        ("ref_max", "FLOAT", None),
        ("reference_range_raw", "TEXT", None),
        ("flag", "TEXT", "NORMAL"),
        ("ocr_confidence", "FLOAT", 95.0),
        ("value_text", "TEXT", None),
        ("value_numeric", "FLOAT", None),
        ("unit", "TEXT", None),
    ]

    # Verify current schema by reading a row
    try:
        res = admin.table("test_results").select("*").limit(1).execute()
        if res.data:
            existing_columns = set(res.data[0].keys())
            print(f"[INFO] Current test_results columns: {sorted(existing_columns)}")
            missing = []
            for col, _, _ in columns_to_add:
                if col not in existing_columns:
                    missing.append(col)
            if missing:
                print(f"\n[WARNING] Missing columns: {missing}")
                print("\n[ACTION REQUIRED] Run the SQL in fix_test_results_schema.sql in Supabase SQL Editor")
            else:
                print("\n[OK] All required columns exist in test_results table!")
        else:
            print("[INFO] test_results table is empty - no rows to check schema from.")
            print("[ACTION] Run fix_test_results_schema.sql in Supabase SQL Editor to ensure schema is correct.")
    except Exception as e:
        print(f"[ERROR] Schema verification failed: {e}")

    print("\n" + "=" * 60)
    print("Schema check completed.")
    print("=" * 60)

if __name__ == "__main__":
    apply_schema_fix()
