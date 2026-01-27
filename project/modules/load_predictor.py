"""Passenger load predictor using historical averages."""
from typing import List, Dict, Optional

def predict_load(flight_id: str, historical: Optional[List[Dict]] = None) -> Dict:
    """Return expected load plus simple over/under-utilization flags."""
    if not historical:
        return {"flight_id": flight_id, "expected": None, "overbooking_risk": False, "under_utilized": False}
    # Use historical booked/checked-in counts to find averages
    booked = [h.get("booked", 0) for h in historical]
    checked = [h.get("checked_in", 0) for h in historical]
    avg_booked = int(sum(booked) / len(booked)) if booked else 0
    avg_checked = int(sum(checked) / len(checked)) if checked else 0
    capacity = historical[-1].get("capacity")  # assume latest record has capacity
    overbooking = capacity is not None and avg_booked > capacity
    under = capacity is not None and avg_checked < (capacity * 0.5)
    return {"flight_id": flight_id, "expected": avg_booked, "overbooking_risk": overbooking, "under_utilized": under}
