
import pandas as pd
import glob
import os

for f in glob.glob('cleaned_csv_daily/processed_data_final_*.csv'):
    try:
        df = pd.read_csv(f)
        if 'Scrape_Date' not in df.columns:
            print(f"File {f} is MISSING Scrape_Date column. Columns: {list(df.columns)}")
            continue
        if df['Scrape_Date'].isnull().any():
            print(f"File {f} has {df['Scrape_Date'].isnull().sum()} NaNs in Scrape_Date")
    except Exception as e:
        print(f"Error reading {f}: {e}")
