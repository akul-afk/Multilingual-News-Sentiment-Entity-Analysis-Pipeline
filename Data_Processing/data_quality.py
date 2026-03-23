"""
Data Quality Validation Module
Validates scraped CSV data using assertion-based checks.
Outputs JSON validation reports to Data_Output/quality_reports/.
"""

import os
import json
import pandas as pd
from datetime import datetime


def validate_raw_data(csv_path, report_dir=None):
    """
    Run data quality checks on a raw scraped CSV file.

    Returns:
        dict: Validation report with pass/fail status for each check.
    """
    if report_dir is None:
        project_root = os.getcwd()
        report_dir = os.path.join(project_root, "Data_Output", "quality_reports")

    os.makedirs(report_dir, exist_ok=True)

    report = {
        "file": os.path.basename(csv_path),
        "timestamp": datetime.now().isoformat(),
        "overall_status": "PASS",
        "checks": [],
        "summary": {}
    }

    # ── Load Data ──────────────────────────────────────────────
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        report["overall_status"] = "FAIL"
        report["checks"].append({
            "name": "file_exists",
            "status": "FAIL",
            "detail": f"File not found: {csv_path}"
        })
        _save_report(report, report_dir)
        return report
    except pd.errors.EmptyDataError:
        report["overall_status"] = "FAIL"
        report["checks"].append({
            "name": "file_not_empty",
            "status": "FAIL",
            "detail": "CSV file is empty"
        })
        _save_report(report, report_dir)
        return report

    # ── Check 1: Schema Validation ─────────────────────────────
    expected_columns = {
        'Scrape_Date', 'Source_URL', 'Source_Language_Code',
        'Original_Headline', 'Translated_Headline', 'Polarity', 'Entities_Raw'
    }
    actual_columns = set(df.columns)
    missing = expected_columns - actual_columns
    extra = actual_columns - expected_columns - {'Sentiment_Label'}  # allow new column

    report["checks"].append({
        "name": "schema_validation",
        "status": "PASS" if not missing else "FAIL",
        "expected_columns": sorted(expected_columns),
        "missing_columns": sorted(missing),
        "extra_columns": sorted(extra),
        "detail": f"Missing: {missing}" if missing else "All expected columns present"
    })

    if missing:
        report["overall_status"] = "FAIL"

    # ── Check 2: Minimum Row Count ─────────────────────────────
    min_rows = 10  # At least 10 headlines expected (6 sources × ~10 each)
    row_count = len(df)

    report["checks"].append({
        "name": "minimum_row_count",
        "status": "PASS" if row_count >= min_rows else "WARN",
        "expected_min": min_rows,
        "actual": row_count,
        "detail": f"{row_count} rows found (min: {min_rows})"
    })

    if row_count < min_rows:
        report["overall_status"] = "WARN" if report["overall_status"] != "FAIL" else "FAIL"

    # ── Check 3: No Null Headlines ─────────────────────────────
    null_translated = df['Translated_Headline'].isna().sum() if 'Translated_Headline' in df.columns else 0
    null_original = df['Original_Headline'].isna().sum() if 'Original_Headline' in df.columns else 0

    report["checks"].append({
        "name": "no_null_headlines",
        "status": "PASS" if null_translated == 0 and null_original == 0 else "WARN",
        "null_translated": int(null_translated),
        "null_original": int(null_original),
        "detail": f"Null translated: {null_translated}, null original: {null_original}"
    })

    # ── Check 4: Polarity Range ────────────────────────────────
    if 'Polarity' in df.columns:
        polarity_min = float(df['Polarity'].min())
        polarity_max = float(df['Polarity'].max())
        in_range = polarity_min >= -1.0 and polarity_max <= 1.0

        report["checks"].append({
            "name": "polarity_in_range",
            "status": "PASS" if in_range else "FAIL",
            "expected_range": [-1.0, 1.0],
            "actual_range": [round(polarity_min, 4), round(polarity_max, 4)],
            "detail": f"Range: [{polarity_min:.4f}, {polarity_max:.4f}]"
        })

        if not in_range:
            report["overall_status"] = "FAIL"

    # ── Check 5: Source Diversity ──────────────────────────────
    if 'Source_URL' in df.columns:
        unique_sources = df['Source_URL'].nunique()
        expected_min_sources = 3  # At least 3 of 6 sources should have data

        report["checks"].append({
            "name": "source_diversity",
            "status": "PASS" if unique_sources >= expected_min_sources else "WARN",
            "expected_min_sources": expected_min_sources,
            "actual_sources": unique_sources,
            "source_list": df['Source_URL'].unique().tolist(),
            "detail": f"{unique_sources} unique sources found (min: {expected_min_sources})"
        })

    # ── Check 6: No Duplicate Headlines ─────────────────────────
    if 'Translated_Headline' in df.columns:
        dupes = df.duplicated(subset=['Translated_Headline', 'Source_URL'], keep=False).sum()

        report["checks"].append({
            "name": "no_duplicate_headlines",
            "status": "PASS" if dupes == 0 else "WARN",
            "duplicate_count": int(dupes),
            "detail": f"{dupes} duplicate headline-source pairs found"
        })

    # ── Check 7: Headline Length ────────────────────────────────
    if 'Translated_Headline' in df.columns:
        short = (df['Translated_Headline'].str.len() < 10).sum()
        long = (df['Translated_Headline'].str.len() > 500).sum()

        report["checks"].append({
            "name": "headline_length_reasonable",
            "status": "PASS" if short == 0 and long == 0 else "WARN",
            "too_short": int(short),
            "too_long": int(long),
            "detail": f"Short (<10 chars): {short}, Long (>500 chars): {long}"
        })

    # ── Check 8: Date Format ───────────────────────────────────
    if 'Scrape_Date' in df.columns:
        date_str = str(df['Scrape_Date'].iloc[0])
        valid_format = len(date_str) == 10 and date_str.count('_') == 2

        report["checks"].append({
            "name": "date_format_valid",
            "status": "PASS" if valid_format else "WARN",
            "sample_date": date_str,
            "expected_format": "YYYY_MM_DD",
            "detail": f"Sample date: {date_str}"
        })

    # ── Summary ────────────────────────────────────────────────
    passed = sum(1 for c in report["checks"] if c["status"] == "PASS")
    warned = sum(1 for c in report["checks"] if c["status"] == "WARN")
    failed = sum(1 for c in report["checks"] if c["status"] == "FAIL")

    report["summary"] = {
        "total_checks": len(report["checks"]),
        "passed": passed,
        "warnings": warned,
        "failed": failed,
        "row_count": row_count
    }

    # Print summary
    status_icon = {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL"}
    print(f"\n  [DATA QUALITY] {report['overall_status']} — "
          f"{passed} passed, {warned} warnings, {failed} failed "
          f"({row_count} rows)")

    for check in report["checks"]:
        icon = status_icon[check["status"]]
        print(f"    [{icon}] {check['name']}: {check['detail']}")

    _save_report(report, report_dir)
    return report


def _save_report(report, report_dir):
    """Save validation report as JSON."""
    filename = f"quality_report_{report['file'].replace('.csv', '')}.json"
    filepath = os.path.join(report_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"  [DATA QUALITY] Report saved to {filepath}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        validate_raw_data(sys.argv[1])
    else:
        print("Usage: python data_quality.py <path_to_csv>")
