
import csv
import subprocess
import os
from datetime import date 


import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from textblob import TextBlob
import spacy

try:
    import en_core_web_sm
except ImportError:
    print("en_core_web_sm not found. Downloading...")
    try:

        subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
        import en_core_web_sm
    except Exception as e:
        print(f"Failed to download spacy model: {e}")
        exit()
nlp = spacy.load('en_core_web_sm')
SITE_CONFIGS = [
    {
        "url": "https://www.bbc.com/mundo",
        "tag": "h3",
        "class": "bbc-pam0zn e47bds20",
        "src_language": "es"  # Spanish
    },
    {
        "url": "https://www.bbc.com/hindi",
        "tag": "h3",
        "class": "bbc-1kr00f0 e47bds20",
        "src_language": "hi"  # Hindi
    },
    {
        "url": "https://www.bbc.com/portuguese",
        "tag": "h3",
        "class": "bbc-pam0zn e47bds20",
        "src_language": "pt"  # Portuguese
    },
    {
        "url": "https://www.bbc.com/russian",
        "tag": "h3",
        "class": "bbc-pam0zn e47bds20",
        "src_language": "ru"  # Russian
    },
    {
        "url": "https://www.bbc.com/japanese",
        "tag": "h3",
        "class": "bbc-7k6nqm e47bds20",
        "src_language": "ja"  # Japanese
    },
    {
        "url": "https://www.bbc.com/zhongwen/simp",  
        "tag": "h3",
        "class": "bbc-pam0zn e47bds20",
        "src_language": "zh"  # Chinese
    }
]


def fetch_headlines(url, headline_tag, headline_class):
    """Fetches the top headlines from a given URL using BeautifulSoup."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        page = requests.get(url, headers=headers, timeout=10)
        page.raise_for_status() 
        soup = BeautifulSoup(page.content, 'html.parser')

        headlines = soup.find_all(headline_tag, class_=headline_class)
        return [headline.get_text(strip=True) for headline in headlines[:5]]
    except Exception as e:
        print(f"Error fetching headlines from {url}: {e}")
        return []


def translate_headline(headline, src_language):
    """Translates a single headline to English using GoogleTranslator."""
    translator = GoogleTranslator(source=src_language, target='en')
    try:
        if not headline.strip():
            return ""
        return translator.translate(headline)
    except Exception as e:
        print(f"Error translating headline: '{headline[:30]}...'. Error: {e}")
        return headline 


def analyze_sentiment(headline_en):
    """Calculates sentiment polarity (-1.0 to 1.0) of the English headline."""
    analysis = TextBlob(headline_en)
    return analysis.sentiment.polarity


def perform_ner(text):
    """Performs Named Entity Recognition (NER) using spaCy."""
    doc = nlp(text)

    return [(ent.text, ent.label_) for ent in doc.ents]


def main():
    """Main function to orchestrate scraping, analysis, and data saving."""

    output_dir = os.path.join(os.pardir, "Data_Processing")
    os.makedirs(output_dir, exist_ok=True)
    csv_filepath = os.path.join(output_dir, "raw_headlines_data.csv")

    data_to_save = []

    print("--- Starting News Headline Collection and Analysis ---")

    for config in SITE_CONFIGS:
        source_name = config['url'].split('/')[-1]
        print(f"\nProcessing source: {source_name.upper()}...")

        headlines_original = fetch_headlines(config['url'], config['tag'], config['class'])

        if not headlines_original:
            print(f"Skipping {source_name} due to fetch error.")
            continue

        for original_headline in headlines_original:
            # 1. Translation
            translated_headline = translate_headline(original_headline, config['src_language'])

            # 2. Sentiment Analysis (on English text)
            polarity = analyze_sentiment(translated_headline)
            # 3. Named Entity Recognition (on English text)
            entities = perform_ner(translated_headline)

            data_to_save.append({
                'Source_URL': config['url'],
                'Source_Language_Code': config['src_language'],
                'Original_Headline': original_headline,
                'Translated_Headline': translated_headline,
                'Polarity': polarity,
                'Entities_Raw': str(entities)
            })

            print(f"   -> Translated: {translated_headline} | Polarity: {polarity:.2f}")
    fieldnames = ['Source_URL', 'Source_Language_Code', 'Original_Headline',
                  'Translated_Headline', 'Polarity', 'Entities_Raw']

    with open(csv_filepath, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_to_save)

    print(f"\n--- Analysis complete. Raw data saved to {csv_filepath} ---")

if __name__ == "__main__":
    main()
