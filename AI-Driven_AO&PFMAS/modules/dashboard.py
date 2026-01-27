"""Console dashboard renderer - Compact version."""
from tabulate import tabulate

def render_dashboard(summary: dict):
    print("\n" + "="*60)
    print("AIRLINE OPERATIONS DASHBOARD")
    print("="*60 + "\n")
    
    # Summary Stats
    print("STATUS OVERVIEW:")
    print(f"  Total Flights: {summary.get('total_flights', 0)}")
    print(f"  Delayed Flights: {len(summary.get('predicted_delays', []))}")
    print(f"  Critical Alerts: {len(summary.get('critical_alerts', []))}")
    print(f"  Crew Shortages: {len(summary.get('crew_shortages', []))}\n")
    
    # Load Factor
    avg = summary.get('avg_load_factor')
    if avg:
        pct = avg * 100
        status = "VERY HIGH" if pct > 95 else "HIGH" if pct > 85 else "MODERATE" if pct > 70 else "LOW"
        print(f"PASSENGER LOAD: {pct:.1f}% ({status})\n")
    
    # Delays
    delays = summary.get('predicted_delays', [])
    if delays:
        print("FLIGHT DELAYS:")
        tbl = [[d.get('flight'), f"{d.get('delay', 0)} min", d.get('reasons', [])[:1]] for d in delays]
        print(tabulate(tbl, headers=["Flight", "Delay", "Reason"], tablefmt="simple"))
        print()
    
    # Alerts
    alerts = summary.get('critical_alerts', [])
    if alerts:
        print("CRITICAL ALERTS:")
        for i, a in enumerate(alerts, 1):
            print(f"  {i}. {a}")
        print()
    
    # Crew
    crew = summary.get('crew_shortages', [])
    if crew:
        print("CREW SHORTAGES:")
        for i, f in enumerate(crew, 1):
            print(f"  {i}. Flight {f}")
        print()
    
    # Weather
    weather = summary.get('weather_risks', [])
    if weather:
        print("WEATHER RISKS:")
        for i, w in enumerate(weather[:3], 1):
            print(f"  {i}. {str(w)[:80]}")
        print()
    
    # Diversions
    div = summary.get('route_diversions', [])
    if div:
        print("ROUTE DIVERSIONS:")
        for i, d in enumerate(div, 1):
            alt = ', '.join(d.get('suggested_alternates', []))
            print(f"  {i}. {d.get('flight_id')}: {d.get('issue')} -> {alt} (+{d.get('extra_time_min')}min)")
        print()
    
    print("="*60 + "\n")