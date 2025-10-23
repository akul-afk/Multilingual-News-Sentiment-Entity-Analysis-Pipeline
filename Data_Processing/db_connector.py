import os
import sys

import mysql.connector
import pandas as pd
from mysql.connector import errorcode

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


def create_database_and_tables(cnx, cursor):
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
        return True
    except mysql.connector.Error as err:
        return False


def insert_data_to_mysql(df_headlines, df_entities):
    
    try:
        cnx = mysql.connector.connect(host=DB_CONFIG['host'], user=DB_CONFIG['user'], password=DB_CONFIG['password'],
                                     port=DB_CONFIG['port'])
        cursor = cnx.cursor()
    except mysql.connector.Error as err:
        return

    if not create_database_and_tables(cnx, cursor):
        cursor.close()
        cnx.close()
        return

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


if __name__ == "__main__":
    
    try:
        df_h, df_e = run_analysis_pipeline() 
        if df_h is not None:
            insert_data_to_mysql(df_h, df_e)
    except NameError:
        pass