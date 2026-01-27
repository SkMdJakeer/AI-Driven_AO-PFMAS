"""Monitors engine and altitude logs and writes alerts."""
from pathlib import Path
import json
from datetime import datetime

BASE = Path(__file__).resolve().parents[1]
LOGS = BASE / "logs"
CONFIG_PATH = BASE / "airline_config.json"
DATA_PATH = BASE / "data"

def load_config():
    return json.load(CONFIG_PATH.open()) if CONFIG_PATH.exists() else {}

def monitor_health(engine_logs, altitude_logs):
    cfg = load_config()
    alerts, health_alerts, critical_alerts = [], [], []
    cabin_logs = json.load((DATA_PATH / "cabin_pressure_logs.json").open()) if (DATA_PATH / "cabin_pressure_logs.json").exists() else []
    
    # Engine vibration (CRITICAL)
    for e in [x for x in engine_logs if x.get("vibration", 0) > cfg.get("engine_vibration_threshold", 5.0)]:
        alerts.append(f"{e.get('timestamp')} {e.get('flight_id')} HIGH_VIBRATION vibration={e.get('vibration')}")
        kv = f"timestamp: {e.get('timestamp')}, flight: {e.get('flight_id')}, alert: HIGH_VIBRATION, vibration: {e.get('vibration')}, threshold: 5.0"
        health_alerts.append(kv)
        critical_alerts.append(kv)
    
    # Rapid altitude (CRITICAL)
    for a in [x for x in altitude_logs if x.get("altitude", 0) < 1500 and x.get("turbulence", 0) > cfg.get("turbulence_moderate_level", 4.0)]:
        alerts.append(f"{a.get('timestamp')} {a.get('flight_id')} RAPID_ALTITUDE_FLUCT altitude={a.get('altitude')} turbulence={a.get('turbulence')}")
        kv = f"timestamp: {a.get('timestamp')}, flight: {a.get('flight_id')}, alert: RAPID_ALTITUDE_FLUCT, altitude: {a.get('altitude')}m, turbulence: {a.get('turbulence')}"
        health_alerts.append(kv)
        critical_alerts.append(kv)
    
    # Repeated turbulence (WARNING)
    turb = {}
    for a in altitude_logs:
        if a.get("turbulence", 0) > cfg.get("turbulence_moderate_level", 4.0):
            turb[a.get('flight_id')] = turb.get(a.get('flight_id'), 0) + 1
    for fid, cnt in [(f, c) for f, c in turb.items() if c >= 2]:
        ts = altitude_logs[-1].get('timestamp', datetime.now().isoformat())
        alerts.append(f"{ts} {fid} REPEATED_TURBULENCE count={cnt}")
        health_alerts.append(f"timestamp: {ts}, flight: {fid}, alert: REPEATED_TURBULENCE, occurrences: {cnt}")
    
    # Abnormal fuel (CRITICAL)
    for e in [x for x in engine_logs if x.get('engine_thrust', 100) < x.get('expected_thrust', 100) * 0.85 and x.get('fuel_burn', 0) > 2600]:
        alerts.append(f"{e.get('timestamp')} {e.get('flight_id')} ABNORMAL_FUEL_BURN fuel_burn={e.get('fuel_burn')} thrust_deviation={(e.get('expected_thrust', 100)-e.get('engine_thrust', 100)):.1f}%")
        kv = f"timestamp: {e.get('timestamp')}, flight: {e.get('flight_id')}, alert: ABNORMAL_FUEL_BURN, fuel_burn: {e.get('fuel_burn')}, thrust_deviation: {e.get('expected_thrust', 100)-e.get('engine_thrust', 100):.1f}%"
        health_alerts.append(kv)
        critical_alerts.append(kv)
    
    # High cabin temp (WARNING)
    for log in [x for x in cabin_logs if x.get("cabin_temperature", 0) > cfg.get("high_cabin_temp_c", 30)]:
        alerts.append(f"{log.get('timestamp')} {log.get('flight_id')} HIGH_CABIN_TEMP temperature={log.get('cabin_temperature')}")
        health_alerts.append(f"timestamp: {log.get('timestamp')}, flight: {log.get('flight_id')}, alert: HIGH_CABIN_TEMP, temperature: {log.get('cabin_temperature')}C, limit: 30C")
    
    # High cabin pressure (WARNING)
    for log in [x for x in cabin_logs if x.get("cabin_altitude", 0) > 8000 or x.get("pressure_rate_change", 0) > 500]:
        alerts.append(f"{log.get('timestamp')} {log.get('flight_id')} HIGH_CABIN_PRESSURE cabin_altitude={log.get('cabin_altitude', 0)} pressure_rate={log.get('pressure_rate_change', 0)}")
        health_alerts.append(f"timestamp: {log.get('timestamp')}, flight: {log.get('flight_id')}, alert: HIGH_CABIN_PRESSURE, cabin_altitude: {log.get('cabin_altitude', 0)}ft, pressure_rate: {log.get('pressure_rate_change', 0)}ft/min")
    
    # Write logs
    LOGS.mkdir(parents=True, exist_ok=True)
    if health_alerts:
        with (LOGS / "aircraft_health_alerts.log").open("w", encoding="utf-8") as f:
            f.write(f"AIRCRAFT HEALTH ALERTS - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("\n".join(health_alerts))
    if critical_alerts:
        with (LOGS / "critical_flight_alerts.log").open("w", encoding="utf-8") as f:
            f.write(f"CRITICAL FLIGHT ALERTS - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("\n".join(critical_alerts))
    
    return alerts