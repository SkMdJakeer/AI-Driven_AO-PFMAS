"""Crew optimizer with double-booking prevention and rest rules."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple
import json

# Prevent double-booking
BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "data"
crew_assignments: Dict[str, str] = {}

def load_crew() -> List[Dict]:
    try:
        return json.load((DATA_DIR / "crew.json").open())
    except FileNotFoundError:
        return []

def _rest_ok(c: Dict, hours: int) -> bool:
    try:
        last_rest_end = datetime.fromisoformat(c.get("last_rest_end"))
        if last_rest_end.tzinfo is None:
            last_rest_end = last_rest_end.replace(tzinfo=timezone.utc)
        rested = datetime.now(timezone.utc) - last_rest_end
    except Exception:
        rested = timedelta.max
    return rested >= timedelta(hours=hours)

# Check double-booking and rest
def _available(c: Dict, flight: str, cfg: Dict) -> bool:
    cid = c.get("crew_id")
    if crew_assignments.get(cid) not in (None, flight):
        return False
    if c.get("assigned_flight") not in (None, flight):
        return False
    return _rest_ok(c, cfg.get("crew_rest_hours", 12))

# Assign, prevent double-booking
def assign_crew(flight: str, crew_list: List[Dict], cfg: Dict) -> Tuple[List[Dict], bool]:  
    req = {"pilot": cfg.get("required_pilots", 2), "cabin": cfg.get("required_cabin_crew", 1)}
    assigned: List[Dict] = []
    for role, needed in req.items():
        for c in [x for x in crew_list if x.get("role", "").lower() == role]:
            if len([a for a in assigned if a.get("role", "").lower() == role]) >= needed:
                break
            if _available(c, flight, cfg):
                cid = c.get("crew_id")
                crew_assignments[cid] = flight
                c["assigned_flight"] = flight
                assigned.append(c)
    shortage = any(len([a for a in assigned if a.get("role", "").lower() == r]) < n for r, n in req.items())
    return assigned, shortage

# On cancellation
def unassign_crew(flight: str, crew_list: List[Dict]) -> None:  
    for c in crew_list:
        if c.get("assigned_flight") == flight:
            crew_assignments.pop(c.get("crew_id"), None)
            c["assigned_flight"] = None

def get_crew_schedule(crew_id: str) -> Dict:
    return {"crew_id": crew_id, "assigned_flight": crew_assignments.get(crew_id), "is_available": crew_id not in crew_assignments}

# Daily reset
def clear_crew_assignments() -> None:  
    crew_assignments.clear()

def suggest_alternate_crews(crew_list: List[Dict], needed: int = 3) -> List[List[Dict]]:
    free = [c for c in crew_list if c.get("crew_id") not in crew_assignments]
    return [free[i:i + needed] for i in (0, needed) if len(free) >= i + needed]

# Audit double-booking
def validate_crew_assignment(flight: str, crew_list: List[Dict]) -> Dict:  
    assigned = [c for c in crew_list if c.get("assigned_flight") == flight]
    issues = []
    for c in assigned:
        cid = c.get("crew_id")
        if crew_assignments.get(cid) not in (None, flight):
            issues.append(f"Crew {cid} is double-booked: assigned to both {flight} and {crew_assignments[cid]}")
    return {
        "flight_id": flight,
        "assigned_crew": [{"crew_id": c.get("crew_id"), "name": c.get("name"), "role": c.get("role")} for c in assigned],
        "double_booking_found": bool(issues),
        "issues": issues,
    }