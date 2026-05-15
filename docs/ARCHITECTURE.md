# Architecture — Global News Pulse

> C4-style architectural documentation for the Multilingual News Sentiment & Entity Analysis Pipeline.

---

## Level 1: System Context

The Global News Pulse system sits at the intersection of **multilingual web data**, **NLP processing**, **data warehousing**, and **AI-powered intelligence generation**.

```
                          ┌───────────────────────┐
                          │   BBC World Service    │
                          │   (6 Language Sites)   │
                          └─────────┬─────────────┘
                                    │ HTTP/HTML
                                    ▼
                    ┌───────────────────────────────┐
                    │                               │
                    │   Global News Pulse System    │
                    │                               │
                    │  Scrape → NLP → Warehouse →   │
                    │  Transform → Archive →        │
                    │  Aggregate → Summarize        │
                    │                               │
                    └──┬────────┬────────┬─────────┘
                       │        │        │
              ┌────────▼──┐ ┌──▼────┐ ┌─▼──────────┐
              │ HuggingFace│ │Google │ │ MySQL/Aiven│
              │ Inference  │ │Gemini │ │ Cloud DB   │
              │ API        │ │ API   │ │            │
              └────────────┘ └───────┘ └────────────┘
```

### External Dependencies

| System | Role | Protocol |
|--------|------|----------|
| BBC World Service | Source data (6 language sites) | HTTP scraping |
| HuggingFace API | RoBERTa sentiment classification | REST API |
| Google Translate | Headline translation to English | REST API |
| Google Gemini | AI executive summary generation | REST API |
| MySQL (Aiven) | Cloud archival database | TCP/MySQL protocol |
| GitHub Actions | CI/CD pipeline orchestration | GitHub API |
| Static Hosting | Dashboard hosting (CDN/GitHub Pages) | HTTPS |

---

## Level 2: Container Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Global News Pulse System                          │
│                                                                             │
│  ┌──────────────────┐   ┌──────────────────┐   ┌────────────────────┐      │
│  │ Scraping Engine   │   │ Processing Engine │   │  Warehouse Engine  │      │
│  │                  │   │                  │   │                    │      │
│  │ • web_scraper.py  │──▶│ • analysis_fn.py  │──▶│ • warehouse.py     │      │
│  │ • requests/BS4    │   │ • data_quality.py │   │ • DuckDB           │      │
│  │ • deep-translator │   │ • spaCy NER       │   │ • Star Schema      │      │
│  │ • RoBERTa via HF  │   │                  │   │                    │      │
│  └──────────────────┘   └──────────────────┘   └────────┬───────────┘      │
│                                                          │                  │
│  ┌──────────────────┐   ┌──────────────────┐   ┌────────▼───────────┐      │
│  │ dbt Transform     │   │ Archive Layer     │   │ Intelligence       │      │
│  │                  │   │                  │   │                    │      │
│  │ • Rolling avgs    │   │ • db_connector.py │   │ • data_aggregator  │      │
│  │ • Source metrics  │   │ • MySQL primary   │   │ • summary_generator│      │
│  │ • Entity rankings │   │ • SQLite fallback │   │ • Gemini AI        │      │
│  │ • dbt-duckdb      │   │                  │   │ • HeadlineDigest   │      │
│  └──────────────────┘   └─────────┬────────┘   └────────┬───────────┘      │
│                                   │                    │                  │
│                            ┌──────┘             ┌──────┘                  │
│                            ▼                    ▼                         │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │               Presentation Layer (Modular Dashboard)                   ││
│  │                                                                        ││
│  │  ┌───────────────────────┐         ┌─────────────────────────────┐     ││
│  │  │ Component Router       │         │ Authentication API          │     ││
│  │  │ (Vanilla JS / Router)  │ ◀─────▶ │ (FastAPI / JWT)             │     ││
│  │  │ • Modular Screens      │         │ • Operator Login (BCrypt)   │     ││
│  │  │ • Leaflet / Chart.js   │         │ • Guest Sessions            │     ││
│  │  │ • SPA Routing Logic    │         │ • Audit Logging             │     ││
│  │  └───────────────────────┘         └──────────────┬──────────────┘     ││
│  │                                                   │                     ││
│  └───────────────────────────────────────────────────┼─────────────────────┘│
│                                                      ▼                      │
│                                             ┌──────────────────┐            │
│                                             │ SQLite / MySQL   │            │
│                                             │ (User & Sessions)│            │
│                                             └──────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Level 3: Component Diagram — Processing Engine

```
┌─────────────────────────────────────────────────────────┐
│                   Processing Engine                      │
│                                                          │
│  ┌────────────────┐      ┌──────────────────────┐       │
│  │ Source Loader   │      │ Entity Extractor      │       │
│  │                 │      │                       │       │
│  │ read_csv()      │─────▶│ spaCy en_core_web_sm  │       │
│  │ categorize()    │      │ PERSON/ORG/GPE/LOC    │       │
│  │ clean()         │      │                       │       │
│  └────────┬───────┘      └──────────┬───────────┘       │
│           │                          │                    │
│           ▼                          ▼                    │
│  ┌─────────────────────────────────────────────┐         │
│  │          Quality Gate                        │         │
│  │                                              │         │
│  │  _assert_not_null()  _assert_unique()        │         │
│  │  _assert_value_range()  validate_raw_data()  │         │
│  │                                              │         │
│  │  8 checks: schema, rows, nulls, polarity,    │         │
│  │  source diversity, dupes, length, date format │         │
│  └──────────────────────────────────────────────┘         │
│                          │                                │
│                          ▼                                │
│  ┌───────────────────────────────────────────────────┐    │
│  │         Output: cleaned CSVs + entity CSVs         │    │
│  │         processed_data_final_YYYY_MM_DD.csv        │    │
│  │         processed_entities_final_YYYY_MM_DD.csv    │    │
│  └───────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

---

## Data Model: DuckDB Star Schema

```
                    ┌─────────────┐
                    │  dim_source  │
                    │─────────────│
                    │ source_key  │◄──────┐
                    │ source_name │       │
                    │ language    │       │
                    │ region      │       │
                    │ base_url    │       │
                    └─────────────┘       │
                                          │
┌──────────────┐   ┌───────────────────┐  │   ┌─────────────────┐
│  dim_date    │   │  fact_articles    │  │   │  dim_entity     │
│──────────────│   │───────────────────│  │   │─────────────────│
│ date_key     │◄──│ article_key (PK)  │  │   │ entity_key (PK) │
│ full_date    │   │ source_key (FK) ──│──┘   │ entity_text     │
│ day/month/yr │   │ date_key (FK) ────│──┐   │ entity_label    │
│ day_of_week  │   │ original_headline │  │   └────────┬────────┘
│ quarter      │   │ translated_hdln   │  │            │
│ is_weekend   │   │ polarity          │  │            │
└──────────────┘   │ sentiment_label   │  │   ┌────────┴────────┐
                   └────────┬──────────┘  │   │ bridge_article  │
                            │             │   │ _entity         │
                            │             │   │─────────────────│
                            └─────────────│──▶│ article_key(FK) │
                                          │   │ entity_key (FK) │
                                          │   └─────────────────┘
                                          │
                                          └── dim_date
```

### Dimension Tables

| Table | Rows (typical) | Description |
|-------|----------------|-------------|
| `dim_source` | 6 | BBC language services |
| `dim_date` | ~365 | Calendar spine covering all data dates |
| `dim_entity` | ~500+ | Unique PERSON/ORG/GPE/LOC entities |

### Fact Tables

| Table | Rows (typical) | Description |
|-------|----------------|-------------|
| `fact_articles` | ~20,000+ | Deduplicated headlines with sentiment scores |
| `bridge_article_entity` | ~50,000+ | M:N mapping between articles and entities |

---

## Intelligence Layer

The **HeadlineDigest** component is the differentiating feature — it transforms raw NLP output into human-readable intelligence:

```
Raw Data                                Intelligence Output
─────────────                           ──────────────────
Polarity: 0.342          ──────▶        "Today's global news cycle is
Polarity: -0.15                         optimistic, with 47 headlines
Polarity: 0.001                         analyzed across 6 language
...                                     services. 22 stories carry
                                        positive sentiment..."

Entities:                ──────▶        "WHO'S MAKING NEWS:
  PERSON: Modi (12)                     People: Modi (12), Putin (8)
  ORG: WHO (8)                          Organizations: WHO (8), UN (5)"
  GPE: Ukraine (15)

Geo Data:                ──────▶        "Regional Dispatch:
  Hindi: +0.12                          Hindi service leads with
  Russian: -0.08                        positive coverage. Russian
                                        carries the most critical tone."
```

---

## Deployment Architecture

```
┌─────────────────────────┐     ┌──────────────────────┐
│   GitHub Actions         │     │   Static Hosting     │
│   (Daily 6 AM UTC)       │     │   (CDN/Pages)        │
│                          │     │                      │
│   run_full_pipeline.py   │────▶│   dashboard/ files   │
│   ▼ artifacts committed  │     │   dashboard_data.json│
│     to repo              │     │   served via HTTP    │
└─────────────────────────┘     └──────────────────────┘
            │
            ▼
    ┌───────────────┐
    │ MySQL / Aiven  │
    │ (cloud archive)│
    └───────────────┘
```

---

## Further Reading

- [UI Design & Aesthetics](UI_DESIGN.md) — Design system & component docs
- [Pipeline Guide](PIPELINE.md) — Step-by-step walkthrough
- [API Reference](API_REFERENCE.md) — Module & function documentation
- [Deployment Guide](DEPLOYMENT.md) — Setup & deployment instructions
