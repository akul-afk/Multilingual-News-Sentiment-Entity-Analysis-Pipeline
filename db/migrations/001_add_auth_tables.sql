-- 001_add_auth_tables.sql

CREATE TABLE IF NOT EXISTS dim_users (
    user_id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'viewer',
    status VARCHAR(20) DEFAULT 'active',
    last_login_at TIMESTAMP NULL,
    failed_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    refresh_token TEXT NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    revoked BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES dim_users(user_id)
);

CREATE TABLE IF NOT EXISTS dim_token_blacklist (
    jti VARCHAR(36) PRIMARY KEY,
    expires_at TIMESTAMP NOT NULL,
    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_guest_sessions (
    guest_token VARCHAR(36) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    page_views INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dim_audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(36),
    event_type VARCHAR(50) NOT NULL,
    description TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
