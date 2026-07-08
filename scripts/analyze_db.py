import sqlite3

conn = sqlite3.connect("codecarbonops.db")
c = conn.cursor()

# --- Historical Carbon ---
print("=" * 60)
print("HISTORICAL_CARBON TABLE - DETAILED ANALYSIS")
print("=" * 60)

c.execute("SELECT COUNT(*) FROM historical_carbon")
print(f"Total rows: {c.fetchone()[0]}")

c.execute("SELECT DISTINCT region FROM historical_carbon")
regions = [r[0] for r in c.fetchall()]
print(f"Unique regions ({len(regions)}): {regions}")

c.execute("SELECT MIN(recorded_at), MAX(recorded_at) FROM historical_carbon")
d = c.fetchone()
print(f"Date range: {d[0]} to {d[1]}")

print("\nPer-region statistics:")
print(f"{'Region':<20} {'Count':>6} {'Min':>8} {'Avg':>8} {'Max':>8}")
print("-" * 55)
c.execute("""
    SELECT region, COUNT(*), MIN(carbon_intensity), 
           ROUND(AVG(carbon_intensity), 1), MAX(carbon_intensity)
    FROM historical_carbon 
    GROUP BY region 
    ORDER BY AVG(carbon_intensity)
""")
for r in c.fetchall():
    print(f"{r[0]:<20} {r[1]:>6} {r[2]:>8.1f} {r[3]:>8.1f} {r[4]:>8.1f}")

# Show sample data for one region (eu-north-1) for 24 hours
print("\nSample: eu-north-1 (Sweden) - First 24 hourly records:")
print(f"{'Hour':>4} {'Carbon':>8} {'Renewable':>10} {'Recorded At':<25}")
print("-" * 50)
c.execute("""
    SELECT hour_of_day, carbon_intensity, renewable_pct, recorded_at 
    FROM historical_carbon 
    WHERE region='eu-north-1' 
    ORDER BY recorded_at ASC 
    LIMIT 24
""")
for r in c.fetchall():
    print(f"{r[0]:>4} {r[1]:>8.1f} {r[2]:>10.2f} {r[3]:<25}")

# --- Energy Measurements ---
print("\n" + "=" * 60)
print("ENERGY_MEASUREMENTS TABLE - FULL DATA")
print("=" * 60)

c.execute("SELECT COUNT(*) FROM energy_measurements")
print(f"Total rows: {c.fetchone()[0]}")

c.execute("SELECT * FROM energy_measurements ORDER BY created_at ASC")
rows = c.fetchall()
cols = [desc[0] for desc in c.description]
print(f"Columns: {cols}")

if rows:
    print(f"\n{'ID':>3} {'RunID':>5} {'Est_kWh':>12} {'Meas_kWh':>12} {'CPU%':>6} {'Dur(s)':>7} {'Power(W)':>9} {'Error%':>8} {'Created':<25}")
    print("-" * 95)
    for r in rows:
        print(f"{r[0]:>3} {str(r[1]):>5} {r[2]:>12.8f} {r[3]:>12.8f} {str(r[4]):>6} {str(r[5]):>7} {str(r[6]):>9} {str(r[7]):>8} {str(r[8]):<25}")
else:
    print("*** TABLE IS EMPTY ***")

# --- Routing Feedback ---
print("\n" + "=" * 60)
print("ROUTING_FEEDBACK TABLE - FULL DATA")
print("=" * 60)

c.execute("SELECT COUNT(*) FROM routing_feedback")
print(f"Total rows: {c.fetchone()[0]}")

c.execute("SELECT * FROM routing_feedback ORDER BY created_at ASC")
rows = c.fetchall()
if rows:
    print(f"\n{'ID':>3} {'Region':<15} {'Urg':>3} {'PredC':>8} {'ActC':>8} {'PredL':>8} {'ActL':>8} {'Satisf':>7} {'Model':<15}")
    print("-" * 90)
    for r in rows:
        print(f"{r[0]:>3} {str(r[1]):<15} {str(r[2]):>3} {str(r[3]):>8} {str(r[4]):>8} {str(r[5]):>8} {str(r[6]):>8} {str(r[7]):>7} {str(r[8]):<15}")
else:
    print("*** TABLE IS EMPTY ***")

# --- Inference Runs ---
print("\n" + "=" * 60)
print("INFERENCE_RUNS TABLE - SUMMARY")
print("=" * 60)

c.execute("SELECT COUNT(*) FROM inference_runs")
total = c.fetchone()[0]
print(f"Total runs: {total}")

c.execute("SELECT model, COUNT(*), AVG(carbon_used_g), AVG(carbon_saved_g) FROM inference_runs GROUP BY model")
print("\nPer-model breakdown:")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]} runs, avg carbon used: {r[2]:.4f}g, avg saved: {r[3]:.4f}g")

c.execute("SELECT server_region, COUNT(*) FROM inference_runs GROUP BY server_region")
print("\nPer-region breakdown:")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]} runs")

conn.close()
