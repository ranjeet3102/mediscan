import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.ocr_engine import ocr_engine
from tests.test_image_preprocessing import create_synthetic_tilted_document

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer dev-user-token"}

def test_ocr_engine_process_document():
    """Verify document OCR execution, confidence calculations, and word extractions."""
    sample_bytes = create_synthetic_tilted_document(angle_degrees=0.0)
    result = ocr_engine.process_document(sample_bytes, mime_type="image/jpeg")

    assert result.full_text is not None
    assert len(result.full_text) > 20
    assert result.average_confidence >= 0.0
    assert result.total_pages >= 1
    assert result.overall_status in ["high_confidence", "moderate", "needs_verification"]

    page = result.pages[0]
    assert page.page_number == 1
    assert len(page.words) > 0
    first_word = page.words[0]
    assert first_word.text is not None
    assert "left" in first_word.bbox
    assert "top" in first_word.bbox

def test_extract_raw_ocr_api():
    """Verify POST /api/v1/ocr/extract-raw endpoint."""
    sample_bytes = create_synthetic_tilted_document(angle_degrees=0.0)
    response = client.post(
        "/api/v1/ocr/extract-raw",
        headers=AUTH_HEADERS,
        files={"file": ("lab_report.jpg", sample_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "full_text" in data["data"]
    assert "average_confidence" in data["data"]
    assert data["data"]["total_pages"] >= 1

def test_process_report_ocr_api():
    """Verify POST /api/v1/ocr/process-report/{report_id} updates report record."""
    # 1. Upload a report
    sample_bytes = create_synthetic_tilted_document(angle_degrees=0.0)
    upload_res = client.post(
        "/api/v1/reports/upload",
        headers=AUTH_HEADERS,
        data={"title": "Thyroid Function Panel"},
        files={"file": ("thyroid.jpg", sample_bytes, "image/jpeg")}
    )
    assert upload_res.status_code == 200
    report_id = upload_res.json()["data"]["id"]

    # 2. Trigger OCR on the uploaded report
    ocr_res = client.post(
        f"/api/v1/ocr/process-report/{report_id}",
        headers=AUTH_HEADERS
    )
    assert ocr_res.status_code == 200
    ocr_data = ocr_res.json()
    assert ocr_data["success"] is True
    assert ocr_data["data"]["report_id"] == report_id
    assert ocr_data["data"]["raw_ocr_text"] is not None
    assert ocr_data["data"]["average_confidence"] > 0

    # 3. Verify report status updated in GET detail
    detail_res = client.get(f"/api/v1/reports/{report_id}", headers=AUTH_HEADERS)
    assert detail_res.status_code == 200
    assert detail_res.json()["ocr_status"] == "completed"
    assert detail_res.json()["raw_ocr_text"] is not None
