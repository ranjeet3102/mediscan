import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.services.doctor_service import doctor_service

client = TestClient(app)

SAMPLE_CLINICAL_ITEMS = [
    {
        "raw_test_name": "Fasting Glucose",
        "normalized_name": "Fasting Blood Glucose",
        "value_numeric": 142.0,
        "unit": "mg/dL",
        "reference_range_raw": "70 - 99",
        "flag": "HIGH",
    },
    {
        "raw_test_name": "HbA1c",
        "normalized_name": "Glycated Hemoglobin (HbA1c)",
        "value_numeric": 7.1,
        "unit": "%",
        "reference_range_raw": "< 5.7",
        "flag": "HIGH",
    },
    {
        "raw_test_name": "Serum Creatinine",
        "normalized_name": "Serum Creatinine",
        "value_numeric": 0.85,
        "unit": "mg/dL",
        "reference_range_raw": "0.7 - 1.3",
        "flag": "NORMAL",
    },
    {
        "raw_test_name": "Haemoglobin",
        "normalized_name": "Haemoglobin",
        "value_numeric": 14.0,
        "unit": "g/dL",
        "reference_range_raw": "13.0 - 17.0",
        "flag": "NORMAL",
    }
]

def test_doctor_questions_generation_priorities():
    questions = doctor_service._generate_doctor_questions(
        report_title="Comprehensive Diabetic Checkup",
        abnormal_items=[
            {"name": "Fasting Blood Glucose", "value": "142.0", "unit": "mg/dL", "reference_range": "70 - 99", "flag": "HIGH"},
            {"name": "Glycated Hemoglobin (HbA1c)", "value": "7.1", "unit": "%", "reference_range": "< 5.7", "flag": "HIGH"},
        ],
        longitudinal_shifts=[
            {"biomarker": "Fasting Blood Glucose", "earliest": 110.0, "latest": 142.0, "delta": 32.0, "delta_pct": 29.1, "unit": "mg/dL", "direction": "concerning"}
        ],
        language="en"
    )

    assert len(questions) >= 4

    # High priority question for Fasting Blood Glucose
    high_q = next((q for q in questions if q.priority == "high"), None)
    assert high_q is not None
    assert "Fasting Blood Glucose" in high_q.question
    assert "142.0" in high_q.question

    # Medium priority question for longitudinal shift
    med_q = next((q for q in questions if q.priority == "medium"), None)
    assert med_q is not None
    assert "Fasting Blood Glucose" in med_q.question
    assert "32.0" in med_q.question or "29.1" in med_q.question

    # General questions
    general_qs = [q for q in questions if q.priority == "general"]
    assert len(general_qs) >= 2

def test_doctor_summary_multilingual():
    # English summary
    summary_en = doctor_service.generate_doctor_summary(
        report_id="test-rep-doc-1",
        user_id="test-u-doc-1",
        report_title="Annual Metabolic Profile",
        report_date="2025-05-10",
        test_results=SAMPLE_CLINICAL_ITEMS,
        patient_email="patient@example.com",
        language="en"
    )
    assert summary_en.report_id == "test-rep-doc-1"
    assert summary_en.total_findings_count == 4
    assert summary_en.abnormal_findings_count == 2
    assert "Fasting Blood Glucose" in summary_en.executive_clinical_summary
    assert len(summary_en.doctor_questions) >= 3

    # Tamil summary
    summary_ta = doctor_service.generate_doctor_summary(
        report_id="test-rep-doc-2",
        user_id="test-u-doc-2",
        report_title="Annual Metabolic Profile",
        report_date="2025-05-10",
        test_results=SAMPLE_CLINICAL_ITEMS,
        patient_email="patient@example.com",
        language="ta"
    )
    assert summary_ta.language == "ta"
    assert "மருத்துவ அறிக்கை" in summary_ta.executive_clinical_summary
    assert any("உணவுமுறை" in q.question for q in summary_ta.doctor_questions)

    # Hindi summary
    summary_hi = doctor_service.generate_doctor_summary(
        report_id="test-rep-doc-3",
        user_id="test-u-doc-3",
        report_title="Annual Metabolic Profile",
        report_date="2025-05-10",
        test_results=SAMPLE_CLINICAL_ITEMS,
        patient_email="patient@example.com",
        language="hi"
    )
    assert summary_hi.language == "hi"
    assert "मेडिकल रिपोर्ट" in summary_hi.executive_clinical_summary

def test_doctor_summary_api_endpoints():
    headers = {"Authorization": "Bearer dev-test-token"}

    # 1. Upload Report
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Title (Doctor Brief Test) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    upload_res = client.post(
        "/api/v1/reports/upload",
        files={"file": ("doc_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"title": "Executive Clinical Profile", "report_type": "lab_report"},
        headers=headers,
    )
    assert upload_res.status_code == 200
    report_id = upload_res.json()["data"]["id"]

    # 2. Run OCR & Extraction
    client.post(f"/api/v1/ocr/process-report/{report_id}", headers=headers)
    client.post(f"/api/v1/reports/{report_id}/extract-structured", headers=headers)

    # 3. GET Doctor Summary
    doc_sum_res = client.get(f"/api/v1/reports/{report_id}/doctor-summary?language=en", headers=headers)
    assert doc_sum_res.status_code == 200
    data = doc_sum_res.json()["data"]
    assert data["report_id"] == report_id
    assert "executive_clinical_summary" in data
    assert "doctor_questions" in data
    assert len(data["doctor_questions"]) > 0

    # 4. GET Doctor Questions
    q_res = client.get(f"/api/v1/reports/{report_id}/doctor-questions?language=en", headers=headers)
    assert q_res.status_code == 200
    q_data = q_res.json()["data"]
    assert isinstance(q_data, list)
    assert len(q_data) > 0
