# Note: Exposing Clusters Array in reports JSON

As part of the reports screen UI updates, the topic index sidebar now expects a `clusters` array in each report type (daily, weekly, monthly) to render the actual cluster topic names instead of parsing them from text.

Please update `Data_Processing/data_aggregator.py` to populate and expose a `clusters` key inside each report dictionary in the generated JSON.

Each cluster object in the array should follow this structure:
```json
{
  "topic": "Topic Name",
  "count": 12
}
```

Currently, the front-end will log a warning: `clusters not in JSON — using section fallback` and automatically fall back to parsing section names from the briefing text.
