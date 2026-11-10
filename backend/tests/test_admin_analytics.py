import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.telemetry_service import telemetry_service

client = TestClient(app)

def test_telemetry_service_recording_and_stats():
    # Record events
    telemetry_service.record_event("ocr_processed", 210.5, "success", 0)
    telemetry_service.record_event("ai_chat_completed", 450.0, "success", 180)
    telemetry_service.record_event("doctor_summary_generated", 380.0, "success", 95)

    stats = telemetry_service.get_stats()
    assert "total_users" in stats
    assert "total_reports_processed" in stats
    assert "ocr_requests_count" in stats
    assert "ai_requests_count" in stats
    assert stats["average_processing_time_ms"] > 0
    assert stats["api_success_rate"] >= 90.0

def test_telemetry_timeseries_and_breakdown():
    # Time series
    ts = telemetry_service.get_time_series(hours=12)
    assert len(ts) == 12
    assert "time" in ts[0]
    assert "ocr_requests" in ts[0]
    assert "ai_queries" in ts[0]
    assert "avg_latency_ms" in ts[0]

    # Breakdown
    bd = telemetry_service.get_module_breakdown()
    assert len(bd) > 0
    assert any(b["module_name"] == "OCR & Image Preprocessing" for b in bd)
    assert any(b["module_name"] == "Ask My Report Conversational Q&A" for b in bd)
    assert all("percentage" in b and "avg_latency_ms" in b for b in bd)

def test_admin_rbac_access_control():
    # 1. Normal User Token (Role = user) -> dev-user-token
    user_headers = {"Authorization": "Bearer dev-user-token"}

    # Should be rejected with 403 Forbidden
    res1 = client.get("/api/v1/admin/stats", headers=user_headers)
    assert res1.status_code == 403

    res2 = client.get("/api/v1/admin/telemetry/overview", headers=user_headers)
    assert res2.status_code == 403

    res3 = client.get("/api/v1/admin/telemetry/timeseries", headers=user_headers)
    assert res3.status_code == 403

    # 2. Admin Token (Role = admin) -> dev-admin-token
    admin_headers = {"Authorization": "Bearer dev-admin-token"}

    # Should succeed with 200 OK
    res_stats = client.get("/api/v1/admin/stats", headers=admin_headers)
    assert res_stats.status_code == 200
    assert "total_reports_processed" in res_stats.json()

    res_health = client.get("/api/v1/admin/health", headers=admin_headers)
    assert res_health.status_code == 200
    assert "version" in res_health.json()

    res_overview = client.get("/api/v1/admin/telemetry/overview", headers=admin_headers)
    assert res_overview.status_code == 200
    data = res_overview.json()["data"]
    assert "stats" in data
    assert "health" in data
    assert "time_series" in data
    assert "breakdown" in data
    assert "recent_events" in data

    res_ts = client.get("/api/v1/admin/telemetry/timeseries?hours=24", headers=admin_headers)
    assert res_ts.status_code == 200
    assert len(res_ts.json()["data"]) == 24

    res_bd = client.get("/api/v1/admin/telemetry/breakdown", headers=admin_headers)
    assert res_bd.status_code == 200
    assert len(res_bd.json()["data"]) > 0

    res_evts = client.get("/api/v1/admin/telemetry/events?limit=10", headers=admin_headers)
    assert res_evts.status_code == 200
    assert len(res_evts.json()["data"]) <= 10

def test_zero_phi_compliance_guarantee():
    """
    STRICT VERIFICATION: Ensure absolutely zero patient identifiable information (PHI),
    clinical values, report files, or message strings leak through the admin telemetry APIs.
    """
    admin_headers = {"Authorization": "Bearer dev-admin-token"}

    forbidden_phi_keys = {
        "patient_name", "first_name", "last_name", "phone", "address",
        "ssn", "medical_record_number", "test_results", "raw_ocr_text",
        "value_numeric", "value_text", "messages", "chat_history", "file_url"
    }

    # Fetch all admin responses
    endpoints = [
        "/api/v1/admin/stats",
        "/api/v1/admin/health",
        "/api/v1/admin/telemetry/overview",
        "/api/v1/admin/telemetry/timeseries",
        "/api/v1/admin/telemetry/breakdown",
        "/api/v1/admin/telemetry/events",
    ]

    for ep in endpoints:
        resp = client.get(ep, headers=admin_headers)
        assert resp.status_code == 200
        json_str = resp.text.lower()

        # Check key names in raw string
        for phi_key in forbidden_phi_keys:
            assert f'"{phi_key}"' not in json_str, f"PHI Key '{phi_key}' detected in admin endpoint '{ep}'!"
