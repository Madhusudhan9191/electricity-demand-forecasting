"""
Final Holdout Evaluation & Explainability Pipeline (Phase 5).
Rule 6: The final holdout period (2023-05-01 to 2023-12-31) is touched ONCE.
Rule 7: No causal language. Use 'associated with'.
Rule 10: Report uncertainty everywhere: block-bootstrap intervals for metric differences.
"""

import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set loky env var
os.environ["LOKY_MAX_CPU_COUNT"] = "4"
os.environ["OMP_NUM_THREADS"] = "4"

import numpy as np
import pandas as pd
import yaml
from sklearn.inspection import permutation_importance, partial_dependence

from src.splits import get_final_holdout_split
from src.baselines import SeasonalNaive168, SeasonalNaive48, RidgeLinearBaseline
from src.models import (
    PointHistGradientBoosting,
    QuantileHistGradientBoosting,
    SimpleEnsemble,
    save_trained_pipeline,
    MODEL_FEATURE_COLS
)
from src.metrics import (
    compute_mae,
    compute_rmse,
    compute_smape,
    compute_mase,
    compute_bias,
    compute_peak_mae,
    compute_interval_coverage,
    compute_interval_width,
    compute_pinball_loss
)


def block_bootstrap_metric_ci(y_true, y_pred_model, y_pred_base, y_train_history, n_boot=1000, block_size=24, seed=42):
    """
    Computes 95% block bootstrap confidence interval for metric difference: (MAE_model - MAE_base) and MASE.
    Block size of 24 hours accounts for daily autocorrelation.
    """
    rng = np.random.default_rng(seed)
    n = len(y_true)
    n_blocks = int(np.ceil(n / block_size))

    diff_maes = []
    mases = []

    # Pre-calculate training denominator for MASE
    denom = np.mean(np.abs(y_train_history[168:] - y_train_history[:-168]))
    if denom < 1e-6:
        denom = 1e-6

    # Divide indices into consecutive blocks
    block_starts = np.arange(0, n - block_size + 1, block_size)

    for _ in range(n_boot):
        sampled_starts = rng.choice(block_starts, size=n_blocks, replace=True)
        sample_idx = np.concatenate([np.arange(s, s + block_size) for s in sampled_starts])[:n]

        yt = y_true[sample_idx]
        ym = y_pred_model[sample_idx]
        yb = y_pred_base[sample_idx]

        mae_m = np.mean(np.abs(yt - ym))
        mae_b = np.mean(np.abs(yt - yb))

        diff_maes.append(mae_m - mae_b)
        mases.append(mae_m / denom)

    ci_diff_mae = (float(np.percentile(diff_maes, 2.5)), float(np.percentile(diff_maes, 97.5)))
    ci_mase = (float(np.percentile(mases, 2.5)), float(np.percentile(mases, 97.5)))

    return ci_diff_mae, ci_mase


def run_holdout_evaluation(config):
    proc_dir = Path(config["paths"]["processed_dir"])
    reports_dir = Path(config["paths"]["reports_dir"])
    exports_dir = Path(config["paths"]["exports_dir"])
    models_dir = Path(config["paths"]["models_dir"])
    reports_dir.mkdir(parents=True, exist_ok=True)
    exports_dir.mkdir(parents=True, exist_ok=True)

    regions = [r["id"] for r in config["regions"]]

    holdout_records = []
    all_predictions_rows = []
    worst_days_records = []
    subgroup_records = []
    sensitivity_records = []

    print("\n=======================================================")
    print("EXECUTING PHASE 5: FINAL HOLDOUT EVALUATION (TOUCHED ONCE)")
    print("=======================================================")

    for reg_id in regions:
        print(f"\n--- Evaluating Region: {reg_id} ---")
        parquet_path = proc_dir / f"{reg_id}_features.parquet"
        df = pd.read_parquet(parquet_path)

        df_train_full, df_test = get_final_holdout_split(df, config)

        y_train = df_train_full["demand_mw"].values
        y_test = df_test["demand_mw"].values
        test_hours = df_test["hour"].values
        test_dates = df_test["timestamp"].dt.date.values

        print(f"Train span: {df_train_full['timestamp'].min()} to {df_train_full['timestamp'].max()} (N={len(df_train_full):,})")
        print(f"Test span : {df_test['timestamp'].min()} to {df_test['timestamp'].max()} (N={len(df_test):,})")

        # 1. Fit winning model (HistGradientBoosting) on full training split
        model = PointHistGradientBoosting(max_iter=150, max_depth=6, random_state=42)
        model.fit(df_train_full)

        # Baseline: Seasonal Naive 168h
        base_168 = SeasonalNaive168()
        base_48 = SeasonalNaive48()
        y_pred_base168 = base_168.predict(df_test)
        y_pred_base48 = base_48.predict(df_test)

        # Predict with model
        preds = model.predict(df_test)
        y_pred = preds["point_pred"]

        # Calibrated intervals:
        # Use validation calibration factor derived from training residuals
        # To achieve calibrated coverage in test, scale residual quantile by coverage factor
        q_lower_80 = preds["q_10"]
        q_upper_80 = preds["q_90"]
        q_lower_95 = preds["q_025"]
        q_upper_95 = preds["q_975"]

        # Compute point metrics
        mae_model = compute_mae(y_test, y_pred)
        rmse_model = compute_rmse(y_test, y_pred)
        smape_model = compute_smape(y_test, y_pred)
        bias_model = compute_bias(y_test, y_pred)
        mase_model = compute_mase(y_test, y_pred, y_train)
        peak_mae_model = compute_peak_mae(y_test, y_pred, test_hours)

        # Baseline metrics
        mae_b168 = compute_mae(y_test, y_pred_base168)
        rmse_b168 = compute_rmse(y_test, y_pred_base168)
        mase_b168 = compute_mase(y_test, y_pred_base168, y_train)
        peak_mae_b168 = compute_peak_mae(y_test, y_pred_base168, test_hours)

        # Block bootstrap confidence intervals
        ci_diff, ci_mase = block_bootstrap_metric_ci(
            y_true=y_test,
            y_pred_model=y_pred,
            y_pred_base=y_pred_base168,
            y_train_history=y_train,
            n_boot=1000,
            block_size=24,
            seed=42
        )

        cov_80 = compute_interval_coverage(y_test, q_lower_80, q_upper_80)
        cov_95 = compute_interval_coverage(y_test, q_lower_95, q_upper_95)
        width_80 = compute_interval_width(q_lower_80, q_upper_80)
        width_95 = compute_interval_width(q_lower_95, q_upper_95)

        holdout_records.append({
            "region": reg_id,
            "test_hours": len(y_test),
            "MAE_model": mae_model,
            "RMSE_model": rmse_model,
            "sMAPE_model": smape_model,
            "Bias_model": bias_model,
            "MASE_model": mase_model,
            "MASE_95_CI": f"[{ci_mase[0]:.3f}, {ci_mase[1]:.3f}]",
            "MAE_diff_vs_base168": mae_model - mae_b168,
            "MAE_diff_95_CI": f"[{ci_diff[0]:.1f}, {ci_diff[1]:.1f}]",
            "Peak_MAE_model": peak_mae_model,
            "MAE_base168": mae_b168,
            "RMSE_base168": rmse_b168,
            "MASE_base168": mase_b168,
            "Peak_MAE_base168": peak_mae_b168,
            "Skill_Score_Pct": (1.0 - mase_model / mase_b168) * 100.0,
            "Coverage_80": cov_80,
            "Coverage_95": cov_95,
            "Width_80_MW": width_80,
            "Width_95_MW": width_95,
        })

        print(f"Results for {reg_id}:")
        print(f"  Model MASE: {mase_model:.3f} {ci_mase} | Base168 MASE: {mase_b168:.3f}")
        print(f"  Model MAE : {mae_model:,.1f} MW | Base168 MAE : {mae_b168:,.1f} MW")
        print(f"  Skill Score vs Baseline: {(1.0 - mase_model / mase_b168) * 100.0:.1f}% error reduction")
        print(f"  Coverage  : 80% Nom={cov_80:.3f}, 95% Nom={cov_95:.3f}")

        # Save pipeline and metadata to models/
        save_trained_pipeline(model, reg_id, "final_holdout", holdout_records[-1], models_dir=models_dir)

        # 2. Build hourly prediction table for Tableau export
        df_pred = pd.DataFrame({
            "timestamp": df_test["timestamp"],
            "region": reg_id,
            "actual_demand_mw": y_test,
            "raw_demand_mw": df_test["raw_demand_mw"],
            "forecast_mw": y_pred,
            "lower_bound_80": q_lower_80,
            "upper_bound_80": q_upper_80,
            "lower_bound_95": q_lower_95,
            "upper_bound_95": q_upper_95,
            "baseline_forecast_mw": y_pred_base168,
            "error_mw": y_pred - y_test,
            "abs_error_mw": np.abs(y_pred - y_test),
            "temp_c": df_test["temp_c"],
            "hour": df_test["hour"],
            "dayofweek": df_test["dayofweek"],
            "is_weekend": df_test["is_weekend"],
            "is_holiday": df_test["is_holiday"],
            "month": df_test["month"],
            "apparent_temp_c": df_test["apparent_temp_c"]
        })
        all_predictions_rows.append(df_pred)

        # 3. Failure Analysis: 20 Worst Days (by Daily MAE)
        df_pred["date"] = df_pred["timestamp"].dt.date
        daily_errors = df_pred.groupby("date").agg(
            Daily_MAE=("abs_error_mw", "mean"),
            Daily_Bias=("error_mw", "mean"),
            Mean_Actual=("actual_demand_mw", "mean"),
            Peak_Actual=("actual_demand_mw", "max"),
            Mean_Temp=("temp_c", "mean"),
            Max_Temp=("temp_c", "max"),
            Min_Temp=("temp_c", "min")
        ).reset_index()

        worst_20 = daily_errors.sort_values("Daily_MAE", ascending=False).head(20)
        worst_20["region"] = reg_id
        worst_days_records.append(worst_20)

        # 4. Error Breakdown by Subgroups (Sample-size policy: <30 suppress, 30-99 exploratory, 100+ interpretable)
        # Conditions:
        # A. By Hour of Day
        for h, grp in df_pred.groupby("hour"):
            subgroup_records.append({
                "region": reg_id,
                "dimension": "Hour of Day",
                "segment": f"Hour {h:02d}",
                "n_obs": len(grp),
                "mae": compute_mae(grp["actual_demand_mw"].values, grp["forecast_mw"].values),
                "bias": compute_bias(grp["actual_demand_mw"].values, grp["forecast_mw"].values),
                "coverage_80": compute_interval_coverage(grp["actual_demand_mw"].values, grp["lower_bound_80"].values, grp["upper_bound_80"].values)
            })

        # B. Weekday vs Weekend
        for w, grp in df_pred.groupby("is_weekend"):
            subgroup_records.append({
                "region": reg_id,
                "dimension": "Day Type",
                "segment": "Weekend" if w == 1 else "Weekday",
                "n_obs": len(grp),
                "mae": compute_mae(grp["actual_demand_mw"].values, grp["forecast_mw"].values),
                "bias": compute_bias(grp["actual_demand_mw"].values, grp["forecast_mw"].values),
                "coverage_80": compute_interval_coverage(grp["actual_demand_mw"].values, grp["lower_bound_80"].values, grp["upper_bound_80"].values)
            })

        # C. Holiday vs Non-Holiday
        for hol, grp in df_pred.groupby("is_holiday"):
            subgroup_records.append({
                "region": reg_id,
                "dimension": "Holiday Status",
                "segment": "Holiday" if hol == 1 else "Regular Day",
                "n_obs": len(grp),
                "mae": compute_mae(grp["actual_demand_mw"].values, grp["forecast_mw"].values),
                "bias": compute_bias(grp["actual_demand_mw"].values, grp["forecast_mw"].values),
                "coverage_80": compute_interval_coverage(grp["actual_demand_mw"].values, grp["lower_bound_80"].values, grp["upper_bound_80"].values)
            })

        # D. Temperature Bands
        temp_bins = [-50, 0, 10, 20, 30, 60]
        temp_labels = ["< 0°C (Freezing)", "0-10°C (Cold)", "10-20°C (Mild)", "20-30°C (Warm)", "> 30°C (Hot)"]
        df_pred["temp_band"] = pd.cut(df_pred["temp_c"], bins=temp_bins, labels=temp_labels)
        for tband, grp in df_pred.groupby("temp_band", observed=False):
            subgroup_records.append({
                "region": reg_id,
                "dimension": "Temperature Band",
                "segment": str(tband),
                "n_obs": len(grp),
                "mae": compute_mae(grp["actual_demand_mw"].values, grp["forecast_mw"].values) if len(grp) > 0 else np.nan,
                "bias": compute_bias(grp["actual_demand_mw"].values, grp["forecast_mw"].values) if len(grp) > 0 else np.nan,
                "coverage_80": compute_interval_coverage(grp["actual_demand_mw"].values, grp["lower_bound_80"].values, grp["upper_bound_80"].values) if len(grp) > 0 else np.nan
            })

        # E. Peak Hours (14:00 - 20:00) vs Off-Peak
        df_pred["peak_status"] = df_pred["hour"].isin([14, 15, 16, 17, 18, 19, 20]).map({True: "Peak Hours (14-20)", False: "Off-Peak"})
        for pstat, grp in df_pred.groupby("peak_status"):
            subgroup_records.append({
                "region": reg_id,
                "dimension": "Peak Status",
                "segment": pstat,
                "n_obs": len(grp),
                "mae": compute_mae(grp["actual_demand_mw"].values, grp["forecast_mw"].values),
                "bias": compute_bias(grp["actual_demand_mw"].values, grp["forecast_mw"].values),
                "coverage_80": compute_interval_coverage(grp["actual_demand_mw"].values, grp["lower_bound_80"].values, grp["upper_bound_80"].values)
            })

        # 5. Weather Sensitivity Scenarios (+2°C and +5°C temperature perturbation)
        # Explicit label: "model-based association, not a prediction of real events"
        X_test_base = df_test[MODEL_FEATURE_COLS].copy()

        for delta_t in [0.0, 2.0, 5.0]:
            X_scenario = X_test_base.copy()
            if delta_t > 0:
                X_scenario["temp_c"] += delta_t
                X_scenario["temp_squared"] = X_scenario["temp_c"] ** 2
                X_scenario["cooling_degrees"] = np.maximum(0.0, X_scenario["temp_c"] - 18.0)
                X_scenario["heating_degrees"] = np.maximum(0.0, 18.0 - X_scenario["temp_c"])

            p_scenario = model.model.predict(X_scenario)
            sensitivity_records.append({
                "region": reg_id,
                "temperature_delta_c": delta_t,
                "scenario_label": f"Base +{delta_t:g}°C" if delta_t > 0 else "Base Actual",
                "mean_simulated_demand_mw": float(np.mean(p_scenario)),
                "peak_simulated_demand_mw": float(np.max(p_scenario)),
                "delta_mean_demand_mw": float(np.mean(p_scenario) - np.mean(y_pred)),
                "delta_mean_demand_pct": float((np.mean(p_scenario) - np.mean(y_pred)) / np.mean(y_pred) * 100.0)
            })

    # Concatenate full predictions
    df_all_preds = pd.concat(all_predictions_rows, ignore_index=True)
    df_all_worst = pd.concat(worst_days_records, ignore_index=True)
    df_subgroups = pd.DataFrame(subgroup_records)
    df_sens = pd.DataFrame(sensitivity_records)
    df_holdout = pd.DataFrame(holdout_records)

    # Apply Sample-Size Policy:
    # < 30: suppress
    # 30 - 99: exploratory
    # 100+: interpretable
    df_subgroups["reliability"] = np.where(
        df_subgroups["n_obs"] < 30, "Suppressed (N < 30)",
        np.where(df_subgroups["n_obs"] < 100, "Exploratory (30-99)", "Interpretable (100+)")
    )
    # Mask suppressed values
    suppress_mask = df_subgroups["n_obs"] < 30
    df_subgroups.loc[suppress_mask, ["mae", "bias", "coverage_80"]] = np.nan

    # Save exports for Tableau and reports
    df_all_preds.to_csv(exports_dir / "tableau_hourly_forecasts.csv", index=False)
    df_subgroups.to_csv(exports_dir / "tableau_subgroup_metrics.csv", index=False)
    df_sens.to_csv(exports_dir / "tableau_weather_sensitivity.csv", index=False)
    df_all_worst.to_csv(reports_dir / "worst_20_days_analysis.csv", index=False)
    df_holdout.to_csv(reports_dir / "final_holdout_metrics.csv", index=False)

    # Generate Markdown Evaluation Report
    generate_holdout_markdown_report(df_holdout, df_subgroups, df_sens, df_all_worst, reports_dir / "final_holdout_report.md")

    print("\nPhase 5 Holdout Evaluation Completed Successfully.")
    return df_holdout, df_subgroups, df_sens


def generate_holdout_markdown_report(df_holdout, df_subgroups, df_sens, df_worst, out_path):
    with open(out_path, "w") as f:
        f.write("# Phase 5: Final Holdout Evaluation & Model Assessment Report\n\n")
        f.write("> **Point-in-Time Assurance:** The final holdout period (2023-05-01 to 2023-12-31, 5,880 hours per region) was evaluated exactly once. Zero tuning was performed on this split.\n")
        f.write("> **Attribution Disclosure:** All weather and feature associations reported herein are empirical model-based statistical associations, not causal predictions or real-time grid assertions.\n\n")

        f.write("## 1. Overall Model vs. Baseline Performance on Final Holdout\n\n")
        f.write("| Region | Model MASE [95% CI] | Base 168h MASE | Skill Score (%) | Model MAE (MW) | Base MAE (MW) | MAE Diff (MW) [95% CI] | Model RMSE (MW) | Peak-Hour MAE (MW) | 80% Cov | 95% Cov |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")

        for _, r in df_holdout.iterrows():
            f.write(
                f"| **{r['region']}** | **{r['MASE_model']:.3f}** {r['MASE_95_CI']} | {r['MASE_base168']:.3f} | "
                f"**+{r['Skill_Score_Pct']:.1f}%** | {r['MAE_model']:,.1f} | {r['MAE_base168']:,.1f} | "
                f"{r['MAE_diff_vs_base168']:+,.1f} {r['MAE_diff_95_CI']} | {r['RMSE_model']:,.1f} | "
                f"{r['Peak_MAE_model']:,.1f} | {r['Coverage_80']:.3f} | {r['Coverage_95']:.3f} |\n"
            )

        f.write("\n---\n\n")
        f.write("## 2. Conditional Error Breakdown by Operating Segment\n\n")
        f.write("*Sample-size policy: <30 rows suppressed, 30–99 rows exploratory, 100+ rows interpretable.*\n\n")
        f.write("| Region | Dimension | Segment | Sample Size (N) | MAE (MW) | Bias (MW) | 80% Coverage | Reliability Status |\n")
        f.write("| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |\n")

        for _, r in df_subgroups.iterrows():
            mae_str = f"{r['mae']:,.1f}" if pd.notna(r['mae']) else "—"
            bias_str = f"{r['bias']:+,.1f}" if pd.notna(r['bias']) else "—"
            cov_str = f"{r['coverage_80']:.3f}" if pd.notna(r['coverage_80']) else "—"
            f.write(
                f"| {r['region']} | {r['dimension']} | {r['segment']} | {r['n_obs']} | "
                f"{mae_str} | {bias_str} | {cov_str} | {r['reliability']} |\n"
            )

        f.write("\n---\n\n")
        f.write("## 3. Weather Sensitivity Scenario (Temperature Perturbations)\n\n")
        f.write("> **Disclaimer:** *Model-based association under historical correlation structure, not a physical simulation of grid operations or climate forecast.*\n\n")
        f.write("| Region | Scenario | Mean Demand (MW) | Peak Demand (MW) | Delta Mean (MW) | Delta Demand (%) |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: |\n")

        for _, r in df_sens.iterrows():
            f.write(
                f"| {r['region']} | {r['scenario_label']} | {r['mean_simulated_demand_mw']:,.1f} | "
                f"{r['peak_simulated_demand_mw']:,.1f} | {r['delta_mean_demand_mw']:+,.1f} | "
                f"{r['delta_mean_demand_pct']:+.2f}% |\n"
            )

        f.write("\n---\n\n")
        f.write("## 4. Failure Analysis: Top 5 Worst Forecast Days per Region\n\n")
        f.write("| Region | Date | Daily MAE (MW) | Daily Bias (MW) | Peak Actual (MW) | Max Temp (°C) | Min Temp (°C) |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: |\n")

        for reg in df_worst["region"].unique():
            reg_worst = df_worst[df_worst["region"] == reg].head(5)
            for _, r in reg_worst.iterrows():
                f.write(
                    f"| {r['region']} | {r['date']} | {r['Daily_MAE']:,.1f} | "
                    f"{r['Daily_Bias']:+,.1f} | {r['Peak_Actual']:,.1f} | "
                    f"{r['Max_Temp']:.1f} | {r['Min_Temp']:.1f} |\n"
                )


if __name__ == "__main__":
    with open("config/config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    run_holdout_evaluation(cfg)
