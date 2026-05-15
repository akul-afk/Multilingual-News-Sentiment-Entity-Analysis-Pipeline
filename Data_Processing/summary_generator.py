import os
import json
import traceback
from datetime import datetime
from typing import List, Dict, Optional, Any

# Using the modern google-genai SDK
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def _generate_ai_narrative(prompt: str, api_key: str) -> str:
    """Calls the modern Gemini API using the google-genai SDK with model fallbacks.

    Args:
        prompt: The dynamic journalism-style prompt to send to Gemini.
        api_key: The Google AI Studio API key.

    Returns:
        The generated text from the strongest available Gemini model.

    Raises:
        RuntimeError: If all fallback models fail or the API is unavailable.
    """
    if not GENAI_AVAILABLE:
        raise ImportError("The 'google-genai' package is not installed.")

    client = genai.Client(api_key=api_key)
    
    import time
    
    # Validated models based on list_models() for this key
    GEMINI_MODELS = [
        "models/gemini-2.0-flash",
        "models/gemini-2.0-flash-lite",
        "models/gemini-1.5-flash",
        "models/gemini-pro-latest"
    ]

    for model_name in GEMINI_MODELS:
        retries = 2 # Max retries per model if 429
        delay = 5   # Initial backoff in seconds
        
        for attempt in range(retries + 1):
            try:
                print(f"    [GEMINI] Attempting generation with {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.6,
                        top_p=0.95,
                        max_output_tokens=800,
                    )
                )
                
                if response and response.text:
                    print(f"    [GEMINI] Success using {model_name}.")
                    return response.text.strip()
                else:
                    print(f"    [GEMINI] {model_name} returned empty text. Trying next model...")
                    break # Move to next model
            except Exception as e:
                error_msg = str(e).upper()
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if attempt < retries:
                        print(f"    [GEMINI] Quota limit (429) hit. Retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= 2
                        continue
                print(f"    [GEMINI] {model_name} failed: {e}")
                break # Move to next model
            
    raise RuntimeError("All Gemini API fallback models failed to generate content.")


def _generate_fallback_summary(report: Dict[str, Any], period_type: str) -> str:
    """Generates a rule-based journalistic summary when AI models are unavailable.
    
    Args:
        report: The aggregated report object.
        period_type: 'week' or 'month'.
        
    Returns:
        A formatted string containing a statistical narrative.
    """
    total = report.get('total_headlines', 0)
    start = report.get('period_start', 'N/A')
    end = report.get('period_end', 'N/A')
    
    # Extract entities
    entities = report.get('top_entities', {})
    top_entities_str = ", ".join(list(entities.keys())[:5]) if entities else "various global topics"
    
    # Sentiment context
    most_pos = report.get('most_positive_source', 'Global Feeds')
    most_neg = 'Unknown'
    source_sentiment = report.get('source_sentiment', {})
    if source_sentiment:
        most_neg = min(source_sentiment, key=source_sentiment.get)
    
    avg_polarity = report.get('avg_polarity', 0)
    tone = "cautiously optimistic" if avg_polarity > 0.05 else "somewhat somber" if avg_polarity < -0.05 else "relatively neutral"
    
    p1 = f"During the {period_type} of {start} to {end}, our monitoring pipeline processed a total of {total} headlines across the BBC's international multilingual services. The reporting cycle was characterized by a {tone} tone globally, with significant coverage of {top_entities_str}."
    
    p2 = f"Regional reporting showed notable variance in perspective. {most_pos} emerged as the most positive editorial voice this period, while {most_neg} provided the most critical or high-tension coverage. This contrast highlights the diverse geopolitical priorities captured by the BBC's local language bureaus."
    
    p3 = f"Key themes identified through entity extraction suggest a focus on international relations and regional stability. As we move into the next reporting cycle, the overall sentiment trajectory remains {tone}, reflecting the ongoing complexities of the global news landscape."
    
    return f"{p1}\n\n{p2}\n\n{p3}"


def create_summary_prompt(report: Dict[str, Any], period_type: str, master_entities_list: Optional[List[Dict[str, Any]]] = None) -> str:
    """Constructs a professional journalism-style prompt for the Gemini AI.

    Args:
        report: The aggregated report object from dashboard_data.json.
        period_type: Either 'week' or 'month'.
        master_entities_list: Full list of entity objects with labels (PERSON, ORG, etc.).

    Returns:
        A formatted string containing the structured prompt.
    """
    total = report.get('total_headlines', 0)
    
    # Extract entities by category using the master list from the aggregator
    top_entities_dict = report.get('top_entities', {})
    top_names = list(top_entities_dict.keys())
    
    people, orgs, locs = [], [], []
    if master_entities_list:
        label_map = {e.get('name'): e.get('label', '') for e in master_entities_list}
        for name in top_names:
            lbl = label_map.get(name, "")
            if lbl == "PERSON":
                people.append(name)
            elif lbl in ("ORG", "ORGANIZATION"):
                orgs.append(name)
            elif lbl in ("GPE", "LOC", "LOCATION"):
                locs.append(name)
    
    # Fallback categorization if meta-data is thin
    if not people and not orgs and not locs:
        people = top_names[:3]
        orgs = top_names[3:6]
        locs = top_names[6:10]
        
    top_persons = ", ".join(people) if people else "None notable"
    top_orgs = ", ".join(orgs) if orgs else "None notable"
    top_locations = ", ".join(locs) if locs else "None notable"
    
    # Format Top Stories
    top_stories = report.get('top_stories', [])
    stories_text = ""
    for s in top_stories:
        stories_text += f"- [{s.get('Source_Name')}]: {s.get('Translated_Headline')}\n"
        
    # Sentiment context extraction
    source_sentiment = report.get('source_sentiment', {})
    most_pos_src = report.get('most_positive_source', 'Unknown')
    most_neg_src = 'Unknown'
    if source_sentiment:
        most_neg_src = min(source_sentiment, key=source_sentiment.get)
        
    most_pos_score = source_sentiment.get(most_pos_src, 0)
    most_neg_score = source_sentiment.get(most_neg_src, 0)
    
    # Sentiment directionality
    takeaways = " ".join(report.get('key_takeaways', []))
    shift_dir = "Neutral"
    if "Up" in takeaways: shift_dir = "Improving/Positive global trend"
    if "Down" in takeaways: shift_dir = "Declining/Negative global trend"

    date_range = f"{report.get('period_start')} to {report.get('period_end')}"
    source_count = len(source_sentiment) if source_sentiment else 6
    source_list = ", ".join(source_sentiment.keys()) if source_sentiment else "BBC World Service multilingual feeds"

    prompt = f"""You are a senior international news correspondent writing a {period_type}ly briefing for a global audience.

Based on the following data extracted from {source_count} international BBC news services
({source_list}) covering the period {date_range}, write a 3-paragraph executive news summary.

TOP HEADLINES THIS PERIOD:
{stories_text}

KEY ENTITIES MENTIONED:
- People: {top_persons}
- Organizations: {top_orgs}
- Locations: {top_locations}

SENTIMENT CONTEXT:
- Most positive source: {most_pos_src} (avg polarity {most_pos_score})
- Most negative source: {most_neg_src} (avg polarity {most_neg_score})
- Overall sentiment direction: {shift_dir}

WRITING INSTRUCTIONS:
- Write in the style of a BBC World Service or Reuters briefing.
- Paragraph 1: Lead with the most significant story or theme of the {period_type}, naming real entities.
- Paragraph 2: Cover regional contrast — which parts of the world had the most notable news and why.
- Paragraph 3: Close with sentiment outlook — was this a tense or calm {period_type} globally, and what themes dominated.
- Do NOT mention polarity scores, numbers, or technical terms like "sentiment" or "NLP".
- Write for a general educated audience, not a data analyst.
- Maximum 180 words total.
- Do not use bullet points — flowing prose only.
- Direct address: Do not say "Based on the data". Start directly with the reporting."""
    return prompt


def generate_all_summaries() -> None:
    """Orchestrates AI summary generation for all reports in dashboard_data.json.

    Reads data, calls the Gemini API for each week/month, and updates the file on success.
    """
    if not GENAI_AVAILABLE:
        print("  [AI_SUMMARY] 'google-genai' package not installed. Skipping AI summaries.")
        return

    # Load API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        try:
            with open(".env", "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.strip().split("=", 1)[1]
                        break
        except Exception:
            pass

    if not api_key:
        print("  [AI_SUMMARY] GEMINI_API_KEY missing. Skipping AI summaries.")
        return

    project_root = os.getcwd()
    dashboard_json_path = os.path.join(project_root, "Data_Output", "dashboard_data.json")

    if not os.path.exists(dashboard_json_path):
        print(f"  [AI_SUMMARY] Dashboard JSON not found: {dashboard_json_path}")
        return

    print("  [AI_SUMMARY] Loading dashboard data for AI narrative enhancement...")
    try:
        with open(dashboard_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [AI_SUMMARY] Error reading JSON: {e}")
        return

    changed = False
    master_entities = data.get('entities', {}).get('entities', [])

    # Process weekly reports
    weekly = data.get("weekly_reports", [])
    for report in weekly:
        # Check if we should re-generate (always overwrite if testing, or skip if exists)
        if report.get("weekly_ai_summary"):
             # If we want to refresh, we could remove this check
             continue
            
        print(f"  [AI_SUMMARY] Generating Weekly AI Summary for {report.get('label')}...")
        prompt = create_summary_prompt(report, "week", master_entities)
        
        try:
            enhanced_text = _generate_ai_narrative(prompt, api_key)
            report["weekly_ai_summary"] = enhanced_text
            changed = True
        except Exception as e:
            print(f"  [AI_SUMMARY] AI generation failed: {e}. Using fallback...")
            report["weekly_ai_summary"] = _generate_fallback_summary(report, "week")
            changed = True

    # Process monthly reports
    monthly = data.get("monthly_reports", [])
    for report in monthly:
        if report.get("monthly_ai_summary"):
            continue
            
        print(f"  [AI_SUMMARY] Generating Monthly AI Summary for {report.get('label')}...")
        prompt = create_summary_prompt(report, "month", master_entities)
        
        try:
            enhanced_text = _generate_ai_narrative(prompt, api_key)
            report["monthly_ai_summary"] = enhanced_text
            changed = True
        except Exception as e:
            print(f"  [AI_SUMMARY] AI generation failed: {e}. Using fallback...")
            report["monthly_ai_summary"] = _generate_fallback_summary(report, "month")
            changed = True
    
    if changed:
        print("  [AI_SUMMARY] Saving enriched dashboard data...")
        try:
            with open(dashboard_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            print("  [AI_SUMMARY] Success.")
        except Exception as e:
            print(f"  [AI_SUMMARY] Error writing JSON: {e}")
    else:
        print("  [AI_SUMMARY] No new summaries generated.")


if __name__ == "__main__":
    generate_all_summaries()
