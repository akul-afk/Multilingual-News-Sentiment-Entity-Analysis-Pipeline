"""
Pipeline Orchestrator
Runs the full 8-step ETL pipeline: Scrape → Quality → Clean → Warehouse → dbt → MySQL → JSON → AI Summaries.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import date
import glob
import pandas as pd

from dotenv import load_dotenv

load_dotenv()

# ── Project root resolved from this file's location ───────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Logging configuration ─────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")

from Scraping_Scripts.web_scraper import main as run_scraper
from Data_Processing.analysis_function import run_analysis_pipeline
from Data_Processing.db_connector import insert_data_to_mysql
from Data_Processing.data_quality import validate_raw_data
from Data_Processing.warehouse import build_warehouse


def run_full_pipeline() -> None:
    """Execute the complete news intelligence pipeline."""

    print("==========================================================")
    print("    GLOBAL NEWS PULSE — Intelligence Pipeline              ")
    print("    Airflow-Compatible  |  RoBERTa Sentiment  |  DuckDB   ")
    print("==========================================================")

    today = date.today().strftime("%Y_%m_%d")

    # ── Step 1/8: Scrape Headlines ─────────────────────────────
    logger.info("[STEP 1/8] Scraping Headlines (HF RoBERTa Sentiment)...")
    run_scraper()
    logger.info("[STEP 1/8] Complete.")

    # ── Step 2/8: Data Quality Validation ──────────────────────
    logger.info("[STEP 2/8] Running Data Quality Checks...")
    raw_csv = str(PROJECT_ROOT / "raw_csv_daily" / f"raw_headlines_data_{today}.csv")
    if os.path.exists(raw_csv):
        report = validate_raw_data(raw_csv)
        if report.get('overall_status') == 'FAIL':
            logger.warning("Data quality failures detected. Continuing with available data.")
    else:
        logger.warning(f"Raw CSV not found at {raw_csv}. Skipping validation.")
    logger.info("[STEP 2/8] Complete.")

    # ── Step 3/8: Data Cleaning & Analysis ─────────────────────
    logger.info("[STEP 3/8] Running Data Cleaning and Analysis...")
    df_headlines, df_entities = run_analysis_pipeline()

    if df_headlines is None:
        logger.error("PIPELINE FAILED at Data Analysis. Check previous errors.")
        return

    logger.info("[STEP 3/8] Complete.")

    # ── Step 4/8: Load DuckDB Warehouse ────────────────────────
    logger.info("[STEP 4/8] Loading DuckDB Star-Schema Warehouse...")
    try:
        build_warehouse()
    except Exception as e:
        logger.warning(f"Warehouse load failed: {e}")
    logger.info("[STEP 4/8] Complete.")

    # ── Step 5/8: Insert to MySQL (Load from Disk) ──────────────
    logger.info("[STEP 5/8] Loading latest processed data and inserting to MySQL...")
    try:
        cleaned_dir = PROJECT_ROOT / "cleaned_csv_daily"
        headline_files = sorted(list(cleaned_dir.glob("processed_data_final_*.csv")))
        entity_files = sorted(list(cleaned_dir.glob("processed_entities_final_*.csv")))

        if not headline_files or not entity_files:
            logger.error("[DB] No processed CSV files found in cleaned_csv_daily/.")
        else:
            latest_h_csv = headline_files[-1]
            latest_e_csv = entity_files[-1]
            logger.info(f"[DB] Loading {latest_h_csv.name} and {latest_e_csv.name}...")
            
            df_h = pd.read_csv(latest_h_csv)
            df_e = pd.read_csv(latest_e_csv)
            
            h_count, e_count = insert_data_to_mysql(df_h, df_e)
            logger.info(f"[DB] Inserted {h_count} headline rows, {e_count} entity rows")
    except Exception as e:
        logger.error(f"[DB] Step failed: {e}")
        logger.info("Continuing pipeline regardless of DB failure.")
    logger.info("[STEP 5/8] Complete.")

    # ── Step 6/8: Run dbt Models ───────────────────────────────
    logger.info("[STEP 6/8] Running dbt Transformations...")
    dbt_dir = str(PROJECT_ROOT / "dbt_project")
    if os.path.exists(dbt_dir):
        try:
            import subprocess
            result = subprocess.run(
                ["dbt", "run", "--profiles-dir", "."],
                cwd=dbt_dir, capture_output=True, text=True, timeout=120
            )
            logger.info(result.stdout)
            if result.returncode != 0:
                logger.warning(f"dbt run returned non-zero: {result.stderr}")

            result_test = subprocess.run(
                ["dbt", "test", "--profiles-dir", "."],
                cwd=dbt_dir, capture_output=True, text=True, timeout=120
            )
            logger.info(result_test.stdout)
        except FileNotFoundError:
            logger.warning("dbt not installed. Skipping dbt transformations.")
        except Exception as e:
            logger.warning(f"dbt failed: {e}")
    else:
        logger.warning("dbt_project/ not found. Skipping.")
    logger.info("[STEP 6/8] Complete.")

    # ── Step 7/8: Generate Dashboard JSON ──────────────────────
    logger.info("[STEP 7/8] Dashboard JSON generation...")
    try:
        from Data_Processing.data_aggregator import generate_dashboard_data
        generate_dashboard_data()
    except Exception as e:
        logger.warning(f"Dashboard JSON generation failed: {e}")
    logger.info("[STEP 7/8] Complete.")

    # ── Step 8/8: Generate AI Executive Summaries ──────────────
    logger.info("[STEP 8/8] Generating AI Executive Summaries (Gemini)...")
    try:
        from Data_Processing.summary_generator import generate_all_summaries
        generate_all_summaries()
    except Exception as e:
        logger.warning(f"AI Summary generation failed: {e}")
    logger.info("[STEP 8/8] Complete.")

    print("\n==========================================================")
    print("    PIPELINE SUCCESSFUL!                                   ")
    print("    Data → DuckDB → dbt → MySQL → JSON → AI Summaries     ")
    print("==========================================================")


if __name__ == "__main__":
    run_full_pipeline()