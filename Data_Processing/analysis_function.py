"""
Analysis & Cleaning Module
Cleans raw scraped CSVs, categorizes sources, extracts entities,
and generates Matplotlib visualizations.
"""
import os
import ast
import logging
from pathlib import Path
from datetime import date
import glob
from typing import Optional, Tuple

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

today = date.today().strftime("%Y_%m_%d")
PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_FILE = PROJECT_ROOT / f"raw_csv_daily/raw_headlines_data_{today}.csv"

OUTPUT_DIR = PROJECT_ROOT / "cleaned_csv_daily"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / f"processed_data_final_{today}.csv"
ENTITIES_OUTPUT_FILE = OUTPUT_DIR / f"processed_entities_final_{today}.csv"

CHART_DIR = PROJECT_ROOT / "Data_Output/Matplotlib_Charts"


def load_cumulative_entities(entities_dir: Path) -> pd.DataFrame:
    """Load all entity CSVs in the directory and merge them into one DataFrame."""
    all_files = glob.glob(os.path.join(entities_dir, "processed_entities_final_*.csv"))
    
    if not all_files:
        return pd.DataFrame()
        
    df_list = []
    for filename in all_files:
        try:
            df_list.append(pd.read_csv(filename))
        except pd.errors.EmptyDataError:
            continue
        
    if not df_list:
        return pd.DataFrame()
        
    return pd.concat(df_list, ignore_index=True)


def load_and_clean_data(input_filepath: Path) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Load raw CSV data, clean it, categorize sources, and return (headlines_df, entities_df)."""
    try:
        df = pd.read_csv(input_filepath)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        logger.error(f"File not found or empty: {input_filepath}")
        return None, None

    def clean_source(url: str) -> str:
        """Map a raw source URL to its human-readable BBC service name."""
        parts = url.split('/')
        if 'mundo' in parts: return 'BBC Spanish'
        if 'hindi' in parts: return 'BBC Hindi'
        if 'portuguese' in parts: return 'BBC Portuguese'
        if 'russian' in parts: return 'BBC Russian'
        if 'japanese' in parts: return 'BBC Japanese'
        if 'swahili' in parts: return 'BBC Swahili'
        return 'Other'

    df['Source_Name'] = df['Source_URL'].apply(clean_source)

    df['Entities_List'] = df['Entities_Raw'].apply(lambda x: ast.literal_eval(x) if pd.notna(x) and x.strip() else [])

    entities_df = df.explode('Entities_List').dropna(subset=['Entities_List'])
    entities_df[['Entity', 'Label']] = pd.DataFrame(
        entities_df['Entities_List'].tolist(), index=entities_df.index
    )
    df_entities_clean = entities_df[['Source_Name', 'Entity', 'Label', 'Scrape_Date']].copy()

    df_headlines_clean = df[['Source_Name', 'Original_Headline', 'Translated_Headline', 'Polarity','Scrape_Date']].copy()

    return df_headlines_clean, df_entities_clean


def generate_visualizations(df_headlines, df_entities_cumulative, chart_dir):
    pathlib.Path(chart_dir).mkdir(parents=True, exist_ok=True)
    
    sentiment_summary = df_headlines.groupby('Source_Name')['Polarity'].mean().sort_values()

    plt.figure(figsize=(10, 6))
    sentiment_summary.plot(kind='bar', color=['#4CAF50' if p > 0 else '#FF5722' for p in sentiment_summary.values])
    plt.title('Average Sentiment Polarity by News Source (Daily Score)', fontsize=14)
    plt.ylabel('Average Polarity')
    plt.xlabel('News Source')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(chart_dir, f'sentiment_by_source_{today}.png')) 
    plt.close()

    if not df_entities_cumulative.empty:
        top_entities = df_entities_cumulative[df_entities_cumulative['Label'].isin(['ORG', 'PERSON', 'GPE'])]['Entity'].value_counts().head(10)

        plt.figure(figsize=(10, 6))
        top_entities.sort_values().plot(kind='barh', color='#2196F3')
        plt.title('Top 10 Named Entities (Cumulative)', fontsize=14)
        plt.xlabel('Frequency')
        plt.ylabel('Entity Name')
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(chart_dir, 'top_entities.png'))
        plt.close()


def run_analysis_pipeline():
    df_headlines, df_entities = load_and_clean_data(INPUT_FILE)

    if df_headlines is None:
        return None, None

    df_headlines.to_csv(OUTPUT_FILE, index=False)
    df_entities.to_csv(ENTITIES_OUTPUT_FILE, index=False)

    df_entities_cumulative = load_cumulative_entities(OUTPUT_DIR)
    
    generate_visualizations(df_headlines, df_entities_cumulative, CHART_DIR)

    # Generate dashboard JSON data
    try:
        from Data_Processing.data_aggregator import generate_dashboard_data
        print("\n[STEP 2.5] Generating dashboard JSON data...")
        generate_dashboard_data()
    except ImportError:
        try:
            from data_aggregator import generate_dashboard_data
            print("\n[STEP 2.5] Generating dashboard JSON data...")
            generate_dashboard_data()
        except ImportError:
            print("  [WARNING] data_aggregator module not found, skipping JSON generation.")

    return df_headlines, df_entities


if __name__ == "__main__":
    run_analysis_pipeline()