"""
Data Aggregator Module
Consolidates daily CSVs into a single dashboard_data.json for the frontend.
Generates: daily_summary, weekly_reports, monthly_reports, entities, geo_data, recent_headlines.
"""

import os
import json
import glob
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

try:
    # Try relative import first
    import Data_Processing.summary_generator as summary_generator
    generate_all_briefings = summary_generator.generate_all_briefings
    SOURCE_REGION_MAP = summary_generator.SOURCE_REGION_MAP
except ImportError:
    try:
        # Try local import
        import summary_generator
        generate_all_briefings = summary_generator.generate_all_briefings
        SOURCE_REGION_MAP = summary_generator.SOURCE_REGION_MAP
    except ImportError:
        print("  [AGGREGATOR] CRITICAL: summary_generator module not found.")
        generate_all_briefings = None
        SOURCE_REGION_MAP = {}

import pandas as pd

logger = logging.getLogger(__name__)

# ── Project root resolved from this file's location ───────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── Global Geopolitical Entity Mapping (GPE/LOC) ───────────────────────────
GPE_LAT_LNG = {
    # Nations & Major Regions
    'US': {'lat': 37.09, 'lng': -95.71, 'region': 'North America'},
    'United States': {'lat': 37.09, 'lng': -95.71, 'region': 'North America'},
    'USA': {'lat': 37.09, 'lng': -95.71, 'region': 'North America'},
    'Ukraine': {'lat': 48.37, 'lng': 31.16, 'region': 'Eastern Europe'},
    'Russia': {'lat': 61.52, 'lng': 105.31, 'region': 'Northern Eurasia'},
    'China': {'lat': 35.86, 'lng': 104.19, 'region': 'East Asia'},
    'India': {'lat': 20.59, 'lng': 78.96, 'region': 'South Asia'},
    'Israel': {'lat': 31.04, 'lng': 34.85, 'region': 'Middle East'},
    'Palestine': {'lat': 31.95, 'lng': 35.23, 'region': 'Middle East'},
    'Gaza': {'lat': 31.35, 'lng': 34.30, 'region': 'Middle East'},
    'Iran': {'lat': 32.42, 'lng': 53.68, 'region': 'Middle East'},
    'UAE': {'lat': 23.42, 'lng': 53.84, 'region': 'Middle East'},
    'Saudi Arabia': {'lat': 23.88, 'lng': 45.07, 'region': 'Middle East'},
    'UK': {'lat': 55.37, 'lng': -3.43, 'region': 'Western Europe'},
    'Britain': {'lat': 55.37, 'lng': -3.43, 'region': 'Western Europe'},
    'France': {'lat': 46.22, 'lng': 2.21, 'region': 'Western Europe'},
    'Germany': {'lat': 51.16, 'lng': 10.45, 'region': 'Western Europe'},
    'Brazil': {'lat': -14.23, 'lng': -51.92, 'region': 'South America'},
    'Venezuela': {'lat': 6.42, 'lng': -66.58, 'region': 'South America'},
    'Tanzania': {'lat': -6.36, 'lng': 34.88, 'region': 'East Africa'},
    'Japan': {'lat': 36.20, 'lng': 138.25, 'region': 'East Asia'},
    'South Korea': {'lat': 35.90, 'lng': 127.76, 'region': 'East Asia'},
    'North Korea': {'lat': 40.33, 'lng': 127.51, 'region': 'East Asia'},
    'Australia': {'lat': -25.27, 'lng': 133.77, 'region': 'Oceania'},
    'Canada': {'lat': 56.13, 'lng': -106.34, 'region': 'North America'},
    'Mexico': {'lat': 23.63, 'lng': -102.55, 'region': 'North America'},
    'Spain': {'lat': 40.46, 'lng': -3.74, 'region': 'Southern Europe'},
    'Italy': {'lat': 41.87, 'lng': 12.56, 'region': 'Southern Europe'},
    'Turkey': {'lat': 38.96, 'lng': 35.24, 'region': 'Middle East'},
    'Egypt': {'lat': 26.82, 'lng': 30.80, 'region': 'North Africa'},
    'South Africa': {'lat': -30.55, 'lng': 22.93, 'region': 'Southern Africa'},
    'Nigeria': {'lat': 9.08, 'lng': 8.67, 'region': 'West Africa'},
    'Pakistan': {'lat': 30.37, 'lng': 69.34, 'region': 'South Asia'},
    'Bangladesh': {'lat': 23.68, 'lng': 90.35, 'region': 'South Asia'},
    'Afghanistan': {'lat': 33.93, 'lng': 67.70, 'region': 'South Asia'},
    'Syria': {'lat': 34.80, 'lng': 38.99, 'region': 'Middle East'},
    'Iraq': {'lat': 33.22, 'lng': 43.67, 'region': 'Middle East'},
    'Yemen': {'lat': 15.55, 'lng': 48.51, 'region': 'Middle East'},
    'Lebanon': {'lat': 33.85, 'lng': 35.86, 'region': 'Middle East'},
    'Taiwan': {'lat': 23.69, 'lng': 120.96, 'region': 'East Asia'},
    'Philippines': {'lat': 12.87, 'lng': 121.77, 'region': 'Southeast Asia'},
    'Vietnam': {'lat': 14.05, 'lng': 108.27, 'region': 'Southeast Asia'},
    'Thailand': {'lat': 15.87, 'lng': 100.99, 'region': 'Southeast Asia'},
    'Indonesia': {'lat': -0.78, 'lng': 113.92, 'region': 'Southeast Asia'},
    'Poland': {'lat': 51.91, 'lng': 19.14, 'region': 'Central Europe'},
    'Sweden': {'lat': 60.12, 'lng': 18.64, 'region': 'Northern Europe'},
    'Norway': {'lat': 60.47, 'lng': 8.46, 'region': 'Northern Europe'},
    'Finland': {'lat': 61.92, 'lng': 25.74, 'region': 'Northern Europe'},
    'Greece': {'lat': 39.07, 'lng': 21.82, 'region': 'Southern Europe'},
    'Argentina': {'lat': -38.41, 'lng': -63.61, 'region': 'South America'},
    'Colombia': {'lat': 4.57, 'lng': -74.29, 'region': 'South America'},
    'Chile': {'lat': -35.67, 'lng': -71.54, 'region': 'South America'},
    'Kenya': {'lat': -0.02, 'lng': 37.90, 'region': 'East Africa'},
    'Ethiopia': {'lat': 9.14, 'lng': 40.48, 'region': 'East Africa'},
    'Sudan': {'lat': 12.86, 'lng': 30.21, 'region': 'North Africa'},
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


def _build_daily_summary(df_headlines, df_entities=None):
    """Build per-date, per-source aggregated stats with sentiment breakdown and top entities."""
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

    # Add totals, sentiment breakdown, and top entities per day
    for date_key, data in result.items():
        day_df = df_headlines[df_headlines['Scrape_Date'] == date_key]
        total = len(day_df)
        data['total_headlines'] = total
        data['avg_polarity'] = round(float(day_df['Polarity'].mean()), 4)

        # Sentiment distribution
        sentiments = day_df['Polarity'].apply(_sentiment_label).value_counts()
        pos = int(sentiments.get('Positive', 0))
        neu = int(sentiments.get('Neutral', 0))
        neg = int(sentiments.get('Negative', 0))
        data['sentiment_distribution'] = {
            'positive': pos,
            'neutral': neu,
            'negative': neg,
            'positive_pct': round(pos / total * 100, 1) if total else 0,
            'neutral_pct': round(neu / total * 100, 1) if total else 0,
            'negative_pct': round(neg / total * 100, 1) if total else 0,
        }

        # Most positive / negative source
        src_sent = data['sources']
        if src_sent:
            data['most_positive_source'] = max(src_sent, key=lambda s: src_sent[s]['avg_polarity'])
            data['most_negative_source'] = min(src_sent, key=lambda s: src_sent[s]['avg_polarity'])

        # Top 5 entities for this day
        if df_entities is not None and not df_entities.empty and 'Scrape_Date' in df_entities.columns:
            day_ents = df_entities[df_entities['Scrape_Date'] == date_key]
            if not day_ents.empty and 'Entity' in day_ents.columns:
                ent_counts = Counter(day_ents['Entity'].tolist())
                data['top_entities'] = dict(ent_counts.most_common(5))
            else:
                data['top_entities'] = {}
        else:
            data['top_entities'] = {}

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


def _build_geo_data(df_headlines, df_entities):
    """Build geographic heatmap data based on GPE/LOC entities mentioned in headlines."""
    if df_entities.empty:
        return []

    # Filter for geographic entities
    geo_entities = df_entities[df_entities['Label'].isin(['GPE', 'LOC'])].copy()
    if geo_entities.empty:
        return []

    # Aggregate mentions per entity
    entity_counts = geo_entities.groupby('Entity').size().reset_index(name='total_mentions')
    
    # Merge with headlines to get sentiment per mention
    # Note: This is an approximation since multiple entities can exist in one headline
    # We group by source and date to get a sentiment proxy for those mentions
    source_date_sentiment = df_headlines.groupby(['Source_Name', 'Scrape_Date'])['Polarity'].mean().reset_index()
    geo_with_sentiment = pd.merge(geo_entities, source_date_sentiment, on=['Source_Name', 'Scrape_Date'], how='left')
    
    entity_sentiment = geo_with_sentiment.groupby('Entity')['Polarity'].mean().reset_index()
    
    geo_data = []
    for _, row in entity_counts.iterrows():
        name = row['Entity']
        mentions = int(row['total_mentions'])
        
        # Check if we have coordinates for this entity
        coords = GPE_LAT_LNG.get(name)
        
        # Simple fuzzy match for 'the United States' etc.
        if not coords:
            clean_name = name.replace('the ', '').strip()
            coords = GPE_LAT_LNG.get(clean_name)

        if not coords:
            continue

        avg_pol = entity_sentiment[entity_sentiment['Entity'] == name]['Polarity'].values[0]
        avg_pol = round(float(avg_pol), 4) if not pd.isna(avg_pol) else 0.0

        geo_data.append({
            'location_name': name,
            'region': coords['region'],
            'lat': coords['lat'],
            'lng': coords['lng'],
            'total_mentions': mentions,
            'avg_polarity': avg_pol,
            'intensity': min(1.0, mentions / 20),  # Normalized intensity
            'type': 'entity_mention'
        })

    return sorted(geo_data, key=lambda x: x['total_mentions'], reverse=True)


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


def generate_dashboard_data(force_summaries: bool = False) -> None:
    """Main entry point: reads all CSVs and writes dashboard_data.json."""
    cleaned_dir = str(PROJECT_ROOT / 'cleaned_csv_daily')
    output_dir = str(PROJECT_ROOT / 'Data_Output')
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
        daily_summary = _build_daily_summary(df_headlines, df_entities)

        print("  [AGGREGATOR] Building weekly reports...")
        weekly_reports = _build_period_reports(df_headlines, df_entities, 'weekly')

        print("  [AGGREGATOR] Building monthly reports...")
        monthly_reports = _build_period_reports(df_headlines, df_entities, 'monthly')

        print("  [AGGREGATOR] Building entity data...")
        entity_data = _build_entity_data(df_entities)

        print("  [AGGREGATOR] Building geo heatmap data...")
        geo_data = _build_geo_data(df_headlines, df_entities)

        print("  [AGGREGATOR] Building recent headlines...")
        recent_headlines = _build_recent_headlines(df_headlines)

        # Ensure Scrape_Date is string type
        df_headlines['Scrape_Date'] = df_headlines['Scrape_Date'].astype(str)
        if not df_entities.empty and 'Scrape_Date' in df_entities.columns:
            df_entities['Scrape_Date'] = df_entities['Scrape_Date'].astype(str)

        # Generate AI intelligence briefings
        print("  [AGGREGATOR] Generating intelligence briefings...")
        briefings = {}
        if generate_all_briefings:
            try:
                briefings = generate_all_briefings(force_regenerate=force_summaries)
            except Exception as e:
                print(f"  [AGGREGATOR] Briefing generation failed: {e}")

        # Build the reports structure with briefings + supporting entity data
        top_entity_list = entity_data.get('entities', [])[:10]
        top_entities_compact = [{'text': e['name'], 'label': e.get('label', ''), 'count': e['count']} for e in top_entity_list]

        reports = {}
        for period in ['daily', 'weekly', 'monthly']:
            b = briefings.get(period, {})
            period_label = ''
            if period == 'daily':
                period_label = b.get('period_start', datetime.now().strftime('%Y-%m-%d'))
            elif period == 'weekly':
                period_label = f"{b.get('period_start', '')} – {b.get('period_end', '')}"
            else:
                try:
                    period_label = datetime.strptime(b.get('period_start', ''), '%Y-%m-%d').strftime('%B %Y')
                except Exception:
                    period_label = b.get('period_start', '')

            reports[period] = {
                'date': b.get('period_start', ''),
                'period': period_label,
                'sources_count': b.get('sources_count', 0),
                'headlines_analyzed': b.get('headlines_analyzed', 0),
                'briefing': b.get('briefing', f'No {period} briefing available yet.'),
                'top_entities': top_entities_compact[:5] if period == 'daily' else top_entities_compact,
            }

        # Determine most active region for weekly
        if weekly_reports:
            latest_weekly = weekly_reports[-1]
            src_sent = latest_weekly.get('source_sentiment', {})
            if src_sent:
                most_active_src = max(src_sent, key=lambda k: abs(src_sent[k]))
                reports.get('weekly', {})['most_active_region'] = SOURCE_REGION_MAP.get(most_active_src, 'Global')

        dashboard_data = {
            'generated_at': datetime.now().isoformat(),
            'total_headlines': int(len(df_headlines)),
            'total_entities': int(len(df_entities)),
            'date_range': {
                'start': str(sorted(df_headlines['Scrape_Date'].unique())[0]),
                'end': str(sorted(df_headlines['Scrape_Date'].unique())[-1]),
            },
            'reports': reports,
            'daily_summary': daily_summary,
            'weekly_reports': weekly_reports,
            'monthly_reports': monthly_reports,
            'entities': entity_data,
            'geo_data': geo_data,
            'recent_headlines': recent_headlines,
            'pipeline_health': {
                'last_run_timestamp': datetime.now().isoformat(),
                'records_today': int(len(df_headlines[df_headlines['Scrape_Date'] == datetime.now().strftime('%Y_%m_%d')])),
                'avg_records_7d': int(len(df_headlines) / 7),
                'data_freshness_hours': 0
            }
        }

    output_path = os.path.join(output_dir, 'dashboard_data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, ensure_ascii=False, default=str)

    print(f"  [AGGREGATOR] Dashboard data written to {output_path}")
    print(f"  [AGGREGATOR] JSON size: {os.path.getsize(output_path) / 1024:.1f} KB")

    return dashboard_data


if __name__ == '__main__':
    generate_dashboard_data()
