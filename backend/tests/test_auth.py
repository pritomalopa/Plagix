import pytest
from uuid import uuid4


def test_register_user_success(client):
    email = f"teacher_{uuid4()}@test.edu"
    response = client.post("/api/auth/register", json={
        "email": email,
        "password": "SecurePassword123!",
        "name": "Dr. Alice Smith",
        "tenant_name": "Smith Academy"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert "id" in data
    assert "tenant_id" in data
    assert data["role"] == "teacher"
    
    # Verify cookie was set
    assert "access_token" in response.cookies


def test_register_duplicate_email(client):
    email = f"duplicate_{uuid4()}@test.edu"
    # First registration
    response1 = client.post("/api/auth/register", json={
        "email": email,
        "password": "SecurePassword123!",
        "name": "Teacher One"
    })
    assert response1.status_code == 201
    
    # Second registration with same email
    response2 = client.post("/api/auth/register", json={
        "email": email,
        "password": "DifferentPassword123!",
        "name": "Teacher Two"
    })
    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"]


def test_login_success_and_logout(client):
    email = f"login_{uuid4()}@test.edu"
    password = "MySecretPassword123!"
    
    # Register
    client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "name": "Login Test Teacher"
    })
    
    # Logout first to clear cookie
    client.post("/api/auth/logout")
    
    # Login with valid credentials
    response = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert response.status_code == 200
    assert response.json()["email"] == email
    assert "access_token" in response.cookies
    
    # Test /api/auth/me with cookie
    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email
    
    # Logout
    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200
    
    # /api/auth/me should fail now
    me_after_logout = client.get("/api/auth/me")
    assert me_after_logout.status_code == 401


def test_login_invalid_password(client):
    email = f"badpass_{uuid4()}@test.edu"
    client.post("/api/auth/register", json={
        "email": email,
        "password": "CorrectPassword123!",
        "name": "Bad Pass Teacher"
    })
    
    response = client.post("/api/auth/login", json={
        "email": email,
        "password": "WrongPassword999!"
    })
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_unauthorized_access(client):
    client.cookies.clear()
    response = client.get("/api/auth/me")
    assert response.status_code == 401
