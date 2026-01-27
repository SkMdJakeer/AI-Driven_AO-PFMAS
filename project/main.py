"""
Main runner for the system.

Author: Sk Md Jakeer
Date: 2026-01-27

Description:
    Coordinates loading logs, running predictions, monitoring system
    health, rendering the dashboard, and writing summary reports for
    the AI-Driven AO&PFMAS project.

"""
from pathlib import Path
from datetime import date

BASE = Path(__file__).resolve().parents[0]
from modules.log_processor import load_json, get_all_flights
from modules.delay_predictor import predict_delay_for_flight
from modules.crew_optimizer import load_crew, assign_crew, suggest_alternate_crews
from modules.load_predictor import predict_load
from modules.health_monitor import monitor_health, load_config
from modules.dashboard import render_dashboard
from modules.reporter import write_report, generate_report_text

# Coordinates loading, prediction, dashboard, and report
def run():
    engine_logs = load_json("engine_logs.json")
    weather_logs = load_json("weather_logs.json")
    altitude_logs = load_json("altitude_logs.json")
    passenger_logs = load_json("passenger_load.json")
    crew_list = load_crew()
    cfg = load_config()
    flights = get_all_flights()
    predicted_delays = []
    critical_alerts = monitor_health(engine_logs, altitude_logs)
    crew_shortages = []
    load_factors = []
    popular_routes = {}
    weather_risks = []
    # Build diversions using config-provided alternates
    route_diversions = []
    for log in weather_logs:
        if log.get("thunderstorm") or log.get("visibility", 5000) < cfg.get("visibility_threshold_m", 1500):
            dest = log.get("destination", "DEL")
            alternates = cfg.get("alternate_airports", {}).get(dest, [])
            route_diversions.append({
                "flight_id": log.get("flight_id"),
                "issue": "Bad weather on route",
                "suggested_alternates": alternates,
                "extra_time_min": 30 + (10 * len(alternates))
            })
    details = []

    for f in flights:
        delay, reasons = predict_delay_for_flight(f, engine_logs, weather_logs, altitude_logs, cfg)
        if delay > 0:
            predicted_delays.append({"flight": f, "delay": delay, "reasons": reasons})
        assigned, shortage = assign_crew(f, crew_list, cfg)
        if shortage:
            crew_shortages.append(f)
            alt = suggest_alternate_crews(crew_list, needed=3)
            details.append(f"Crew shortage for {f}. Suggestions: {alt}")
        history = [p for p in passenger_logs if p.get("flight_id") == f]
        lp = predict_load(f, history)
        if lp.get("expected") is not None and history:
            lf = lp["expected"] / (history[-1].get("capacity") or 1)
            load_factors.append(lf)
        for w in weather_logs:
            if w.get("flight_id") == f and (w.get("crosswind",0) > cfg.get("crosswind_threshold_knots",40) or w.get("thunderstorm") or w.get("visibility",999999) < cfg.get("visibility_threshold_m",1500)):
                weather_risks.append(f"{f}: {w}")
        details.append(f"Flight {f} -> Delay: {delay} reasons: {reasons} load_pred: {lp}")
    
    summary = {
        "total_flights": len(flights),
        "predicted_delays": predicted_delays,
        "critical_alerts": critical_alerts,
        "crew_shortages": crew_shortages,
        "avg_load_factor": (sum(load_factors)/len(load_factors)) if load_factors else None,
        "popular_routes": popular_routes,
        "weather_risks": weather_risks,
        "route_diversions": route_diversions
    }
    render_dashboard(summary)
    report_text = generate_report_text(summary, details)
    fname = write_report(date.today().isoformat(), report_text)
    print(f"Report written to: {fname}")

if __name__ == '__main__':
    run()