"""
Data loader module for downloading and caching immutable raw demand and weather datasets.
Rule 1: Never modify raw files. Every transformation is scripted, re-runnable and documented.
"""

import os
import urllib.request
import json
import logging
from pathlib import Path
import pandas as pd
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_config(config_path="config/config.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def download_raw_demand(config):
    """
    Downloads raw EIA-930 hourly demand files from the peer-reviewed repository:
    truggles/EIA_Cleaned_Hourly_Electricity_Demand_Data (Nature Scientific Data 2020 / Jan 2025 release).
    Saves unmodified raw files into data/raw/demand/.
    """
    raw_dir = Path(config["paths"]["raw_demand_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    region_map = {
        "ERCOT": "TEX.csv",
        "PJM": "MIDA.csv",
        "NYIS": "NY.csv"
    }

    base_url = (
        "https://raw.githubusercontent.com/truggles/EIA_Cleaned_Hourly_Electricity_Demand_Data"
        "/master/data/release_2025_Jan_include_subregions/regions"
    )

    downloaded_files = {}
    for region_id, filename in region_map.items():
        dest = raw_dir / f"{region_id}_raw.csv"
        url = f"{base_url}/{filename}"
        if not dest.exists():
            logger.info(f"Downloading raw demand for {region_id} from {url}...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read()
                with open(dest, "wb") as f:
                    f.write(content)
            logger.info(f"Saved {dest} ({len(content)} bytes).")
        else:
            logger.info(f"Raw demand file already exists at {dest}.")
        downloaded_files[region_id] = dest

    return downloaded_files


def download_raw_weather(config):
    """
    Downloads raw historical hourly weather data from Open-Meteo ERA5 Reanalysis API.
    Saves unmodified JSON files into data/raw/weather/.
    """
    raw_dir = Path(config["paths"]["raw_weather_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    start_date = "2020-01-01"
    end_date = "2024-12-31"

    downloaded_files = {}
    for region in config["regions"]:
        region_id = region["id"]
        lat = region["weather_lat"]
        lon = region["weather_lon"]
        dest = raw_dir / f"{region_id}_weather_raw.json"

        if not dest.exists():
            url = (
                f"https://archive-api.open-meteo.com/v1/archive?"
                f"latitude={lat}&longitude={lon}&"
                f"start_date={start_date}&end_date={end_date}&"
                f"hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,cloud_cover,direct_normal_irradiance&"
                f"timezone=UTC"
            )
            logger.info(f"Downloading ERA5 weather for {region_id} ({lat}, {lon}) from Open-Meteo...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
                with open(dest, "w") as f:
                    json.dump(data, f)
            logger.info(f"Saved weather data to {dest}.")
        else:
            logger.info(f"Raw weather file already exists at {dest}.")
        downloaded_files[region_id] = dest

    return downloaded_files


if __name__ == "__main__":
    cfg = load_config()
    print("Downloading raw demand...")
    download_raw_demand(cfg)
    print("Downloading raw weather...")
    download_raw_weather(cfg)
    print("Data download completed successfully.")
