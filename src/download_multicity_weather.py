"""
Download and compute population-weighted multi-city weather data from Open-Meteo ERA5 archive.
Attribution: Open-Meteo (CC-BY 4.0), European Centre for Medium-Range Weather Forecasts (ECMWF) ERA5.
"""

import json
import os
import time
import urllib.request
import numpy as np
import yaml

CONFIG_PATH = "config/config.yaml"
OUTPUT_DIR = "data/raw/weather"
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

START_DATE = "2020-01-01"
END_DATE = "2024-12-31"

def fetch_station(lat, lon, start_date=START_DATE, end_date=END_DATE):
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}"
        f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,direct_normal_irradiance"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "ElectricityForecastingPortfolio/1.0"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                return data
        except Exception as e:
            print(f"  Attempt {attempt+1} failed for ({lat}, {lon}): {e}. Retrying in 3s...")
            time.sleep(3)
    raise RuntimeError(f"Failed to fetch data for lat={lat}, lon={lon}")

def process_region(region_cfg):
    reg_id = region_cfg["id"]
    stations = region_cfg["weather_stations"]
    print(f"\nProcessing region {reg_id} ({len(stations)} stations)...")
    
    station_data = []
    weights = []
    
    for st in stations:
        city = st["city"]
        lat = st["lat"]
        lon = st["lon"]
        wt = st["weight"]
        print(f"  Fetching {city} (lat={lat}, lon={lon}, weight={wt})...")
        d = fetch_station(lat, lon)
        station_data.append(d["hourly"])
        weights.append(wt)
        time.sleep(1) # respectful API pacing
        
    weights = np.array(weights)
    weights = weights / np.sum(weights) # ensure exact sum = 1.0
    
    timestamps = station_data[0]["time"]
    n_hours = len(timestamps)
    print(f"  Aggregating {n_hours} hours across {len(stations)} stations with weights {weights.tolist()}...")
    
    variables = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "direct_normal_irradiance"]
    weighted_hourly = {"time": timestamps}
    
    for var in variables:
        mat = np.zeros((len(stations), n_hours), dtype=float)
        for i, s_hourly in enumerate(station_data):
            vals = s_hourly[var]
            mat[i, :] = [0.0 if v is None else float(v) for v in vals]
        weighted_vals = np.sum(mat * weights[:, None], axis=0)
        weighted_hourly[var] = [round(float(v), 2) for v in weighted_vals]
        
    out_obj = {
        "region": reg_id,
        "stations": stations,
        "hourly_units": {
            "time": "iso8601",
            "temperature_2m": "°C",
            "relative_humidity_2m": "%",
            "wind_speed_10m": "km/h",
            "direct_normal_irradiance": "W/m²"
        },
        "hourly": weighted_hourly
    }
    
    out_path = os.path.join(OUTPUT_DIR, f"{reg_id}_weather_raw.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f)
    print(f"  Saved {reg_id} composite weather to {out_path} ({os.path.getsize(out_path):,} bytes).")

if __name__ == "__main__":
    for reg in config["regions"]:
        process_region(reg)
    print("\nAll regional composite weather files successfully downloaded and processed.")
