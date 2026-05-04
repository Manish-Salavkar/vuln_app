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
import subprocess

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

app = FastAPI(debug=False)


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


@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get(
    "/login",
    responses={
        401: {"description": "Invalid credentials"}
    }
)
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


@app.get(
    "/ping",
    responses={
        400: {"description": "Invalid host"}
    }
)
def ping(host: str):

    allowed_hosts = ["127.0.0.1", "localhost"]

    if host not in allowed_hosts:
        raise HTTPException(status_code=400, detail="Invalid host")

    
    subprocess.run(["ping", "-c", "1", host], check=True)
    return {"message": "Ping executed safely"}


@app.get(
    "/read-file",
    responses={
        400: {"description": "Invalid file path"},
        404: {"description": "File not found"}
    }
)
def read_file(filename: str):

    base_dir = os.path.abspath("files")
    file_path = os.path.abspath(os.path.join(base_dir, filename))

    if not file_path.startswith(base_dir):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(file_path, "r", encoding="utf-8") as f:
        return {"content": f.read()}


@app.post(
    "/deserialize",
    responses={
        400: {"description": "Unsafe operation disabled"}
    }
)
async def deserialize(request: Request):
    raise HTTPException(status_code=400, detail="Unsafe operation disabled")


@app.get("/hash")
def hash_password(password: str):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return {"hash": hashed.decode()}


@app.get(
    "/fetch",
    responses={
        400: {"description": "Invalid endpoint"}
    }
)
def fetch(endpoint: str):

    base_url = "https://api.github.com"

    allowed_endpoints = {
        "users": "/users",
        "repos": "/repositories"
    }

    if endpoint not in allowed_endpoints:
        raise HTTPException(status_code=400, detail="Invalid endpoint")

    url = base_url + allowed_endpoints[endpoint]

    response = requests.get(url, timeout=5)

    return {"status": response.status_code}

@app.get(
    "/redirect",
    responses={
        400: {"description": "Invalid redirect target"}
    }
)
def redirect(target: str):

    allowed_redirects = {
        "home": "/home",
        "dashboard": "/dashboard"
    }

    if target not in allowed_redirects:
        raise HTTPException(status_code=400, detail="Invalid redirect target")

    return RedirectResponse(url=allowed_redirects[target])