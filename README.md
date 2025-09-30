
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

### Showcasing a TreeMap for entities variance in the headlines

<img width="708" height="779" alt="image" src="https://github.com/user-attachments/assets/4df73ade-abfd-46d6-93bd-5977c81c1f51" />


### Database Schema (Relational Model)


<img width="520" height="551" alt="image" src="https://github.com/user-attachments/assets/4ec3de73-00b5-4fa4-8e0b-8680a436fd68" />




Schema Note: Data is archived in two tables linked by a One-to-Many relationship (headlines.id -> entities.headline_id), ensuring accurate count of Named Entities per headline for historical analysis.

**For more POWER BI visualization and matplotlib analysis got to->** [Click](https://akul-afk.github.io/Multilingual-News-Sentiment-Entity-Analysis-Pipeline/)
 
> 📁 Project Structure

> News_Sentiment_Analysis/

> ── Data_Processing/

>         ├── analysis_functions.py    # Cleaning, Pandas processing, Matplotlib charts

>         ├── db_connector.py          # MySQL connection and insertion logic

>         └── Data_Output/             # Cleaned CSVs and charts

> ── Scraping_Scripts/

>           └── web_scraper.py           # Core scraping, translation, and NLP logic

> ── run_full_pipeline.py         # Master automation script (One-click execution)

> ── requirements.txt             # Project dependencies


```mermaid
graph TD
    subgraph "Phase 1: Orchestration & Data Acquisition"
        A["Start: run_full_pipeline.py"] --> B["Configuration: site_configs.json"];
        B --> C["web_scraper.py: Fetch Headlines from BBC"];
        C --> D["Deep Translator: Translate to English"];
        D --> E["spaCy: Named Entity Recognition"];
        E --> F["TextBlob: Sentiment Analysis"];
        F --> G["Raw Data: raw_headlines_data.csv"];
    end

    subgraph "Phase 2: Data Processing & Storage"
        G --> H["analysis_function.py: Data Cleaning & Transformation"];
        H --> I["Processed Data: processed_data_final_[date].csv"];
        H --> J["Processed Entities: processed_entities_final_[date].csv"];
        I --> K["db_connector.py: Insert into MySQL 'headlines' table"];
        J --> L["db_connector.py: Insert into MySQL 'entities' table"];
        K & L --> M["MySQL Database: newsanalysisdb Historical Data"];
        H --> N["Generate Matplotlib Charts"];
    end

    subgraph "Phase 3: Visualization & Presentation"
        M --> O["Power BI: Connect to MySQL"];
        O --> P["Power BI: Build Interactive Dashboard"];
        N --> Q["Power BI: Import Matplotlib Images"];
        P --> R["Screenshot: Power BI Dashboard Visuals"];
        Q --> R;
        R --> S["index.html: Showcase on GitHub Pages"];
        M --> S;
    end

    S --> T["End: Project Accessible Online"];

    %% Style definitions are retained but adjusted to use the corrected node IDs
    style A fill:#D4EDDA,stroke:#28A745,stroke-width:2px,color:#28A745
    style T fill:#D4EDDA,stroke:#28A745,stroke-width:2px,color:#28A745
    style B fill:#E0E0E0,stroke:#6C757D,stroke-width:1px,color:#343A40
    style D fill:#CDE3F7,stroke:#007BFF,stroke-width:1px,color:#007BFF
    style E fill:#CDE3F7,stroke:#007BFF,stroke-width:1px,color:#007BFF
    style F fill:#CDE3F7,stroke:#007BFF,stroke-width:1px,color:#007BFF
    style G fill:#FFF3CD,stroke:#FFC107,stroke-width:1px,color:#343A40
    style H fill:#E0E0E0,stroke:#6C757D,stroke-width:1px,color:#343A40
    style I fill:#FFF3CD,stroke:#FFC107,stroke-width:1px,color:#343A40
    style J fill:#FFF3CD,stroke:#FFC107,stroke-width:1px,color:#343A40
    style K fill:#C8DCEF,stroke:#0056B3,stroke-width:1px,color:#0056B3
    style L fill:#C8DCEF,stroke:#0056B3,stroke-width:1px,color:#0056B3
    style M fill:#ADD8E6,stroke:#17A2B8,stroke-width:2px,color:#17A2B8
    style N fill:#E0E0E0,stroke:#6C757D,stroke-width:1px,color:#343A40
    style O fill:#E6F0FF,stroke:#007BFF,stroke-width:1px,color:#007BFF
    style P fill:#E6F0FF,stroke:#007BFF,stroke-width:1px,color:#007BFF
    style Q fill:#FFF3CD,stroke:#FFC107,stroke-width:1px,color:#343A40
    style R fill:#ADD8E6,stroke:#17A2B8,stroke-width:2px,color:#17A2B8
    style S fill:#D4EDDA,stroke:#28A745,stroke-width:2px,color:#28A745
```
