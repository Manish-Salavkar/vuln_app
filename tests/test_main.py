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
    response = client.get("/redirect?target=home", allow_redirects=False)
    assert response.status_code in (200, 307)


def test_redirect_invalid():
    response = client.get("/redirect?target=evil")
    assert response.status_code == 400


def test_deserialize_disabled():
    response = client.post("/deserialize")
    assert response.status_code == 400


def test_login_success():
    import bcrypt
    from main import cursor, conn

    password = "validpass"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("testuser", hashed)
    )
    conn.commit()

    response = client.get("/login?username=testuser&password=validpass")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_login_wrong_password():
    import bcrypt
    from main import cursor, conn

    password = "correct"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("user2", hashed)
    )
    conn.commit()

    response = client.get("/login?username=user2&password=wrong")
    assert response.status_code == 401


def test_read_file_valid():
    import os

    os.makedirs("files", exist_ok=True)
    with open("files/test.txt", "w") as f:
        f.write("hello")

    response = client.get("/read-file?filename=test.txt")
    assert response.status_code == 200
    assert response.json()["content"] == "hello"


def test_fetch_repos():
    response = client.get("/fetch?endpoint=repos")
    assert response.status_code == 200
    assert "status" in response.json()


def test_hash_password_different_each_time():
    r1 = client.get("/hash?password=test_input")
    r2 = client.get("/hash?password=test_input")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["hash"] != r2.json()["hash"]


def test_redirect_dashboard():
    response = client.get("/redirect?target=dashboard", allow_redirects=False)
    assert response.status_code in (200, 307)