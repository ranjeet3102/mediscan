import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "API is running" in data["message"]

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "online"

def test_signup_and_login_flow():
    import time
    test_email = f"test.unit_{int(time.time())}@example.com"
    signup_resp = client.post(
        "/api/v1/auth/signup",
        json={
            "email": test_email,
            "password": "SecurePassword123!",
            "role": "user",
            "preferred_language": "en"
        }
    )
    assert signup_resp.status_code == 200
    data = signup_resp.json()
    assert data["success"] is True
    assert data["data"]["email"] == test_email
    assert data["data"]["role"] == "user"

    # Test login with the newly created account
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_email,
            "password": "SecurePassword123!"
        }
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert login_data["user"]["role"] == "user"

def test_admin_stats_access_control():
    # User token attempting to access admin route should be blocked (403 Forbidden)
    user_headers = {"Authorization": "Bearer dev-user-token"}
    user_resp = client.get("/api/v1/admin/stats", headers=user_headers)
    assert user_resp.status_code == 403
    assert "Administrator role required" in user_resp.json()["detail"]

    # Admin token should succeed
    admin_headers = {"Authorization": "Bearer dev-admin-token"}
    admin_resp = client.get("/api/v1/admin/stats", headers=admin_headers)
    assert admin_resp.status_code == 200
    admin_data = admin_resp.json()
    assert "total_users" in admin_data
    assert "total_reports_processed" in admin_data
    # Zero-PHI validation: ensure NO patient fields exist in the response
    assert "patient_name" not in admin_data
    assert "raw_ocr_text" not in admin_data
    assert "test_results" not in admin_data
