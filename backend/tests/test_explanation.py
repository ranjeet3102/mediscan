import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.services.ollama_service import ollama_service
from app.services.explanation_service import grounded_explanation_service

client = TestClient(app)

def test_ollama_prompt_construction():
    test_items = [
        {"raw_test_name": "Haemoglobin", "normalized_name": "Haemoglobin", "value_numeric": 14.2, "unit": "g/dL", "reference_range_raw": "13.0 - 17.0", "flag": "NORMAL"},
        {"raw_test_name": "Fasting Glucose", "normalized_name": "Fasting Blood Glucose", "value_numeric": 118.0, "unit": "mg/dL", "reference_range_raw": "70 - 99", "flag": "HIGH"},
    ]
    glossary_context = [
        {"canonical_name": "Haemoglobin", "patient_friendly_summary": "Oxygen carrying protein", "organs_involved": "Lungs, marrow", "high_value_meaning": "Dehydration", "low_value_meaning": "Anemia"},
        {"canonical_name": "Fasting Blood Glucose", "patient_friendly_summary": "Baseline blood sugar", "organs_involved": "Pancreas, liver", "high_value_meaning": "Elevated blood sugar", "low_value_meaning": "Low blood sugar"},
    ]
    system_p, user_p = ollama_service.construct_grounded_prompt(
        report_title="Annual Routine Lab Panel",
        test_items=test_items,
        glossary_context=glossary_context,
        language="en"
    )
    assert "STRICT RULES TO PREVENT MEDICAL MISINFORMATION" in system_p
    assert "Haemoglobin" in user_p
    assert "14.2 g/dL" in user_p
    assert "Fasting Blood Glucose" in user_p
    assert "118.0 mg/dL" in user_p

def test_fallback_grounded_generator_citations():
    test_items = [
        {"raw_test_name": "Hb", "normalized_name": "Haemoglobin", "value_numeric": 14.2, "unit": "g/dL", "reference_range_raw": "13.0 - 17.0", "flag": "NORMAL"},
        {"raw_test_name": "TSH", "normalized_name": "Thyroid Stimulating Hormone (TSH)", "value_numeric": 6.8, "unit": "uIU/mL", "reference_range_raw": "0.35 - 4.50", "flag": "HIGH"},
    ]
    glossary_map = {
        "haemoglobin": {"high_value_meaning": "Dehydration", "low_value_meaning": "Anemia"},
        "thyroid stimulating hormone (tsh)": {"high_value_meaning": "Underactive thyroid signal (Hypothyroidism)", "low_value_meaning": "Overactive thyroid signal"},
    }
    explanation = ollama_service.generate_fallback_explanation(
        report_title="Thyroid & Blood Panel",
        test_items=test_items,
        glossary_map=glossary_map,
        language="en"
    )
    assert explanation["is_mock_fallback"] is True
    assert "Thyroid & Blood Panel" in explanation["executive_summary"]
    assert "Haemoglobin (14.2 g/dL)" in explanation["normal_findings_summary"]
    assert "Thyroid Stimulating Hormone (TSH) was measured at 6.8 uIU/mL" in explanation["abnormal_findings_summary"]
    assert len(explanation["doctor_questions"]) >= 3

def test_ai_status_api():
    headers = {"Authorization": "Bearer dev-test-token"}
    response = client.get("/api/v1/ai/status", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "model" in data["data"]
    assert "ollama_url" in data["data"]

def test_report_explanation_flow_api():
    headers = {"Authorization": "Bearer dev-test-token"}
    
    # 1. Upload sample report
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (AI Explanation Test) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    upload_res = client.post(
        "/api/v1/reports/upload",
        files={"file": ("test_panel.pdf", io.BytesIO(pdf_content), "application/pdf")},
        data={"title": "Comprehensive Metabolic Panel", "report_type": "lab_report"},
        headers=headers,
    )
    assert upload_res.status_code == 200
    report_id = upload_res.json()["data"]["id"]

    # 2. Trigger OCR
    ocr_res = client.post(f"/api/v1/ocr/process-report/{report_id}", headers=headers)
    assert ocr_res.status_code == 200

    # 3. Extract structured test results
    extract_res = client.post(f"/api/v1/reports/{report_id}/extract-structured", headers=headers)
    assert extract_res.status_code == 200

    # 4. Generate AI Explanation
    explain_res = client.post(f"/api/v1/reports/{report_id}/explain?language=en", headers=headers)
    assert explain_res.status_code == 200
    exp_data = explain_res.json()["data"]
    assert exp_data["report_id"] == report_id
    assert exp_data["title"] == "Comprehensive Metabolic Panel"
    assert len(exp_data["citations"]) > 0
    assert len(exp_data["doctor_questions"]) > 0

    # 5. Fetch cached explanation
    get_exp_res = client.get(f"/api/v1/reports/{report_id}/explanation?language=en", headers=headers)
    assert get_exp_res.status_code == 200
    cached_data = get_exp_res.json()["data"]
    assert cached_data["executive_summary"] == exp_data["executive_summary"]
