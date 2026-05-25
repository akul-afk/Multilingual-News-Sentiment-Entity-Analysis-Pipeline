"""
Web Scraper Module
Scrapes headlines from global news sources (HTML & RSS),
translates them to English, and performs sentiment + NER analysis.
"""

import os
import re
import csv
import json
import logging
import random
import time
import subprocess
import requests
import xml.etree.ElementTree as ET
from datetime import date
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import spacy

# ── Setup SpaCy ───────────────────────────────────────────────────────────
try:
    import en_core_web_sm
except ImportError:
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
    import en_core_web_sm

nlp = spacy.load('en_core_web_sm')

# ── Constants & Config ─────────────────────────────────────────────────────
MIN_HEADLINE_LENGTH = 20
MAX_HEADLINES_PER_SOURCE = 10

HF_API_TOKEN = os.environ.get('HF_API_TOKEN', '')
HF_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
HF_API_URL = f"https://router.huggingface.co/models/{HF_MODEL}"

LABEL_TO_POLARITY = {
    'negative': -1.0,
    'neutral':   0.0,
    'positive':  1.0,
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# ── Source Registry ────────────────────────────────────────────────────────
SOURCES = [
    # BBC Language Sites (Legacy)
    {"name": "BBC Mundo", "language": "es", "region": "Latin America", "url": "https://www.bbc.com/mundo", "type": "html", "selector": "h3", "requires_translation": True, "enabled": True},
    {"name": "BBC Hindi", "language": "hi", "region": "South Asia", "url": "https://www.bbc.com/hindi", "type": "html", "selector": "h3", "requires_translation": True, "enabled": True},
    {"name": "BBC Portuguese", "language": "pt", "region": "Latin America", "url": "https://www.bbc.com/portuguese", "type": "html", "selector": "h3", "requires_translation": True, "enabled": True},
    {"name": "BBC Russian", "language": "ru", "region": "Eastern Europe", "url": "https://www.bbc.com/russian", "type": "html", "selector": "h3", "requires_translation": True, "enabled": True},
    {"name": "BBC Japanese", "language": "ja", "region": "East Asia", "url": "https://www.bbc.com/japanese", "type": "html", "selector": "h3", "requires_translation": True, "enabled": True},
    {"name": "BBC Swahili", "language": "sw", "region": "Africa", "url": "https://www.bbc.com/swahili", "type": "html", "selector": "h3", "requires_translation": True, "enabled": True},
    
    # New International Sources
    {"name": "Al Jazeera", "language": "en", "region": "Middle East", "url": "https://www.aljazeera.com/news", "type": "html", "selector": "h2.article-card__title", "requires_translation": False, "enabled": True},
    {"name": "France 24", "language": "en", "region": "Global", "url": "https://www.france24.com/en", "type": "html", "selector": "h2.a-daily-news-link__title", "requires_translation": False, "enabled": True},
    {"name": "The Hindu", "language": "en", "region": "South Asia", "url": "https://www.thehindu.com", "type": "html", "selector": "h3.title", "requires_translation": False, "enabled": True},
    {"name": "Reuters", "language": "en", "region": "Global", "url": "https://www.reuters.com", "type": "html", "selector": "a[data-testid='Heading'] span", "requires_translation": False, "enabled": False}, # SKIP (JS Req)
    
    # RSS Feeds
    {"name": "BBC World RSS", "language": "en", "region": "Global", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "type": "rss", "selector": None, "requires_translation": False, "enabled": True},
    {"name": "NYT World RSS", "language": "en", "region": "Global", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "type": "rss", "selector": None, "requires_translation": False, "enabled": True}
]

# ── Core Functions ─────────────────────────────────────────────────────────

def scrape_html_source(source: dict) -> List[str]:
    """Scrapes headlines from an HTML source using BeautifulSoup."""
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    try:
        response = requests.get(source["url"], headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        selector = source["selector"]
        if '.' in selector:
            tag, cls = selector.split('.', 1)
            elements = soup.find_all(tag, class_=cls)
        elif '[' in selector:
            elements = soup.select(selector)
        else:
            elements = soup.find_all(selector)

        # BBC Special Fallback
        if not elements and "bbc.com" in source["url"]:
            main_list = soup.find('ul', class_='bbc-1rrncb9') or soup.find('div', class_='bbc-1ajedpd')
            if main_list:
                elements = main_list.find_all('h3')

        headlines = []
        for el in elements:
            text = el.get_text(strip=True)
            if len(text) >= MIN_HEADLINE_LENGTH:
                headlines.append(text)
            if len(headlines) >= MAX_HEADLINES_PER_SOURCE:
                break
        return headlines
    except Exception as e:
        print(f"    [SCRAPE ERROR] {source['name']}: {e}")
        return []

def scrape_rss_source(source: dict) -> List[str]:
    """Scrapes headlines from an RSS source using ElementTree."""
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    try:
        response = requests.get(source["url"], headers=headers, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        titles = root.findall('.//item/title')
        
        headlines = []
        for t in titles:
            text = t.text.strip() if t.text else ""
            if len(text) >= MIN_HEADLINE_LENGTH:
                headlines.append(text)
            if len(headlines) >= MAX_HEADLINES_PER_SOURCE:
                break
        return headlines
    except Exception as e:
        print(f"    [RSS ERROR] {source['name']}: {e}")
        return []

def translate_headline(headline: str, src_language: str) -> str:
    """Translate a headline from source language to English."""
    if not headline.strip(): return ""
    try:
        translator = GoogleTranslator(source=src_language, target='en')
        return translator.translate(headline)
    except Exception:
        return headline

def analyze_sentiment(headline_en: str) -> Tuple[float, str]:
    """Analyze sentiment using RoBERTa (HF API) or keyword fallback."""
    if not HF_API_TOKEN:
        return _fallback_sentiment(headline_en)

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": headline_en}

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                predictions = result[0] if isinstance(result[0], list) else result
                polarity = 0.0
                top_label, top_score = 'neutral', 0.0
                for pred in predictions:
                    label = pred.get('label', '').lower()
                    score = pred.get('score', 0.0)
                    weight = LABEL_TO_POLARITY.get(label, 0.0)
                    polarity += weight * score
                    if score > top_score:
                        top_score, top_label = score, label
                return round(polarity, 4), top_label
        return _fallback_sentiment(headline_en)
    except Exception:
        return _fallback_sentiment(headline_en)

def _fallback_sentiment(headline_en: str) -> Tuple[float, str]:
    text = headline_en.lower()
    positive_words = {'good', 'great', 'success', 'win', 'peace', 'growth', 'progress', 'victory', 'improve'}
    negative_words = {'war', 'kill', 'death', 'attack', 'crisis', 'fail', 'disaster', 'conflict', 'terror'}
    pos = sum(1 for w in positive_words if w in text)
    neg = sum(1 for w in negative_words if w in text)
    total = pos + neg
    if total == 0: return 0.0, 'neutral'
    polarity = round((pos - neg) / total, 4)
    label = 'positive' if polarity > 0 else ('negative' if polarity < 0 else 'neutral')
    return polarity, label

def perform_ner(text: str) -> List[Tuple[str, str]]:
    doc = nlp(text)
    return [(ent.text, ent.label_) for ent in doc.ents]

# ── Main Entry Point ───────────────────────────────────────────────────────

def main():
    current_date_str = date.today().strftime("%Y_%m_%d")
    output_dir = os.path.join(os.getcwd(), "raw_csv_daily")
    os.makedirs(output_dir, exist_ok=True)
    csv_filepath = os.path.join(output_dir, f"raw_headlines_data_{current_date_str}.csv")

    data_to_save = []
    total_sources = 0
    failed_sources = 0

    print(f"\n--- Intelligence Gathering: {current_date_str} ---")

    for source in SOURCES:
        if not source["enabled"]:
            continue
        
        total_sources += 1
        print(f"\n[*] Processing {source['name']} ({source['region']})...")
        
        # --- PHASE 4: Try/Except Safeguard per Source ---
        try:
            # 1. Scrape
            if source["type"] == "html":
                raw_headlines = scrape_html_source(source)
            else:
                raw_headlines = scrape_rss_source(source)

            if not raw_headlines:
                # --- PHASE 4: [WARN] logging ---
                print(f"    [WARN] {source['name']} returned 0 headlines.")
                failed_sources += 1
                time.sleep(1) # Maintain rhythm
                continue

            print(f"    Fetched {len(raw_headlines)} headlines.")

            # 2. Process Headlines
            for original_headline in raw_headlines:
                # Double check length safeguard
                if len(original_headline) < MIN_HEADLINE_LENGTH:
                    continue

                # Translation phase
                if source["requires_translation"]:
                    translated_headline = translate_headline(original_headline, source["language"])
                else:
                    translated_headline = original_headline

                # Analysis phase
                polarity, sentiment_label = analyze_sentiment(translated_headline)
                entities = perform_ner(translated_headline)

                # Safe console print
                try:
                    print(f"    -> [{sentiment_label}] {polarity:+.2f} | {translated_headline[:70]}...")
                except UnicodeEncodeError:
                    print(f"    -> [{sentiment_label}] {polarity:+.2f} | [Encoded Content]")

                # --- PHASE 4: CSV Schema Preservation ---
                data_to_save.append({
                    'Scrape_Date': current_date_str,
                    'Source_Name': source['name'],
                    'Source_URL': source['url'],
                    'Source_Language_Code': source['language'],
                    'Source_Region': source['region'], # Regional data for dashboard
                    'Original_Headline': original_headline,
                    'Translated_Headline': translated_headline,
                    'Polarity': polarity,
                    'Sentiment_Label': sentiment_label,
                    'Entities_Raw': str(entities)
                })

        except Exception as e:
            print(f"    [CRITICAL ERROR] Failed to process source {source['name']}: {e}")
            failed_sources += 1

        # --- PHASE 4: Rate Limiting ---
        time.sleep(1)

    if data_to_save:
        # Downstream scripts expect these columns
        fieldnames = ['Scrape_Date', 'Source_Name', 'Source_URL', 'Source_Language_Code', 'Source_Region', 
                      'Original_Headline', 'Translated_Headline', 'Polarity', 'Sentiment_Label', 'Entities_Raw']

        with open(csv_filepath, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_to_save)

    print(f"\n[DONE] {len(data_to_save)} headlines collected from {total_sources - failed_sources} sources. {failed_sources} sources failed.")

if __name__ == "__main__":
    main()