from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
import pickle
import hashlib
import requests

app = FastAPI(debug=True)  # VULN 1: Debug mode enabled

# VULN 2: Insecure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# VULN 3: Hardcoded secret
SECRET_KEY = "SUPER_SECRET_KEY_123456"

# VULN 4: Hardcoded AWS credentials
AWS_ACCESS_KEY = "AKIAFAKEKEY123456"
AWS_SECRET_KEY = "fakeSecretKey123456"

# Database setup
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
conn.commit()


@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html") as f:
        return f.read()


# 🔴 SQL Injection
@app.get("/login")
def login(username: str, password: str):
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    result = cursor.execute(query).fetchall()
    return {"result": result}


# 🔴 Command Injection
@app.get("/ping")
def ping(host: str):
    os.system(f"ping -c 1 {host}")  # User input injected into system call
    return {"message": "Ping executed"}


# 🔴 Path Traversal
@app.get("/read-file")
def read_file(filename: str):
    with open("files/" + filename, "r") as f:
        return {"content": f.read()}


# 🔴 Insecure Deserialization
@app.post("/deserialize")
async def deserialize(request: Request):
    data = await request.body()
    obj = pickle.loads(data)
    return {"data": str(obj)}


# 🔴 Weak Hashing
@app.get("/hash")
def hash_password(password: str):
    hashed = hashlib.md5(password.encode()).hexdigest()
    return {"hash": hashed}


# 🔴 SSRF
@app.get("/fetch")
def fetch(url: str):
    response = requests.get(url)
    return {"status": response.status_code}


# 🔴 Open Redirect
@app.get("/redirect")
def redirect(url: str):
    return {"redirect_to": url}