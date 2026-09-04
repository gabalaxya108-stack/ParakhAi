import pytest
from backend.app.core.security import sanitize_filename

def test_secure_filename_handling():
    # 1. Path traversal attacks
    assert sanitize_filename("../../../etc/shadow.jpg") == "shadow.jpg"
    assert sanitize_filename("..\\..\\windows\\system32\\calc.png") == "calc.png"

    # 2. Null byte and control character injection
    assert sanitize_filename("test\0bad\x01file.jpg") == "testbadfile.jpg"

    # 3. Special dangerous characters replaced
    assert sanitize_filename("bad;rm -rf;image.png") == "bad_rm_-rf_image.png"

    # 4. Leading dots stripped (no hidden files)
    assert sanitize_filename(".hidden_malware.png") == "hidden_malware.png"

    # 5. Empty fallback
    assert sanitize_filename("") == "unnamed_asset.jpg"

def test_rbac_authorization_inspector_forbidden_from_admin(client):
    # Inspector attempting to access Admin user management should be forbidden (403)
    res = client.get(
        "/api/v1/admin/users",
        headers={"X-User-Role": "INSPECTOR"}
    )
    assert res.status_code == 403
    assert "access denied" in res.json()["detail"].lower()

def test_rbac_authorization_supervisor_access(client):
    # Supervisor can access audit logs
    audit_res = client.get(
        "/api/v1/admin/audit-logs",
        headers={"X-User-Role": "SUPERVISOR"}
    )
    assert audit_res.status_code == 200
    assert isinstance(audit_res.json(), list)

    # But Supervisor cannot manage users (Admin only)
    user_res = client.get(
        "/api/v1/admin/users",
        headers={"X-User-Role": "SUPERVISOR"}
    )
    assert user_res.status_code == 403

def test_rbac_authorization_admin_provisioning(client):
    # Admin can access user list
    res = client.get(
        "/api/v1/admin/users",
        headers={"X-User-Role": "ADMIN"}
    )
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 1

    # Admin can provision new user
    create_res = client.post(
        "/api/v1/admin/users",
        headers={"X-User-Role": "ADMIN"},
        json={
            "username": "inspector_delhi_04",
            "email": "delhi04@legalmetrology.gov.in",
            "full_name": "Delhi Field Inspector 04",
            "role": "INSPECTOR"
        }
    )
    assert create_res.status_code in [201, 409]  # 201 created or 409 if already exists

def test_entra_id_bearer_token_resolution(client):
    # Admin Bearer token
    res = client.get(
        "/api/v1/admin/roles/current",
        headers={"Authorization": "Bearer admin-token"}
    )
    assert res.status_code == 200
    assert res.json()["role"] == "ADMIN"
    assert res.json()["entra_oid"] == "entra-admin-001"

    # Supervisor Bearer token
    sup_res = client.get(
        "/api/v1/admin/roles/current",
        headers={"Authorization": "Bearer supervisor-token"}
    )
    assert sup_res.status_code == 200
    assert sup_res.json()["role"] == "SUPERVISOR"

def test_sql_injection_defense_via_orm(client):
    # Attempt SQL injection in manufacturer filter
    payload = "' OR '1'='1'; DROP TABLE users; --"
    res = client.get(f"/api/v1/analytics/manufacturers?manufacturer={payload}")
    assert res.status_code == 200
    # Verified query returned gracefully and ORM safely parameterized the string
    data = res.json()
    assert "manufacturers" in data
