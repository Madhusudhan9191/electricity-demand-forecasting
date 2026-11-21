"""
Data Manifest and SHA-256 Verification Script.
Audits downloaded raw datasets, computes cryptographic SHA-256 hashes,
and generates data/raw/data_manifest.json for audit reproducibility.
Rule 1: Never modify raw files. Keep a verifiable data receipt.
"""

import hashlib
import json
import time
from pathlib import Path
import pandas as pd


def compute_sha256(filepath):
    """Computes SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def audit_raw_data_manifest():
    raw_demand_dir = Path("data/raw/demand")
    raw_weather_dir = Path("data/raw/weather")
    manifest_path = Path("data/raw/data_manifest.json")

    manifest = {
        "audit_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files": []
    }

    # Audit Demand Files
    demand_files = list(raw_demand_dir.glob("*.csv"))
    weather_files = list(raw_weather_dir.glob("*.json"))

    print(f"\n--- SHA-256 Data Integrity Manifest Audit ---")
    print(f"Auditing raw files in {raw_demand_dir} and {raw_weather_dir}...\n")

    for fpath in demand_files + weather_files:
        file_size = fpath.stat().st_size
        sha256 = compute_sha256(fpath)

        info = {
            "file_name": fpath.name,
            "category": "demand" if "csv" in fpath.suffix else "weather",
            "file_path": str(fpath).replace("\\", "/"),
            "file_size_bytes": file_size,
            "sha256": sha256
        }

        if fpath.suffix == ".csv":
            try:
                df = pd.read_csv(fpath)
                info["row_count"] = len(df)
                info["columns"] = list(df.columns)
                if "date_time" in df.columns:
                    info["start_timestamp"] = str(df["date_time"].min())
                    info["end_timestamp"] = str(df["date_time"].max())
            except Exception as e:
                info["parse_error"] = str(e)

        manifest["files"].append(info)
        print(f"[{info['category'].upper():<7}] {fpath.name:<25} | {file_size:>10,} bytes | SHA256: {sha256[:16]}...")

    with open(manifest_path, "w") as mf:
        json.dump(manifest, mf, indent=2)

    print(f"\nManifest successfully written to {manifest_path}")
    return manifest


if __name__ == "__main__":
    audit_raw_data_manifest()
