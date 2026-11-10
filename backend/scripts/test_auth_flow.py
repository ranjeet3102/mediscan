import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth():
    print("=" * 60)
    print("Testing End-to-End Auth Flows (User & Admin in Supabase)")
    print("=" * 60)

    # 1. Test Admin Login
    print("\n1. Testing Admin Login (admin@medicalocr.com)...")
    admin_login_payload = {
        "email": "admin@medicalocr.com",
        "password": "AdminSecurePass123!"
    }
    r = client.post("/api/v1/auth/login", json=admin_login_payload)
    print(f"Status Code: {r.status_code}")
    if r.status_code == 200:
        admin_data = r.json()
        print(f"[SUCCESS] Admin logged in! User: {admin_data['user']['email']}, Role: {admin_data['user']['role']}")
        admin_token = admin_data["access_token"]
        
        # Test /auth/me with Admin token
        me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
        print(f"/auth/me Status: {me_resp.status_code}, User: {me_resp.json().get('email')}, Role: {me_resp.json().get('role')}")
        assert me_resp.json().get("role") == "admin"
        
        # Test /admin/health with Admin token
        health_resp = client.get("/api/v1/admin/health", headers={"Authorization": f"Bearer {admin_token}"})
        print(f"/admin/health Status: {health_resp.status_code}")
    else:
        print(f"[FAIL] Admin login response: {r.text}")

    # 2. Test User Signup
    import time
    test_user_email = f"patient_{int(time.time())}@medicalocr.com"
    test_user_password = "PatientPass123!"
    print(f"\n2. Testing Fresh User Signup ({test_user_email})...")
    signup_payload = {
        "email": test_user_email,
        "password": test_user_password,
        "role": "user",
        "preferred_language": "ta"
    }
    sr = client.post("/api/v1/auth/signup", json=signup_payload)
    print(f"Signup Status Code: {sr.status_code}")
    print(f"Signup Response: {sr.text}")
    assert sr.status_code == 200

    # 3. Test User Login
    print(f"\n3. Testing User Login ({test_user_email})...")
    user_login_payload = {
        "email": test_user_email,
        "password": test_user_password
    }
    ur = client.post("/api/v1/auth/login", json=user_login_payload)
    print(f"Login Status Code: {ur.status_code}")
    if ur.status_code == 200:
        user_data = ur.json()
        print(f"[SUCCESS] User logged in! User: {user_data['user']['email']}, Role: {user_data['user']['role']}, Lang: {user_data['user']['preferred_language']}")
        user_token = user_data["access_token"]
        
        # Test /auth/me with User token
        me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {user_token}"})
        print(f"/auth/me Status: {me_resp.status_code}, User: {me_resp.json().get('email')}, Role: {me_resp.json().get('role')}")
        assert me_resp.json().get("role") == "user"
    else:
        print(f"[FAIL] User login response: {ur.text}")

    print("\n" + "=" * 60)
    print("ALL AUTH FLOW CHECKS COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    test_auth()
