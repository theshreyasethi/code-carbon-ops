import httpx
import time

base_url = "http://127.0.0.1:8000/api/v1/ci/predict"

print("Seeding database with 5 normal CI runs to establish a baseline for anomaly detection...")

for i in range(5):
    payload = {
        "repo": "my-org/core",
        "job_type": "build_and_test",
        "code_metrics": {"files_changed": 5, "lines_added": 50, "lines_removed": 10}
    }
    r = httpx.post(base_url, json=payload)
    if r.status_code == 200:
        print(f"Run {i+1} successful. Predicted Carbon: {r.json()['prediction']['carbon_g']}g")
    time.sleep(0.5)

print("\nSeeding complete! You can now run your Large and Anomalous curl commands again.")
