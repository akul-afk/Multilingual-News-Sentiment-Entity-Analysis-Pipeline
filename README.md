<div align="center">

# 🌐 Global News Pulse

**Multilingual News Sentiment & Entity Analysis Pipeline**

[![Daily Pipeline](https://github.com/akul-afk/Multilingual-News-Sentiment-Entity-Analysis-Pipeline/actions/workflows/daily_pipeline_run.yml/badge.svg)](https://github.com/akul-afk/Multilingual-News-Sentiment-Entity-Analysis-Pipeline/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![DuckDB](https://img.shields.io/badge/warehouse-DuckDB-FFF000?logo=duckdb)](https://duckdb.org)
[![dbt](https://img.shields.io/badge/transforms-dbt-FF694B?logo=dbt)](https://getdbt.com)
[![Gemini AI](https://img.shields.io/badge/summaries-Gemini_AI-4285F4?logo=google)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

*An end-to-end data engineering pipeline that scrapes, translates, analyzes, warehouses, and summarizes multilingual news headlines from 6 BBC World Service sites — then renders them as human-readable intelligence digests.*

</div>

---

## ✨ What It Does

| Stage | What Happens |
|-------|-------------|
| **Scrape** | Extracts ~60 headlines daily from BBC Spanish, Hindi, Portuguese, Russian, Japanese & Swahili |
| **Translate** | Google Translate API normalizes all headlines to English |
| **Sentiment** | HuggingFace RoBERTa model scores each headline [-1.0, +1.0] |
| **NER** | spaCy extracts Named Entities (People, Organizations, Locations) |
| **Quality** | 8-point data quality assertion suite validates schema, nulls, ranges |
| **Warehouse** | DuckDB star-schema (dim_source, dim_date, dim_entity, fact_articles) |
| **Transform** | dbt models compute rolling averages, source reliability, entity rankings |
| **Archive** | MySQL (Aiven cloud) with SQLite local fallback |
| **Aggregate** | Consolidates into `dashboard_data.json` with geo, trend & period reports |
| **Summarize** | Google Gemini generates executive-quality AI news summaries |
| **Visualize** | Vintage Press dashboard with intelligence digests, sentiment gauges, entity maps |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
│    Airflow DAG  ·  GitHub Actions  ·  run_full_pipeline.py     │
├─────────────┬───────────────┬───────────────┬──────────────────┤
│  EXTRACT    │  TRANSFORM    │  LOAD         │  INTELLIGENCE    │
│             │               │               │                  │
│  web_scraper│  analysis_fn  │  warehouse.py │  summary_gen     │
│  (requests) │  (spaCy/NER)  │  (DuckDB)     │  (Gemini AI)     │
│  (RoBERTa)  │  data_quality │  db_connector │  data_aggregator │
│  (Translate)│               │  (MySQL/SQLite│  HeadlineDigest  │
│             │               │   + dbt)      │                  │
├─────────────┴───────────────┴───────────────┴──────────────────┤
│                    PRESENTATION LAYER                           │
│   Dashboard (Node.js)  ↔  Auth API (FastAPI)  ↔  MySQL/SQLite   │
│   (Static Assets)      │  (JWT / BCrypt)     │  (User Data)     │
└────────────────────────┴─────────────────────┴──────────────────┘
```

> 📖 For detailed C4-level documentation, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (Backend & ETL)
- **Node.js 18+** (Dashboard Server)
- **MySQL** (optional — SQLite fallback is automatic)

### 1. Clone & Setup

```bash
git clone https://github.com/akul-afk/Multilingual-News-Sentiment-Entity-Analysis-Pipeline.git
cd Multilingual-News-Sentiment-Entity-Analysis-Pipeline

# Create environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r Requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure Secrets

```bash
cp .env.example .env
# Edit .env with your API keys:
#   HF_API_TOKEN=...    (HuggingFace — for RoBERTa sentiment)
#   GEMINI_API_KEY=...   (Google Gemini — for AI summaries)
#   JWT_SECRET_KEY=...   (For dashboard authentication)
```

### 3. Run the Pipeline

```bash
python run_full_pipeline.py
```

### 4. Launch Dashboard & Auth Server

The dashboard now requires both the frontend server and the authentication backend.

```bash
# Terminal 1: Launch Auth API
python auth/auth_server.py

# Terminal 2: Launch Dashboard Server
cd dashboard
node server.js
```

Open `http://localhost:3000` to access the dashboard. 

> 💡 **Note**: You can access as a **Guest** (Read-Only) or log in as an **Operator** if you have configured credentials in the database.

---

## 🔐 Authentication & Security

The dashboard implements a secure, archival-inspired authentication system:

- **Dual Access Modes**: Support for authenticated **Operators** (Full Access) and **Guests** (Read-Only).
- **JWT Security**: Stateless authentication using JSON Web Tokens with HTTP-only refresh cookies.
- **BCrypt Hashing**: All operator credentials are salted and hashed using industry-standard BCrypt.
- **Audit Logging**: Every access attempt and session activity is logged in the `dim_audit_log` table.
- **Role-Based UI**: Sidebar badges and restricted features (e.g., refresh feed) automatically adjust based on session role.

---

## 📊 Dashboard Screens

| Screen | Description |
|--------|-------------|
| **Overview** | KPI cards, sentiment trends, intelligence brief, top entities |
| **Sentiment** | Detailed polarity distributions over time by source |
| **Cross-Language** | Comparative sentiment analysis across 6 language services |
| **Entity Explorer** | Named entity frequency, co-occurrence, source breakdown |
| **Geo Heatmap** | Leaflet world map showing news activity by region |
| **Reports** | Weekly/Monthly executive summaries + **Intelligence Digest** |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_data_quality.py -v
pytest tests/test_data_aggregator.py -v
```

---

## 📚 Documentation

| [Architecture](docs/ARCHITECTURE.md) | C4-style system context, containers, and component diagrams |
| [UI Design](docs/UI_DESIGN.md) | Vintage Press design tokens, typography, and layout logic |
| [Pipeline Guide](docs/PIPELINE.md) | Step-by-step walkthrough of the 8-stage ETL pipeline |
| [API Reference](docs/API_REFERENCE.md) | Function-level documentation for all Python modules |
| [Deployment Guide](docs/DEPLOYMENT.md) | Local, Docker, CI/CD, and cloud deployment instructions |

---

## 🛠️ Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Scraping** | `requests`, `BeautifulSoup4`, `deep-translator` |
| **NLP** | HuggingFace RoBERTa (sentiment), spaCy `en_core_web_sm` (NER) |
| **Warehouse** | DuckDB (star schema), dbt-core + dbt-duckdb |
| **Database** | MySQL (Aiven cloud), SQLite (local fallback) |
| **AI** | Google Gemini (executive summary generation) |
| **Frontend** | Vanilla ES Modules, CSS, Chart.js, Leaflet.js |
| **Orchestration** | Apache Airflow, GitHub Actions |
| **Deployment** | Static Hosting (CDN/GitHub Pages), GitHub Actions |

---

## 📁 Project Structure

```
NewsScraping2/
├── run_full_pipeline.py          # 8-step orchestrator
├── auth/                         # Authentication & Security Layer
│   └── auth_server.py            # FastAPI Auth API (JWT/BCrypt)
├── Scraping_Scripts/
│   └── web_scraper.py            # Multilingual scraper + RoBERTa sentiment
├── Data_Processing/
│   ├── analysis_function.py      # Cleaning, NER, visualization
│   ├── data_quality.py           # 8-point quality validation suite
│   ├── warehouse.py              # DuckDB star-schema builder
│   ├── db_connector.py           # MySQL/SQLite dual-write connector
│   ├── data_aggregator.py        # Dashboard JSON consolidation
│   └── summary_generator.py      # Gemini AI executive summaries
├── dbt_project/                  # dbt transformation models
├── dashboard/                    # Pure Static Dashboard (HTML/CSS/JS)
│   ├── server.js                 # Node.js Static Server & Auth Proxy
│   ├── data/                     # dashboard_data.json
│   ├── scripts/                  # Pure JS Modules (main, router, etc.)
│   ├── styles/                   # Consolidated Vintage Press CSS
│   └── index.html                # Main entry point (CDN dependencies)
├── airflow/                      # Docker Airflow DAG
├── tests/                        # pytest test suite
├── docs/                         # Architecture & API documentation
└── .github/workflows/            # CI/CD pipeline definitions
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

*Built with ❤️ for data engineering excellence*

**[Live Dashboard](https://news-scraping2.vercel.app)** · **[Documentation](docs/)** · **[Report Bug](https://github.com/akul-afk/Multilingual-News-Sentiment-Entity-Analysis-Pipeline/issues)**

</div>
