"""
Backtesting and Model Selection Orchestrator (Phase 2, 3, and 4).
Executes rolling-origin backtests for all candidate models across 4 folds (Calendar 2023) and 3 regions (TEX, MIDA, NY).
Implements pre-declared programmatic selection rule based strictly on validation folds:
1. Coverage constraint: Mean 80% interval coverage must be in [0.77, 0.83].
2. Primary metric: Minimize Geometric Mean rMAE vs Seasonal Naive 168h.
3. Tie-break 1: Minimize Mean Validation RMSE.
4. Tie-break 2: Model parsimony.
"""

import json
import os
import sys
import time
from pathlib import Path

os.environ["LOKY_MAX_CPU_COUNT"] = "4"
os.environ["OMP_NUM_THREADS"] = "4"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import yaml

from src.splits import get_folds_definition, split_data_for_fold
from src.baselines import (
    SeasonalNaive168,
    SeasonalNaive48,
    SeasonalMovingAverage,
    ETSSeasonalBaseline,
    RidgeLinearBaseline
)
from src.models import (
    PointHistGradientBoosting,
    ResidualHistGradientBoosting,
    SimpleEnsemble
)
from src.metrics import evaluate_forecast, compute_geometric_mean


def load_all_features(config):
    proc_dir = Path(config["paths"]["processed_dir"])
    features_dict = {}
    for region in config["regions"]:
        reg_id = region["id"]
        parquet_path = proc_dir / f"{reg_id}_features.parquet"
        if not parquet_path.exists():
            raise FileNotFoundError(f"Missing {parquet_path}")
        df_feat = pd.read_parquet(parquet_path)
        features_dict[reg_id] = df_feat
    return features_dict


def run_rolling_origin_backtests(config, features_dict):
    folds = get_folds_definition(config)
    regions = config["regions"]
    reports_dir = Path(config["paths"]["reports_dir"])
    reports_dir.mkdir(parents=True, exist_ok=True)

    all_results = []
    print("\n--- Starting 2023 Rolling-Origin Backtests across TEX, MIDA, NY ---")
    start_time = time.time()

    for fold_cfg in folds:
        fold_name = fold_cfg["name"]
        print(f"\nProcessing Fold: {fold_name} ({fold_cfg['val_start']} to {fold_cfg['val_end']})")

        for reg_meta in regions:
            reg_id = reg_meta["id"]
            df = features_dict[reg_id]
            df_train, df_val = split_data_for_fold(df, fold_cfg)

            y_train = df_train["demand_mw"].values
            y_val = df_val["demand_mw"].values
            val_hours = df_val["hour"].values
            val_base168 = df_val["lag_168h"].values

            # Season peak hours
            # Summer: [15..20] Central (TEX), [14..19] Eastern (MIDA, NY)
            # Other seasons: [7..9, 17..20]
            if "summer" in fold_name:
                peak_hours = reg_meta["peak_windows"]["summer"]
            else:
                peak_hours = reg_meta["peak_windows"]["winter_evening"]

            models_map = {
                "Seasonal_Naive_168h": SeasonalNaive168(),
                "Seasonal_Naive_48h": SeasonalNaive48(),
                "Seasonal_MA_4Week": SeasonalMovingAverage(),
                "ETS_HoltWinters": ETSSeasonalBaseline(),
                "Ridge_Linear_Baseline": RidgeLinearBaseline(alpha=10.0),
                "HistGradientBoosting_Point_Conformal": PointHistGradientBoosting(max_iter=120, max_depth=6),
                "HistGradientBoosting_Residual": ResidualHistGradientBoosting(max_iter=120, max_depth=6),
                "Ensemble_Ridge_HGBResidual": SimpleEnsemble()
            }

            for cand_name, model in models_map.items():
                t0 = time.time()
                
                # Extreme event weight treatment for tree models
                if cand_name in ["HistGradientBoosting_Point_Conformal", "HistGradientBoosting_Residual"]:
                    model.fit(df_train, extreme_event_weight=1.0)
                else:
                    model.fit(df_train)

                # Predictions with rolling conformal calibration
                if cand_name in ["HistGradientBoosting_Point_Conformal", "HistGradientBoosting_Residual", "Ensemble_Ridge_HGBResidual"]:
                    out = model.predict(df_val, y_test_true=y_val)
                    point_pred = out["point_pred"]
                    q_lower_80 = out["q_10"]
                    q_upper_80 = out["q_90"]
                    q_lower_95 = out["q_025"]
                    q_upper_95 = out["q_975"]
                else:
                    point_pred = model.predict(df_val)
                    # For baselines without dynamic conformal, use in-sample rolling residuals
                    resid = np.abs(y_train[168:] - y_train[:-168])
                    std_err = float(np.percentile(resid, 80.0))
                    std_err95 = float(np.percentile(resid, 95.0))
                    q_lower_80 = point_pred - std_err
                    q_upper_80 = point_pred + std_err
                    q_lower_95 = point_pred - std_err95
                    q_upper_95 = point_pred + std_err95

                fit_time = round(time.time() - t0, 2)

                # Evaluation metrics
                eval_metrics = evaluate_forecast(
                    y_true=y_val,
                    y_pred=point_pred,
                    y_train_history=y_train,
                    hours=val_hours,
                    y_base168=val_base168,
                    peak_hours=peak_hours,
                    q_lower_80=q_lower_80,
                    q_upper_80=q_upper_80,
                    q_lower_95=q_lower_95,
                    q_upper_95=q_upper_95
                )

                record = {
                    "model": cand_name,
                    "region": reg_id,
                    "fold": fold_name,
                    "val_hours": len(y_val),
                    "fit_time_sec": fit_time,
                    **eval_metrics
                }
                all_results.append(record)
                print(f"  [{reg_id} | {fold_name}] {cand_name:<36}: rMAE={eval_metrics['rMAE']:.3f}, MAE={eval_metrics['MAE']:.1f}, Cov80={eval_metrics['Coverage_80']:.3f}")

    total_time = round(time.time() - start_time, 1)
    print(f"\nAll rolling backtests finished in {total_time}s.")

    df_results = pd.DataFrame(all_results)
    csv_path = reports_dir / "rolling_origin_backtest_results.csv"
    df_results.to_csv(csv_path, index=False)

    # Aggregate by candidate model
    # Note: rMAE is aggregated via Geometric Mean!
    summary_records = []
    for model_name, grp in df_results.groupby("model"):
        gm_rmae = compute_geometric_mean(grp["rMAE"].values)
        summary_records.append({
            "model": model_name,
            "GM_rMAE": gm_rmae,
            "Mean_MASE": float(grp["MASE"].mean()),
            "Mean_MAE": float(grp["MAE"].mean()),
            "Mean_RMSE": float(grp["RMSE"].mean()),
            "Mean_sMAPE": float(grp["sMAPE"].mean()),
            "Mean_Bias": float(grp["Bias"].mean()),
            "Mean_Peak_MAE": float(grp["Peak_MAE"].mean()),
            "Mean_Coverage_80": float(grp["Coverage_80"].mean()),
            "Mean_Coverage_95": float(grp["Coverage_95"].mean()),
            "Mean_Width_80": float(grp["Width_80"].mean())
        })

    agg_table = pd.DataFrame(summary_records)

    # Selection Rule:
    # 1. Coverage constraint: Mean_Coverage_80 in [0.77, 0.83]
    # 2. Minimize GM_rMAE
    # 3. Tie-break: Minimize Mean_RMSE
    cov_low, cov_high = config["metrics"]["selection_rule"]["coverage_80_range"]
    agg_table["Coverage_80_Compliant"] = (agg_table["Mean_Coverage_80"] >= cov_low) & (agg_table["Mean_Coverage_80"] <= cov_high)

    # Sort compliant models first, then by GM_rMAE, then by Mean_RMSE
    compliant_models = agg_table[agg_table["Coverage_80_Compliant"]].sort_values(["GM_rMAE", "Mean_RMSE"])

    if len(compliant_models) > 0:
        winning_model = compliant_models.iloc[0]["model"]
        rule_status = f"PASSED: Winner satisfies pre-declared 80% coverage constraint [{cov_low}, {cov_high}]"
    else:
        winning_model = agg_table.sort_values(["GM_rMAE"]).iloc[0]["model"]
        rule_status = f"WARNING: No candidate fully met [{cov_low}, {cov_high}] coverage. Selected best GM_rMAE candidate."

    agg_table = agg_table.sort_values("GM_rMAE").reset_index(drop=True)

    print(f"\n=======================================================")
    print(f"PROGRAMMATIC MODEL SELECTION WINNER: {winning_model}")
    print(f"Selection Rule Status: {rule_status}")
    print(f"=======================================================")

    # Generate Model Selection Markdown Report
    md_path = reports_dir / "model_selection_comparison.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Model Comparison & Selection Report (Rolling-Origin Validation Folds 2023)\n\n")
        f.write(f"**Pre-declared Decision Rule:** Minimize Geometric-Mean Relative MAE ($\text{{rMAE}}$) subject to empirical 80% coverage constraint in [{cov_low}, {cov_high}].\n")
        f.write(f"**Rule Audit Status:** {rule_status}\n\n")
        f.write("### Model Leaderboard (Averaged Across 4 Folds and 3 Regions: TEX, MIDA, NY)\n\n")
        f.write("| Rank | Model | GM rMAE | Mean MASE | Mean MAE (MW) | Mean RMSE (MW) | Mean sMAPE (%) | Mean Bias (MW) | Peak MAE (MW) | 80% Coverage | 95% Coverage | Status |\n")
        f.write("| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |\n")

        for idx, row in agg_table.iterrows():
            if row["model"] == winning_model:
                status = "**SELECTED WINNER**"
            elif row["Coverage_80_Compliant"]:
                status = "Compliant"
            else:
                status = f"Non-compliant ({row['Mean_Coverage_80']:.1%})"
            f.write(
                f"| {idx+1} | `{row['model']}` | **{row['GM_rMAE']:.3f}** | {row['Mean_MASE']:.3f} | {row['Mean_MAE']:,.1f} | "
                f"{row['Mean_RMSE']:,.1f} | {row['Mean_sMAPE']:.2f}% | {row['Mean_Bias']:+,.1f} | "
                f"{row['Mean_Peak_MAE']:,.1f} | {row['Mean_Coverage_80']:.3f} | {row['Mean_Coverage_95']:.3f} | {status} |\n"
            )

        f.write("\n---\n\n")
        f.write("### Fold-by-Fold Detailed Breakdown (rMAE by Fold across Regions)\n\n")
        pivot_rmae = df_results.pivot_table(index="model", columns="fold", values="rMAE", aggfunc="mean").round(3)
        cols = list(pivot_rmae.columns)
        f.write("| Model | " + " | ".join(cols) + " |\n")
        f.write("| :--- | " + " | ".join([":---:"] * len(cols)) + " |\n")
        for idx, row in pivot_rmae.iterrows():
            vals = [f"{row[c]:.3f}" for c in cols]
            f.write(f"| `{idx}` | " + " | ".join(vals) + " |\n")
        f.write("\n\n---\n")

    return winning_model, df_results, agg_table


if __name__ == "__main__":
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    feats = load_all_features(cfg)
    run_rolling_origin_backtests(cfg, feats)
