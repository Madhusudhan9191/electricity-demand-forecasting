"""
Process and serialize feature matrices for all regions (TEX, MIDA, NY).
Saves to data/processed/{REGION}_features.parquet.
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
import yaml
import pandas as pd
from src.features import construct_feature_dataset

CONFIG_PATH = "config/config.yaml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

OUT_DIR = "data/processed"
os.makedirs(OUT_DIR, exist_ok=True)

for reg in config["regions"]:
    reg_id = reg["id"]
    tz_str = reg["timezone"]
    print(f"\nProcessing features for {reg_id} ({tz_str})...")

    demand_path = os.path.join(config["paths"]["raw_demand_dir"], f"{reg_id}_raw.csv")
    df_demand = pd.read_csv(demand_path)

    weather_path = os.path.join(config["paths"]["raw_weather_dir"], f"{reg_id}_weather_raw.json")
    with open(weather_path, "r", encoding="utf-8") as wf:
        wdata = json.load(wf)
    w_hourly = wdata["hourly"]

    df_weather = pd.DataFrame({
        "timestamp": pd.to_datetime(w_hourly["time"], utc=True),
        "temp_c": w_hourly["temperature_2m"],
        "rel_humidity_pct": w_hourly["relative_humidity_2m"],
        "wind_speed_kmh": w_hourly["wind_speed_10m"],
        "cloud_cover_pct": w_hourly.get("cloud_cover", [0.0] * len(w_hourly["time"])),
        "direct_solar_wm2": w_hourly.get("direct_normal_irradiance", [0.0] * len(w_hourly["time"]))
    })

    df_features = construct_feature_dataset(df_demand, df_weather, reg_id, timezone_str=tz_str)
    
    out_file = os.path.join(OUT_DIR, f"{reg_id}_features.parquet")
    df_features.to_parquet(out_file, index=False)
    print(f"  Successfully wrote {out_file}: {len(df_features):,} rows, {len(df_features.columns)} cols ({os.path.getsize(out_file):,} bytes).")

print("\nAll feature parquet files generated successfully.")
