import csv
import subprocess
import os
from datetime import date
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import spacy
import time
import sys
import json

try:
    import en_core_web_sm
except ImportError:
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
    import en_core_web_sm

nlp = spacy.load('en_core_web_sm')

# ── HuggingFace Inference API Config ────────────────────────────────────────
HF_API_TOKEN = os.environ.get('HF_API_TOKEN', '')
HF_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

# Label mapping: RoBERTa outputs → polarity float
# Model labels: negative, neutral, positive
LABEL_TO_POLARITY = {
    'negative': -1.0,
    'neutral':   0.0,
    'positive':  1.0,
}

SITE_CONFIGS = [
    {
        "url": "https://www.bbc.com/mundo",
        "tag": "h3",
        "class": "bbc-pam0zn e47bds20",
        "src_language": "es"
    },
    {
        "url": "https://www.bbc.com/hindi",
        "tag": "h3",
        "class": "bbc-1kr00f0 e47bds20",
        "src_language": "hi"
    },
    {
        "url": "https://www.bbc.com/portuguese",
        "tag": "h3",
        "class": "bbc-pam0zn e47bds20",
        "src_language": "pt"
    },
    {
        "url": "https://www.bbc.com/russian",
        "tag": "h3",
        "class": "bbc-pam0zn e47bds20",
        "src_language": "ru"
    },
    {
        "url": "https://www.bbc.com/japanese",
        "tag": "h3",
        "class": "bbc-7k6nqm e47bds20",
        "src_language": "ja"
    },
    {
        "url": "https://www.bbc.com/swahili",
        "tag": "h3",
        "class": "bbc-pam0zn e47bds20",
        "src_language": "sw"  # Swahili (East Africa)
    }
]


def fetch_headlines(url, headline_tag, headline_class):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }

    try:
        page = requests.get(url, headers=headers, timeout=15)
        page.raise_for_status()
        soup = BeautifulSoup(page.content, 'html.parser')

        main_list = soup.find('ul', class_='bbc-1rrncb9')

        if not main_list:
             main_list = soup.find('div', class_='bbc-1ajedpd')
             if not main_list:
                 return []

        headlines = []

        for item in main_list.find_all('li', recursive=False):
            headline_element = item.find('h3')

            if headline_element:
                headline_text = headline_element.a.get_text(strip=True) if headline_element.a else headline_element.get_text(strip=True)

                if len(headline_text) > 10:
                    headlines.append(headline_text)

            if len(headlines) >= 10:
                break

        return headlines

    except Exception:
        return []


def translate_headline(headline, src_language):
    translator = GoogleTranslator(source=src_language, target='en')
    try:
        if not headline.strip():
            return ""
        return translator.translate(headline)
    except Exception:
        return headline


def analyze_sentiment_hf(headline_en):
    """
    Analyze sentiment using cardiffnlp/twitter-roberta-base-sentiment-latest
    via HuggingFace Inference API.

    Returns:
        polarity (float): weighted sentiment score in [-1, +1]
        label (str): 'positive', 'negative', or 'neutral'
    """
    if not HF_API_TOKEN:
        return _fallback_sentiment(headline_en)

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": headline_en}

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=15)

        if response.status_code == 503:
            # Model loading — wait and retry once
            time.sleep(20)
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            return _fallback_sentiment(headline_en)

        result = response.json()

        # API returns [[{label, score}, ...]] — list of predictions sorted by confidence
        if isinstance(result, list) and len(result) > 0:
            predictions = result[0] if isinstance(result[0], list) else result

            # Compute weighted polarity from all label scores
            polarity = 0.0
            top_label = 'neutral'
            top_score = 0.0

            for pred in predictions:
                label = pred.get('label', '').lower()
                score = pred.get('score', 0.0)
                weight = LABEL_TO_POLARITY.get(label, 0.0)
                polarity += weight * score

                if score > top_score:
                    top_score = score
                    top_label = label

            return round(polarity, 4), top_label

        return _fallback_sentiment(headline_en)

    except Exception:
        return _fallback_sentiment(headline_en)


def _fallback_sentiment(headline_en):
    """Simple keyword-based fallback when HF API is unavailable."""
    text = headline_en.lower()
    positive_words = {'good', 'great', 'success', 'win', 'peace', 'growth', 'progress',
                      'positive', 'hope', 'agreement', 'victory', 'celebrate', 'improve'}
    negative_words = {'war', 'kill', 'death', 'attack', 'crisis', 'fail', 'disaster',
                      'conflict', 'bomb', 'victim', 'destroy', 'terror', 'threat', 'collapse'}

    pos = sum(1 for w in positive_words if w in text)
    neg = sum(1 for w in negative_words if w in text)
    total = pos + neg

    if total == 0:
        return 0.0, 'neutral'

    polarity = round((pos - neg) / total, 4)
    label = 'positive' if polarity > 0 else ('negative' if polarity < 0 else 'neutral')
    return polarity, label


def perform_ner(text):
    doc = nlp(text)
    return [(ent.text, ent.label_) for ent in doc.ents]


def main():
    current_date_str = date.today().strftime("%Y_%m_%d")

    project_root = os.getcwd()
    output_dir = os.path.join(project_root, "raw_csv_daily")

    os.makedirs(output_dir, exist_ok=True)
    csv_filepath = os.path.join(output_dir, f"raw_headlines_data_{current_date_str}.csv")

    data_to_save = []

    sentiment_model = "RoBERTa (HF API)" if HF_API_TOKEN else "Keyword Fallback"
    print(f"\n  Sentiment model: {sentiment_model}")

    for config in SITE_CONFIGS:
        headlines_original = fetch_headlines(config['url'], config['tag'], config['class'])
        source_name = config['url'].split('/')[-1]
        print(f"\nProcessing source: {source_name.upper()}...")
        if not headlines_original:
            continue

        for original_headline in headlines_original:
            translated_headline = translate_headline(original_headline, config['src_language'])
            polarity, sentiment_label = analyze_sentiment_hf(translated_headline)
            entities = perform_ner(translated_headline)

            print(f"   -> {config['src_language'].upper()} [{sentiment_label}] {polarity:+.4f} | {translated_headline[:80]}")

            data_to_save.append({
                'Scrape_Date': current_date_str,
                'Source_URL': config['url'],
                'Source_Language_Code': config['src_language'],
                'Original_Headline': original_headline,
                'Translated_Headline': translated_headline,
                'Polarity': polarity,
                'Sentiment_Label': sentiment_label,
                'Entities_Raw': str(entities)
            })

        time.sleep(2)

    if data_to_save:
        fieldnames = ['Scrape_Date', 'Source_URL', 'Source_Language_Code', 'Original_Headline',
                      'Translated_Headline', 'Polarity', 'Sentiment_Label', 'Entities_Raw']

        with open(csv_filepath, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_to_save)

    print(f"\n  Saved {len(data_to_save)} headlines to {csv_filepath}")

if __name__ == "__main__":
    main()