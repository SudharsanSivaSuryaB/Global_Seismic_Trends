import requests
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed  # It is used for the improving the speed of retrieve data
import time
import re  # For using the regex this import is used 
import numpy as np

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
                     

                       
                        "id": f.get("id"),
                        "time": pd.to_datetime(p.get("time"), unit="ms"),
                        "updated": pd.to_datetime(p.get("updated"), unit="ms"),

                      
                        "latitude": g[1] if g else None,
                        "longitude": g[0] if g else None,
                        "depth_km": g[2] if g else None,

                        
                        "mag": p.get("mag"),
                        "magType": p.get("magType"),
                        "place": p.get("place"),
                        "status": p.get("status"),

                        "tsunami": p.get("tsunami"),
                        "sig": p.get("sig"),
                        "net": p.get("net"),

                        "nst": p.get("nst"),
                        "dmin": p.get("dmin"),
                        "rms": p.get("rms"),
                        "gap": p.get("gap"),

                        "magError": p.get("magError"),
                        "depthError": p.get("depthError"),
                        "magNst": p.get("magNst"),

                        "locationSource": p.get("locationSource"),
                        "magSource": p.get("magSource"),
                        "types": p.get("types"),

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

print("Initial rows:", df.shape[0])

# Text field cleaning

def extract_country(place):
    """Extract likely country or final token from place string."""
    if not place or not isinstance(place, str):
        return None
    # Common USGS format: "XX km SE of Place, Country"
    m = re.search(r",\s*([^,]+)$", place)  # It is got from the use of AI Tools 
    if m:
        candidate = m.group(1).strip()
        # remove leading prepositions
        candidate = re.sub(r"^(of|near|offshore of)\s+", "", candidate, flags=re.I)
        candidate = re.sub(r"\bkm\b", "", candidate, flags=re.I).strip()
        if re.search(r"\d", candidate) or len(candidate) < 2:
            return None
        return candidate
    # fallback: last word group
    m2 = re.search(r"([A-Za-z\s]+)$", place)
    if m2:
        cand = m2.group(1).strip()
        return cand if len(cand) > 1 else None
    return None

# Normalize string fields
string_fields = ['magType', 'status', 'type', 'net', 'sources', 'types', 'place']
for col in string_fields:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df.loc[df[col].str.lower().isin(['', 'nan', 'none', 'null']), col] = np.nan
        # normalize to lowercase except `place` (keep place casing)
        if col != 'place':
            df[col] = df[col].str.lower()

# Normalize alert field if exists
if 'alert' in df.columns:
    df['alert'] = df['alert'].astype(str).str.strip().str.lower()
    df.loc[df['alert'].str.lower().isin(['', 'nan', 'none', 'null']), 'alert'] = np.nan

# Extract country from place
if 'place' in df.columns:
    df['country'] = df['place'].apply(extract_country)

# Numeric field cleaning
numeric_fields = ['mag', 'depth_km', 'nst', 'dmin', 'rms', 'gap', 'magError', 'depthError', 'magNst', 'sig']
for col in numeric_fields:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Fill numeric NaNs with median if available, otherwise 0
for col in numeric_fields:
    if col in df.columns:
        med = df[col].median(skipna=True)
        fill_value = 0 if np.isnan(med) else med
        df[col] = df[col].fillna(fill_value)

# Basic validity cleaning
# Drop duplicate ids
if 'id' in df.columns:
    before = df.shape[0]
    df = df.drop_duplicates(subset=['id'])
    print(f"Dropped {before - df.shape[0]} duplicate rows by id")

# Ensure latitude/longitude numeric
for col in ['latitude', 'longitude']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Remove rows missing critical location/magnitude
before = df.shape[0]
required = [c for c in ['latitude', 'longitude', 'mag'] if c in df.columns]
if required:
    df = df.dropna(subset=required)
    print(f"Dropped {before - df.shape[0]} rows missing required fields: {required}")

# Remove negative depths
if 'depth_km' in df.columns:
    before = df.shape[0]
    df = df[df['depth_km'] >= 0]
    print(f"Dropped {before - df.shape[0]} rows with negative depth")

# Derive year/month
if 'time' in df.columns:
    df['year'] = df['time'].dt.year
    df['month'] = df['time'].dt.month
    # Add day and weekday
    df['day'] = df['time'].dt.day
    df['day_of_week'] = df['time'].dt.day_name()

# Derived flags
# Shallow/intermediate/deep classification
if 'depth_km' in df.columns:
    def depth_category(d):
        if pd.isna(d):
            return None
        if d < 70:
            return 'shallow'
        if d <= 300:
            return 'intermediate'
        return 'deep'
    df['depth_category'] = df['depth_km'].apply(depth_category)

# Strong and destructive flags based on magnitude
# default thresholds: strong >= 6.0, destructive >= 7.0
if 'mag' in df.columns:
    df['is_strong'] = df['mag'] >= 6.0
    df['is_destructive'] = df['mag'] >= 7.0

# Reset index and save
df = df.reset_index(drop=True)
df.to_csv("data/earthquakes_cleaned.csv", index=False)
print("Cleaned data saved to data/earthquakes_cleaned.csv")
print("Final Rows:", df.shape[0])
print("Columns:", df.shape[1])
print(df.head())
           
