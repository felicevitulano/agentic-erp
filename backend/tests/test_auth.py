def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_success(client):
    response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "testpass",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client):
    response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "wrongpass",
    })
    assert response.status_code == 401


def test_get_me(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


def test_get_me_no_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 403


def test_refresh_token(client):
    login = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "testpass",
    })
    refresh = login.json()["refresh_token"]
    response = client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200
    assert "access_token" in response.json()
