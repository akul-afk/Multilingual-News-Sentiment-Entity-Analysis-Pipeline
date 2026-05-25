
import pandas as pd
from pathlib import Path

def fix_raw_csv():
    file_path = Path('raw_csv_daily/raw_headlines_data_2026_05_16.csv')
    if not file_path.exists():
        print("File not found.")
        return
        
    df = pd.read_csv(file_path)
    
    def get_source_name(url):
        if 'mundo' in url: return 'BBC Spanish'
        if 'hindi' in url: return 'BBC Hindi'
        if 'portuguese' in url: return 'BBC Portuguese'
        if 'russian' in url: return 'BBC Russian'
        if 'japanese' in url: return 'BBC Japanese'
        if 'swahili' in url: return 'BBC Swahili'
        if 'aljazeera' in url: return 'Al Jazeera'
        if 'france24' in url: return 'France 24'
        if 'thehindu' in url: return 'The Hindu'
        if 'apnews' in url: return 'AP News'
        if 'nytimes' in url: return 'NYT World'
        return 'Other'

    if 'Source_Name' not in df.columns:
        df.insert(1, 'Source_Name', df['Source_URL'].apply(get_source_name))
        df.to_csv(file_path, index=False)
        print("Fixed Source_Name in raw CSV.")
    else:
        print("Source_Name already exists.")

if __name__ == "__main__":
    fix_raw_csv()
