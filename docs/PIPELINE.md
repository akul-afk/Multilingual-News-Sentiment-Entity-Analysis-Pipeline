# Pipeline Guide — Global News Pulse

> Step-by-step walkthrough of the 8-stage ETL + AI intelligence pipeline.

## Pipeline Overview

```
Step 1       Step 2        Step 3       Step 4
SCRAPE  ──▶  QUALITY  ──▶  CLEAN   ──▶  WAREHOUSE
             (8 checks)    (NER)        (DuckDB)

Step 5       Step 6        Step 7       Step 8
DBT     ──▶  ARCHIVE  ──▶  AGGREGATE──▶ SUMMARIZE
             (MySQL)       (JSON)       (Gemini AI)
```

## Step 1: Scrape Headlines
**Module:** `Scraping_Scripts/web_scraper.py`

Extracts ~60 headlines from 6 BBC sites, translates to English, scores sentiment via HuggingFace RoBERTa.

## Step 2: Data Quality
**Module:** `Data_Processing/data_quality.py`

8-point assertion suite: schema, row count, nulls, polarity range, source diversity, duplicates, headline length, date format.

## Step 3: Clean & Analyze
**Module:** `Data_Processing/analysis_function.py`

Categorizes sources, extracts Named Entities (spaCy), generates Matplotlib charts.

## Step 4: DuckDB Warehouse
**Module:** `Data_Processing/warehouse.py`

Star schema: dim_source, dim_date, dim_entity, fact_articles, bridge_article_entity.

## Step 5: dbt Transforms
**Directory:** `dbt_project/`

Rolling averages, source reliability, entity rankings, cross-language correlations.

## Step 6: MySQL Archive
**Module:** `Data_Processing/db_connector.py`

MySQL (Aiven) with SQLite fallback. Upsert semantics for idempotent ingestion.

## Step 7: Dashboard Aggregation
**Module:** `Data_Processing/data_aggregator.py`

Consolidates into `dashboard_data.json` with daily summaries, period reports, entity data, geo data.

## Step 8: AI Summaries
**Module:** `Data_Processing/summary_generator.py`

Gemini AI generates executive-quality weekly/monthly news summaries.

## Orchestration
- **Local:** `python run_full_pipeline.py`
- **Airflow:** `cd airflow && docker-compose up -d`
- **CI/CD:** GitHub Actions daily at 6 AM UTC
