import time
import uuid
from app.core.supabase_client import get_supabase_admin_client
from app.services.parser import medical_parser

def main():
    sb = get_supabase_admin_client()
    report_id = "f3b9c58a-202f-4136-908d-d8dd144033c8"
    
    for attempt in range(3):
        try:
            print(f"Fetching report (attempt {attempt+1})...")
            rep_res = sb.table("reports").select("*").eq("id", report_id).single().execute()
            rep = rep_res.data
            break
        except Exception as e:
            print(f"Fetch failed: {e}")
            time.sleep(2)
    else:
        print("Could not fetch report.")
        return

    text = rep.get("raw_ocr_text", "")
    parsed = medical_parser.parse_text(text)
    print(f"Parsed {len(parsed)} items from OCR text.")

    # Delete existing
    for attempt in range(3):
        try:
            sb.table("test_results").delete().eq("report_id", report_id).execute()
            print("Deleted old test results.")
            break
        except Exception as e:
            print(f"Delete failed: {e}")
            time.sleep(2)

    rows = []
    for p in parsed:
        rows.append({
            "id": str(uuid.uuid4()),
            "report_id": report_id,
            "user_id": rep["user_id"],
            "raw_test_name": p.raw_test_name,
            "normalized_name": p.normalized_name,
            "value_numeric": p.value_numeric,
            "value_text": p.value_text,
            "unit": p.unit,
            "reference_range_raw": p.reference_range_raw,
            "ref_min": p.ref_min,
            "ref_max": p.ref_max,
            "flag": p.flag,
            "ocr_confidence": p.ocr_confidence,
            "verification_status": p.verification_status,
        })

    for attempt in range(3):
        try:
            res = sb.table("test_results").insert(rows).execute()
            print(f"Successfully inserted {len(res.data)} clean test results into Supabase!")
            for item in res.data:
                print(f" - {item['normalized_name']}: {item['value_numeric']} {item['unit']} (Ref: {item['reference_range_raw']}, Flag: {item['flag']})")
            return
        except Exception as e:
            print(f"Insert failed: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
