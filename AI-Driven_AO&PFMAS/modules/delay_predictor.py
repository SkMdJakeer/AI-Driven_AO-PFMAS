"""Rule-based delay predictor."""
from typing import List, Tuple, Dict
from pathlib import Path
import json

DATA_PATH = Path(__file__).resolve().parents[1] / "data"

def predict_delay_for_flight(flight_id: str, engine_logs: List[dict], weather_logs: List[dict],
                             altitude_logs: List[dict], config: Dict) -> Tuple[int, List[str]]:
    reasons, delay = [], 0
    cabin_file = DATA_PATH / "cabin_pressure_logs.json"
    cabin_logs = json.load(cabin_file.open()) if cabin_file.exists() else []
    
    # Weather delays
    for w in [x for x in weather_logs if x.get("flight_id") == flight_id]:
        if w.get("crosswind", 0) > config.get("crosswind_threshold_knots", 40):
            reasons.append("High crosswind")
            delay += 30
        if w.get("thunderstorm", False):
            reasons.append("Thunderstorm reported")
            delay += 60
        if w.get("visibility", 999999) < config.get("visibility_threshold_m", 1500):
            reasons.append("Low visibility")
            delay += 45
    
    # Engine delays
    for e in [x for x in engine_logs if x.get("flight_id") == flight_id]:
        if e.get("expected_thrust") and abs(e.get("engine_thrust", 0) - e.get("expected_thrust")) / e.get("expected_thrust") * 100 > config.get("engine_thrust_deviation_pct", 20):
            reasons.append("Engine thrust deviation")
            delay += 50
        if e.get("vibration", 0) > config.get("engine_vibration_threshold", 5.0):
            reasons.append("High engine vibration")
            delay += 40
    
    # Turbulence delays
    if any(a.get("turbulence", 0) >= config.get("turbulence_moderate_level", 4.0) for a in altitude_logs if a.get("flight_id") == flight_id):
        reasons.append("Turbulence advisory")
        delay += 15
    
    # Cabin pressure delays
    prev = None
    for c in [x for x in cabin_logs if x.get("flight_id") == flight_id]:
        if c.get("pressure_rate_change", 0) > config.get("cabin_pressure_drop_threshold", 500):
            reasons.append("Sudden cabin pressure drop")
            delay += 35
        if prev and abs(c.get("cabin_pressure", 0) - prev) > 300:
            reasons.append("Rapid cabin pressure change")
            delay += 25
        prev = c.get("cabin_pressure", 0)
    
    return int(delay), reasons