"""Report generator for aviation operations."""
from pathlib import Path; import datetime
BASE = Path(__file__).resolve().parents[1]; OUTPUT = BASE / "output" / "reports"

def write_report(date_str: str, content: str) -> str:
    """Create the report folder and save a single text file, removing old reports."""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    # Clean up all previous report files (txt and pdf)
    for old_file in OUTPUT.glob("aviation_report_*.*"):
        old_file.unlink()  # delete old reports
    # Write the new report
    p = OUTPUT / f"aviation_report_{date_str}.txt"
    with p.open("w", encoding="utf-8") as f: f.write(content)  # UTF-8 for Windows safety
    return str(p)

def generate_report_text(summary: dict, details: list) -> str:
    """Compose a clean operations snapshot from aggregated data."""
    lines=[]; add=lines.append  # tiny helper keeps code short
    add("Aviation Operations Report"); add("="*60); add(f"Date: {datetime.date.today().isoformat()}"); add("")
    # At-a-glance numbers for quick triage
    delays=summary.get('predicted_delays',[]) or []; alerts=summary.get('critical_alerts',[]) or []
    crew=summary.get('crew_shortages',[]) or []; diversions=summary.get('route_diversions',[]) or []; avg=summary.get('avg_load_factor')
    add("SUMMARY:"); add("-"*60)
    add(f"Total Flights: {summary.get('total_flights',0)}; Delays: {len(delays)}; Alerts: {len(alerts)}")
    add(f"Crew Shortages: {len(crew)}; Diversions: {len(diversions)}")
    if avg is not None: add(f"Average Load Factor: {avg*100:.1f}%")
    # Predicted delays per flight — what to expect
    if delays:
        add(""); add("PREDICTED DELAYS:"); add("-"*60)
        for d in delays:
            m=d.get('delay') or d.get('delay_minutes') or 0; r=d.get('reasons',[])
            add(f"{d.get('flight','Unknown')}: {m} min | Reasons: {', '.join(r) if r else 'None'}")
    # Critical maintenance/operational alerts — act fast
    if alerts:
        add(""); add("CRITICAL ALERTS:"); add("-"*60)
        for i,a in enumerate(alerts,1): add(f"{i}. {a}")
    # Crew issues — flag flights needing attention
    if crew:
        add(""); add("CREW ASSIGNMENT:"); add("-"*60)
        for f in crew: add(f"{f}: CREW SHORTAGE - action needed")
    # Load factor guidance — quick business read
    add(""); add("PASSENGER LOAD:"); add("-"*60)
    if avg is not None:
        pct=avg*100; add(f"Average Load Factor: {pct:.1f}%")
        add("Status: "+("VERY HIGH" if pct>95 else "HIGH" if pct>85 else "MODERATE" if pct>70 else "LOW"))
    # Weather risks and diversions
    wr=summary.get('weather_risks',[]) or []
    if wr:
        add(""); add("WEATHER RISKS:"); add("-"*60)
        for i,r in enumerate(wr,1): add(f"{i}. {r}")
    if diversions:
        add(""); add("DIVERSION RECOMMENDATIONS:"); add("-"*60)
        for i,d in enumerate(diversions,1):
            alts=", ".join(d.get('suggested_alternates',[])) or "None"
            add(f"{i}. Flight {d.get('flight_id','Unknown')} | Issue: {d.get('issue','Unknown')} | Alternates: {alts} | +{d.get('extra_time_min',0)} min")
    # Footer — simple audit trail
    add(""); add("="*60); add("Report Generated: "+datetime.datetime.now().isoformat()); add("="*60)
    return "\n".join(lines)