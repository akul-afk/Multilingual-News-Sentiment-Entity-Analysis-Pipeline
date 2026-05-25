import os
import sys
import json
import sqlite3
import random
import traceback
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple

# ── Gemini Fallback Configuration ───────────────────────────
GEMINI_MODELS = [
    "gemini-2.5-flash",        # Best quality, 20 RPD
    "gemini-2.5-flash-lite-preview-06-17",    # 20 RPD backup
    "gemini-3.1-flash-lite",   # 500 RPD — highest quota, lower quality
    "gemma-4-26b-it",          # 1500 RPD — emergency fallback
]

# ── Ensure project root is in sys.path ───────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# ── DB Configuration ──────────────────────────────────────────
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_DATABASE', 'NewsHeadlines'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'local_password'),
    'port': int(os.environ.get('DB_PORT', 3306))
}

SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'news_headlines.db')

# Map source names to approximate regions
SOURCE_REGION_MAP = {
    'BBC Hindi': 'South Asia',
    'BBC Japanese': 'East Asia',
    'BBC Portuguese': 'Latin America',
    'BBC Russian': 'Eastern Europe',
    'BBC Spanish': 'Latin America',
    'BBC Swahili': 'Africa',
    'Reuters': 'Global',
    'Al Jazeera': 'Middle East',
    'AP News': 'Global',
    'DW News': 'Europe',
    'France 24': 'Europe',
    'The Hindu': 'South Asia',
    'Dawn': 'South Asia',
    'Le Monde': 'Europe',
}


# ── Prompt Templates (PHASE 3 Overhaul) ───────────────────────

DAILY_PROMPT = """You are a foreign correspondent filing tonight's daily briefing.
The headlines below have been grouped by topic. Each group represents a real ongoing story.
Your job is to write what is ACTUALLY happening — synthesize each topic cluster into coherent reporting.

Rules:
- Write in past tense, declarative prose. No hedging.
- Do not say "headlines show" or "reports indicate" — report the facts directly.
- Do not invent details not present in the headlines.
- Do not include any meta-commentary about sources, languages, or data.
- Skip any topic cluster that is trivially local, entertainment, or sport unless it has clear international significance.
- Minimum 400 words, maximum 600 words.

Use this exact structure:

THE DAY'S LEAD
[The most significant topic cluster. 3-4 sentences. Name the people, the stakes, what happened today specifically.]

WHAT ELSE IS HAPPENING
[One paragraph per remaining major topic cluster, 2-3 sentences each. Cover at least 4 topics. Name real actors and real events.]

TO WATCH
[3 specific unresolved situations from today's clusters — what decision, deadline, or escalation is pending? One sentence each. Be specific, not vague.]

CLUSTERED HEADLINES:
{clustered_headlines}"""

WEEKLY_PROMPT = """You are a senior analyst writing a weekly situation report from clustered news data.
Each topic cluster below represents a story that generated sustained coverage this week.

Rules:
- Write about what actually happened, with specific details from the headlines.
- Do not reference the data, sources, or methodology.
- Distinguish between stories that resolved, escalated, or stalled this week.
- Minimum 550 words, maximum 750 words.

Structure:

THE WEEK'S DEFINING STORY
[The largest cluster. 4-5 sentences covering the arc of the story across the week — how did it start, develop, and where does it stand now?]

MAJOR DEVELOPMENTS
[One titled subsection per major cluster. Title = the topic name. 3-4 sentences of substantive reporting per subsection. Cover at least 5 topics.]

ONGOING SITUATIONS
[Clusters with fewer headlines but persistent presence — stories that didn't dominate but didn't resolve. 2 sentences each, 3-4 situations.]

WHAT TO WATCH
[3-4 specific things: named negotiations, scheduled votes, expiring ceasefires, pending verdicts, upcoming summits. One sentence each.]

CLUSTERED HEADLINES:
{clustered_headlines}"""

MONTHLY_PROMPT = """You are a chief analyst writing the monthly intelligence summary from a full month of clustered news data.
Each cluster represents a story or theme that generated sustained international coverage this month.

Rules:
- Be comprehensive and specific. This is a record of the month, not a highlight reel.
- Name the key figures, decisions, turning points, and outcomes where the headlines support it.
- Do not mention data sources, languages, or methodology.
- Minimum 750 words, maximum 1000 words.

Structure:

THE MONTH IN BRIEF
[5-6 sentences. What defined this month globally? What were the 2-3 dominant forces shaping international events?]

STORY OF THE MONTH
[The single largest cluster. A full narrative paragraph of 5-6 sentences covering the complete arc: origin, key developments, current status, significance.]

MAJOR STORIES
[One titled subsection per major cluster. Title = topic. 4-5 sentences each. Cover at least 6 topics. Include: what happened, who was involved, what changed, what it means going forward.]

REGIONAL OVERVIEW
[Group stories by region. 2-3 sentences per region. Cover at least 5 regions. What was the dominant story in each region this month?]

KEY FIGURES
[4-5 individuals or institutions that drove major news. One sentence on what they did and why it mattered.]

LOOKING AHEAD
[4-5 sentences. What is unresolved? What decisions, elections, negotiations, or flashpoints carry into next month?]

CLUSTERED HEADLINES:
{clustered_headlines}"""


# ══════════════════════════════════════════════════════════════
#  DATABASE LAYER
# ══════════════════════════════════════════════════════════════

def _get_mysql_connection():
    if not MYSQL_AVAILABLE: return None
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        return cnx
    except Exception: return None

def _get_sqlite_connection():
    return sqlite3.connect(SQLITE_PATH)

def _get_latest_data_date() -> str:
    query = "SELECT MAX(scrape_date) FROM headlines"
    cnx = _get_mysql_connection()
    if cnx:
        try:
            cursor = cnx.cursor(); cursor.execute(query); row = cursor.fetchone(); cursor.close(); cnx.close()
            if row and row[0]: return str(row[0])
        except Exception: pass
    try:
        conn = _get_sqlite_connection(); cursor = conn.cursor(); cursor.execute(query); row = cursor.fetchone(); cursor.close(); conn.close()
        if row and row[0]: return str(row[0])
    except Exception: pass
    return datetime.now().strftime('%Y-%m-%d')

def _fetch_headlines_from_db(period_start: str, period_end: str) -> List[Dict]:
    p_start_norm = period_start.replace('-', '_')
    p_end_norm = period_end.replace('-', '_')
    cols = "id, translated_headline, original_headline, source_name, polarity, scrape_date"
    query_mysql = f"SELECT {cols} FROM headlines WHERE scrape_date BETWEEN %s AND %s OR scrape_date BETWEEN %s AND %s ORDER BY scrape_date DESC"
    query_sqlite = f"SELECT {cols} FROM headlines WHERE scrape_date BETWEEN ? AND ? OR scrape_date BETWEEN ? AND ? ORDER BY scrape_date DESC"
    
    rows = []
    cnx = _get_mysql_connection()
    if cnx:
        try:
            cursor = cnx.cursor(dictionary=True); cursor.execute(query_mysql, (period_start, period_end, p_start_norm, p_end_norm))
            rows = cursor.fetchall(); cursor.close(); cnx.close()
        except Exception: 
            try: cnx.close()
            except Exception: pass
    if not rows:
        try:
            conn = _get_sqlite_connection(); cursor = conn.cursor(); cursor.execute(query_sqlite, (period_start, period_end, p_start_norm, p_end_norm))
            c_names = [d[0] for d in cursor.description]
            rows = [dict(zip(c_names, r)) for r in cursor.fetchall()]; cursor.close(); conn.close()
        except Exception: pass
    for r in rows: r['region'] = SOURCE_REGION_MAP.get(r['source_name'], 'Global')
    return rows

def _get_entities_for_headlines(headline_ids: List[int]) -> Dict[int, List[Dict]]:
    if not headline_ids: return {}
    ph = ",".join(["%s"] * len(headline_ids))
    ph_sq = ",".join(["?"] * len(headline_ids))
    query_mysql = f"SELECT headline_id, entity_text, entity_label FROM entities WHERE headline_id IN ({ph})"
    query_sqlite = f"SELECT headline_id, entity_text, entity_label FROM entities WHERE headline_id IN ({ph_sq})"
    entities_map = {}
    cnx = _get_mysql_connection()
    rows = []
    if cnx:
        try:
            cursor = cnx.cursor(dictionary=True); cursor.execute(query_mysql, tuple(headline_ids))
            rows = cursor.fetchall(); cursor.close(); cnx.close()
        except Exception: 
            try: cnx.close()
            except Exception: pass
    if not rows:
        try:
            conn = _get_sqlite_connection(); cursor = conn.cursor(); cursor.execute(query_sqlite, tuple(headline_ids))
            c_names = [d[0] for d in cursor.description]
            rows = [dict(zip(c_names, r)) for r in cursor.fetchall()]; cursor.close(); conn.close()
        except Exception: pass
    for r in rows:
        hid = r['headline_id']
        if hid not in entities_map: entities_map[hid] = []
        entities_map[hid].append({'text': r['entity_text'], 'label': r['entity_label']})
    return entities_map

# ── Processing & Clustering (PHASE 1 & 2) ─────────────────────

def _clean_and_deduplicate_headlines(headlines: List[Dict]) -> List[Dict]:
    if not headlines: return []
    filtered = []
    noise = ["Live:", "Watch:", "In pictures", "Quiz:", "Why does", "Video:", "In photos"]
    for h in headlines:
        text = str(h.get('translated_headline', '')).strip()
        if not text or len(text) < 25 or text.endswith('?') or any(n in text for n in noise): continue
        filtered.append(h)
    filtered.sort(key=lambda x: abs(float(x.get('polarity', 0))), reverse=True)
    unique = []
    def get_words(s): return set(re.findall(r'\w+', s.lower()))
    for h in filtered:
        h_words = get_words(h['translated_headline'])
        is_dup = False
        for u in unique:
            u_words = get_words(u['translated_headline'])
            if not h_words or not u_words: continue
            if len(h_words.intersection(u_words)) / max(len(h_words), len(u_words)) > 0.70:
                is_dup = True; break
        if not is_dup: unique.append(h)
    return unique

def cluster_headlines(headlines: List[Dict]) -> List[Dict]:
    if not headlines: return []
    h_ids = [h['id'] for h in headlines if 'id' in h]
    entities_map = _get_entities_for_headlines(h_ids)
    clusters = defaultdict(list)
    for h in headlines:
        hid = h.get('id')
        ents = [e['text'] for e in entities_map.get(hid, []) if e['label'] in ['PERSON', 'ORG', 'GPE']]
        if ents: clusters[ents[0]].append(h)
        else: clusters["Other"].append(h)
    final = []
    for topic, hdls in clusters.items():
        final.append({"topic": topic, "headlines": hdls, "count": len(hdls)})
    return sorted(final, key=lambda x: x['count'], reverse=True)

def _format_clustered_headlines(clusters: List[Dict]) -> str:
    output = []
    for c in clusters:
        output.append(f"TOPIC: {c['topic']} ({c['count']} headlines)")
        for h in c['headlines'][:15]: output.append(f"- {h['translated_headline']}")
        output.append("")
    return "\n".join(output)

# ── Caching Layer (PHASE 4) ───────────────────────────────────

def _get_cached_summary(period_type: str, period_start: str) -> Optional[str]:
    query_mysql = "SELECT content FROM summaries WHERE period_type = %s AND period_start = %s LIMIT 1"
    query_sqlite = "SELECT content FROM summaries WHERE period_type = ? AND period_start = ? LIMIT 1"
    cnx = _get_mysql_connection()
    if cnx:
        try:
            cursor = cnx.cursor(); cursor.execute(query_mysql, (period_type, period_start)); row = cursor.fetchone(); cursor.close(); cnx.close()
            if row: return row[0]
        except Exception: 
            try: cnx.close()
            except Exception: pass
    try:
        conn = _get_sqlite_connection(); cursor = conn.cursor(); cursor.execute(query_sqlite, (period_type, period_start)); row = cursor.fetchone(); cursor.close(); conn.close()
        if row: return row[0]
    except Exception: pass
    return None

def _store_cached_summary(period_type: str, period_start: str, period_end: str, content: str, model_used: str = "unknown"):
    q_mysql = "INSERT INTO summaries (period_type, period_start, period_end, content, model_used) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE content = VALUES(content), model_used = VALUES(model_used)"
    q_sqlite = "INSERT OR REPLACE INTO summaries (period_type, period_start, period_end, content, model_used) VALUES (?, ?, ?, ?, ?)"
    params = (period_type, period_start, period_end, content, model_used)
    cnx = _get_mysql_connection()
    if cnx:
        try:
            cursor = cnx.cursor(); cursor.execute(q_mysql, params); cnx.commit(); cursor.close(); cnx.close()
            return
        except Exception: 
            try: cnx.close()
            except Exception: pass
    try:
        conn = _get_sqlite_connection(); cursor = conn.cursor(); cursor.execute(q_sqlite, params); conn.commit(); cursor.close(); conn.close()
    except Exception: pass

def _delete_cached_summary(period_type: str, period_start: str):
    q_mysql = "DELETE FROM summaries WHERE period_type = %s AND period_start = %s"
    q_sqlite = "DELETE FROM summaries WHERE period_type = ? AND period_start = ?"
    cnx = _get_mysql_connection()
    if cnx:
        try:
            cursor = cnx.cursor(); cursor.execute(q_mysql, (period_type, period_start)); cnx.commit(); cursor.close(); cnx.close()
        except Exception: 
            try: cnx.close()
            except Exception: pass
    try:
        conn = _get_sqlite_connection(); cursor = conn.cursor(); cursor.execute(q_sqlite, (period_type, period_start)); conn.commit(); cursor.close(); conn.close()
    except Exception: pass

# ── Main Generator Logic ──────────────────────────────────────

def generate_briefing(period_type: str, api_key: str, anchor_date: Optional[str] = None, force_regenerate: bool = False) -> Dict[str, Any]:
    if not anchor_date: anchor_date = _get_latest_data_date()
    try: anchor_dt = datetime.strptime(anchor_date.replace('_', '-'), '%Y-%m-%d')
    except Exception: anchor_dt = datetime.now()

    if period_type == 'daily':
        p_start = p_end = anchor_dt.strftime('%Y-%m-%d')
        prompt_template = DAILY_PROMPT; max_tokens = 2048
    elif period_type == 'weekly':
        monday = anchor_dt - timedelta(days=anchor_dt.weekday())
        p_start = monday.strftime('%Y-%m-%d'); p_end = anchor_dt.strftime('%Y-%m-%d')
        prompt_template = WEEKLY_PROMPT; max_tokens = 3072
    else:
        p_start = anchor_dt.replace(day=1).strftime('%Y-%m-%d'); p_end = anchor_dt.strftime('%Y-%m-%d')
        prompt_template = MONTHLY_PROMPT; max_tokens = 4096

    print(f"  [BRIEFING] Period: {period_type} | Key Start: {p_start}")
    
    if force_regenerate: _delete_cached_summary(period_type, p_start)
    else:
        cached = _get_cached_summary(period_type, p_start)
        if cached: return {'briefing': cached, 'cached': True}

    headlines = _fetch_headlines_from_db(p_start, p_end)
    if period_type == 'daily' and len(headlines) < 30:
        print(f"  [BRIEFING] Pulling supplemental context for daily...")
        prev_start = (anchor_dt - timedelta(days=2)).strftime('%Y-%m-%d')
        prev_end = (anchor_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        supp = _fetch_headlines_from_db(prev_start, prev_end)
        for s in supp: s['translated_headline'] = f"[PRIOR DAY] {s['translated_headline']}"
        headlines.extend(supp)

    cleaned = _clean_and_deduplicate_headlines(headlines)
    print(f"  [BRIEFING] Final count for Gemini: {len(cleaned)}")
    
    clusters = cluster_headlines(cleaned)
    clustered_text = _format_clustered_headlines(clusters)
    prompt = prompt_template.format(clustered_headlines=clustered_text)

    content, model_used = call_gemini_with_fallback(prompt, period_type, api_key, max_tokens)
    
    if not content:
        print(f"  [BRIEFING] All Gemini models failed, using rule-based fallback")
        content = rule_based_briefing(clusters, period_type, p_start)
        model_used = "fallback"

    _store_cached_summary(period_type, p_start, p_end, content, model_used)
    return {'briefing': content, 'headlines_analyzed': len(cleaned), 'model_used': model_used}

def call_gemini_with_fallback(prompt: str, context_label: str, api_key: str, max_tokens: int) -> tuple[str, str]:
    """
    Try each model in order. Return (response_text, model_used).
    Implements exponential backoff per model before moving to next.
    """
    if not GENAI_AVAILABLE:
        return None, "fallback"

    client = genai.Client(api_key=api_key)

    for model in GEMINI_MODELS:
        retries = 3
        wait_times = [10, 30, 60]
        for attempt in range(retries):
            try:
                print(f"[GEMINI] Trying {model} for {context_label} (attempt {attempt+1})")
                # Thinking models (2.5-*) use thinking tokens that eat into
                # max_output_tokens. Set a dedicated thinking budget so the
                # visible output isn't truncated.
                is_thinking_model = '2.5' in model
                config_kwargs = {
                    'temperature': 0.3,
                    'max_output_tokens': max_tokens,
                }
                if is_thinking_model:
                    config_kwargs['thinking_config'] = types.ThinkingConfig(
                        thinking_budget=1024
                    )
                response = client.models.generate_content(
                    model=model, 
                    contents=prompt,
                    config=types.GenerateContentConfig(**config_kwargs)
                )
                text = response.text.strip()
                if text:
                    print(f"[GEMINI] Success with {model}")
                    return text, model
            except Exception as e:
                error_str = str(e)
                if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                    if attempt < retries - 1:
                        wait = wait_times[attempt]
                        print(f"[GEMINI] {model} rate limited, waiting {wait}s...")
                        time.sleep(wait)
                    else:
                        print(f"[GEMINI] {model} exhausted after {retries} attempts, trying next model")
                        break
                else:
                    print(f"[GEMINI] {model} failed with non-quota error: {e}")
                    break  # non-quota error, skip to next model immediately

    print("[GEMINI] All models exhausted, using rule-based fallback")
    return None, "fallback"

def rule_based_briefing(clusters: list, period_type: str, period_label: str) -> str:
    """
    Synthesize a report from clusters using rule-based templates.
    Used when AI models are exhausted or unavailable.
    """
    top = [c for c in sorted(clusters, key=lambda x: x['count'], reverse=True)
           if c['topic'] != 'Other']

    def format_headlines(headlines, n=3):
        # Extract string from headline dict if needed
        texts = []
        for h in headlines:
            if isinstance(h, dict):
                text = h.get('translated_headline', '')
            else:
                text = str(h)
            text = text.strip().rstrip('.')
            if len(text) > 25:
                texts.append(text)
        return '. '.join(texts[:n])

    sections = []

    if period_type == 'daily':
        lead = top[0] if top else None
        if lead:
            sections.append(f"THE DAY'S LEAD\n{format_headlines(lead['headlines'], 3)}.")
        sections.append("WHAT ELSE IS HAPPENING")
        for c in top[1:6]:
            sections.append(f"{c['topic'].upper()}\n{format_headlines(c['headlines'], 2)}.")
        sections.append("TO WATCH")
        for c in top[6:9]:
            if c['headlines']:
                h_text = c['headlines'][0].get('translated_headline', '') if isinstance(c['headlines'][0], dict) else str(c['headlines'][0])
                sections.append(f"- {c['topic']}: {h_text[:120]}")

    elif period_type == 'weekly':
        lead = top[0] if top else None
        if lead:
            sections.append(f"THE WEEK'S DEFINING STORY\n{format_headlines(lead['headlines'], 4)}.")
        sections.append("MAJOR DEVELOPMENTS")
        for c in top[1:7]:
            sections.append(f"{c['topic'].upper()}\n{format_headlines(c['headlines'], 3)}.")
        sections.append("ONGOING SITUATIONS")
        for c in top[7:11]:
            if c['headlines']:
                h_text = c['headlines'][0].get('translated_headline', '') if isinstance(c['headlines'][0], dict) else str(c['headlines'][0])
                sections.append(f"- {c['topic']}: {h_text[:120]}")
        sections.append("WHAT TO WATCH NEXT WEEK")
        for c in top[11:14]:
            if c['headlines']:
                h_text = c['headlines'][0].get('translated_headline', '') if isinstance(c['headlines'][0], dict) else str(c['headlines'][0])
                sections.append(f"- {c['topic']}: {h_text[:120]}")

    elif period_type == 'monthly':
        lead = top[0] if top else None
        if lead:
            sections.append(f"THE MONTH IN BRIEF\n{format_headlines(lead['headlines'], 4)}.")
        sections.append("MAJOR STORIES")
        for c in top[1:8]:
            sections.append(f"{c['topic'].upper()}\n{format_headlines(c['headlines'], 3)}.")
        sections.append("REGIONAL OVERVIEW")
        for c in top[8:13]:
            if c['headlines']:
                sections.append(f"- {c['topic']}: {format_headlines(c['headlines'], 2)}")
        sections.append("LOOKING AHEAD")
        for c in top[13:16]:
            if c['headlines']:
                h_text = c['headlines'][0].get('translated_headline', '') if isinstance(c['headlines'][0], dict) else str(c['headlines'][0])
                sections.append(f"- {c['topic']}: {h_text[:120]}")

    return '\n\n'.join(sections)

def generate_all_briefings(force_regenerate: bool = False) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        try:
            with open(os.path.join(PROJECT_ROOT, '.env'), "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="): api_key = line.split("=", 1)[1].strip(); break
        except Exception: pass
    if not api_key: return {}
    
    results = {}
    anchor = _get_latest_data_date()
    periods = ['daily', 'weekly', 'monthly']
    
    now = datetime.now()
    
    for i, p in enumerate(periods):
        # Phase 3: Smart force logic
        should_force = force_regenerate
        if p == 'daily':
            should_force = True  # Always force daily for fresh context
        elif p == 'weekly' and now.weekday() == 0:
            should_force = True  # Force weekly on Mondays
        elif p == 'monthly' and now.day == 1:
            should_force = True  # Force monthly on the 1st
            
        try: 
            results[p] = generate_briefing(p, api_key, anchor, force_regenerate=should_force)
            if i < len(periods) - 1:
                print(f"[BRIEFING] Waiting 5s before next report to avoid quota issues...")
                time.sleep(5)
        except Exception as e: 
            results[p] = {'briefing': f"Error: {str(e)}"}
    return results

if __name__ == "__main__":
    generate_all_briefings()
