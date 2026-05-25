
import pandas as pd
import glob
import os
import re

def patch_csvs():
    files = glob.glob('cleaned_csv_daily/processed_data_final_*.csv')
    for f in files:
        df = pd.read_csv(f)
        changed = False
        
        # Infer date from filename
        match = re.search(r'processed_data_final_(\d{4}_\d{2}_\d{2})\.csv', f)
        if match:
            file_date = match.group(1)
        else:
            file_date = 'unknown'

        if 'Source_Name' not in df.columns:
            print(f"[*] Patching Source_Name in {f}")
            df['Source_Name'] = 'BBC News'
            changed = True
            
        if 'Scrape_Date' not in df.columns:
            print(f"[*] Patching Scrape_Date in {f} with {file_date}")
            df['Scrape_Date'] = file_date
            changed = True
        elif df['Scrape_Date'].isnull().any():
            print(f"[*] Fixing NaNs in Scrape_Date in {f}")
            df['Scrape_Date'] = df['Scrape_Date'].fillna(file_date)
            changed = True
            
        if changed:
            df.to_csv(f, index=False)

if __name__ == "__main__":
    patch_csvs()
