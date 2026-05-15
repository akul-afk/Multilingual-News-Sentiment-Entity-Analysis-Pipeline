# Deployment Guide — Global News Pulse

## Local Development

### Prerequisites
- Python 3.10+, Static File Server (Python `http.server`), MySQL (optional)

### Backend Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r Requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env   # Add your API keys
python run_full_pipeline.py
```

### Frontend Setup
```bash
cd dashboard
python -m http.server 8000   # Open http://localhost:8000
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HF_API_TOKEN` | Yes | HuggingFace API token for RoBERTa sentiment |
| `GEMINI_API_KEY` | Yes | Google Gemini API key for AI summaries |
| `DB_HOST` | No | MySQL host (defaults to localhost) |
| `DB_PORT` | No | MySQL port (defaults to 3306) |
| `DB_USER` | No | MySQL user (defaults to root) |
| `DB_PASSWORD` | No | MySQL password |
| `DB_DATABASE` | No | MySQL database name (defaults to NewsHeadlines) |

## CI/CD — GitHub Actions

**Workflow:** `.github/workflows/daily_pipeline_run.yml`

- **Schedule:** Daily at 6 AM UTC
- **Steps:** Install deps → Run pipeline → Commit artifacts → Sync Vercel
- **Secrets required:** `HF_API_TOKEN`, `GEMINI_API_KEY`, `DB_*` (if using cloud MySQL)

## Frontend Deployment — Static Hosting

1. Upload the `dashboard/` directory to any static host (GitHub Pages, Netlify, Vercel).
2. Ensure `dashboard_data.json` is correctly placed in `dashboard/data/`.
3. No build command is needed. Set the entry point to `index.html`.

## Apache Airflow (Optional)

```bash
cd airflow
docker-compose up -d
```

Access Airflow UI at `http://localhost:8080` (admin/admin). The `news_pipeline_dag` runs all 8 steps.
