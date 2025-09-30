
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
        print("Warning: analysis_functions not found. Database connector cannot run in standalone mode without data.")

DB_CONFIG = {
    'host': 'localhost',
    'database': 'NewsAnalysisDB',
    'user': 'root', 
    'password': '4KUL@mysql',
    'port': 3306
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
    """Creates the database and tables if they do not exist."""
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
                print(f"   -> Database '{DB_CONFIG['database']}' created successfully.")
            except mysql.connector.Error as err:
                print(f"   -> Failed to create database: {err}")
                return False
        else:
            print(f"   -> Database connection error: {err}")
            return False

    try:
        cursor.execute(HEADLINES_TABLE_SQL)
        print("   -> 'headlines' table verified/created.")
        cursor.execute(ENTITIES_TABLE_SQL)
        print("   -> 'entities' table verified/created.")
        return True
    except mysql.connector.Error as err:
        print(f"   -> Error creating tables: {err}")
        return False


def insert_data_to_mysql(df_headlines, df_entities):
    """Inserts processed Pandas DataFrames into MySQL tables."""
    print("\n--- Starting MySQL Data Insertion ---")

    # Establish Connection
    try:
        cnx = mysql.connector.connect(host=DB_CONFIG['host'], user=DB_CONFIG['user'], password=DB_CONFIG['password'],
                                      port=DB_CONFIG['port'])
        cursor = cnx.cursor()
    except mysql.connector.Error as err:
        print(f"Error: Could not connect to MySQL. Check credentials and server status.")
        print(f"Error details: {err}")
        return

    if not create_database_and_tables(cnx, cursor):
        cursor.close()
        cnx.close()
        return


    headline_insert_query = (
        "INSERT INTO headlines (source_name, original_headline, translated_headline, polarity) "
        "VALUES (%s, %s, %s, %s)"
    )

    headline_map = {}

    for index, row in df_headlines.iterrows():
        headline_data = (row['Source_Name'], row['Original_Headline'], row['Translated_Headline'], row['Polarity'])
        try:
            cursor.execute(headline_insert_query, headline_data)
            headline_id = cursor.lastrowid
            headline_map[index] = headline_id 
        except mysql.connector.Error as err:
            print(f"Error inserting headline: {err}")
    entity_insert_query = (
        "INSERT INTO entities (headline_id, entity_text, entity_label) "
        "VALUES (%s, %s, %s)"
    )

    entities_inserted_count = 0
    for index, row in df_entities.iterrows():
        headline_id = headline_map.get(index)

        if headline_id:
            entity_data = (headline_id, row['Entity'], row['Label'])
            try:
                cursor.execute(entity_insert_query, entity_data)
                entities_inserted_count += 1
            except mysql.connector.Error as err:
                print(f"Error inserting entity: {err}")

    cnx.commit()

    print(f"   -> Successfully inserted {len(df_headlines)} headlines and {entities_inserted_count} entities.")
    print("--- MySQL Data Insertion Complete ---")

    cursor.close()
    cnx.close()


if __name__ == "__main__":
 
    print("Running db_connector standalone...")
 
    try:
        df_h, df_e = run_analysis_pipeline()
        if df_h is not None:
            insert_data_to_mysql(df_h, df_e)
    except NameError:
        print("Cannot run standalone: Missing run_analysis_pipeline import.")
