"""
Tests for Scraping_Scripts/web_scraper.py
Tests translation and sentiment functions without making live API calls.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestTranslateHeadline:
    """Tests for the translate_headline function."""

    @patch('Scraping_Scripts.web_scraper.GoogleTranslator')
    def test_translates_non_empty(self, mock_translator_cls):
        from Scraping_Scripts.web_scraper import translate_headline
        mock_instance = MagicMock()
        mock_instance.translate.return_value = 'Hello World'
        mock_translator_cls.return_value = mock_instance

        result = translate_headline('Hola Mundo', 'es')
        assert result == 'Hello World'

    @patch('Scraping_Scripts.web_scraper.GoogleTranslator')
    def test_empty_string_returns_empty(self, mock_translator_cls):
        from Scraping_Scripts.web_scraper import translate_headline
        result = translate_headline('   ', 'es')
        assert result == ''

    @patch('Scraping_Scripts.web_scraper.GoogleTranslator')
    def test_translation_error_returns_original(self, mock_translator_cls):
        from Scraping_Scripts.web_scraper import translate_headline
        mock_instance = MagicMock()
        mock_instance.translate.side_effect = Exception('API Error')
        mock_translator_cls.return_value = mock_instance

        result = translate_headline('Hola', 'es')
        assert result == 'Hola'


class TestAnalyzeSentimentHF:
    """Tests for the analyze_sentiment_hf function."""

    @patch('Scraping_Scripts.web_scraper.HF_API_TOKEN', 'fake_token')
    @patch('Scraping_Scripts.web_scraper.requests.post')
    def test_positive_sentiment(self, mock_post):
        from Scraping_Scripts.web_scraper import analyze_sentiment_hf
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [[
            {'label': 'POSITIVE', 'score': 0.85},
            {'label': 'NEGATIVE', 'score': 0.15},
        ]]
        mock_post.return_value = mock_response

        polarity, label = analyze_sentiment_hf('Great news for the economy')
        assert polarity > 0
        assert label == 'positive'

    @patch('Scraping_Scripts.web_scraper.HF_API_TOKEN', 'fake_token')
    @patch('Scraping_Scripts.web_scraper.requests.post')
    def test_api_error_returns_fallback(self, mock_post):
        from Scraping_Scripts.web_scraper import analyze_sentiment_hf
        mock_post.side_effect = Exception('API Error')

        polarity, label = analyze_sentiment_hf('Test headline')
        # Fallback sentiment returns TextBlob's polarity, which is 0 for 'Test headline'
        assert polarity == 0.0
        assert label == 'neutral'

    @patch('Scraping_Scripts.web_scraper.HF_API_TOKEN', '')
    def test_no_token_uses_fallback(self):
        from Scraping_Scripts.web_scraper import analyze_sentiment_hf
        polarity, label = analyze_sentiment_hf('There is a terrible war and crisis happening')
        assert polarity < 0
        assert label == 'negative'
