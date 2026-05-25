import sqlite3
import os

SQLITE_PATH = r'c:\Users\akulc\Desktop\DA\NewsScraping2\Data_Processing\news_headlines.db'

def check_db():
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT period_type, period_start, model_used FROM summaries ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
