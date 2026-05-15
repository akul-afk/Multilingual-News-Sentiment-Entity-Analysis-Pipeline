"""
Shared test fixtures for the Global News Pulse test suite.
"""

import os
import pytest
import pandas as pd
from pathlib import Path


# ── Project Root ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_headlines_df():
    """Minimal valid headlines DataFrame for testing."""
    return pd.DataFrame({
        'Scrape_Date': ['2025_01_15'] * 12,
        'Source_URL': [
            'https://www.bbc.com/mundo/news1',
            'https://www.bbc.com/mundo/news2',
            'https://www.bbc.com/hindi/news1',
            'https://www.bbc.com/hindi/news2',
            'https://www.bbc.com/portuguese/news1',
            'https://www.bbc.com/portuguese/news2',
            'https://www.bbc.com/russian/news1',
            'https://www.bbc.com/russian/news2',
            'https://www.bbc.com/japanese/news1',
            'https://www.bbc.com/japanese/news2',
            'https://www.bbc.com/swahili/news1',
            'https://www.bbc.com/swahili/news2',
        ],
        'Source_Language_Code': ['es', 'es', 'hi', 'hi', 'pt', 'pt', 'ru', 'ru', 'ja', 'ja', 'sw', 'sw'],
        'Original_Headline': [
            'Titular en español uno',
            'Titular en español dos',
            'हिंदी शीर्षक एक',
            'हिंदी शीर्षक दो',
            'Manchete em português um',
            'Manchete em português dois',
            'Русский заголовок один',
            'Русский заголовок два',
            '日本語見出し一',
            '日本語見出し二',
            'Kichwa cha Kiswahili moja',
            'Kichwa cha Kiswahili mbili',
        ],
        'Translated_Headline': [
            'Spanish headline one about the economy',
            'Spanish headline two about politics',
            'Hindi headline one about technology',
            'Hindi headline two about health',
            'Portuguese headline one about climate change',
            'Portuguese headline two about sports',
            'Russian headline one about diplomacy',
            'Russian headline two about energy markets',
            'Japanese headline one about innovation',
            'Japanese headline two about culture',
            'Swahili headline one about agriculture',
            'Swahili headline two about education',
        ],
        'Polarity': [0.35, -0.12, 0.08, 0.42, -0.55, 0.01, -0.33, 0.15, 0.67, -0.05, 0.22, -0.18],
        'Entities_Raw': [
            '[("Madrid", "GPE")]',
            '[("Congress", "ORG")]',
            '[("Delhi", "GPE"), ("Modi", "PERSON")]',
            '[("WHO", "ORG")]',
            '[("Amazon", "LOC")]',
            '[("FIFA", "ORG")]',
            '[("Moscow", "GPE"), ("Putin", "PERSON")]',
            '[("Gazprom", "ORG")]',
            '[("Tokyo", "GPE"), ("Sony", "ORG")]',
            '[("Kyoto", "GPE")]',
            '[("Nairobi", "GPE")]',
            '[("UNESCO", "ORG")]',
        ],
    })


@pytest.fixture
def sample_entities_df():
    """Minimal valid entities DataFrame for testing."""
    return pd.DataFrame({
        'Source_Name': ['BBC Spanish', 'BBC Hindi', 'BBC Hindi', 'BBC Russian', 'BBC Russian', 'BBC Japanese'],
        'Scrape_Date': ['2025_01_15'] * 6,
        'Entity': ['Madrid', 'Modi', 'Delhi', 'Putin', 'Moscow', 'Tokyo'],
        'Label': ['GPE', 'PERSON', 'GPE', 'PERSON', 'GPE', 'GPE'],
    })


@pytest.fixture
def sample_raw_csv(tmp_path, sample_headlines_df):
    """Write sample headlines to a temporary CSV and return path."""
    csv_path = tmp_path / "raw_headlines_data_2025_01_15.csv"
    sample_headlines_df.to_csv(csv_path, index=False)
    return str(csv_path)


@pytest.fixture
def empty_csv(tmp_path):
    """Create an empty CSV file."""
    csv_path = tmp_path / "empty.csv"
    csv_path.touch()
    return str(csv_path)
