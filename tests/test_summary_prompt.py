import pytest
from Data_Processing.summary_generator import create_summary_prompt

def test_create_summary_prompt():
    report = {
        'total_headlines': 150,
        'period_start': '2025-10-01',
        'period_end': '2025-10-07',
        'top_entities': {'Trump': 50, 'UN': 30, 'London': 20},
        'top_stories': [
            {'Source_Name': 'BBC Spanish', 'Translated_Headline': 'El clima está cambiando', 'Polarity': -0.1}
        ],
        'source_sentiment': {'BBC Spanish': -0.05, 'BBC Hindi': 0.1},
        'most_positive_source': 'BBC Hindi',
        'key_takeaways': ['Sentiment went Up this week.']
    }
    
    master_entities = [
        {'name': 'Trump', 'label': 'PERSON'},
        {'name': 'UN', 'label': 'ORG'},
        {'name': 'London', 'label': 'LOC'}
    ]
    
    prompt = create_summary_prompt(report, "week", master_entities)
    
    assert "week" in prompt, "Should mention the period type 'week'"
    assert "Trump" in prompt, "Should format top PERSON"
    assert "UN" in prompt, "Should format top ORG"
    assert "London" in prompt, "Should format top LOC"
    assert "BBC Hindi" in prompt, "Should mention most positive source"
    assert "BBC Spanish" in prompt, "Should mention most negative source"
