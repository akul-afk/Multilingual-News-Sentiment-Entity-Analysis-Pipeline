import csv
import subprocess
import os
from datetime import date 
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from textblob import TextBlob
import spacy
import time
import sys

try:
    import en_core_web_sm
except ImportError:
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
    import en_core_web_sm

nlp = spacy.load('en_core_web_sm')
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


def analyze_sentiment(headline_en):
    analysis = TextBlob(headline_en)
    return analysis.sentiment.polarity


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

    for config in SITE_CONFIGS:
        headlines_original = fetch_headlines(config['url'], config['tag'], config['class']) 
        source_name = config['url'].split('/')[-1] 
        print(f"\nProcessing source: {source_name.upper()}...")
        if not headlines_original:
            continue

        for original_headline in headlines_original:
            translated_headline = translate_headline(original_headline, config['src_language'])
            polarity = analyze_sentiment(translated_headline)
            entities = perform_ner(translated_headline)


            print(f"   -> {config['src_language'].upper()} Translated: {translated_headline} | Polarity: {polarity:.2f}")

            data_to_save.append({
                'Scrape_Date': current_date_str,
                'Source_URL': config['url'],
                'Source_Language_Code': config['src_language'],
                'Original_Headline': original_headline,
                'Translated_Headline': translated_headline,
                'Polarity': polarity,
                'Entities_Raw': str(entities)
            })
        
        time.sleep(2)

    if data_to_save:
        fieldnames = ['Scrape_Date', 'Source_URL', 'Source_Language_Code', 'Original_Headline',
                      'Translated_Headline', 'Polarity', 'Entities_Raw']

        with open(csv_filepath, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_to_save)

if __name__ == "__main__":
    main()