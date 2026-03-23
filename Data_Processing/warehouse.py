"""
DuckDB Star-Schema Data Warehouse
Loads cleaned CSV data into a dimensional model:
  - dim_source, dim_date, dim_entity
  - fact_articles, bridge_article_entity
"""

import os
import glob
import duckdb
import pandas as pd
from datetime import datetime, timedelta


WAREHOUSE_PATH = os.path.join(os.getcwd(), "Data_Output", "warehouse.duckdb")


def build_warehouse(cleaned_dir=None, warehouse_path=None):
    """Build or refresh the DuckDB star-schema warehouse from cleaned CSVs."""

    if cleaned_dir is None:
        cleaned_dir = os.path.join(os.getcwd(), "cleaned_csv_daily")
    if warehouse_path is None:
        warehouse_path = WAREHOUSE_PATH

    os.makedirs(os.path.dirname(warehouse_path), exist_ok=True)

    print(f"\n  [WAREHOUSE] Building star schema in {warehouse_path}")

    con = duckdb.connect(warehouse_path)

    # Drop in reverse dependency order to avoid FK conflicts
    for tbl in ['bridge_article_entity', 'fact_articles', 'dim_entity', 'dim_date', 'dim_source']:
        con.execute(f"DROP TABLE IF EXISTS {tbl}")

    # ── Load all cleaned headline CSVs ─────────────────────────
    headline_files = sorted(glob.glob(os.path.join(cleaned_dir, "processed_data_final_*.csv")))
    entity_files = sorted(glob.glob(os.path.join(cleaned_dir, "processed_entities_final_*.csv")))

    if not headline_files:
        print("  [WAREHOUSE] No headline CSVs found. Skipping.")
        con.close()
        return

    # Load headlines
    headline_frames = []
    for f in headline_files:
        try:
            df = pd.read_csv(f, on_bad_lines='skip')
            if not df.empty:
                headline_frames.append(df)
        except Exception as e:
            print(f"  [WAREHOUSE] Skipping {os.path.basename(f)}: {e}")

    if not headline_frames:
        print("  [WAREHOUSE] No valid headline data. Skipping.")
        con.close()
        return

    df_headlines = pd.concat(headline_frames, ignore_index=True)
    df_headlines['Scrape_Date'] = df_headlines['Scrape_Date'].astype(str)

    # Load entities
    entity_frames = []
    for f in entity_files:
        try:
            df = pd.read_csv(f, on_bad_lines='skip')
            if not df.empty:
                entity_frames.append(df)
        except Exception:
            continue

    df_entities = pd.concat(entity_frames, ignore_index=True) if entity_frames else pd.DataFrame()

    print(f"  [WAREHOUSE] Loaded {len(df_headlines)} headlines, {len(df_entities)} entity records")

    # ═══════════════════════════════════════════════════════════
    #  DIMENSION TABLES
    # ═══════════════════════════════════════════════════════════

    # ── dim_source ─────────────────────────────────────────────
    con.execute("""
        CREATE TABLE dim_source (
            source_key INTEGER PRIMARY KEY,
            source_name VARCHAR NOT NULL,
            language_code VARCHAR,
            region VARCHAR,
            base_url VARCHAR
        )
    """)

    source_map = {
        'BBC Spanish':    ('es', 'Latin America',    'https://www.bbc.com/mundo'),
        'BBC Hindi':      ('hi', 'South Asia',       'https://www.bbc.com/hindi'),
        'BBC Portuguese': ('pt', 'South America',    'https://www.bbc.com/portuguese'),
        'BBC Russian':    ('ru', 'Eastern Europe',   'https://www.bbc.com/russian'),
        'BBC Japanese':   ('ja', 'East Asia',        'https://www.bbc.com/japanese'),
        'BBC Swahili':    ('sw', 'East Africa',      'https://www.bbc.com/swahili'),
    }

    for i, (name, (lang, region, url)) in enumerate(source_map.items(), 1):
        con.execute(
            "INSERT INTO dim_source VALUES (?, ?, ?, ?, ?)",
            [i, name, lang, region, url]
        )

    # Create lookup dict: source_name -> source_key
    src_keys = {name: i for i, name in enumerate(source_map.keys(), 1)}

    # ── dim_date ───────────────────────────────────────────────
    con.execute("""
        CREATE TABLE dim_date (
            date_key INTEGER PRIMARY KEY,
            full_date DATE NOT NULL,
            day INTEGER,
            month INTEGER,
            year INTEGER,
            day_of_week VARCHAR,
            week_of_year INTEGER,
            quarter INTEGER,
            is_weekend BOOLEAN
        )
    """)

    # Parse dates from data
    def parse_date(d):
        for fmt in ('%Y_%m_%d', '%Y-%m-%d'):
            try:
                return datetime.strptime(str(d), fmt).date()
            except (ValueError, TypeError):
                continue
        return None

    all_dates = set()
    for d in df_headlines['Scrape_Date'].unique():
        parsed = parse_date(d)
        if parsed:
            all_dates.add(parsed)

    if all_dates:
        min_date = min(all_dates)
        max_date = max(all_dates)
        # Fill all dates in range
        current = min_date
        date_key = 1
        date_keys = {}  # date -> key
        while current <= max_date:
            is_weekend = current.weekday() >= 5
            con.execute(
                "INSERT INTO dim_date VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [date_key, current, current.day, current.month, current.year,
                 current.strftime('%A'), current.isocalendar()[1],
                 (current.month - 1) // 3 + 1, is_weekend]
            )
            date_keys[current] = date_key
            date_key += 1
            current += timedelta(days=1)

    print(f"  [WAREHOUSE] dim_date: {len(date_keys)} date records")

    # ── dim_entity ─────────────────────────────────────────────
    con.execute("""
        CREATE TABLE dim_entity (
            entity_key INTEGER PRIMARY KEY,
            entity_text VARCHAR NOT NULL,
            entity_label VARCHAR NOT NULL
        )
    """)

    entity_keys = {}
    if not df_entities.empty and 'Entity' in df_entities.columns and 'Label' in df_entities.columns:
        unique_entities = df_entities[['Entity', 'Label']].drop_duplicates()
        for i, (_, row) in enumerate(unique_entities.iterrows(), 1):
            con.execute(
                "INSERT INTO dim_entity VALUES (?, ?, ?)",
                [i, str(row['Entity']), str(row['Label'])]
            )
            entity_keys[(str(row['Entity']), str(row['Label']))] = i

    print(f"  [WAREHOUSE] dim_entity: {len(entity_keys)} unique entities")

    # ═══════════════════════════════════════════════════════════
    #  FACT TABLE
    # ═══════════════════════════════════════════════════════════

    con.execute("""
        CREATE TABLE fact_articles (
            article_key INTEGER PRIMARY KEY,
            source_key INTEGER REFERENCES dim_source(source_key),
            date_key INTEGER REFERENCES dim_date(date_key),
            original_headline VARCHAR,
            translated_headline VARCHAR,
            polarity DOUBLE,
            sentiment_label VARCHAR
        )
    """)

    # Deduplicate on (translated_headline, source_name)
    df_headlines = df_headlines.drop_duplicates(subset=['Translated_Headline', 'Source_Name'], keep='last')

    article_key = 1
    article_keys_map = {}  # (headline, source) -> article_key
    source_date_to_articles = {}  # (source_name, scrape_date) -> [article_keys]

    for _, row in df_headlines.iterrows():
        source_name = row.get('Source_Name', '')
        sk = src_keys.get(source_name, None)
        if sk is None:
            continue

        parsed = parse_date(row['Scrape_Date'])
        dk = date_keys.get(parsed, None) if parsed else None

        polarity = float(row['Polarity']) if pd.notna(row.get('Polarity')) else 0.0
        sentiment = row.get('Sentiment_Label', 'neutral') if 'Sentiment_Label' in row.index else (
            'positive' if polarity > 0.05 else ('negative' if polarity < -0.05 else 'neutral')
        )

        con.execute(
            "INSERT INTO fact_articles VALUES (?, ?, ?, ?, ?, ?, ?)",
            [article_key, sk, dk,
             str(row.get('Original_Headline', '')),
             str(row.get('Translated_Headline', '')),
             round(polarity, 4), sentiment]
        )

        key = (str(row.get('Translated_Headline', '')), source_name)
        article_keys_map[key] = article_key

        # Track article keys by (source, date) for fast bridge building
        sd_key = (source_name, str(row['Scrape_Date']))
        if sd_key not in source_date_to_articles:
            source_date_to_articles[sd_key] = []
        source_date_to_articles[sd_key].append(article_key)

        article_key += 1

    print(f"  [WAREHOUSE] fact_articles: {article_key - 1} records")

    # ═══════════════════════════════════════════════════════════
    #  BRIDGE TABLE (article <-> entity)
    # ═══════════════════════════════════════════════════════════

    con.execute("""
        CREATE TABLE bridge_article_entity (
            article_key INTEGER REFERENCES fact_articles(article_key),
            entity_key INTEGER REFERENCES dim_entity(entity_key),
            PRIMARY KEY (article_key, entity_key)
        )
    """)

    bridge_count = 0
    seen_bridges = set()

    if not df_entities.empty and 'Entity' in df_entities.columns and 'Source_Name' in df_entities.columns:
        # Iterate entities and link to articles by (source, date)
        for _, erow in df_entities.iterrows():
            entity_text = str(erow.get('Entity', ''))
            entity_label = str(erow.get('Label', ''))
            source_name = str(erow.get('Source_Name', ''))
            scrape_date = str(erow.get('Scrape_Date', ''))

            ek = entity_keys.get((entity_text, entity_label))
            if ek is None:
                continue

            # Match by source + date
            sd_key = (source_name, scrape_date)
            matched_articles = source_date_to_articles.get(sd_key, [])

            for ak in matched_articles:
                bridge_key = (ak, ek)
                if bridge_key not in seen_bridges:
                    try:
                        con.execute(
                            "INSERT INTO bridge_article_entity VALUES (?, ?)",
                            [ak, ek]
                        )
                        seen_bridges.add(bridge_key)
                        bridge_count += 1
                    except Exception:
                        pass

    print(f"  [WAREHOUSE] bridge_article_entity: {bridge_count} links")

    # ── Verify ─────────────────────────────────────────────────
    tables = con.execute("SHOW TABLES").fetchall()
    print(f"\n  [WAREHOUSE] Tables created: {[t[0] for t in tables]}")

    for table_row in tables:
        table_name = table_row[0]
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"    {table_name}: {count} rows")

    con.close()
    print(f"  [WAREHOUSE] Star schema built successfully at {warehouse_path}")
    return warehouse_path


if __name__ == "__main__":
    build_warehouse()
