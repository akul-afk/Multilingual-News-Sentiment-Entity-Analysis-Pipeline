"""
Data Aggregator Module
Consolidates daily CSVs into a single dashboard_data.json for the frontend.
Generates: daily_summary, weekly_reports, monthly_reports, entities, geo_data, recent_headlines.
"""

import os
import json
import glob
from datetime import datetime, timedelta
from collections import Counter, defaultdict

import pandas as pd


# ── Region mapping for heatmap ──────────────────────────────────────────────
SOURCE_GEO_MAP = {
    'BBC Spanish':    {'region': 'Latin America',     'lat': 19.43, 'lng': -99.13, 'lang_code': 'es'},
    'BBC Hindi':      {'region': 'South Asia',        'lat': 20.59, 'lng': 78.96,  'lang_code': 'hi'},
    'BBC Portuguese': {'region': 'South America',     'lat': -14.24, 'lng': -51.93, 'lang_code': 'pt'},
    'BBC Russian':    {'region': 'Eastern Europe',    'lat': 55.75, 'lng': 37.62,  'lang_code': 'ru'},
    'BBC Japanese':   {'region': 'East Asia',         'lat': 36.20, 'lng': 138.25, 'lang_code': 'ja'},
    'BBC Swahili':    {'region': 'East Africa',       'lat': -1.29, 'lng': 36.82,  'lang_code': 'sw'},
}


def _parse_date(date_str):
    """Parse date string in YYYY_MM_DD format."""
    try:
        return datetime.strptime(str(date_str).strip(), "%Y_%m_%d")
    except (ValueError, TypeError):
        return None


def _load_all_csvs(directory, prefix):
    """Load all CSVs matching a prefix from a directory into a single DataFrame."""
    pattern = os.path.join(directory, f"{prefix}*.csv")
    files = sorted(glob.glob(pattern))

    if not files:
        return pd.DataFrame()

    frames = []
    for f in files:
        try:
            df = pd.read_csv(f, on_bad_lines='skip')
            if not df.empty:
                frames.append(df)
        except Exception as e:
            print(f"  [AGGREGATOR] Skipping corrupt file: {os.path.basename(f)} ({e})")
            continue

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def _sentiment_label(polarity):
    """Classify polarity into sentiment category."""
    if polarity > 0.05:
        return 'Positive'
    elif polarity < -0.05:
        return 'Negative'
    return 'Neutral'


def _generate_executive_summary(df_period, df_prev_period, period_label):
    """Generate an AI-style executive summary from aggregated stats."""
    if df_period.empty:
        return f"No data available for {period_label}."

    total = len(df_period)
    avg_polarity = df_period['Polarity'].mean()
    sources = df_period.groupby('Source_Name')['Polarity'].mean().sort_values()

    most_negative_src = sources.index[0] if len(sources) > 0 else 'N/A'
    most_positive_src = sources.index[-1] if len(sources) > 0 else 'N/A'
    neg_val = sources.iloc[0] if len(sources) > 0 else 0
    pos_val = sources.iloc[-1] if len(sources) > 0 else 0

    # Sentiment shift
    shift_text = ""
    if not df_prev_period.empty:
        prev_avg = df_prev_period['Polarity'].mean()
        shift = avg_polarity - prev_avg
        direction = "improved" if shift > 0 else "declined"
        shift_text = f" Overall sentiment {direction} by {abs(shift):.2f} compared to the previous period."

    summary = (
        f"During {period_label}, a total of {total} headlines were analyzed across "
        f"{len(sources)} language services. {most_positive_src} maintained the most "
        f"positive outlook ({pos_val:+.2f} avg polarity), while {most_negative_src} "
        f"showed the most negative sentiment ({neg_val:+.2f}).{shift_text}"
    )

    return summary


def _build_daily_summary(df_headlines):
    """Build per-date, per-source aggregated stats."""
    if df_headlines.empty:
        return []

    grouped = df_headlines.groupby(['Scrape_Date', 'Source_Name']).agg(
        count=('Polarity', 'size'),
        avg_polarity=('Polarity', 'mean')
    ).reset_index()

    result = {}
    for _, row in grouped.iterrows():
        date_key = str(row['Scrape_Date'])
        if date_key not in result:
            result[date_key] = {'date': date_key, 'sources': {}}

        result[date_key]['sources'][row['Source_Name']] = {
            'count': int(row['count']),
            'avg_polarity': round(float(row['avg_polarity']), 4)
        }

    # Add totals per day
    for date_key, data in result.items():
        day_df = df_headlines[df_headlines['Scrape_Date'] == date_key]
        data['total_headlines'] = len(day_df)
        data['avg_polarity'] = round(float(day_df['Polarity'].mean()), 4)

    return list(result.values())


def _build_period_reports(df_headlines, df_entities, period_type='weekly'):
    """Build weekly or monthly report structures."""
    if df_headlines.empty:
        return []

    df = df_headlines.copy()
    df['parsed_date'] = df['Scrape_Date'].apply(_parse_date)
    df = df.dropna(subset=['parsed_date'])

    if period_type == 'weekly':
        df['period_key'] = df['parsed_date'].apply(lambda d: f"{d.isocalendar()[0]}_W{d.isocalendar()[1]:02d}")
        df['period_start'] = df['parsed_date'].apply(lambda d: (d - timedelta(days=d.weekday())).strftime('%Y-%m-%d'))
        df['period_end'] = df['parsed_date'].apply(lambda d: (d - timedelta(days=d.weekday()) + timedelta(days=6)).strftime('%Y-%m-%d'))
    else:
        df['period_key'] = df['parsed_date'].apply(lambda d: d.strftime('%Y_%m'))
        df['period_start'] = df['parsed_date'].apply(lambda d: d.replace(day=1).strftime('%Y-%m-%d'))
        df['period_end'] = df['parsed_date'].apply(lambda d: d.strftime('%Y-%m-%d'))

    reports = []
    period_keys = sorted(df['period_key'].unique())

    for i, pk in enumerate(period_keys):
        period_df = df[df['period_key'] == pk]
        prev_df = df[df['period_key'] == period_keys[i - 1]] if i > 0 else pd.DataFrame()

        period_start = period_df['period_start'].iloc[0]
        period_end = period_df['period_end'].iloc[-1]
        label = f"Week {pk.split('_W')[1]}" if period_type == 'weekly' else datetime.strptime(pk, '%Y_%m').strftime('%B %Y')

        # Sentiment by source
        source_sentiment = period_df.groupby('Source_Name')['Polarity'].mean().round(4).to_dict()
        prev_sentiment = prev_df.groupby('Source_Name')['Polarity'].mean().round(4).to_dict() if not prev_df.empty else {}

        # Top stories (highest absolute polarity = most impactful)
        top_stories = period_df.nlargest(5, 'Polarity')[
            ['Source_Name', 'Translated_Headline', 'Polarity']
        ].to_dict('records')

        # Day-by-day breakdown
        daily_breakdown = {}
        for date_val, day_group in period_df.groupby('Scrape_Date'):
            daily_breakdown[str(date_val)] = {
                'count': len(day_group),
                'avg_polarity': round(float(day_group['Polarity'].mean()), 4),
                'headlines': day_group[['Source_Name', 'Translated_Headline', 'Polarity']].head(10).to_dict('records')
            }

        # Period entities
        period_dates = period_df['Scrape_Date'].unique()
        period_entities_df = df_entities[df_entities['Scrape_Date'].isin(period_dates)] if 'Scrape_Date' in df_entities.columns else df_entities
        entity_counts = Counter()
        if not period_entities_df.empty and 'Entity' in period_entities_df.columns:
            entity_counts = Counter(period_entities_df['Entity'].tolist())

        # Sentiment distribution
        sentiments = period_df['Polarity'].apply(_sentiment_label).value_counts()
        total = len(period_df)

        report = {
            'period_key': pk,
            'period_type': period_type,
            'label': label,
            'period_start': period_start,
            'period_end': period_end,
            'summary': _generate_executive_summary(period_df, prev_df, label),
            'total_headlines': int(total),
            'avg_polarity': round(float(period_df['Polarity'].mean()), 4),
            'unique_entities': len(entity_counts),
            'sentiment_distribution': {
                'positive': int(sentiments.get('Positive', 0)),
                'neutral': int(sentiments.get('Neutral', 0)),
                'negative': int(sentiments.get('Negative', 0)),
            },
            'source_sentiment': source_sentiment,
            'prev_source_sentiment': prev_sentiment,
            'top_stories': top_stories,
            'top_entities': dict(entity_counts.most_common(10)),
            'daily_breakdown': daily_breakdown,
            'most_active_source': max(source_sentiment, key=lambda k: period_df[period_df['Source_Name'] == k].shape[0]) if source_sentiment else 'N/A',
            'most_positive_source': max(source_sentiment, key=source_sentiment.get) if source_sentiment else 'N/A',
        }

        # Key takeaways
        takeaways = []
        if prev_sentiment:
            prev_avg = sum(prev_sentiment.values()) / len(prev_sentiment) if prev_sentiment else 0
            curr_avg = sum(source_sentiment.values()) / len(source_sentiment) if source_sentiment else 0
            shift_pct = ((curr_avg - prev_avg) / abs(prev_avg) * 100) if prev_avg != 0 else 0
            direction = 'Up' if shift_pct > 0 else 'Down'
            takeaways.append(f"Sentiment {direction} {abs(shift_pct):.0f}%")

        if entity_counts:
            top_entity = entity_counts.most_common(1)[0][0]
            takeaways.append(f"{top_entity} Dominated")

        takeaways.append(f"{len(entity_counts)} Unique Entities")
        report['key_takeaways'] = takeaways

        reports.append(report)

    return reports


def _build_entity_data(df_entities):
    """Build cumulative entity frequency data."""
    if df_entities.empty:
        return {'entities': [], 'co_occurrence': []}

    # Top entities by frequency
    entity_freq = df_entities.groupby(['Entity', 'Label']).size().reset_index(name='count')
    entity_freq = entity_freq.sort_values('count', ascending=False).head(50)

    # Source breakdown per entity
    entity_sources = df_entities.groupby(['Entity', 'Source_Name']).size().reset_index(name='count')
    source_breakdown = defaultdict(dict)
    for _, row in entity_sources.iterrows():
        source_breakdown[row['Entity']][row['Source_Name']] = int(row['count'])

    entities = []
    for _, row in entity_freq.iterrows():
        entities.append({
            'name': row['Entity'],
            'label': row['Label'],
            'count': int(row['count']),
            'sources': source_breakdown.get(row['Entity'], {})
        })

    # Co-occurrence: entities appearing in headlines together
    co_occurrence = []
    if 'Scrape_Date' in df_entities.columns and 'Source_Name' in df_entities.columns:
        # Group entities by their headline (same source + date combination)
        grouped = df_entities.groupby(['Scrape_Date', 'Source_Name'])['Entity'].apply(list)
        pair_counts = Counter()
        for entity_list in grouped:
            unique_entities = list(set(entity_list))
            for i in range(len(unique_entities)):
                for j in range(i + 1, len(unique_entities)):
                    pair = tuple(sorted([unique_entities[i], unique_entities[j]]))
                    pair_counts[pair] += 1

        for (e1, e2), count in pair_counts.most_common(30):
            co_occurrence.append({'source': e1, 'target': e2, 'weight': count})

    return {'entities': entities, 'co_occurrence': co_occurrence}


def _build_geo_data(df_headlines):
    """Build geographic heatmap data."""
    if df_headlines.empty:
        return []

    geo_data = []
    for source_name, geo_info in SOURCE_GEO_MAP.items():
        source_df = df_headlines[df_headlines['Source_Name'] == source_name]
        if source_df.empty:
            continue

        # Last 7 days activity
        source_df_copy = source_df.copy()
        source_df_copy['parsed_date'] = source_df_copy['Scrape_Date'].apply(_parse_date)
        source_df_copy = source_df_copy.dropna(subset=['parsed_date'])

        daily_counts = source_df_copy.groupby('parsed_date').size().to_dict()
        last_7 = sorted(daily_counts.items(), key=lambda x: x[0])[-7:]
        activity_timeline = [{'date': d.strftime('%Y-%m-%d'), 'count': int(c)} for d, c in last_7]

        # Sentiment distribution
        sentiments = source_df['Polarity'].apply(_sentiment_label).value_counts()
        total = len(source_df)

        # Top entities for this source
        # (We'd need entity data linked to source, handled separately)

        geo_data.append({
            'source_name': source_name,
            'region': geo_info['region'],
            'lat': geo_info['lat'],
            'lng': geo_info['lng'],
            'lang_code': geo_info['lang_code'],
            'total_headlines': int(total),
            'avg_polarity': round(float(source_df['Polarity'].mean()), 4),
            'sentiment': {
                'positive': int(sentiments.get('Positive', 0)),
                'neutral': int(sentiments.get('Neutral', 0)),
                'negative': int(sentiments.get('Negative', 0)),
            },
            'activity_timeline': activity_timeline,
            'intensity': min(1.0, total / 100),  # Normalized 0-1 for heatmap
        })

    return geo_data


def _build_recent_headlines(df_headlines, days=7):
    """Get the most recent N days of headlines for the detail tables."""
    if df_headlines.empty:
        return []

    df = df_headlines.copy()
    df['parsed_date'] = df['Scrape_Date'].apply(_parse_date)
    df = df.dropna(subset=['parsed_date'])
    df = df.sort_values('parsed_date', ascending=False)

    cutoff = df['parsed_date'].max() - timedelta(days=days)
    recent = df[df['parsed_date'] >= cutoff]

    records = recent[['Source_Name', 'Original_Headline', 'Translated_Headline', 'Polarity', 'Scrape_Date']].to_dict('records')

    for r in records:
        r['sentiment'] = _sentiment_label(r['Polarity'])
        r['Polarity'] = round(float(r['Polarity']), 4)

    return records


def generate_dashboard_data():
    """Main entry point: reads all CSVs and writes dashboard_data.json."""
    project_root = os.getcwd()
    cleaned_dir = os.path.join(project_root, 'cleaned_csv_daily')
    output_dir = os.path.join(project_root, 'Data_Output')
    os.makedirs(output_dir, exist_ok=True)

    print("  [AGGREGATOR] Loading all processed headline CSVs...")
    df_headlines = _load_all_csvs(cleaned_dir, 'processed_data_final_')

    print("  [AGGREGATOR] Loading all processed entity CSVs...")
    df_entities = _load_all_csvs(cleaned_dir, 'processed_entities_final_')

    if df_headlines.empty:
        print("  [AGGREGATOR] WARNING: No headline data found. Writing empty JSON.")
        dashboard_data = {
            'generated_at': datetime.now().isoformat(),
            'daily_summary': [], 'weekly_reports': [], 'monthly_reports': [],
            'entities': {'entities': [], 'co_occurrence': []},
            'geo_data': [], 'recent_headlines': []
        }
    else:
        print(f"  [AGGREGATOR] Found {len(df_headlines)} total headlines, {len(df_entities)} entity records.")

        # Ensure Scrape_Date exists in entities (backward compat)
        if 'Scrape_Date' not in df_entities.columns and not df_entities.empty:
            df_entities['Scrape_Date'] = 'unknown'

        print("  [AGGREGATOR] Building daily summary...")
        daily_summary = _build_daily_summary(df_headlines)

        print("  [AGGREGATOR] Building weekly reports...")
        weekly_reports = _build_period_reports(df_headlines, df_entities, 'weekly')

        print("  [AGGREGATOR] Building monthly reports...")
        monthly_reports = _build_period_reports(df_headlines, df_entities, 'monthly')

        print("  [AGGREGATOR] Building entity data...")
        entity_data = _build_entity_data(df_entities)

        print("  [AGGREGATOR] Building geo heatmap data...")
        geo_data = _build_geo_data(df_headlines)

        print("  [AGGREGATOR] Building recent headlines...")
        recent_headlines = _build_recent_headlines(df_headlines)

        # Ensure Scrape_Date is string type
        df_headlines['Scrape_Date'] = df_headlines['Scrape_Date'].astype(str)
        if not df_entities.empty and 'Scrape_Date' in df_entities.columns:
            df_entities['Scrape_Date'] = df_entities['Scrape_Date'].astype(str)

        dashboard_data = {
            'generated_at': datetime.now().isoformat(),
            'total_headlines': int(len(df_headlines)),
            'total_entities': int(len(df_entities)),
            'date_range': {
                'start': str(sorted(df_headlines['Scrape_Date'].unique())[0]),
                'end': str(sorted(df_headlines['Scrape_Date'].unique())[-1]),
            },
            'daily_summary': daily_summary,
            'weekly_reports': weekly_reports,
            'monthly_reports': monthly_reports,
            'entities': entity_data,
            'geo_data': geo_data,
            'recent_headlines': recent_headlines,
        }

    output_path = os.path.join(output_dir, 'dashboard_data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, ensure_ascii=False, default=str)

    print(f"  [AGGREGATOR] Dashboard data written to {output_path}")
    print(f"  [AGGREGATOR] JSON size: {os.path.getsize(output_path) / 1024:.1f} KB")

    return dashboard_data


if __name__ == '__main__':
    generate_dashboard_data()
