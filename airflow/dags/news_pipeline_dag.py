"""
Apache Airflow DAG — News Sentiment Pipeline

Orchestrates the complete pipeline with proper task dependencies,
retries, and logging. Can run locally via Docker Compose or serve
as the reference DAG for the GitHub Actions hybrid approach.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import os
import sys

# ── Add project root to path ──────────────────────────────────
PROJECT_ROOT = os.environ.get('PROJECT_ROOT', '/opt/airflow/project')
sys.path.insert(0, PROJECT_ROOT)


# ── Default DAG args ──────────────────────────────────────────
default_args = {
    'owner': 'news-pipeline',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}


# ── Task Functions ────────────────────────────────────────────
def task_scrape_headlines(**context):
    """Step 1: Scrape headlines from 6 BBC language services."""
    from Scraping_Scripts.web_scraper import main as run_scraper
    print("[AIRFLOW] Starting headline scraping...")
    run_scraper()
    print("[AIRFLOW] Scraping complete.")


def task_validate_data_quality(**context):
    """Step 2: Run data quality checks on scraped CSV."""
    from Data_Processing.data_quality import validate_raw_data
    from datetime import date

    today = date.today().strftime("%Y_%m_%d")
    csv_path = os.path.join(PROJECT_ROOT, f"raw_csv_daily/raw_headlines_data_{today}.csv")

    print(f"[AIRFLOW] Running data quality checks on {csv_path}...")
    report = validate_raw_data(csv_path)

    if report.get('overall_status') == 'FAIL':
        print("[AIRFLOW] WARNING: Data quality checks have failures!")
        # Log but don't fail — let pipeline continue with available data
    print("[AIRFLOW] Data quality validation complete.")


def task_analyze_and_clean(**context):
    """Step 3: Clean data, extract entities, generate charts."""
    from Data_Processing.analysis_function import run_analysis_pipeline
    print("[AIRFLOW] Running analysis and cleaning...")
    df_h, df_e = run_analysis_pipeline()
    if df_h is None:
        raise ValueError("Analysis pipeline returned None — no data to process.")
    print(f"[AIRFLOW] Analysis complete: {len(df_h)} headlines, {len(df_e)} entities.")


def task_load_warehouse(**context):
    """Step 4: Load cleaned data into DuckDB star schema."""
    from Data_Processing.warehouse import build_warehouse
    print("[AIRFLOW] Building DuckDB warehouse...")
    build_warehouse()
    print("[AIRFLOW] Warehouse load complete.")


def task_load_mysql(**context):
    """Step 5: Insert data into Aiven MySQL."""
    from Data_Processing.analysis_function import load_and_clean_data
    from Data_Processing.db_connector import insert_data_to_mysql
    from datetime import date

    today = date.today().strftime("%Y_%m_%d")
    input_file = os.path.join(PROJECT_ROOT, f"raw_csv_daily/raw_headlines_data_{today}.csv")

    print("[AIRFLOW] Loading data into MySQL...")
    df_h, df_e = load_and_clean_data(input_file)
    if df_h is not None:
        insert_data_to_mysql(df_h, df_e)
    print("[AIRFLOW] MySQL load complete.")


def task_generate_dashboard_json(**context):
    """Step 6: Generate dashboard JSON for the frontend."""
    from Data_Processing.data_aggregator import generate_dashboard_data
    print("[AIRFLOW] Generating dashboard JSON...")
    generate_dashboard_data()
    print("[AIRFLOW] Dashboard JSON generated.")


# ── DAG Definition ────────────────────────────────────────────
with DAG(
    dag_id='news_sentiment_pipeline',
    default_args=default_args,
    description='Multilingual News Sentiment & Entity Analysis Pipeline',
    schedule_interval='0 8 * * *',   # Daily at 8 AM UTC
    start_date=datetime(2025, 12, 1),
    catchup=False,
    max_active_runs=1,
    tags=['news', 'sentiment', 'nlp', 'etl'],
) as dag:

    # Step 1: Scrape
    t_scrape = PythonOperator(
        task_id='scrape_headlines',
        python_callable=task_scrape_headlines,
        retries=3,
        retry_delay=timedelta(minutes=10),
    )

    # Step 2: Data Quality
    t_quality = PythonOperator(
        task_id='validate_data_quality',
        python_callable=task_validate_data_quality,
    )

    # Step 3: Analyze & Clean
    t_analyze = PythonOperator(
        task_id='analyze_and_clean',
        python_callable=task_analyze_and_clean,
    )

    # Step 4: Load Warehouse
    t_warehouse = PythonOperator(
        task_id='load_warehouse',
        python_callable=task_load_warehouse,
    )

    # Step 5: dbt Run
    t_dbt = BashOperator(
        task_id='run_dbt_models',
        bash_command=f'cd {PROJECT_ROOT}/dbt_project && dbt run --profiles-dir . && dbt test --profiles-dir .',
    )

    # Step 6: Load MySQL
    t_mysql = PythonOperator(
        task_id='load_mysql',
        python_callable=task_load_mysql,
    )

    # Step 7: Dashboard JSON
    t_dashboard = PythonOperator(
        task_id='generate_dashboard_json',
        python_callable=task_generate_dashboard_json,
    )

    # ── Task Dependencies ─────────────────────────────────────
    # scrape → quality → analyze → [warehouse, mysql] → dbt → dashboard
    t_scrape >> t_quality >> t_analyze
    t_analyze >> [t_warehouse, t_mysql]
    t_warehouse >> t_dbt >> t_dashboard
