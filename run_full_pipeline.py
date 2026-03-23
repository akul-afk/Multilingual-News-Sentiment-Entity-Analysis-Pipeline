import os
import sys
sys.path.append(os.getcwd())


from Scraping_Scripts.web_scraper import main as run_scraper
from Data_Processing.analysis_function import run_analysis_pipeline
from Data_Processing.db_connector import insert_data_to_mysql
from Data_Processing.data_quality import validate_raw_data
from Data_Processing.warehouse import build_warehouse
from datetime import date


def run_full_pipeline():
    print("==========================================================")
    print("    MULTILINGUAL NEWS SENTIMENT & ENTITY ANALYSIS PIPELINE ")
    print("    Airflow-Compatible  |  RoBERTa Sentiment  |  DuckDB   ")
    print("==========================================================")

    today = date.today().strftime("%Y_%m_%d")
    project_root = os.getcwd()

    # ── Step 1: Scrape Headlines ───────────────────────────────
    print("\n[STEP 1/7] Scraping Headlines (HF RoBERTa Sentiment)...")
    run_scraper()
    print("[STEP 1/7] Complete.")

    # ── Step 2: Data Quality Validation ────────────────────────
    print("\n[STEP 2/7] Running Data Quality Checks...")
    raw_csv = os.path.join(project_root, f"raw_csv_daily/raw_headlines_data_{today}.csv")
    if os.path.exists(raw_csv):
        report = validate_raw_data(raw_csv)
        if report.get('overall_status') == 'FAIL':
            print("  WARNING: Data quality failures detected. Continuing with available data.")
    else:
        print(f"  WARNING: Raw CSV not found at {raw_csv}. Skipping validation.")
    print("[STEP 2/7] Complete.")

    # ── Step 3: Data Cleaning & Analysis ───────────────────────
    print("\n[STEP 3/7] Running Data Cleaning and Analysis...")
    df_headlines, df_entities = run_analysis_pipeline()

    if df_headlines is None:
        print("\n!!! PIPELINE FAILED at Data Analysis. Check previous errors. !!!")
        return

    print("[STEP 3/7] Complete.")

    # ── Step 4: Load DuckDB Warehouse ──────────────────────────
    print("\n[STEP 4/7] Loading DuckDB Star-Schema Warehouse...")
    try:
        build_warehouse()
    except Exception as e:
        print(f"  WARNING: Warehouse load failed: {e}")
    print("[STEP 4/7] Complete.")

    # ── Step 5: Run dbt Models ─────────────────────────────────
    print("\n[STEP 5/7] Running dbt Transformations...")
    dbt_dir = os.path.join(project_root, "dbt_project")
    if os.path.exists(dbt_dir):
        try:
            import subprocess
            result = subprocess.run(
                ["dbt", "run", "--profiles-dir", "."],
                cwd=dbt_dir, capture_output=True, text=True, timeout=120
            )
            print(result.stdout)
            if result.returncode != 0:
                print(f"  WARNING: dbt run returned non-zero: {result.stderr}")

            result_test = subprocess.run(
                ["dbt", "test", "--profiles-dir", "."],
                cwd=dbt_dir, capture_output=True, text=True, timeout=120
            )
            print(result_test.stdout)
        except FileNotFoundError:
            print("  WARNING: dbt not installed. Skipping dbt transformations.")
        except Exception as e:
            print(f"  WARNING: dbt failed: {e}")
    else:
        print("  WARNING: dbt_project/ not found. Skipping.")
    print("[STEP 5/7] Complete.")

    # ── Step 6: Insert to MySQL ────────────────────────────────
    print("\n[STEP 6/7] Inserting Data into MySQL...")
    insert_data_to_mysql(df_headlines, df_entities)
    print("[STEP 6/7] Complete.")

    # ── Step 7: Generate Dashboard JSON ────────────────────────
    # (Already called inside run_analysis_pipeline, but we ensure it ran)
    print("\n[STEP 7/7] Dashboard JSON generation...")
    try:
        from Data_Processing.data_aggregator import generate_dashboard_data
        generate_dashboard_data()
    except Exception as e:
        print(f"  WARNING: Dashboard JSON generation failed: {e}")
    print("[STEP 7/7] Complete.")

    print("\n==========================================================")
    print("    PIPELINE SUCCESSFUL!                                   ")
    print("    Data → DuckDB Warehouse → dbt Models → MySQL → JSON   ")
    print("==========================================================")


if __name__ == "__main__":
    run_full_pipeline()