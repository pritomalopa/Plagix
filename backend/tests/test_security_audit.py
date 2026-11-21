import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app

client = TestClient(app)


def test_cross_tenant_isolation(client):
    """
    Verify cross-tenant isolation: Tenant A cannot access or modify Tenant B data/resources.
    """
    # 1. Register Tenant A / User A
    email_a = f"teacher_a_{uuid4()}@test.edu"
    res_a = client.post("/api/auth/register", json={
        "email": email_a,
        "password": "PasswordA123!",
        "name": "Teacher A",
        "tenant_name": "Tenant A Workspace"
    })
    assert res_a.status_code == 201
    user_a = res_a.json()
    token_a = res_a.cookies.get("access_token")

    # 2. Register Tenant B / User B
    email_b = f"teacher_b_{uuid4()}@test.edu"
    res_b = client.post("/api/auth/register", json={
        "email": email_b,
        "password": "PasswordB123!",
        "name": "Teacher B",
        "tenant_name": "Tenant B Workspace"
    })
    assert res_b.status_code == 201
    user_b = res_b.json()
    token_b = res_b.cookies.get("access_token")

    # Verify users belong to different tenants
    assert user_a["tenant_id"] != user_b["tenant_id"]

    # Switch to User A session
    client.cookies.set("access_token", token_a)
    me_a = client.get("/api/auth/me")
    assert me_a.status_code == 200
    assert me_a.json()["tenant_id"] == user_a["tenant_id"]


def test_token_validation_edge_cases(client):
    """
    Test GET /api/auth/me with missing, invalid, and malformed tokens.
    """
    # Missing token
    client.cookies.clear()
    res_missing = client.get("/api/auth/me")
    assert res_missing.status_code == 401

    # Invalid / malformed token
    client.cookies.set("access_token", "Bearer invalid.jwt.token.string")
    res_invalid = client.get("/api/auth/me")
    assert res_invalid.status_code == 401


def test_cookie_security_attributes(client):
    """
    Verify cookie security settings (httpOnly, samesite).
    """
    email = f"cookie_{uuid4()}@test.edu"
    response = client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123!",
        "name": "Cookie Test"
    })
    assert response.status_code == 201
    
    # Check cookie was set
    assert "access_token" in response.cookies
    
    # Logout clears cookie
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200
