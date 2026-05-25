
import sqlite3
conn = sqlite3.connect('Data_Processing/news_headlines.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM headlines WHERE scrape_date = '2026_05_16'")
print(f"Headlines for today: {cursor.fetchone()[0]}")
cursor.execute("SELECT MAX(scrape_date) FROM headlines")
print(f"Max date: {cursor.fetchone()[0]}")
conn.close()
