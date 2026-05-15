import os
import sqlite3
import mysql.connector
from dotenv import load_dotenv
import bcrypt
import uuid

load_dotenv()

SQLITE_DB_PATH = "Data_Processing/news_headlines.db"
MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")

def get_mysql_conn():
    try:
        return mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
            database=os.environ.get("DB_DATABASE", "NewsHeadlines"),
            port=int(os.environ.get("DB_PORT", 3306))
        )
    except Exception as e:
        print(f"Could not connect to MySQL: {e}")
        return None

def get_sqlite_conn():
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    return sqlite3.connect(SQLITE_DB_PATH)

def run_migration_file(conn, file_path, is_mysql=False):
    with open(file_path, 'r') as f:
        sql = f.read()
    
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    cursor = conn.cursor()
    for stmt in statements:
        # SQLite doesn't support some MySQL specific types easily, but these CREATE TABLE IF NOT EXISTS are standard enough
        if not is_mysql:
            # Simple fix for SQLite (no TIMESTAMP DEFAULT CURRENT_TIMESTAMP unless we do it correctly, but SQLite handles it)
            pass
        try:
            cursor.execute(stmt)
        except Exception as e:
            print(f"Error executing {stmt[:50]}: {e}")
    conn.commit()

def seed_admin(conn, is_mysql=False):
    cursor = conn.cursor()
    
    # Check if admin exists
    admin_user = os.environ.get("ADMIN_USER", "admin")
    admin_pass = os.environ.get("ADMIN_PASS", "admin123")
    
    if is_mysql:
        cursor.execute("SELECT user_id FROM dim_users WHERE username = %s", (admin_user,))
    else:
        cursor.execute("SELECT user_id FROM dim_users WHERE username = ?", (admin_user,))
        
    res = cursor.fetchone()
    if res:
        print(f"Admin '{admin_user}' already exists.")
        return

    admin_hash = bcrypt.hashpw(admin_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin_id = str(uuid.uuid4())
    
    if is_mysql:
        cursor.execute(
            "INSERT INTO dim_users (user_id, username, email, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
            (admin_id, admin_user, f"{admin_user}@example.com", admin_hash, "admin")
        )
    else:
        cursor.execute(
            "INSERT INTO dim_users (user_id, username, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (admin_id, admin_user, f"{admin_user}@example.com", admin_hash, "admin")
        )
    conn.commit()
    print(f"Admin '{admin_user}' created.")

def main():
    migration_files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql')])
    
    # Run for SQLite
    sqlite_conn = get_sqlite_conn()
    print("Running migrations for SQLite...")
    for f in migration_files:
        print(f"  Running {f}...")
        run_migration_file(sqlite_conn, os.path.join(MIGRATIONS_DIR, f), is_mysql=False)
    seed_admin(sqlite_conn, is_mysql=False)
    sqlite_conn.close()

    # Run for MySQL if available
    mysql_conn = get_mysql_conn()
    if mysql_conn:
        print("Running migrations for MySQL...")
        for f in migration_files:
            print(f"  Running {f}...")
            run_migration_file(mysql_conn, os.path.join(MIGRATIONS_DIR, f), is_mysql=True)
        seed_admin(mysql_conn, is_mysql=True)
        mysql_conn.close()
    else:
        print("Skipping MySQL migrations (connection failed).")

if __name__ == "__main__":
    main()
