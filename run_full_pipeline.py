import os
import sys


sys.path.append(os.getcwd())


# CORRECTED IMPORTS: Now Python finds 'web_scraper' inside the 
# 'Scraping_Scripts' folder and 'analysis_function' inside the 'Data_Processing' folder.
from Scraping_Scripts.web_scraper import main as run_scraper
from Data_Processing.analysis_function import run_analysis_pipeline
from Data_Processing.db_connector import insert_data_to_mysql


def run_full_pipeline():
    print("==========================================================")
    print("         STARTING FULL NEWS HEADLINE ANALYSIS PIPELINE    ")
    print("==========================================================")

    print("\n[STEP 1/3] Running Web Scraper...")
    run_scraper()
    print("[STEP 1/3] Complete.")
    
    print("\n[STEP 2/3] Running Data Cleaning and Analysis...")
    df_headlines, df_entities = run_analysis_pipeline()

    if df_headlines is None:
        print("\n!!! PIPELINE FAILED at Data Analysis. Check previous errors. !!!")
        return
        
    print("[STEP 2/3] Complete.")
    
    print("\n[STEP 3/3] Inserting Data into MySQL...")
    insert_data_to_mysql(df_headlines, df_entities)
    print("[STEP 3/3] Complete.")

    print("\n==========================================================")
    print("         PIPELINE SUCCESSFUL! Data is ready for Power BI. ")
    print("==========================================================")


if __name__ == "__main__":
    run_full_pipeline()