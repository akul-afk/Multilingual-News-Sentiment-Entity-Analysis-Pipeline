
# 🌐 Multilingual News Sentiment & Entity Analysis Pipeline
Project Overview
This project implements an end-to-end automated data pipeline that scrapes top news headlines from six different BBC international language services, performs Natural Language Processing (NLP) for translation and sentiment analysis, and persists the results in a historical MySQL database. The output is then visualized in an interactive Power BI dashboard to track global news sentiment trends over time.

This project demonstrates proficiency across Python Automation, Web Scraping, NLP, Relational Database Design, and Business Intelligence (BI).

## 🛠️ Tech Stack & Key Skills

| Category | Tools & Libraries Used | Skill Demonstrated | 
 | ----- | ----- | ----- | 
| **Automation & Orchestration** | **Python**, `run_full_pipeline.py` | Full Pipeline Automation, Modular Code Design, `sys.path` management. | 
| **Data Acquisition** | `requests`, `BeautifulSoup4` | Web Scraping, Handling Multilingual HTML/Encodings. | 
| **Data Processing & NLP** | `pandas`, `TextBlob`, `spaCy`, `deep_translator` | Data Cleaning, Sentiment Analysis, Named Entity Recognition (NER). | 
| **Data Storage** | **MySQL** (`mysql.connector`) | Relational Database Modeling (One-to-Many), Data Archiving for time-series analysis. | 
| **Visualization** | **Power BI**, `matplotlib` | Interactive Dashboard Design, Time-Series Analysis, Data Modeling. | 

## 🚀 Pipeline Execution (The One-Click Run)
The entire pipeline, from scraping to database insertion, is automated and executed via a single command.

**Prerequisites**
1. Python 3.x

2. MySQL Server running locally (ensure port 3306 is open).

3. Power BI Desktop (for the final dashboard).

4. Dependencies: Install all required Python packages:

`pip install -r requirements.txt`
`python -m spacy download en_core_web_sm`

5. Configuration: Update the MySQL credentials in Data_Processing/db_connector.py.

**Run Command**

Execute the main automation script from the project root directory:

`python run_full_pipeline.py`

Output: The script sequentially runs the scraper, cleans and processes the data, generates Matplotlib charts, and appends all results to the historical newsanalysisdb database.
## Process Snapshots

* ### Initial Data collection*

<img width="1120" height="750" alt="image" src="https://github.com/user-attachments/assets/dde1f57e-0817-4979-941d-2a2e6c16cd3f" />

### Data cleaned and saved to MySQL

<img width="1079" height="746" alt="image" src="https://github.com/user-attachments/assets/3d709351-67d3-4f20-91b3-5c276912a5bf" />

### Data viewed and accessed on MySQL workbench

<img width="1058" height="658" alt="image" src="https://github.com/user-attachments/assets/6dadff03-b91f-4d8a-b331-6b10e12c1ab0" />


## 📊 Visualizations and Key Findings
1. The Automated Dashboard (Power BI)
(Goal: Show the final, interactive dashboard with multiple visuals and slicers.)

[PLACEHOLDER: Add a link or image here of your Power BI Dashboard.]

<img src="path/to/power_bi_dashboard_main.png" alt="Interactive Power BI Dashboard showing sentiment trends." width="800"/>

Key Insight: [Example: Insert a brief summary of a key finding, e.g., "The average sentiment polarity across all sources showed a 15% drop over the last week, primarily driven by negative headlines in BBC Russian and BBC Spanish."]

2. Matplotlib Analysis (Sentiment Distribution)
(Goal: Show the quick, in-code Matplotlib output that validates the scraping and sentiment logic.)

[PLACEHOLDER: Add a link or image here of your Sentiment Bar Chart.]

<img src="Data_Processing/Data_Output/Matplotlib_Charts/sentiment_by_source.png" alt="Matplotlib chart comparing average sentiment by source." width="400"/>

Key Insight: [Example: "BBC Portuguese consistently reported the highest average sentiment (0.15), while BBC Hindi had the most neutral reporting (0.01) across the sampling period."]

3. Database Schema (Relational Model)
(Goal: Show the data model in Power BI or MySQL Workbench to highlight the relational design.)

[PLACEHOLDER: Add a link or image here of your Power BI Data Model View.]

<img src="path/to/power_bi_data_model.png" alt="Power BI data model showing the one-to-many relationship." width="500"/>

Schema Note: Data is archived in two tables linked by a One-to-Many relationship (headlines.id -> entities.headline_id), ensuring accurate count of Named Entities per headline for historical analysis.

> 📁 Project Structure
> News_Sentiment_Analysis/
> ── Data_Processing/
>    ├── analysis_functions.py    # Cleaning, Pandas processing, Matplotlib charts
>    ├── db_connector.py          # MySQL connection and insertion logic
>    └── Data_Output/             # Cleaned CSVs and charts
> ── Scraping_Scripts/
>    └── web_scraper.py           # Core scraping, translation, and NLP logic
> ── run_full_pipeline.py         # Master automation script (One-click execution)
> ── requirements.txt             # Project dependencies
