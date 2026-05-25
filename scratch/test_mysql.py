
import os
import sys
from dotenv import load_dotenv
import mysql.connector

load_dotenv()
config = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'database': os.environ.get('DB_DATABASE')
}

print(f"Connecting to {config['host']}...")
try:
    cnx = mysql.connector.connect(**config, connection_timeout=10)
    print("Connected to MySQL!")
    cnx.close()
except Exception as e:
    print(f"MySQL Connection Failed: {e}")
