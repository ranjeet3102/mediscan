import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer dev-user-token"}

def create_mock_pdf_bytes() -> bytes:
    """Returns minimal valid PDF bytes starting with %PDF."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"

def create_mock_png_bytes() -> bytes:
    """Returns minimal valid PNG bytes starting with PNG magic header."""
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

def test_upload_valid_pdf_report():
    pdf_content = create_mock_pdf_bytes()
    response = client.post(
        "/api/v1/reports/upload",
        headers=AUTH_HEADERS,
        data={
            "title": "Complete Blood Count Test",
            "report_type": "lab_report",
            "report_date": "2026-09-27"
        },
        files={
            "file": ("blood_test.pdf", pdf_content, "application/pdf")
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["title"] == "Complete Blood Count Test"
    assert data["data"]["ocr_status"] in ("pending", "completed")
    assert "signed_url" in data["data"]
    assert data["data"]["id"] is not None

def test_upload_valid_png_report():
    png_content = create_mock_png_bytes()
    response = client.post(
        "/api/v1/reports/upload",
        headers=AUTH_HEADERS,
        data={
            "title": "Prescription Image Scan",
            "report_type": "prescription",
            "report_date": "2026-09-27"
        },
        files={
            "file": ("prescription.png", png_content, "image/png")
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["report_type"] == "prescription"

def test_reject_empty_file():
    response = client.post(
        "/api/v1/reports/upload",
        headers=AUTH_HEADERS,
        data={"title": "Empty File"},
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]

def test_reject_invalid_extension():
    response = client.post(
        "/api/v1/reports/upload",
        headers=AUTH_HEADERS,
        data={"title": "Invalid File"},
        files={"file": ("malicious.exe", b"MZ\x90\x00", "application/x-msdownload")}
    )
    assert response.status_code == 415

def test_list_and_get_reports():
    # 1. Upload a report first
    pdf_content = create_mock_pdf_bytes()
    upload_res = client.post(
        "/api/v1/reports/upload",
        headers=AUTH_HEADERS,
        data={"title": "Thyroid Profile TFT"},
        files={"file": ("thyroid.pdf", pdf_content, "application/pdf")}
    )
    report_id = upload_res.json()["data"]["id"]

    # 2. List reports
    list_res = client.get("/api/v1/reports/", headers=AUTH_HEADERS)
    assert list_res.status_code == 200
    reports = list_res.json()
    assert len(reports) >= 1
    assert any(r["id"] == report_id for r in reports)

    # 3. Get specific report
    detail_res = client.get(f"/api/v1/reports/{report_id}", headers=AUTH_HEADERS)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == report_id
    assert detail["title"] == "Thyroid Profile TFT"

def test_delete_report():
    pdf_content = create_mock_pdf_bytes()
    upload_res = client.post(
        "/api/v1/reports/upload",
        headers=AUTH_HEADERS,
        data={"title": "Report to be Deleted"},
        files={"file": ("temp.pdf", pdf_content, "application/pdf")}
    )
    report_id = upload_res.json()["data"]["id"]

    # Delete
    del_res = client.delete(f"/api/v1/reports/{report_id}", headers=AUTH_HEADERS)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Check 404 after deletion
    detail_res = client.get(f"/api/v1/reports/{report_id}", headers=AUTH_HEADERS)
    assert detail_res.status_code == 404
