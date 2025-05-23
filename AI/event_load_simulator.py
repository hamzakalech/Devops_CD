import requests
import random
import time
import threading
from datetime import datetime

BASE_URL = "https://hamzakalech.com/api/event"

# Sample event payload
def random_event():
    return {
        "title": f"Test Event {random.randint(1, 9999)}",
        "description": "Load test event",
        "location": "Online",
        "startDate": "2025-06-01",
        "endDate": "2025-06-02"
    }

def simulate_user():
    try:
        # 1. Fetch all events
        r1 = requests.get(f"{BASE_URL}/retrieve-all-events")
        if r1.status_code == 200 and r1.json():
            all_ids = [e["idEvent"] for e in r1.json()]
        else:
            all_ids = []

        # 2. Add new event
        new_event = random_event()
        r2 = requests.post(f"{BASE_URL}/addevent", json=new_event)

        # 3. Fetch event by ID
        if all_ids:
            event_id = random.choice(all_ids)
            r3 = requests.get(f"{BASE_URL}/retrieve-event/{event_id}")

        # 4. Delete a random event (50% chance)
        if all_ids and random.random() < 0.5:
            r4 = requests.delete(f"{BASE_URL}/remove-event/{random.choice(all_ids)}")

    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")

# 🔁 Launch multiple users
def run_load_simulation(concurrent_users=5, duration_seconds=120):
    print(f"🚀 Starting load with {concurrent_users} users for {duration_seconds} seconds...")
    start_time = time.time()
    while time.time() - start_time < duration_seconds:
        threads = []
        for _ in range(concurrent_users):
            t = threading.Thread(target=simulate_user)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        time.sleep(random.uniform(1, 3))  # Random pause between waves

    print("✅ Load simulation completed.")

# === Run the script ===
if __name__ == "__main__":
    run_load_simulation(concurrent_users=3, duration_seconds=180)
