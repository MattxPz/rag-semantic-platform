def test_register_creates_user(client):
    response = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert "id" in data
    assert "hashed_password" not in data  # password must never leak


def test_register_duplicate_email_fails(client):
    client.post("/auth/register", json={"email": "dup@example.com", "password": "password123"})
    response = client.post(
        "/auth/register",
        json={"email": "dup@example.com", "password": "password123"},
    )
    assert response.status_code == 400


def test_login_returns_token(client):
    client.post("/auth/register", json={"email": "login@example.com", "password": "password123"})
    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password_fails(client):
    client.post("/auth/register", json={"email": "wrong@example.com", "password": "password123"})
    response = client.post(
        "/auth/login",
        data={"username": "wrong@example.com", "password": "incorrect"},
    )
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"