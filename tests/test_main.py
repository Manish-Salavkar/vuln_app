from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200


def test_login_invalid_user():
    response = client.get("/login?username=abc&password=xyz")
    assert response.status_code == 401


def test_hash_password():
    response = client.get("/hash?password=test123")
    assert response.status_code == 200
    assert "hash" in response.json()


def test_ping_allowed():
    response = client.get("/ping?host=localhost")
    assert response.status_code == 200


def test_ping_blocked():
    response = client.get("/ping?host=google.com")
    assert response.status_code == 400


def test_read_file_invalid_path():
    response = client.get("/read-file?filename=../../etc/passwd")
    assert response.status_code == 400


def test_read_file_not_found():
    response = client.get("/read-file?filename=nonexistent.txt")
    assert response.status_code == 404


def test_fetch_valid():
    response = client.get("/fetch?endpoint=users")
    assert response.status_code == 200


def test_fetch_invalid():
    response = client.get("/fetch?endpoint=evil")
    assert response.status_code == 400


def test_redirect_valid():
    response = client.get("/redirect?target=home")
    assert response.status_code in (200, 307)


def test_redirect_invalid():
    response = client.get("/redirect?target=evil")
    assert response.status_code == 400


def test_deserialize_disabled():
    response = client.post("/deserialize")
    assert response.status_code == 400