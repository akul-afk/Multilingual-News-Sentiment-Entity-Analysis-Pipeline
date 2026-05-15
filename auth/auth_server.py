import os
import uuid
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict

from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import bcrypt

# Import dual-write connection helper
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from Data_Processing.db_connector import get_auth_connection, ensure_auth_tables
except ImportError:
    # fallback if not found
    import sqlite3
    def get_auth_connection(is_sqlite=True):
        return sqlite3.connect('Data_Processing/news_headlines.db', check_same_thread=False)
    
    def ensure_auth_tables(cursor, is_sqlite=True):
        # Fallback SQL creation if db_connector is missing
        cursor.execute("""CREATE TABLE IF NOT EXISTS dim_users (
            user_id VARCHAR(36) PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT 'viewer',
            status VARCHAR(20) DEFAULT 'active',
            last_login_at TIMESTAMP NULL,
            failed_attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS dim_sessions (
            session_id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            refresh_token TEXT NOT NULL,
            ip_address VARCHAR(45),
            user_agent TEXT,
            revoked BOOLEAN DEFAULT FALSE,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES dim_users(user_id)
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS dim_token_blacklist (
            jti VARCHAR(36) PRIMARY KEY,
            expires_at TIMESTAMP NOT NULL,
            blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS dim_guest_sessions (
            guest_token VARCHAR(36) PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            ip_address VARCHAR(45),
            page_views INTEGER DEFAULT 0
        )""")
        
        audit_sql = "CREATE TABLE IF NOT EXISTS dim_audit_log (log_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id VARCHAR(36), event_type VARCHAR(50) NOT NULL, description TEXT, ip_address VARCHAR(45), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        if not is_sqlite:
            audit_sql = audit_sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "INT AUTO_INCREMENT PRIMARY KEY")
        cursor.execute(audit_sql)

# Read environment variables
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "fallback_secret_key")
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", 7))
GUEST_TOKEN_EXPIRE_HOURS = int(os.environ.get("GUEST_TOKEN_EXPIRE_HOURS", 24))

app = FastAPI(title="GNP Auth API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Configuration
dashboard_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dashboard'))


@app.on_event("startup")
def startup_event():
    # Ensure tables exist on startup
    conn = get_auth_connection(is_sqlite=False)
    is_sqlite = 'sqlite3' in str(type(conn))
    cursor = conn.cursor()
    ensure_auth_tables(cursor, is_sqlite=is_sqlite)
    conn.commit()
    conn.close()

def get_db():
    # Attempt MySQL first, then fallback to SQLite handled within get_auth_connection
    # We pass is_sqlite=False to try MySQL first
    conn = get_auth_connection(is_sqlite=False)
    return conn


class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

@app.post("/auth/login")
def login(request: LoginRequest, response: Response):
    conn = get_db()
    
    # Determine parameter style based on connection type
    is_sqlite = 'sqlite3' in str(type(conn))
    param = "?" if is_sqlite else "%s"
    
    cursor = conn.cursor()
    cursor.execute(f"SELECT user_id, password_hash, role FROM dim_users WHERE username = {param}", (request.username,))
    res = cursor.fetchone()
    if not res:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
        
    user_id, password_hash, role = res
    if not verify_password(request.password, password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # Access Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id, "role": role}, expires_delta=access_token_expires
    )

    # Refresh Token
    refresh_token = str(uuid.uuid4())
    refresh_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    session_id = str(uuid.uuid4())
    
    cursor.execute(
        f"INSERT INTO dim_sessions (session_id, user_id, refresh_token, expires_at) VALUES ({param}, {param}, {param}, {param})",
        (session_id, user_id, refresh_token, refresh_expires)
    )
    conn.commit()

    # Set httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="Strict",
        path="/auth/refresh",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    return {"access_token": access_token, "token_type": "bearer", "role": role}

@app.post("/auth/guest")
def login_guest(request: Request, response: Response):
    conn = get_db()
    is_sqlite = 'sqlite3' in str(type(conn))
    param = "?" if is_sqlite else "%s"
    
    # Generate Guest Token
    guest_token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(hours=GUEST_TOKEN_EXPIRE_HOURS)
    client_ip = request.client.host if request.client else "unknown"
    
    # Create guest access token as a real JWT
    access_token = create_access_token(
        data={"sub": f"guest_{guest_token[:8]}", "role": "guest", "jti": guest_token}, 
        expires_delta=timedelta(hours=GUEST_TOKEN_EXPIRE_HOURS)
    )

    # Record guest session
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT INTO dim_guest_sessions (guest_token, expires_at, ip_address) VALUES ({param}, {param}, {param})",
        (guest_token, expires, client_ip)
    )
    conn.commit()

    # Guest refresh token is just the guest token itself stored in cookie
    response.set_cookie(
        key="refresh_token",
        value=guest_token,
        httponly=True,
        samesite="Strict",
        path="/auth/refresh",
        max_age=GUEST_TOKEN_EXPIRE_HOURS * 60 * 60
    )

    return {"access_token": access_token, "token_type": "bearer", "role": "guest"}

@app.post("/auth/refresh")
def refresh_token(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    conn = get_db()
    is_sqlite = 'sqlite3' in str(type(conn))
    param = "?" if is_sqlite else "%s"
    cursor = conn.cursor()
    
    # Check if it's a guest token
    cursor.execute(
        f"SELECT guest_token FROM dim_guest_sessions WHERE guest_token = {param} AND expires_at > CURRENT_TIMESTAMP",
        (refresh_token,)
    )
    guest_res = cursor.fetchone()

    if guest_res:
        access_token = create_access_token(
            data={"sub": f"guest_{refresh_token[:8]}", "role": "guest", "jti": refresh_token}, 
            expires_delta=timedelta(hours=GUEST_TOKEN_EXPIRE_HOURS)
        )
        return {"access_token": access_token, "token_type": "bearer", "role": "guest"}
    
    # Otherwise check regular user session
    cursor.execute(
        f"SELECT user_id FROM dim_sessions WHERE refresh_token = {param} AND revoked = FALSE AND expires_at > CURRENT_TIMESTAMP", 
        (refresh_token,)
    )
    res = cursor.fetchone()

    if not res:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = res[0]
    cursor.execute(f"SELECT role FROM dim_users WHERE user_id = {param}", (user_id,))
    user_res = cursor.fetchone()
    role = user_res[0] if user_res else "viewer"

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id, "role": role}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "role": role}

@app.post("/auth/logout")
def logout(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        conn = get_db()
        is_sqlite = 'sqlite3' in str(type(conn))
        param = "?" if is_sqlite else "%s"
        cursor = conn.cursor()
        cursor.execute(f"UPDATE dim_sessions SET revoked = TRUE WHERE refresh_token = {param}", (refresh_token,))
        conn.commit()
        
    response.delete_cookie("refresh_token", path="/auth/refresh")
    return {"message": "Logged out successfully"}

@app.get("/auth/me")
def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"user_id": payload.get("sub"), "role": payload.get("role")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/auth/guest/pageview")
def guest_pageview(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        conn = get_db()
        is_sqlite = 'sqlite3' in str(type(conn))
        param = "?" if is_sqlite else "%s"
        cursor = conn.cursor()
        cursor.execute(f"UPDATE dim_guest_sessions SET page_views = page_views + 1 WHERE guest_token = {param}", (refresh_token,))
        conn.commit()
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}

# Mount Dashboard Static Files at Root (Must be last)
app.mount("/", StaticFiles(directory=dashboard_path, html=True), name="dashboard")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
