
import requests
import pandas as pd
import datetime
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
PROMETHEUS_URL = "https://prometheus.hamzakalech.com"
NAMESPACE = "hamzadevops"
STEP = 60  # seconds
DAYS = 2   # how many days of data

# Time range
end_time = datetime.datetime.utcnow()
start_time = end_time - datetime.timedelta(days=DAYS)

start_unix = int(start_time.timestamp())
end_unix = int(end_time.timestamp())

# PromQL queries
cpu_query = f"rate(container_cpu_usage_seconds_total{{container!='',namespace='{NAMESPACE}'}}[2m])"
pod_query = f"count(kube_pod_status_phase{{namespace='{NAMESPACE}',phase='Running'}})"
node_query = "count(kube_node_status_condition{condition='Ready',status='true'})"

def query_prometheus(query, start, end, step):
    url = f"{PROMETHEUS_URL}/prometheus/api/v1/query_range"
    params = {
        "query": query,
        "start": start,
        "end": end,
        "step": step
    }
    response = requests.get(url, params=params, verify=True)
    print(f"🔍 Query: {query[:50]}... → Status {response.status_code}")
    if not response.ok:
        print("❌ Error:", response.text[:300])
    return response.json()

print("📡 Fetching CPU usage...")
cpu_data = query_prometheus(cpu_query, start_unix, end_unix, STEP)
print("📡 Fetching pod count...")
pod_data = query_prometheus(pod_query, start_unix, end_unix, STEP)
print("📡 Fetching node count...")
node_data = query_prometheus(node_query, start_unix, end_unix, STEP)

# Convert to DataFrames
def extract_single_series(prom_data, label):
    values = prom_data.get("data", {}).get("result", [])
    if not values:
        return pd.DataFrame()
    series = values[0]["values"]
    return pd.DataFrame([(datetime.datetime.fromtimestamp(float(ts)), float(val)) for ts, val in series], columns=["timestamp", label])

cpu_rows = []
for pod in cpu_data.get("data", {}).get("result", []):
    pod_name = pod["metric"].get("pod", "unknown")
    for point in pod["values"]:
        ts = datetime.datetime.fromtimestamp(float(point[0]))
        value = float(point[1])
        cpu_rows.append({"timestamp": ts, "pod": pod_name, "cpu_usage": value})

df_cpu = pd.DataFrame(cpu_rows)

df_pod = extract_single_series(pod_data, "pod_count")
df_node = extract_single_series(node_data, "node_count")

# Merge DataFrames
df_cpu = df_cpu.sort_values("timestamp")
df_full = df_cpu.merge(df_pod, on="timestamp", how="left").merge(df_node, on="timestamp", how="left")

# Save to CSV
df_full.to_csv("prometheus_metrics.csv", index=False)
print("✅ Saved enriched data to prometheus_metrics.csv")
