# API Reference — Global News Pulse

> Function-level documentation for all Python backend modules.

## `Scraping_Scripts/web_scraper.py`

### `scrape_bbc_headlines(url: str) -> List[str]`
Scrapes up to 10 headlines from a BBC World Service page.

### `translate_headline(headline: str, src_language: str) -> str`
Translates a headline from source language to English via Google Translate.

### `get_sentiment(headline: str) -> float`
Scores a headline's sentiment via HuggingFace RoBERTa. Returns [-1.0, +1.0].

### `main() -> None`
Entry point. Iterates all 6 sources, scrapes, translates, scores, and writes CSV.

---

## `Data_Processing/analysis_function.py`

### `load_and_clean_data(input_filepath) -> Tuple[Optional[DataFrame], Optional[DataFrame]]`
Loads raw CSV, categorizes sources, extracts entities via spaCy. Returns (headlines_df, entities_df).

### `run_analysis_pipeline() -> Tuple[Optional[DataFrame], Optional[DataFrame]]`
Full pipeline: load → clean → visualize → write output CSVs.

---

## `Data_Processing/data_quality.py`

### `validate_raw_data(csv_path: str, report_dir: Optional[str]) -> Dict[str, Any]`
Runs 8 quality checks on a raw CSV. Returns structured report dict.

### `_assert_not_null(df: DataFrame, column: str) -> Dict`
Assert a column has no null values.

### `_assert_unique(df: DataFrame, column: str) -> Dict`
Assert a column has no duplicate values.

### `_assert_value_range(df: DataFrame, column: str, min_val, max_val) -> Dict`
Assert all values fall within [min_val, max_val].

### `DataQualityConfig` (dataclass)
Configuration for validation thresholds: min_rows, min_sources, polarity_range, etc.

---

## `Data_Processing/warehouse.py`

### `build_warehouse(cleaned_dir: Optional[str], warehouse_path: Optional[str]) -> Optional[str]`
Builds the DuckDB star-schema from cleaned CSVs. Returns warehouse path on success.

---

## `Data_Processing/db_connector.py`

### `insert_data_to_mysql(df_headlines: DataFrame, df_entities: DataFrame) -> None`
Inserts data into MySQL with upsert semantics. Falls back to SQLite on connection failure.

### `insert_data_to_sqlite(df_headlines: DataFrame, df_entities: DataFrame) -> None`
SQLite fallback writer.

### `create_database_and_tables(cnx, cursor) -> bool`
Creates the database and tables if they don't exist.

---

## `Data_Processing/data_aggregator.py`

### `generate_dashboard_data() -> None`
Main entry point. Reads all CSVs, builds all sections, writes `dashboard_data.json`.

### `synthesize_digest(data: dict) -> Optional[dict]` *(frontend)*
Translates raw NLP data into human-readable intelligence digest.

---

## `Data_Processing/summary_generator.py`

### `generate_all_summaries() -> None`
Generates AI summaries for all weekly/monthly periods using Google Gemini.

---

---

## `auth/auth_server.py` (FastAPI)

### `POST /auth/login`
Authenticates an operator and returns a JWT access token plus a refresh token cookie.

### `POST /auth/guest`
Generates a temporary read-only guest session and JWT access token.

### `POST /auth/refresh`
Uses the HTTP-only refresh token cookie to issue a new access token.

### `POST /auth/logout`
Revokes the current session and clears the refresh token cookie.

### `GET /auth/me`
Returns details about the currently authenticated user (ID and role).

### `POST /auth/guest/pageview`
Increments the page view counter for the current guest session.

---

## `dashboard/server.js` (Node.js)

### `http.createServer()`
A lightweight Node.js server that serves the static dashboard files.

### `Proxy /auth`
Intercepts all requests starting with `/auth` and proxies them to the FastAPI backend at `localhost:8001`.

### `SPA Routing`
Automatically serves `index.html` for non-existent paths to support client-side routing.

---

## `run_full_pipeline.py`

### `run_full_pipeline() -> None`
Executes the complete 8-step pipeline sequentially.
