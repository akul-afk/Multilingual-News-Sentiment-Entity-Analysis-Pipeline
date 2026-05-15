"""
Tests for Data_Processing/data_quality.py
Validates the assertion helpers and the full validation pipeline.
"""

import pytest
import pandas as pd
from Data_Processing.data_quality import (
    validate_raw_data,
    _assert_not_null,
    _assert_unique,
    _assert_value_range,
    DataQualityConfig,
)


# ═══════════════════════════════════════════════════════════════
#  Assertion Helper Tests
# ═══════════════════════════════════════════════════════════════

class TestAssertNotNull:
    """Tests for the _assert_not_null helper."""

    def test_pass_no_nulls(self, sample_headlines_df):
        result = _assert_not_null(sample_headlines_df, 'Translated_Headline')
        assert result['passed'] is True
        assert result['failed_count'] == 0

    def test_fail_with_nulls(self):
        df = pd.DataFrame({'col': ['a', None, 'c', None]})
        result = _assert_not_null(df, 'col')
        assert result['passed'] is False
        assert result['failed_count'] == 2


class TestAssertUnique:
    """Tests for the _assert_unique helper."""

    def test_pass_all_unique(self, sample_headlines_df):
        result = _assert_unique(sample_headlines_df, 'Translated_Headline')
        assert result['passed'] is True

    def test_fail_with_duplicates(self):
        df = pd.DataFrame({'col': ['a', 'b', 'a', 'c']})
        result = _assert_unique(df, 'col')
        assert result['passed'] is False
        assert result['failed_count'] == 1  # 'a' is duplicated once


class TestAssertValueRange:
    """Tests for the _assert_value_range helper."""

    def test_pass_within_range(self, sample_headlines_df):
        result = _assert_value_range(sample_headlines_df, 'Polarity', -1.0, 1.0)
        assert result['passed'] is True

    def test_fail_out_of_range(self):
        df = pd.DataFrame({'val': [0.5, 1.2, -0.3, -1.5]})
        result = _assert_value_range(df, 'val', -1.0, 1.0)
        assert result['passed'] is False
        assert result['failed_count'] == 2


class TestDataQualityConfig:
    """Tests for the DataQualityConfig dataclass."""

    def test_default_values(self):
        config = DataQualityConfig()
        assert config.min_rows == 10
        assert config.min_sources == 3
        assert config.polarity_range == (-1.0, 1.0)

    def test_custom_values(self):
        config = DataQualityConfig(min_rows=5, min_sources=2)
        assert config.min_rows == 5
        assert config.min_sources == 2


# ═══════════════════════════════════════════════════════════════
#  Full Validation Pipeline Tests
# ═══════════════════════════════════════════════════════════════

class TestValidateRawData:
    """Tests for the validate_raw_data function."""

    def test_valid_csv_passes(self, sample_raw_csv, tmp_path):
        report = validate_raw_data(sample_raw_csv, report_dir=str(tmp_path))
        assert report['overall_status'] in ('PASS', 'WARN')
        assert report['summary']['failed'] == 0

    def test_missing_file_fails(self, tmp_path):
        report = validate_raw_data('/nonexistent/path.csv', report_dir=str(tmp_path))
        assert report['overall_status'] == 'FAIL'
        assert any(c['name'] == 'file_exists' for c in report['checks'])

    def test_empty_file_fails(self, empty_csv, tmp_path):
        report = validate_raw_data(empty_csv, report_dir=str(tmp_path))
        assert report['overall_status'] == 'FAIL'

    def test_schema_validation_detects_missing_columns(self, tmp_path):
        df = pd.DataFrame({'Wrong_Column': ['a']})
        csv_path = tmp_path / "bad_schema.csv"
        df.to_csv(csv_path, index=False)
        report = validate_raw_data(str(csv_path), report_dir=str(tmp_path))
        schema_check = next(c for c in report['checks'] if c['name'] == 'schema_validation')
        assert schema_check['status'] == 'FAIL'

    def test_report_saved_as_json(self, sample_raw_csv, tmp_path):
        validate_raw_data(sample_raw_csv, report_dir=str(tmp_path))
        reports = list(tmp_path.glob('quality_report_*.json'))
        assert len(reports) >= 1

    def test_polarity_out_of_range_fails(self, tmp_path, sample_headlines_df):
        sample_headlines_df.loc[0, 'Polarity'] = 2.5  # Out of range
        csv_path = tmp_path / "bad_polarity.csv"
        sample_headlines_df.to_csv(csv_path, index=False)
        report = validate_raw_data(str(csv_path), report_dir=str(tmp_path))
        polarity_check = next(c for c in report['checks'] if c['name'] == 'polarity_in_range')
        assert polarity_check['status'] == 'FAIL'
