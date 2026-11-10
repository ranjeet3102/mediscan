import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.services.comparison_service import comparison_service
import app.api.v1.reports as rep_mod

client = TestClient(app)

def test_biomarker_trends_aggregation():
    user_id = "test-user-trends-1"
    report_a_id = "rep-trends-a"
    report_b_id = "rep-trends-b"

    # Seed mock reports and test results
    rep_mod._DEV_REPORTS_DB.extend([
        {
            "id": report_a_id,
            "user_id": user_id,
            "title": "Baseline Lab Panel",
            "report_date": "2025-01-15",
            "report_type": "lab_report",
            "ocr_status": "completed",
            "created_at": "2025-01-15T10:00:00Z",
        },
        {
            "id": report_b_id,
            "user_id": user_id,
            "title": "6-Month Follow-up Panel",
            "report_date": "2025-07-15",
            "report_type": "lab_report",
            "ocr_status": "completed",
            "created_at": "2025-07-15T10:00:00Z",
        }
    ])

    rep_mod._DEV_TEST_RESULTS_DB.extend([
        # Fasting Glucose: 135 -> 95 (Improved)
        {
            "id": "tr-1",
            "report_id": report_a_id,
            "user_id": user_id,
            "normalized_name": "Fasting Blood Glucose",
            "raw_test_name": "FBS",
            "value_numeric": 135.0,
            "unit": "mg/dL",
            "ref_min": 70.0,
            "ref_max": 99.0,
            "reference_range_raw": "70 - 99",
            "flag": "HIGH",
        },
        {
            "id": "tr-2",
            "report_id": report_b_id,
            "user_id": user_id,
            "normalized_name": "Fasting Blood Glucose",
            "raw_test_name": "FBS",
            "value_numeric": 95.0,
            "unit": "mg/dL",
            "ref_min": 70.0,
            "ref_max": 99.0,
            "reference_range_raw": "70 - 99",
            "flag": "NORMAL",
        },
        # Haemoglobin: 14.5 -> 14.2 (Stable Normal)
        {
            "id": "tr-3",
            "report_id": report_a_id,
            "user_id": user_id,
            "normalized_name": "Haemoglobin",
            "raw_test_name": "Hb",
            "value_numeric": 14.5,
            "unit": "g/dL",
            "ref_min": 13.0,
            "ref_max": 17.0,
            "reference_range_raw": "13.0 - 17.0",
            "flag": "NORMAL",
        },
        {
            "id": "tr-4",
            "report_id": report_b_id,
            "user_id": user_id,
            "normalized_name": "Haemoglobin",
            "raw_test_name": "Hb",
            "value_numeric": 14.2,
            "unit": "g/dL",
            "ref_min": 13.0,
            "ref_max": 17.0,
            "reference_range_raw": "13.0 - 17.0",
            "flag": "NORMAL",
        },
    ])

    trends = comparison_service.get_biomarker_trends(user_id=user_id)
    assert len(trends) == 2

    # Verify Fasting Glucose series
    fbs_trend = next((t for t in trends if t.normalized_name == "Fasting Blood Glucose"), None)
    assert fbs_trend is not None
    assert len(fbs_trend.data_points) == 2
    assert fbs_trend.earliest_value == 135.0
    assert fbs_trend.latest_value == 95.0
    assert fbs_trend.overall_change == -40.0
    assert fbs_trend.trend_direction == "improving"

    # Verify available biomarker names
    names = comparison_service.get_available_biomarkers(user_id=user_id)
    assert "Fasting Blood Glucose" in names
    assert "Haemoglobin" in names

def test_two_report_comparative_diff_engine():
    user_id = "test-user-compare-1"
    rep_a = "rep-comp-a"
    rep_b = "rep-comp-b"

    rep_mod._DEV_REPORTS_DB.extend([
        {
            "id": rep_a,
            "user_id": user_id,
            "title": "Annual Checkup 2024",
            "report_date": "2024-06-01",
            "report_type": "lab_report",
            "ocr_status": "completed",
            "created_at": "2024-06-01T10:00:00Z",
        },
        {
            "id": rep_b,
            "user_id": user_id,
            "title": "Annual Checkup 2025",
            "report_date": "2025-06-01",
            "report_type": "lab_report",
            "ocr_status": "completed",
            "created_at": "2025-06-01T10:00:00Z",
        }
    ])

    rep_mod._DEV_TEST_RESULTS_DB.extend([
        # Improved: TSH 6.8 -> 2.5
        {
            "id": "tr-comp-1",
            "report_id": rep_a,
            "user_id": user_id,
            "normalized_name": "Thyroid Stimulating Hormone (TSH)",
            "raw_test_name": "TSH",
            "value_numeric": 6.8,
            "unit": "uIU/mL",
            "reference_range_raw": "0.35 - 4.50",
            "flag": "HIGH",
        },
        {
            "id": "tr-comp-2",
            "report_id": rep_b,
            "user_id": user_id,
            "normalized_name": "Thyroid Stimulating Hormone (TSH)",
            "raw_test_name": "TSH",
            "value_numeric": 2.5,
            "unit": "uIU/mL",
            "reference_range_raw": "0.35 - 4.50",
            "flag": "NORMAL",
        },
        # Deteriorated: Total Cholesterol 185 -> 240
        {
            "id": "tr-comp-3",
            "report_id": rep_a,
            "user_id": user_id,
            "normalized_name": "Total Cholesterol",
            "raw_test_name": "Cholesterol Total",
            "value_numeric": 185.0,
            "unit": "mg/dL",
            "reference_range_raw": "< 200",
            "flag": "NORMAL",
        },
        {
            "id": "tr-comp-4",
            "report_id": rep_b,
            "user_id": user_id,
            "normalized_name": "Total Cholesterol",
            "raw_test_name": "Cholesterol Total",
            "value_numeric": 240.0,
            "unit": "mg/dL",
            "reference_range_raw": "< 200",
            "flag": "HIGH",
        },
        # New in follow-up: HbA1c
        {
            "id": "tr-comp-5",
            "report_id": rep_b,
            "user_id": user_id,
            "normalized_name": "Glycated Hemoglobin (HbA1c)",
            "raw_test_name": "HbA1c",
            "value_numeric": 5.4,
            "unit": "%",
            "reference_range_raw": "< 5.7",
            "flag": "NORMAL",
        }
    ])

    res = comparison_service.compare_two_reports(
        report_a_id=rep_a,
        report_b_id=rep_b,
        user_id=user_id,
        language="en"
    )

    assert res.report_a_id == rep_a
    assert res.report_b_id == rep_b
    assert res.total_compared == 3
    assert res.improved_count == 1
    assert res.deteriorated_count == 1

    tsh_item = next(it for it in res.items if "TSH" in it.normalized_name)
    assert tsh_item.status_shift == "IMPROVED_TO_NORMAL"
    assert tsh_item.delta_numeric == -4.3

    chol_item = next(it for it in res.items if "Cholesterol" in it.normalized_name)
    assert chol_item.status_shift == "DETERIORATED_TO_ABNORMAL"
    assert chol_item.delta_numeric == 55.0

    assert len(res.ai_summary) > 0
    assert "Annual Checkup 2024" in res.ai_summary
    assert "Annual Checkup 2025" in res.ai_summary

def test_comparison_api_endpoints():
    headers = {"Authorization": "Bearer dev-test-token"}

    # 1. Upload Report A
    pdf_a = b"%PDF-1.4\n1 0 obj\n<< /Title (Comparison Test A) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    res_a = client.post(
        "/api/v1/reports/upload",
        files={"file": ("report_a.pdf", io.BytesIO(pdf_a), "application/pdf")},
        data={"title": "Baseline Lipid Panel", "report_type": "lab_report", "report_date": "2024-01-01"},
        headers=headers,
    )
    assert res_a.status_code == 200
    rep_a_id = res_a.json()["data"]["id"]

    # 2. Upload Report B
    pdf_b = b"%PDF-1.4\n1 0 obj\n<< /Title (Comparison Test B) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    res_b = client.post(
        "/api/v1/reports/upload",
        files={"file": ("report_b.pdf", io.BytesIO(pdf_b), "application/pdf")},
        data={"title": "Follow-up Lipid Panel", "report_type": "lab_report", "report_date": "2024-07-01"},
        headers=headers,
    )
    assert res_b.status_code == 200
    rep_b_id = res_b.json()["data"]["id"]

    # Trigger OCR & extraction for both
    client.post(f"/api/v1/ocr/process-report/{rep_a_id}", headers=headers)
    client.post(f"/api/v1/reports/{rep_a_id}/extract-structured", headers=headers)

    client.post(f"/api/v1/ocr/process-report/{rep_b_id}", headers=headers)
    client.post(f"/api/v1/reports/{rep_b_id}/extract-structured", headers=headers)

    # 3. Test trends endpoints
    trends_res = client.get("/api/v1/trends/biomarkers", headers=headers)
    assert trends_res.status_code == 200
    assert trends_res.json()["success"] is True

    names_res = client.get("/api/v1/trends/biomarker-names", headers=headers)
    assert names_res.status_code == 200
    assert "names" in names_res.json()["data"]

    # 4. Test compare endpoint
    compare_payload = {
        "report_a_id": rep_a_id,
        "report_b_id": rep_b_id,
        "language": "en"
    }
    comp_res = client.post("/api/v1/reports/compare", json=compare_payload, headers=headers)
    assert comp_res.status_code == 200
    comp_data = comp_res.json()["data"]
    assert comp_data["report_a_id"] == rep_a_id
    assert comp_data["report_b_id"] == rep_b_id
    assert "ai_summary" in comp_data
    assert "items" in comp_data
