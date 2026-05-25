import sqlite3
import mysql.connector
import os

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_DATABASE', 'NewsHeadlines'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'local_password'),
    'port': int(os.environ.get('DB_PORT', 3306))
}

SQLITE_PATH = r'c:\Users\akulc\Desktop\DA\NewsScraping2\Data_Processing\news_headlines.db'

def update_sqlite():
    print("Updating SQLite...")
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(summaries)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'model_used' not in columns:
            cursor.execute("ALTER TABLE summaries ADD COLUMN model_used VARCHAR(60)")
            conn.commit()
            print("Added model_used to SQLite summaries table.")
        else:
            print("model_used already exists in SQLite.")
        conn.close()
    except Exception as e:
        print(f"Error updating SQLite: {e}")

def update_mysql():
    print("Updating MySQL...")
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()
        cursor.execute("DESCRIBE summaries")
        columns = [row[0] for row in cursor.fetchall()]
        if 'model_used' not in columns:
            cursor.execute("ALTER TABLE summaries ADD COLUMN model_used VARCHAR(60)")
            cnx.commit()
            print("Added model_used to MySQL summaries table.")
        else:
            print("model_used already exists in MySQL.")
        cursor.close()
        cnx.close()
    except Exception as e:
        print(f"Error updating MySQL: {e}")

if __name__ == "__main__":
    update_sqlite()
    # update_mysql() # Only if environment variables are set and MySQL is reachable
