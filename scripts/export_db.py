import sqlite3
import csv
import os

DB_PATH = "codecarbonops.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=== ALL TABLES ===")
for t in tables:
    print(f"  {t[0]}")
    cursor.execute(f"SELECT COUNT(*) FROM {t[0]}")
    count = cursor.fetchone()[0]
    print(f"    Rows: {count}")

print("\n=== HISTORICAL_CARBON TABLE ===")
cursor.execute("SELECT * FROM historical_carbon ORDER BY recorded_at ASC")
rows = cursor.fetchall()
cols = [desc[0] for desc in cursor.description]
print(f"Columns: {cols}")
print(f"Total rows: {len(rows)}")

# Export to CSV
with open("historical_carbon_export.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(cols)
    writer.writerows(rows)
print("Exported to historical_carbon_export.csv")

# Show first 5 and last 5 rows
print("\nFirst 5 rows:")
for row in rows[:5]:
    print(f"  {row}")
print("\nLast 5 rows:")
for row in rows[-5:]:
    print(f"  {row}")

# Unique regions
cursor.execute("SELECT DISTINCT region FROM historical_carbon")
regions = [r[0] for r in cursor.fetchall()]
print(f"\nUnique regions ({len(regions)}): {regions}")

# Date range
cursor.execute("SELECT MIN(recorded_at), MAX(recorded_at) FROM historical_carbon")
date_range = cursor.fetchone()
print(f"Date range: {date_range[0]} to {date_range[1]}")

print("\n=== ENERGY_MEASUREMENTS TABLE ===")
cursor.execute("SELECT * FROM energy_measurements ORDER BY created_at ASC")
rows2 = cursor.fetchall()
cols2 = [desc[0] for desc in cursor.description]
print(f"Columns: {cols2}")
print(f"Total rows: {len(rows2)}")

with open("energy_measurements_export.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(cols2)
    writer.writerows(rows2)
print("Exported to energy_measurements_export.csv")

print("\nAll rows:")
for row in rows2:
    print(f"  {row}")

print("\n=== ROUTING_FEEDBACK TABLE ===")
cursor.execute("SELECT * FROM routing_feedback ORDER BY created_at ASC")
rows3 = cursor.fetchall()
cols3 = [desc[0] for desc in cursor.description]
print(f"Columns: {cols3}")
print(f"Total rows: {len(rows3)}")

with open("routing_feedback_export.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(cols3)
    writer.writerows(rows3)
print("Exported to routing_feedback_export.csv")

print("\nAll rows:")
for row in rows3:
    print(f"  {row}")

print("\n=== INFERENCE_RUNS TABLE ===")
cursor.execute("SELECT * FROM inference_runs ORDER BY created_at ASC")
rows4 = cursor.fetchall()
cols4 = [desc[0] for desc in cursor.description]
print(f"Columns: {cols4}")
print(f"Total rows: {len(rows4)}")

with open("inference_runs_export.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(cols4)
    writer.writerows(rows4)
print("Exported to inference_runs_export.csv")

print("\nFirst 10 rows:")
for row in rows4[:10]:
    print(f"  {row}")

print("\n=== CI_RUNS TABLE ===")
cursor.execute("SELECT * FROM ci_runs ORDER BY created_at ASC")
rows5 = cursor.fetchall()
cols5 = [desc[0] for desc in cursor.description]
print(f"Columns: {cols5}")
print(f"Total rows: {len(rows5)}")

with open("ci_runs_export.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(cols5)
    writer.writerows(rows5)
print("Exported to ci_runs_export.csv")

print("\nAll rows:")
for row in rows5:
    print(f"  {row}")

conn.close()
print("\n=== DONE ===")
