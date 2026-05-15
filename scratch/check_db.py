import sqlite3
import os

db_path = 'Data_Processing/news_headlines.db'
if not os.path.exists(db_path):
    print(f"Database {db_path} does not exist.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in SQLite database:")
    for t in tables:
        table_name = t[0]
        print(f"\n - {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"    - {col[1]} ({col[2]})")
    conn.close()
