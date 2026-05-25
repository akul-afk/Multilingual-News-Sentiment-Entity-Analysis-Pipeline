import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from Data_Processing.summary_generator import generate_all_briefings

if __name__ == "__main__":
    print("Manually forcing regeneration of all summaries...")
    results = generate_all_briefings(force_regenerate=True)
    for period, result in results.items():
        print(f"Result for {period}: {result.get('model_used', 'unknown')}")
