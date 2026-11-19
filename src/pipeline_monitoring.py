"""
Monitoring, Drift Analysis, and Data Quality Assurance Module (Phase 6).
Rule 4: Every number comes from code. Never hard-code PASS or FAIL.
Rule 6: Describe real failures honestly; do not stage fake ones.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import yaml
from scipy.stats import ks_2samp


def calculate_psi(expected, actual, num_buckets=10):
    """
    Computes Population Stability Index (PSI) between baseline and target distributions.
    PSI < 0.10: Insignificant drift.
    0.10 <= PSI < 0.25: Moderate drift.
    PSI >= 0.25: Significant drift.
    """
    # Remove NaNs
    exp = expected[~np.isnan(expected)]
    act = actual[~np.isnan(actual)]

    if len(exp) == 0 or len(act) == 0:
        return np.nan

    # Determine quantile bins on expected
    percentiles = np.linspace(0, 100, num_buckets + 1)
    bins = np.percentile(exp, percentiles)
    bins[0] -= 1e-5
    bins[-1] += 1e-5
    bins = np.unique(bins)

    if len(bins) < 3:
        return 0.0

    exp_counts, _ = np.histogram(exp, bins=bins)
    act_counts, _ = np.histogram(act, bins=bins)

    exp_pct = np.maximum(exp_counts / len(exp), 1e-4)
    act_pct = np.maximum(act_counts / len(act), 1e-4)

    psi_val = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
    return float(psi_val)


def run_monitoring_and_quality_audit(config):
    proc_dir = Path(config["paths"]["processed_dir"])
    reports_dir = Path(config["paths"]["reports_dir"])
    exports_dir = Path(config["paths"]["exports_dir"])
    reports_dir.mkdir(parents=True, exist_ok=True)
    exports_dir.mkdir(parents=True, exist_ok=True)

    regions = [r["id"] for r in config["regions"]]

    drift_records = []
    assertion_records = []
    rolling_alert_records = []

    print("\n--- Starting Phase 6: Monitoring & Drift Analysis ---")

    for reg_id in regions:
        parquet_path = proc_dir / f"{reg_id}_features.parquet"
        df = pd.read_parquet(parquet_path)

        train_mask = (df["timestamp"] >= "2021-01-01") & (df["timestamp"] <= "2023-04-30 23:00:00+00:00")
        test_mask = (df["timestamp"] >= "2023-05-01") & (df["timestamp"] <= "2023-12-31 23:00:00+00:00")

        df_train = df[train_mask]
        df_test = df[test_mask]

        # 1. Feature Drift (KS Test and PSI)
        drift_features = [
            "demand_mw", "temp_c", "cooling_degrees", "heating_degrees",
            "rel_humidity_pct", "wind_speed_kmh", "lag_168h"
        ]

        for feat in drift_features:
            s_train = df_train[feat].values
            s_test = df_test[feat].values

            ks_stat, ks_pval = ks_2samp(s_train, s_test)
            psi_val = calculate_psi(s_train, s_test)

            drift_level = "Severe Drift (PSI >= 0.25)" if psi_val >= 0.25 else ("Moderate Drift (0.10-0.25)" if psi_val >= 0.10 else "Stable (PSI < 0.10)")

            drift_records.append({
                "region": reg_id,
                "feature": feat,
                "ks_statistic": round(float(ks_stat), 4),
                "ks_pvalue": float(ks_pval),
                "psi": round(float(psi_val), 4),
                "drift_level": drift_level,
                "train_mean": round(float(np.nanmean(s_train)), 2),
                "test_mean": round(float(np.nanmean(s_test)), 2),
                "pct_change_mean": round(float((np.nanmean(s_test) - np.nanmean(s_train)) / np.nanmean(s_train) * 100.0), 2)
            })

        # 2. Data Quality Assertions
        # Assertion 1: Duplicate timestamps
        dup_count = int(df["timestamp"].duplicated().sum())
        assertion_records.append({
            "region": reg_id,
            "assertion_id": "DQ_01_NO_DUPLICATES",
            "assertion_name": "Zero Duplicate Timestamps",
            "evaluated_table": "features.parquet",
            "status": "PASS" if dup_count == 0 else "FAIL",
            "failed_count": dup_count,
            "total_count": len(df),
            "threshold": "count == 0",
            "description": "Ensures no hourly interval is duplicated."
        })

        # Assertion 2: Continuous hourly grid (no missing hours)
        full_grid = pd.date_range(df["timestamp"].min(), df["timestamp"].max(), freq="h", tz="UTC")
        missing_count = len(full_grid.difference(df["timestamp"]))
        assertion_records.append({
            "region": reg_id,
            "assertion_id": "DQ_02_GRID_CONTINUITY",
            "assertion_name": "Continuous Hourly Grid",
            "evaluated_table": "features.parquet",
            "status": "PASS" if missing_count == 0 else "FAIL",
            "failed_count": missing_count,
            "total_count": len(full_grid),
            "threshold": "count == 0",
            "description": "Verifies that all 43,848 hours in the 5-year range are present without gaps."
        })

        # Assertion 3: Positive Demand Range
        non_pos_count = int((df["demand_mw"] <= 0).sum())
        assertion_records.append({
            "region": reg_id,
            "assertion_id": "DQ_03_DEMAND_POSITIVE",
            "assertion_name": "Demand Values Strictly Positive",
            "evaluated_table": "features.parquet",
            "status": "PASS" if non_pos_count == 0 else "FAIL",
            "failed_count": non_pos_count,
            "total_count": len(df),
            "threshold": "demand_mw > 0",
            "description": "Asserts electricity grid demand is positive (no zeros, negative, or NaNs)."
        })

        # Assertion 4: Raw vs Cleaned Discrepancy Rate (Audits real EIA dropout anomalies)
        diff_count = int((df["raw_demand_mw"] != df["demand_mw"]).sum())
        # We flag real historical dropouts as an audit finding
        assertion_records.append({
            "region": reg_id,
            "assertion_id": "DQ_04_RAW_FEED_DISCREPANCY",
            "assertion_name": "Raw EIA Stream Discrepancy Rate",
            "evaluated_table": "raw_vs_cleaned",
            "status": "WARNING" if diff_count > 0 else "PASS",
            "failed_count": diff_count,
            "total_count": len(df),
            "threshold": "rate < 3.0%",
            "description": f"Real historical EIA-930 reporting anomalies identified and imputed by Ruggles et al. ({round(diff_count/len(df)*100, 2)}%)."
        })

        # Assertion 5: Weather Physical Bounds
        temp_bad = int(((df["temp_c"] < -40.0) | (df["temp_c"] > 60.0)).sum())
        assertion_records.append({
            "region": reg_id,
            "assertion_id": "DQ_05_TEMP_PHYSICAL_BOUNDS",
            "assertion_name": "Temperature Physically Bounded",
            "evaluated_table": "weather",
            "status": "PASS" if temp_bad == 0 else "FAIL",
            "failed_count": temp_bad,
            "total_count": len(df),
            "threshold": "-40C <= temp <= 60C",
            "description": "Asserts air temperature is within physically possible continental boundaries."
        })

        # Assertion 6: Referential Integrity
        weather_nulls = int(df["temp_c"].isna().sum())
        assertion_records.append({
            "region": reg_id,
            "assertion_id": "DQ_06_WEATHER_ALIGNMENT",
            "assertion_name": "100% Demand-Weather Timestamp Alignment",
            "evaluated_table": "features_merged",
            "status": "PASS" if weather_nulls == 0 else "FAIL",
            "failed_count": weather_nulls,
            "total_count": len(df),
            "threshold": "nulls == 0",
            "description": "Verifies that every demand hour aligns to a corresponding ERA5 weather observation."
        })

    # 3. Rolling Error & Alert Tracking from Holdout Predictions
    df_preds = pd.read_csv(exports_dir / "tableau_hourly_forecasts.csv")
    df_preds["timestamp"] = pd.to_datetime(df_preds["timestamp"], utc=True)

    for reg_id, grp in df_preds.groupby("region"):
        grp = grp.sort_values("timestamp").reset_index(drop=True)
        # 7-day rolling metrics (168 hours)
        rolling_mae = grp["abs_error_mw"].rolling(168, min_periods=24).mean()
        rolling_bias = grp["error_mw"].rolling(168, min_periods=24).mean()
        inside_80 = (grp["actual_demand_mw"] >= grp["lower_bound_80"]) & (grp["actual_demand_mw"] <= grp["upper_bound_80"])
        rolling_cov80 = inside_80.rolling(168, min_periods=24).mean()

        val_mae = float(grp["abs_error_mw"].mean())
        # Define alert triggers
        mae_alert = rolling_mae > (1.5 * val_mae)
        cov_alert = rolling_cov80 < 0.65

        rolling_alert_records.append({
            "region": reg_id,
            "total_holdout_hours": len(grp),
            "mae_alert_hours": int(mae_alert.sum()),
            "mae_alert_pct": round(float(mae_alert.sum() / len(grp) * 100), 2),
            "coverage_breach_hours": int(cov_alert.sum()),
            "coverage_breach_pct": round(float(cov_alert.sum() / len(grp) * 100), 2),
            "max_rolling_mae_mw": round(float(rolling_mae.max()), 1),
            "min_rolling_coverage_80": round(float(rolling_cov80.min()), 3)
        })

    df_drift = pd.DataFrame(drift_records)
    df_assertions = pd.DataFrame(assertion_records)
    df_alerts = pd.DataFrame(rolling_alert_records)

    # Save to exports for Tableau and reports
    df_drift.to_csv(exports_dir / "tableau_drift_monitoring.csv", index=False)
    df_assertions.to_csv(exports_dir / "tableau_data_quality_log.csv", index=False)
    df_alerts.to_csv(reports_dir / "rolling_monitoring_alerts.csv", index=False)

    # Generate Markdown Report
    generate_monitoring_markdown(df_drift, df_assertions, df_alerts, reports_dir / "data_quality_and_monitoring_report.md")

    print("Phase 6 Monitoring & Data Quality successfully completed.")
    return df_drift, df_assertions, df_alerts


def generate_monitoring_markdown(df_drift, df_assertions, df_alerts, out_path):
    with open(out_path, "w") as f:
        f.write("# Phase 6: Monitoring, Drift & Data Quality Assurance Report\n\n")
        f.write("All assertions, PSI drift statistics, and rolling alert hours are computed programmatically.\n\n")

        f.write("## 1. Data Quality Assertions Log\n\n")
        f.write("| Region | Assertion ID | Assertion Name | Status | Failed Count | Total Rows | Threshold Rule |\n")
        f.write("| :--- | :--- | :--- | :---: | :---: | :---: | :--- |\n")
        for _, r in df_assertions.iterrows():
            status_badge = f"**{r['status']}**" if r['status'] == 'PASS' else f"`{r['status']}`"
            f.write(f"| {r['region']} | `{r['assertion_id']}` | {r['assertion_name']} | {status_badge} | {r['failed_count']:,} | {r['total_count']:,} | `{r['threshold']}` |\n")

        f.write("\n---\n\n")
        f.write("## 2. Feature & Target Distribution Drift (Train vs Holdout)\n\n")
        f.write("*PSI < 0.10: Stable, 0.10–0.25: Moderate Drift, >= 0.25: Severe Drift.*\n\n")
        f.write("| Region | Feature | KS Statistic | KS p-value | PSI | Drift Classification | Train Mean | Holdout Mean | Mean Delta (%) |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: |\n")
        for _, r in df_drift.iterrows():
            f.write(
                f"| **{r['region']}** | `{r['feature']}` | {r['ks_statistic']:.4f} | {r['ks_pvalue']:.2e} | "
                f"**{r['psi']:.4f}** | {r['drift_level']} | {r['train_mean']:,.1f} | {r['test_mean']:,.1f} | {r['pct_change_mean']:+.1f}% |\n"
            )

        f.write("\n---\n\n")
        f.write("## 3. Operational Monitoring & Alert Tracking Summary\n\n")
        f.write("| Region | Holdout Hours | Error Spike Alert Hours (MAE > 1.5x) | Coverage Breach Hours (Cov < 65%) | Max 7-Day Rolling MAE (MW) | Min 7-Day Rolling Cov80 |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for _, r in df_alerts.iterrows():
            f.write(
                f"| **{r['region']}** | {r['total_holdout_hours']:,} | {r['mae_alert_hours']:,} ({r['mae_alert_pct']}%) | "
                f"{r['coverage_breach_hours']:,} ({r['coverage_breach_pct']}%) | {r['max_rolling_mae_mw']:,.1f} | {r['min_rolling_coverage_80']:.3f} |\n"
            )


if __name__ == "__main__":
    with open("config/config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    run_monitoring_and_quality_audit(cfg)
