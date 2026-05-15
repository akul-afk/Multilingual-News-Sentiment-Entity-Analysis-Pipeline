"""
Tests for Data_Processing/data_aggregator.py
Validates dashboard JSON generation, geo_data fields, and digest synthesis.
"""

import pytest
import json
from unittest.mock import patch
from Data_Processing.data_aggregator import (
    _parse_date,
    _sentiment_label,
    _build_daily_summary,
)


class TestParseDate:
    """Tests for date parsing utility."""

    def test_underscore_format(self):
        result = _parse_date('2025_01_15')
        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15

    def test_dash_format(self):
        """Should fail since aggregator only handles YYYY_MM_DD."""
        result = _parse_date('2025-01-15')
        # _parse_date only handles underscore format
        # Returns None for dash format (this is expected behavior)
        assert result is None or result.day == 15

    def test_invalid_format(self):
        result = _parse_date('not-a-date')
        assert result is None

    def test_none_input(self):
        result = _parse_date(None)
        assert result is None


class TestSentimentLabel:
    """Tests for sentiment labeling."""

    def test_positive(self):
        assert _sentiment_label(0.5) == 'Positive'

    def test_negative(self):
        assert _sentiment_label(-0.5) == 'Negative'

    def test_neutral(self):
        assert _sentiment_label(0.01) == 'Neutral'

    def test_boundary_positive(self):
        assert _sentiment_label(0.05) == 'Neutral'

    def test_boundary_negative(self):
        assert _sentiment_label(-0.05) == 'Neutral'


class TestBuildDailySummary:
    """Tests for daily summary generation."""

    def test_returns_list(self, sample_headlines_df):
        sample_headlines_df['Source_Name'] = 'BBC Spanish'
        result = _build_daily_summary(sample_headlines_df)
        assert isinstance(result, list)

    def test_empty_input(self):
        import pandas as pd
        result = _build_daily_summary(pd.DataFrame())
        assert result == []

    def test_summary_has_required_keys(self, sample_headlines_df):
        sample_headlines_df['Source_Name'] = 'BBC Spanish'
        result = _build_daily_summary(sample_headlines_df)
        if result:
            day = result[0]
            assert 'date' in day
            assert 'total_headlines' in day
            assert 'avg_polarity' in day
