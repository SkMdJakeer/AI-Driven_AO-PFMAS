"""Utilities to load data logs."""
from pathlib import Path
import json
BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "data"  # shared data folder

def load_json(filename: str):
    """Load a JSON file from data directory; return [] if missing."""
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with path.open() as f:
        return json.load(f)

def get_all_flights():
    """Collect distinct flight_ids across key log files."""
    flights = set()
    for fn in ["engine_logs.json", "weather_logs.json", "altitude_logs.json", "passenger_load.json"]:
        for e in load_json(fn):
            if "flight_id" in e:
                flights.add(e["flight_id"])
    return sorted(list(flights))
