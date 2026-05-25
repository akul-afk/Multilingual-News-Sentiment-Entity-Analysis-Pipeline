
import os
import sys
import pandas as pd
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = Path(os.getcwd())
sys.path.insert(0, str(PROJECT_ROOT))

from Data_Processing.db_connector import insert_data_to_mysql
from Data_Processing.data_aggregator import generate_dashboard_data

def force_ingest_and_aggregate():
    today = date.today().strftime("%Y_%m_%d")
    
    print(f"[*] Loading processed data for {today}...")
    h_file = PROJECT_ROOT / "cleaned_csv_daily" / f"processed_data_final_{today}.csv"
    e_file = PROJECT_ROOT / "cleaned_csv_daily" / f"processed_entities_final_{today}.csv"
    
    if not h_file.exists():
        print(f"Error: {h_file} not found.")
        return
        
    df_h = pd.read_csv(h_file)
    df_e = pd.read_csv(e_file)
    
    print("[*] Ingesting to Database (MySQL fallback to SQLite)...")
    h_count, e_count = insert_data_to_mysql(df_h, df_e)
    print(f"Done: {h_count} headlines, {e_count} entities inserted.")
    
    print("[*] Generating Dashboard Data...")
    generate_dashboard_data()
    print("[*] All done.")

if __name__ == "__main__":
    force_ingest_and_aggregate()
