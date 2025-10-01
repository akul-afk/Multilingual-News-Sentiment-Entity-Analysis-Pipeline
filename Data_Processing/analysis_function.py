
import csv
import os
import ast
import pathlib
import sys
from datetime import date


import pandas as pd
import matplotlib.pyplot as plt


INPUT_FILE = "Data_Processing/raw_headlines_data.csv"


today = date.today().strftime("%Y_%m_%d")

OUTPUT_FILE = f"Data_Processing/processed_data_final_{today}.csv"
ENTITIES_OUTPUT_FILE = f"Data_Processing/processed_entities_final_{today}.csv"
CHART_DIR = "Data_Processing/Data_Output/Matplotlib_Charts"  


def load_and_clean_data(input_filepath):
    """
    Loads the raw CSV data, performs cleaning, standardization,
    and explodes the entity data for analysis.
    """
    try:
        df = pd.read_csv(input_filepath)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_filepath}.")
        print("Please ensure web_scraper.py has been run successfully.")
        return None, None
    except pd.errors.EmptyDataError:
        print(f"Error: Input file {input_filepath} is empty.")
        return None, None

    def clean_source(url):
        parts = url.split('/')
        if 'mundo' in parts: return 'BBC Spanish'
        if 'hindi' in parts: return 'BBC Hindi'
        if 'portuguese' in parts: return 'BBC Portuguese'
        if 'russian' in parts: return 'BBC Russian'
        if 'japanese' in parts: return 'BBC Japanese'
        if 'zhongwen' in parts: return 'BBC Chinese'
        return 'Other'

    df['Source_Name'] = df['Source_URL'].apply(clean_source)

    df['Entities_List'] = df['Entities_Raw'].apply(lambda x: ast.literal_eval(x) if pd.notna(x) and x.strip() else [])

    entities_df = df.explode('Entities_List').dropna(subset=['Entities_List'])
    entities_df[['Entity', 'Label']] = pd.DataFrame(
        entities_df['Entities_List'].tolist(), index=entities_df.index
    )
    df_entities_clean = entities_df[['Source_Name', 'Entity', 'Label']].copy()

    df_headlines_clean = df[['Source_Name', 'Original_Headline', 'Translated_Headline', 'Polarity']].copy()

    return df_headlines_clean, df_entities_clean
def generate_visualizations(df_headlines, df_entities, chart_dir):
    """Generates and saves Matplotlib charts."""
    pathlib.Path(chart_dir).mkdir(parents=True, exist_ok=True)
    sentiment_summary = df_headlines.groupby('Source_Name')['Polarity'].mean().sort_values()

    plt.figure(figsize=(10, 6))
    sentiment_summary.plot(kind='bar', color=['#4CAF50' if p > 0 else '#FF5722' for p in sentiment_summary.values])
    plt.title('Average Sentiment Polarity by News Source (0.0 = Neutral)', fontsize=14)
    plt.ylabel('Average Polarity')
    plt.xlabel('News Source')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(chart_dir, 'sentiment_by_source.png'))
    plt.close()
    print(f"   -> Saved: {os.path.join(chart_dir, 'sentiment_by_source.png')}")

    top_entities = df_entities[df_entities['Label'].isin(['ORG', 'PERSON', 'GPE'])]['Entity'].value_counts().head(10)

    plt.figure(figsize=(10, 6))
    top_entities.sort_values().plot(kind='barh', color='#2196F3')
    plt.title('Top 10 Named Entities Across All Sources', fontsize=14)
    plt.xlabel('Frequency')
    plt.ylabel('Entity Name')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(chart_dir, 'top_entities.png'))
    plt.close()
    print(f"   -> Saved: {os.path.join(chart_dir, 'top_entities.png')}")


def run_analysis_pipeline():
    """Main function to run the full data processing and visualization."""
    print("\n--- Starting Data Cleaning, Processing, and Matplotlib Visualization ---")

    df_headlines, df_entities = load_and_clean_data(INPUT_FILE)

    if df_headlines is None:
        return None, None

    df_headlines.to_csv(OUTPUT_FILE, index=False)
    df_entities.to_csv(ENTITIES_OUTPUT_FILE, index=False)
    print(f"   -> Clean headlines saved to {OUTPUT_FILE}")
    print(f"   -> Clean entities saved to {ENTITIES_OUTPUT_FILE}")

    generate_visualizations(df_headlines, df_entities, CHART_DIR)

    print("--- Data Processing Complete ---")
    return df_headlines, df_entities


if __name__ == "__main__":

    run_analysis_pipeline()
