import requests
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

url = "https://earthquake.usgs.gov/fdsnws/event/1/query"

def fetch_month_data(year, month):
    """Fetch earthquake data for a specific month with retry logic"""
    starttime = f"{year}-{month:02d}-01"
    if month == 12:
        endtime = f"{year + 1}-01-01"
    else:
        endtime = f"{year}-{month + 1:02d}-01"

    params = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
        "minmagnitude": 3,
        "limit": 20000
    }

    # Retry up to 3 times for failed requests
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                records = []
                for f in data.get("features", []):
                    p = f["properties"]
                    g = f["geometry"]["coordinates"]
                    records.append({
                        # "id": f.get("id"),
                        # "time": pd.to_datetime(p.get("time"), unit='ms'),
                        # "updated": pd.to_datetime(p.get("updated"), unit='ms'),
                        # "latitude": g[1] if g else None,
                        # "longitude": g[0] if g else None,
                        # "depth_km": g[2] if g else None,
                        # "mag": p.get("mag"),

                        # 1–3
                        "id": f.get("id"),
                        "time": pd.to_datetime(p.get("time"), unit="ms"),
                        "updated": pd.to_datetime(p.get("updated"), unit="ms"),

                        # 4–6
                        "latitude": g[1] if g else None,
                        "longitude": g[0] if g else None,
                        "depth_km": g[2] if g else None,

                        # 7–10
                        "mag": p.get("mag"),
                        "magType": p.get("magType"),
                        "place": p.get("place"),
                        "status": p.get("status"),

                        # 11–13
                        "tsunami": p.get("tsunami"),
                        "sig": p.get("sig"),
                        "net": p.get("net"),

                        # 14–17
                        "nst": p.get("nst"),
                        "dmin": p.get("dmin"),
                        "rms": p.get("rms"),
                        "gap": p.get("gap"),

                        # 18–20
                        "magError": p.get("magError"),
                        "depthError": p.get("depthError"),
                        "magNst": p.get("magNst"),

                        # 21–23
                        "locationSource": p.get("locationSource"),
                        "magSource": p.get("magSource"),
                        "types": p.get("types"),

                        # 24–26
                        "ids": p.get("ids"),
                        "sources": p.get("sources"),
                        "type": p.get("type")
                    })
                return records
        except Exception as e:
            if attempt < 2:
                time.sleep(1)  # Wait before retry
                continue
            print(f"Failed after retries for {starttime} to {endtime}: {e}")
            return []
    return []

# Generate all month-year combinations
start_year = datetime.now().year - 5
end_year = datetime.now().year
month_ranges = [(year, month) for year in range(start_year, end_year + 1) for month in range(1, 13)]

# Fetch data in parallel (10 concurrent requests)
all_records = []
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(fetch_month_data, year, month): (year, month) for year, month in month_ranges}
    completed = 0
    for future in as_completed(futures):
        records = future.result()
        all_records.extend(records)
        completed += 1
        if completed % 12 == 0:
            print(f"Progress: {completed}/{len(month_ranges)} months fetched")

# Build DataFrame from all records at once
df = pd.DataFrame(all_records)

# Save to CSV for dashboard
df.to_csv("data/earthquakes_cleaned.csv", index=False)
print("Data saved to data/earthquakes_cleaned.csv")

print("Rows:",df.shape[0])
print("Columns:",df.shape[1])
print(df.head())
           