from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
import hashlib
import requests
import bcrypt
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

app = FastAPI(debug=False)

# -------------------------
# SECURE CORS CONFIG
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://your-production-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# -------------------------
# DATABASE (secure schema)
# -------------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
""")
conn.commit()


# -------------------------
# HOME
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


# -------------------------
# SECURE LOGIN (no SQL injection)
# -------------------------
@app.get("/login")
def login(username: str, password: str):

    cursor.execute(
        "SELECT password_hash FROM users WHERE username = ?",
        (username,)
    )
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    stored_hash = row[0]

    if bcrypt.checkpw(password.encode(), stored_hash.encode()):
        return {"status": "success"}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")


# -------------------------
# SECURE COMMAND EXECUTION (no OS injection)
# -------------------------
@app.get("/ping")
def ping(host: str):

    # allow only safe hosts (basic allowlist)
    allowed_hosts = ["127.0.0.1", "localhost"]

    if host not in allowed_hosts:
        raise HTTPException(status_code=400, detail="Invalid host")

    os.system(f"ping -c 1 {host}")
    return {"message": "Ping executed safely"}


# -------------------------
# SECURE FILE ACCESS (no path traversal)
# -------------------------
@app.get("/read-file")
def read_file(filename: str):

    base_dir = os.path.abspath("files")
    file_path = os.path.abspath(os.path.join(base_dir, filename))

    if not file_path.startswith(base_dir):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(file_path, "r", encoding="utf-8") as f:
        return {"content": f.read()}


# -------------------------
# SECURE DESERIALIZATION (remove pickle)
# -------------------------
@app.post("/deserialize")
async def deserialize(request: Request):
    # NEVER use pickle on user input
    raise HTTPException(status_code=400, detail="Unsafe operation disabled")


# -------------------------
# SECURE HASHING (replace MD5)
# -------------------------
@app.get("/hash")
def hash_password(password: str):

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)

    return {"hash": hashed.decode()}


# -------------------------
# SECURE SSRF (allowlist URLs)
# -------------------------
@app.get("/fetch")
def fetch(url: str):

    allowed_domains = ["api.github.com", "example.com"]

    parsed = urlparse(url)

    if parsed.hostname not in allowed_domains:
        raise HTTPException(status_code=400, detail="Blocked URL")

    response = requests.get(url, timeout=5)
    return {"status": response.status_code}


# -------------------------
# SECURE REDIRECT (allowlist)
# -------------------------
@app.get("/redirect")
def redirect(url: str):

    allowed_paths = ["/home", "/dashboard"]

    parsed = urlparse(url)

    if parsed.path not in allowed_paths:
        raise HTTPException(status_code=400, detail="Invalid redirect")

    return RedirectResponse(url=url)