import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.services.chat_service import chat_service

client = TestClient(app)

SAMPLE_TEST_RESULTS = [
    {
        "raw_test_name": "Haemoglobin",
        "normalized_name": "Haemoglobin",
        "value_numeric": 11.2,
        "unit": "g/dL",
        "reference_range_raw": "13.0 - 17.0",
        "flag": "LOW",
    },
    {
        "raw_test_name": "Fasting Glucose",
        "normalized_name": "Fasting Blood Glucose",
        "value_numeric": 128.0,
        "unit": "mg/dL",
        "reference_range_raw": "70 - 99",
        "flag": "HIGH",
    },
    {
        "raw_test_name": "Serum Creatinine",
        "normalized_name": "Serum Creatinine",
        "value_numeric": 0.9,
        "unit": "mg/dL",
        "reference_range_raw": "0.7 - 1.3",
        "flag": "NORMAL",
    },
    {
        "raw_test_name": "TSH",
        "normalized_name": "Thyroid Stimulating Hormone (TSH)",
        "value_numeric": 7.4,
        "unit": "uIU/mL",
        "reference_range_raw": "0.35 - 4.50",
        "flag": "HIGH",
    }
]

def test_chat_context_building():
    context_text, glossary_names, entries = chat_service.build_chat_context(
        report_title="Comprehensive Health Panel",
        test_results=SAMPLE_TEST_RESULTS,
        user_query="What does my high glucose and low hemoglobin mean?",
        language="en"
    )
    assert "Comprehensive Health Panel" in context_text
    assert "Haemoglobin" in context_text
    assert "Fasting Blood Glucose" in context_text
    assert "LOW" in context_text
    assert "HIGH" in context_text
    assert len(glossary_names) > 0

def test_chat_fallback_abnormal_biomarkers():
    reply = chat_service._generate_fallback_reply(
        user_message="Which values are out of range in my report?",
        report_title="Annual Lab Checkup",
        test_results=SAMPLE_TEST_RESULTS,
        language="en"
    )
    assert "Annual Lab Checkup" in reply
    assert "Haemoglobin" in reply
    assert "11.2 g/dL" in reply
    assert "Fasting Blood Glucose" in reply
    assert "128.0 mg/dL" in reply
    assert "Thyroid Stimulating Hormone (TSH)" in reply
    assert "7.4 uIU/mL" in reply

def test_chat_fallback_specific_biomarker_query():
    reply = chat_service._generate_fallback_reply(
        user_message="What does my TSH test indicate?",
        report_title="Thyroid & Blood Panel",
        test_results=SAMPLE_TEST_RESULTS,
        language="en"
    )
    assert "Thyroid Stimulating Hormone (TSH)" in reply
    assert "7.4 uIU/mL" in reply
    assert "HIGH" in reply
    assert "Organs Involved" in reply

def test_chat_fallback_diet_and_doctor_questions():
    diet_reply = chat_service._generate_fallback_reply(
        user_message="What foods contain iron to help my levels?",
        report_title="Blood Panel",
        test_results=SAMPLE_TEST_RESULTS,
        language="en"
    )
    assert "Iron-Rich Foods" in diet_reply
    assert "Spinach" in diet_reply or "lentils" in diet_reply

    doc_reply = chat_service._generate_fallback_reply(
        user_message="What questions should I ask my doctor?",
        report_title="Blood Panel",
        test_results=SAMPLE_TEST_RESULTS,
        language="en"
    )
    assert "questions you can bring to your upcoming doctor's appointment" in doc_reply

def test_chat_multiturn_memory_and_service():
    report_id = "test-report-rep-101"
    user_id = "test-user-u-202"

    # Message 1
    resp1 = chat_service.generate_chat_reply(
        report_id=report_id,
        user_id=user_id,
        report_title="Executive Wellness Check",
        test_results=SAMPLE_TEST_RESULTS,
        user_message="Which values are abnormal?",
        language="en"
    )
    assert resp1.report_id == report_id
    assert len(resp1.messages) == 2  # user + assistant
    assert len(resp1.cited_biomarkers) > 0
    assert len(resp1.suggested_followups) > 0

    # Message 2
    resp2 = chat_service.generate_chat_reply(
        report_id=report_id,
        user_id=user_id,
        report_title="Executive Wellness Check",
        test_results=SAMPLE_TEST_RESULTS,
        user_message="What questions should I ask my doctor about these?",
        language="en"
    )
    assert len(resp2.messages) == 4  # 2 user + 2 assistant
    assert resp2.messages[0].content == "Which values are abnormal?"
    assert resp2.messages[2].content == "What questions should I ask my doctor about these?"

    # History retrieval
    history = chat_service.get_conversation_history(report_id, user_id)
    assert len(history.messages) == 4

    # Clear history
    chat_service.clear_conversation(report_id, user_id)
    cleared_history = chat_service.get_conversation_history(report_id, user_id)
    assert len(cleared_history.messages) == 0

def test_chat_api_endpoints_flow():
    headers = {"Authorization": "Bearer dev-test-token"}

    # 1. Upload mock report
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Chat RAG Test Report) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    upload_res = client.post(
        "/api/v1/reports/upload",
        files={"file": ("chat_test.pdf", io.BytesIO(pdf_content), "application/pdf")},
        data={"title": "Chat Q&A Diagnostic Panel", "report_type": "lab_report"},
        headers=headers,
    )
    assert upload_res.status_code == 200
    report_id = upload_res.json()["data"]["id"]

    # 2. Trigger OCR & Clinical Extraction
    client.post(f"/api/v1/ocr/process-report/{report_id}", headers=headers)
    client.post(f"/api/v1/reports/{report_id}/extract-structured", headers=headers)

    # 3. Post Chat Message
    chat_req = {
        "message": "Can you summarize my results and tell me which tests were out of range?",
        "language": "en"
    }
    chat_res = client.post(f"/api/v1/reports/{report_id}/chat", json=chat_req, headers=headers)
    assert chat_res.status_code == 200
    data = chat_res.json()["data"]
    assert data["report_id"] == report_id
    assert "reply" in data
    assert len(data["messages"]) >= 2
    assert len(data["suggested_followups"]) > 0

    # 4. Get Chat History
    history_res = client.get(f"/api/v1/reports/{report_id}/chat", headers=headers)
    assert history_res.status_code == 200
    hist_data = history_res.json()["data"]
    assert len(hist_data["messages"]) >= 2

    # 5. Clear Chat History
    del_res = client.delete(f"/api/v1/reports/{report_id}/chat", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["cleared"] is True

    # 6. Verify History is Empty
    history_after = client.get(f"/api/v1/reports/{report_id}/chat", headers=headers)
    assert len(history_after.json()["data"]["messages"]) == 0
