"""
Database Connector Module
Handles MySQL (Aiven) and SQLite (local fallback) data persistence.
Supports upsert semantics for idempotent headline/entity ingestion.
"""

import os
import sys
import logging
import sqlite3
from typing import Dict, Optional, Tuple

import mysql.connector
import pandas as pd
from mysql.connector import errorcode

logger = logging.getLogger(__name__)

if __name__ == "__main__":

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
    try:
        from analysis_function import run_analysis_pipeline
    except ImportError:
        pass

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_DATABASE', 'NewsHeadlines'),
    'user': os.environ.get('DB_USER', 'root'), 

    'password': os.environ.get('DB_PASSWORD', 'local_password'),
    
    'port': int(os.environ.get('DB_PORT', 3306))
}

HEADLINES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS headlines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL,
    original_headline TEXT,
    translated_headline TEXT,
    polarity DECIMAL(3, 2),
    scrape_date DATE DEFAULT (CURRENT_DATE)
);
"""

HEADLINES_UNIQUE_INDEX_SQL = """
ALTER TABLE headlines 
ADD UNIQUE INDEX idx_unique_headline (translated_headline(255), source_name);
"""

ENTITIES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS entities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    headline_id INT NOT NULL,
    entity_text VARCHAR(255) NOT NULL,
    entity_label VARCHAR(50) NOT NULL,
    FOREIGN KEY (headline_id) REFERENCES headlines(id) ON DELETE CASCADE
);
"""

def get_auth_connection(is_sqlite=False):
    """Returns an active connection for auth queries."""
    if is_sqlite:
        conn = sqlite3.connect('Data_Processing/news_headlines.db', check_same_thread=False)
        return conn
    else:
        try:
            return mysql.connector.connect(host=DB_CONFIG['host'], user=DB_CONFIG['user'], password=DB_CONFIG['password'], port=DB_CONFIG['port'], database=DB_CONFIG['database'])
        except Exception as e:
            logger.error(f"MySQL auth connection failed: {e}")
            return sqlite3.connect('Data_Processing/news_headlines.db', check_same_thread=False)

def ensure_auth_tables(cursor, is_sqlite=False):
    """Ensure auth tables exist for dual-write."""
    # SQLite fallback creation (MySQL is done via migrations script if possible, but let's ensure here too)
    sqls = [
        """CREATE TABLE IF NOT EXISTS dim_users (
            user_id VARCHAR(36) PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT 'viewer',
            status VARCHAR(20) DEFAULT 'active',
            last_login_at TIMESTAMP NULL,
            failed_attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS dim_sessions (
            session_id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            refresh_token TEXT NOT NULL,
            ip_address VARCHAR(45),
            user_agent TEXT,
            revoked BOOLEAN DEFAULT FALSE,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES dim_users(user_id)
        )""",
        """CREATE TABLE IF NOT EXISTS dim_token_blacklist (
            jti VARCHAR(36) PRIMARY KEY,
            expires_at TIMESTAMP NOT NULL,
            blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS dim_guest_sessions (
            guest_token VARCHAR(36) PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            ip_address VARCHAR(45),
            page_views INTEGER DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS dim_audit_log (
            log_id %s,
            user_id VARCHAR(36),
            event_type VARCHAR(50) NOT NULL,
            description TEXT,
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""" % ("INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "INT AUTO_INCREMENT PRIMARY KEY")
    ]
    for sql in sqls:
        try:
            cursor.execute(sql)
        except Exception as e:
            logger.warning(f"Error creating auth tables: {e}")


def create_database_and_tables(cnx, cursor) -> bool:
    """Create the database and tables if they don't exist. Returns True on success."""
    try:
        cnx.database = DB_CONFIG['database']
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            
            try:
                
                temp_cnx = mysql.connector.connect(host=DB_CONFIG['host'], user=DB_CONFIG['user'],
                                                   password=DB_CONFIG['password'], port=DB_CONFIG['port'])
                temp_cursor = temp_cnx.cursor()
                temp_cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
                temp_cursor.close()
                temp_cnx.close()

                cnx.database = DB_CONFIG['database']
            except mysql.connector.Error as err:
                return False
        else:
            return False

    try:
        cursor.execute(HEADLINES_TABLE_SQL)
        
        try:
            cursor.execute(HEADLINES_UNIQUE_INDEX_SQL)
        except mysql.connector.Error as err:
            if err.errno != errorcode.ER_DUP_KEYNAME and "Duplicate entry" not in str(err):
                 raise err 

        cursor.execute(ENTITIES_TABLE_SQL)
        ensure_auth_tables(cursor, is_sqlite=False)
        return True
    except mysql.connector.Error as err:
        return False


def insert_data_to_sqlite(df_headlines: pd.DataFrame, df_entities: pd.DataFrame) -> Tuple[int, int]:
    """Fallback to local SQLite if MySQL is unreachable. Returns (headlines_count, entities_count)."""
    logger.warning("Falling back to local SQLite database...")
    try:
        conn = sqlite3.connect('Data_Processing/news_headlines.db')
        cursor = conn.cursor()
        
        ensure_auth_tables(cursor, is_sqlite=True)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS headlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            original_headline TEXT,
            translated_headline TEXT,
            polarity REAL,
            scrape_date TEXT DEFAULT (DATE('now')),
            UNIQUE(translated_headline, source_name)
        );
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            headline_id INTEGER NOT NULL,
            entity_text TEXT NOT NULL,
            entity_label TEXT NOT NULL,
            FOREIGN KEY (headline_id) REFERENCES headlines(id) ON DELETE CASCADE
        );
        """)
        
        headline_map = {}
        df_headlines = df_headlines.reset_index(drop=True)
        
        for index, row in df_headlines.iterrows():
            try:
                # SQLite uses ? instead of %s
                cursor.execute(
                    "INSERT OR IGNORE INTO headlines (source_name, original_headline, translated_headline, polarity, scrape_date) VALUES (?, ?, ?, ?, ?)",
                    (row['Source_Name'], row['Original_Headline'], row['Translated_Headline'], row['Polarity'], row['Scrape_Date'])
                )
                
                # Get the ID (either newly inserted or existing)
                cursor.execute("SELECT id FROM headlines WHERE translated_headline = ? AND source_name = ? LIMIT 1", 
                               (row['Translated_Headline'], row['Source_Name']))
                res = cursor.fetchone()
                if res:
                    headline_map[index] = res[0]
            except sqlite3.Error as e:
                print(f"Error inserting headline to SQLite: {e}")

        entities_inserted_count = 0
        # To correctly link entities, we should NOT reset_index(drop=True) on df_entities
        # if the indices correspond to the original df_headlines indices.
        # analysis_function.py returns df_entities where the index matches df_headlines.
        
        for index, row in df_entities.iterrows():
            # index here refers to the headline's index in df_headlines
            headline_id = headline_map.get(index)
            if headline_id:
                try:
                    cursor.execute(
                        "INSERT INTO entities (headline_id, entity_text, entity_label) VALUES (?, ?, ?)",
                        (headline_id, row['Entity'], row['Label'])
                    )
                    entities_inserted_count += 1
                except sqlite3.Error as e:
                    print(f"    [DB] Error inserting entity: {e}")

        conn.commit()
        logger.info(f"Successfully inserted data to local SQLite: {len(headline_map)} headlines, {entities_inserted_count} entities")
        cursor.close()
        conn.close()
        return len(headline_map), entities_inserted_count
    except Exception as e:
        logger.error(f"SQLite fallback failed: {e}")
        return 0, 0

def insert_data_to_mysql(df_headlines: pd.DataFrame, df_entities: pd.DataFrame) -> Tuple[int, int]:
    """Insert headline and entity DataFrames into MySQL with upsert semantics. Returns (headlines_count, entities_count)."""
    
    try:
        cnx = mysql.connector.connect(host=DB_CONFIG['host'], user=DB_CONFIG['user'], password=DB_CONFIG['password'],
                                     port=DB_CONFIG['port'], connection_timeout=5)
        cursor = cnx.cursor()
    except mysql.connector.Error as err:
        logger.error(f"MySQL connection failed ({err.errno}).")
        return insert_data_to_sqlite(df_headlines, df_entities)

    if not create_database_and_tables(cnx, cursor):
        logger.error("Database/Table creation failed.")
        cursor.close()
        cnx.close()
        return insert_data_to_sqlite(df_headlines, df_entities)

    headline_insert_query = (
        "INSERT INTO headlines (source_name, original_headline, translated_headline, polarity, scrape_date) "
        "VALUES (%s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)"
    )

    headline_map = {}
    headlines_inserted_count = 0
    
    df_headlines = df_headlines.reset_index(drop=True) 

    for index, row in df_headlines.iterrows():
        headline_data = (
            row['Source_Name'], 
            row['Original_Headline'], 
            row['Translated_Headline'], 
            row['Polarity'],
            row['Scrape_Date']
        )
        try:
            cursor.execute(headline_insert_query, headline_data)
            
            if cursor.rowcount == 1:
                headline_id = cursor.lastrowid
                headline_map[index] = headline_id
                headlines_inserted_count += 1
            else:
                select_id_query = "SELECT id FROM headlines WHERE translated_headline = %s AND source_name = %s LIMIT 1"
                cursor.execute(select_id_query, (row['Translated_Headline'], row['Source_Name']))
                existing_id = cursor.fetchone()
                if existing_id:
                     headline_map[index] = existing_id[0]
                
        except mysql.connector.Error:
            pass
            
    entity_insert_query = (
        "INSERT INTO entities (headline_id, entity_text, entity_label) "
        "VALUES (%s, %s, %s)"
    )

    entities_inserted_count = 0
    df_entities = df_entities.reset_index(drop=True) 
    
    for index, row in df_entities.iterrows():
        headline_id = headline_map.get(index)

        if headline_id:
            entity_data = (headline_id, row['Entity'], row['Label'])
            try:
                cursor.execute(entity_insert_query, entity_data)
                entities_inserted_count += 1
            except mysql.connector.Error:
                pass

    cnx.commit()

    cursor.close()
    cnx.close()
    
    return headlines_inserted_count, entities_inserted_count


if __name__ == "__main__":
    
    try:
        df_h, df_e = run_analysis_pipeline() 
        if df_h is not None:
            insert_data_to_mysql(df_h, df_e)
    except NameError:
        pass