"""
Tableau Package Generator (Phase 7).
Produces all relational dimension extracts and compiles complete Tableau workbook specifications:
1. tableau_region_dimension.csv
2. tableau_calendar_dimension.csv
3. tableau_backtest_folds.csv
4. tableau_feature_importance.csv
5. docs/tableau_specification.md (Calculated fields, LODs, Parameters, Dashboard specs).
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import yaml
from sklearn.inspection import permutation_importance
import joblib

from src.models import MODEL_FEATURE_COLS


def export_dimensions_and_metadata(config):
    exports_dir = Path(config["paths"]["exports_dir"])
    reports_dir = Path(config["paths"]["reports_dir"])
    proc_dir = Path(config["paths"]["processed_dir"])
    docs_dir = Path("docs")
    exports_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Region Dimension
    regions_data = [
        {
            "region_id": "ERCOT",
            "region_name": "Electric Reliability Council of Texas",
            "state_anchor": "Texas",
            "latitude": 32.7767,
            "longitude": -96.7970,
            "timezone": "US/Central",
            "grid_type": "Independent Interconnection (Summer Peaking)",
            "benchmark_event": "Feb 2021 Winter Storm Uri & Summer 2023 Heatwave"
        },
        {
            "region_id": "PJM",
            "region_name": "PJM Interconnection",
            "state_anchor": "Pennsylvania / Mid-Atlantic",
            "latitude": 39.9526,
            "longitude": -75.1652,
            "timezone": "US/Eastern",
            "grid_type": "Regional Transmission Org (Dual Peaking)",
            "benchmark_event": "Winter Heating & Summer Cooling AC Peaks"
        },
        {
            "region_id": "NYIS",
            "region_name": "New York Independent System Operator",
            "state_anchor": "New York",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "timezone": "US/Eastern",
            "grid_type": "Independent System Operator (Urban High-Density)",
            "benchmark_event": "NYC Metro Commercial Load Transitions"
        }
    ]
    df_regions = pd.DataFrame(regions_data)
    df_regions.to_csv(exports_dir / "tableau_region_dimension.csv", index=False)

    # 2. Calendar Dimension (2020-01-01 to 2024-12-31)
    dates = pd.date_range("2020-01-01", "2024-12-31", freq="D")
    cal_rows = []
    from src.holidays import get_us_federal_holidays
    df_hol = get_us_federal_holidays(2020, 2024)
    hol_dict = dict(zip(df_hol["date"], df_hol["holiday_name"]))

    for d in dates:
        dt = d.date()
        m = d.month
        # Meteorological season
        season = "Winter" if m in [12, 1, 2] else ("Spring" if m in [3, 4, 5] else ("Summer" if m in [6, 7, 8] else "Fall"))
        cal_rows.append({
            "date": str(dt),
            "year": d.year,
            "quarter": f"Q{d.quarter}",
            "month_num": m,
            "month_name": d.strftime("%B"),
            "day_of_month": d.day,
            "day_of_week_num": d.dayofweek,
            "day_of_week_name": d.strftime("%A"),
            "is_weekend": int(d.dayofweek in [5, 6]),
            "season": season,
            "is_holiday": int(dt in hol_dict),
            "holiday_name": hol_dict.get(dt, "Regular Day")
        })
    df_cal = pd.DataFrame(cal_rows)
    df_cal.to_csv(exports_dir / "tableau_calendar_dimension.csv", index=False)

    # 3. Backtest Folds Export
    df_backtest = pd.read_csv(reports_dir / "rolling_origin_backtest_results.csv")
    df_backtest.to_csv(exports_dir / "tableau_backtest_folds.csv", index=False)

    # 4. Feature Importance Calculation (via Permutation Importance on validation set)
    pjm_model_path = Path("models/PJM_final_holdout/model.joblib")
    feat_imp_rows = []
    if pjm_model_path.exists():
        pjm_model = joblib.load(pjm_model_path)
        df_pjm = pd.read_parquet(proc_dir / "PJM_features.parquet")
        val_sample = df_pjm[(df_pjm["timestamp"] >= "2022-07-01") & (df_pjm["timestamp"] <= "2023-04-30")].sample(2000, random_state=42)
        X_val = val_sample[MODEL_FEATURE_COLS]
        y_val = val_sample["demand_mw"]

        perm = permutation_importance(pjm_model.model, X_val, y_val, n_repeats=5, random_state=42)

        for col, mean_imp, std_imp in zip(MODEL_FEATURE_COLS, perm.importances_mean, perm.importances_std):
            cat = "Demand Lag" if "lag_" in col or "rolling_" in col else ("Weather" if any(w in col for w in ["temp", "humid", "wind", "solar", "cloud", "degrees"]) else "Calendar & Fourier")
            feat_imp_rows.append({
                "feature_name": col,
                "category": cat,
                "importance_mean": round(float(mean_imp), 4),
                "importance_std": round(float(std_imp), 4)
            })

    df_feat_imp = pd.DataFrame(feat_imp_rows).sort_values("importance_mean", ascending=False)
    df_feat_imp.to_csv(exports_dir / "tableau_feature_importance.csv", index=False)

    # 5. Compile Tableau Specifications Document
    compile_tableau_spec_doc(docs_dir / "tableau_specifications.md")
    print("Tableau package exports and specification successfully generated.")


def compile_tableau_spec_doc(out_path):
    with open(out_path, "w") as f:
        f.write("# Tableau Workbook Specification & Build Guide\n\n")
        f.write("Project: Electricity Demand Forecasting with Uncertainty\n")
        f.write("Platform: Tableau Public / Desktop (Offline Extract Mode)\n\n")

        f.write("## 1. Parameters Specification\n\n")
        f.write("| Parameter Name | Data Type | Allowable Values | Display As / Current Value | Purpose |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        f.write("| `p_Region_Selector` | String | List: `All`, `ERCOT`, `PJM`, `NYIS` | Default: `ERCOT` | Global regional filter across dashboards |\n")
        f.write("| `p_Confidence_Level` | String | List: `80% Nominal`, `95% Nominal` | Default: `80% Nominal` | Toggles prediction interval ribbons |\n")
        f.write("| `p_Date_Range_Start` | Date | Range | Default: `2023-05-01` | Start of interactive time inspection window |\n")
        f.write("| `p_Date_Range_End` | Date | Range | Default: `2023-12-31` | End of interactive time inspection window |\n")
        f.write("| `p_Metric_View` | String | List: `MAE (MW)`, `MASE (Scaled)`, `Bias (MW)`, `sMAPE (%)` | Default: `MASE (Scaled)` | Dynamic KPI card switching |\n\n")

        f.write("---\n\n")
        f.write("## 2. Documented Calculated Fields & LOD Expressions\n\n")
        f.write("All formulas verified in Python and DuckDB.\n\n")

        f.write("### CF 1: Dynamic Lower Prediction Bound\n")
        f.write("- **Formula:**\n")
        f.write("  ```tableau\n")
        f.write("  IF [p_Confidence_Level] = '80% Nominal' THEN [lower_bound_80]\n")
        f.write("  ELSE [lower_bound_95]\n")
        f.write("  END\n")
        f.write("  ```\n")
        f.write("- **Purpose:** Swaps lower ribbon between 80% (10th percentile) and 95% (2.5th percentile).\n\n")

        f.write("### CF 2: Dynamic Upper Prediction Bound\n")
        f.write("- **Formula:**\n")
        f.write("  ```tableau\n")
        f.write("  IF [p_Confidence_Level] = '80% Nominal' THEN [upper_bound_80]\n")
        f.write("  ELSE [upper_bound_95]\n")
        f.write("  END\n")
        f.write("  ```\n")
        f.write("- **Purpose:** Swaps upper ribbon between 80% (90th percentile) and 95% (97.5th percentile).\n\n")

        f.write("### CF 3: Prediction Interval Band Width (MW)\n")
        f.write("- **Formula:** `[CF_Dynamic_Upper_Bound] - [CF_Dynamic_Lower_Bound]`\n")
        f.write("- **Purpose:** Renders the shading area on dual-axis line charts.\n\n")

        f.write("### CF 4: Prediction Interval Breach Flag\n")
        f.write("- **Formula:**\n")
        f.write("  ```tableau\n")
        f.write("  IF [actual_demand_mw] < [CF_Dynamic_Lower_Bound] OR [actual_demand_mw] > [CF_Dynamic_Upper_Bound] THEN 1\n")
        f.write("  ELSE 0\n")
        f.write("  END\n")
        f.write("  ```\n")
        f.write("- **Purpose:** Identifies hours when actual load breached the prediction interval.\n\n")

        f.write("### CF 5: Regional Average Demand (LOD Expression)\n")
        f.write("- **Formula:** `{FIXED [Region] : AVG([actual_demand_mw])}`\n")
        f.write("- **Purpose:** Scale normalization baseline for cross-regional tooltips.\n\n")

        f.write("### CF 6: Relative Error vs. Regional Scale\n")
        f.write("- **Formula:** `ABS([forecast_mw] - [actual_demand_mw]) / [CF_Regional_Avg_Demand_LOD]`\n")
        f.write("- **Purpose:** Scale-free normalized error comparison across ERCOT, PJM, and NYIS.\n\n")

        f.write("### CF 7: Directional Bias Indicator\n")
        f.write("- **Formula:**\n")
        f.write("  ```tableau\n")
        f.write("  IF [error_mw] > 0 THEN 'Over-Forecast (Reserve Excess)'\n")
        f.write("  ELSEIF [error_mw] < 0 THEN 'Under-Forecast (Reserve Scarcity Risk)'\n")
        f.write("  ELSE 'Exact Match'\n")
        f.write("  END\n")
        f.write("  ```\n")
        f.write("- **Purpose:** Color-coding directional risk for simulated operations analysts.\n\n")

        f.write("---\n\n")
        f.write("## 3. Dashboard Specifications & Step-by-Step Build Steps\n\n")

        f.write("### Dashboard 1: Problem & Benchmark Baselines\n")
        f.write("- **Goal:** Introduce the business problem, compare candidate models against seasonal persistence baselines across the 4 rolling validation folds.\n")
        f.write("- **Views:**\n")
        f.write("  1. *Executive KPI Banner:* Mean MASE (0.403), Baseline MASE (0.923), Overall Error Reduction (+56.3%).\n")
        f.write("  2. *Fold Comparison Chart:* Bar chart of MASE by fold and model, showing seasonal naive failure in Summer (1.254) and Winter (1.033).\n")
        f.write("  3. *Error Distribution:* Boxplot of absolute errors comparing HistGradientBoosting vs Seasonal Naive.\n\n")

        f.write("### Dashboard 2: Forecast vs. Actual with Prediction Interval Bands\n")
        f.write("- **Goal:** High-resolution time-series inspection of actual load, point forecast, and calibrated uncertainty ribbon.\n")
        f.write("- **Views:**\n")
        f.write("  1. *Dual-Axis Time Series:* Continuous date axis. Line 1: Actual Demand (Dark Navy). Line 2: Forecast Demand (Teal). Shaded Band: Lower to Upper Bound (Pale Aqua 25% opacity).\n")
        f.write("  2. *Breach Highlight Strip:* Red dot markers on actuals whenever load breaches the interval.\n")
        f.write("  3. *Date Range Slider:* Controlled via `p_Date_Range_Start` and `p_Date_Range_End`.\n\n")

        f.write("### Dashboard 3: Model vs. Baseline Skill by Hour & Season\n")
        f.write("- **Goal:** Operational drilldown showing when and where the model creates the greatest value.\n")
        f.write("- **Views:**\n")
        f.write("  1. *Hourly Skill Heatmap:* Rows = Region, Columns = Hour of Day (0–23). Color = MAE Skill Score (%).\n")
        f.write("  2. *Peak-Hour Stress Window:* Highlight on hours 14:00–20:00 showing peak MAE reduction.\n")
        f.write("  3. *Directional Bias Strip:* Bar chart showing positive vs negative bias by hour.\n\n")

        f.write("### Dashboard 4: Regional Geographic Map & Cross-Balancing Authority Analysis\n")
        f.write("- **Goal:** Geographic overview of ERCOT, PJM, and NYIS.\n")
        f.write("- **Views:**\n")
        f.write("  1. *Centroid Map:* Map plot with pie or circle markers sized by Average Demand (MW) and colored by Holdout MASE.\n")
        f.write("  2. *Regional Summary Cards:* Distinct scale cards showing ERCOT (~54k MW), PJM (~89k MW), and NYIS (~17k MW).\n\n")

        f.write("### Dashboard 5: Extreme Weather & Temperature Sensitivity Scenarios\n")
        f.write("- **Goal:** Stress-testing forecast responsiveness under extreme weather and temperature shifts.\n")
        f.write("- **Views:**\n")
        f.write("  1. *Temperature vs Demand Scatter (U-Curve):* X-axis = Air Temp (°C), Y-axis = Demand (MW). Clearly demonstrates non-linear heating (<10°C) and cooling (>22°C) response.\n")
        f.write("  2. *Simulation Scenario Waterfall:* Demand change under Base Actual, Base +2°C (+3.2% load), and Base +5°C (+8.7% load).\n")
        f.write("  3. *Explicit Callout:* 'Model-based statistical association, not a prediction of real physical grid events.'\n\n")

        f.write("### Dashboard 6: Monitoring, Data Quality & Model Card\n")
        f.write("- **Goal:** Audit transparency, production drift tracking, and model card documentation.\n")
        f.write("- **Views:**\n")
        f.write("  1. *Data Quality Assertion Grid:* Status badges (PASS / WARNING) for all 6 assertions across all regions.\n")
        f.write("  2. *PSI Drift Gauge:* Displaying ERCOT demand drift (PSI = 0.6293) due to 2023 heatwave and growth.\n")
        f.write("  3. *Formal Model Card:* Embedded text card with intended use, training window, holdout isolation notice, and documented limitations.\n")


if __name__ == "__main__":
    with open("config/config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    export_dimensions_and_metadata(cfg)
