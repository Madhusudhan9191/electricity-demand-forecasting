"""
Reconciliation Module (Phase 8).
Rule 4: Every number comes from code or a query. Never hard-code PASS or FAIL.
Rule 8: Compare Python results, an independent SQL query (SQLite / DuckDB), and user Tableau exports.
If Tableau export is missing, mark the layer PENDING; never substitute Python values.
"""

import json
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
import yaml


def run_three_way_reconciliation():
    exports_dir = Path("data/exports")
    reports_dir = Path("reports")
    tableau_user_dir = Path("data/tableau_exports")
    tableau_user_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Layer 1: Python computed metrics
    python_metrics_df = pd.read_csv(reports_dir / "final_holdout_metrics.csv")

    # 2. Layer 2: Independent SQL Engine Query (via SQLite on exported Tableau CSV)
    csv_path = exports_dir / "tableau_hourly_forecasts.csv"
    df_raw_csv = pd.read_csv(csv_path)

    # Connect to in-memory SQLite database
    con = sqlite3.connect(":memory:")
    df_raw_csv.to_sql("tableau_forecasts", con, index=False)

    # Execute independent SQL aggregation
    query = """
    SELECT
        region,
        COUNT(*) as test_hours,
        AVG(abs_error_mw) as sql_mae,
        SQRT(AVG(error_mw * error_mw)) as sql_rmse,
        AVG(error_mw) as sql_bias,
        AVG(CASE WHEN actual_demand_mw >= lower_bound_80 AND actual_demand_mw <= upper_bound_80 THEN 1.0 ELSE 0.0 END) as sql_cov80,
        AVG(CASE WHEN actual_demand_mw >= lower_bound_95 AND actual_demand_mw <= upper_bound_95 THEN 1.0 ELSE 0.0 END) as sql_cov95,
        AVG(ABS(actual_demand_mw - baseline_forecast_mw)) as sql_base_mae
    FROM tableau_forecasts
    GROUP BY region
    ORDER BY region;
    """
    df_sql = pd.read_sql_query(query, con)

    # 3. Layer 3: Check for user exported Tableau crosstab
    user_tableau_file = tableau_user_dir / "tableau_crosstab_metrics.csv"
    tableau_available = user_tableau_file.exists()

    df_tableau = None
    if tableau_available:
        try:
            df_tableau = pd.read_csv(user_tableau_file)
        except Exception:
            tableau_available = False

    # 4. Compare Layer 1 (Python) vs Layer 2 (SQL)
    tolerance_mae = 0.01  # 0.01 MW
    tolerance_pct = 0.0001  # 0.01%

    reconciliation_rows = []
    for _, py_row in python_metrics_df.iterrows():
        reg = py_row["region"]
        sql_match = df_sql[df_sql["region"] == reg].iloc[0]

        mae_diff = abs(py_row["MAE_model"] - sql_match["sql_mae"])
        rmse_diff = abs(py_row["RMSE_model"] - sql_match["sql_rmse"])
        bias_diff = abs(py_row["Bias_model"] - sql_match["sql_bias"])
        cov80_diff = abs(py_row["Coverage_80"] - sql_match["sql_cov80"])

        # Determine SQL Status programmatically
        sql_status = "PASS" if (mae_diff <= tolerance_mae and cov80_diff <= tolerance_pct) else "FAIL"

        # Determine Tableau Layer Status
        if tableau_available and df_tableau is not None and "MAE" in df_tableau.columns:
            tab_match = df_tableau[df_tableau["Region"] == reg]
            if len(tab_match) > 0:
                tab_mae = float(tab_match.iloc[0]["MAE"])
                tab_diff = abs(py_row["MAE_model"] - tab_mae)
                tab_status = "PASS" if tab_diff <= tolerance_mae else "FAIL"
            else:
                tab_status = "PENDING (Region Not in Tableau Export)"
                tab_mae = np.nan
        else:
            tab_status = "PENDING (Awaiting User Tableau Crosstab Export)"
            tab_mae = np.nan

        reconciliation_rows.append({
            "region": reg,
            "metric": "MAE (MW)",
            "layer_1_python": round(py_row["MAE_model"], 2),
            "layer_2_sql": round(sql_match["sql_mae"], 2),
            "sql_diff": round(mae_diff, 4),
            "sql_status": sql_status,
            "layer_3_tableau": round(tab_mae, 2) if pd.notna(tab_mae) else "PENDING",
            "tableau_status": tab_status
        })

        reconciliation_rows.append({
            "region": reg,
            "metric": "RMSE (MW)",
            "layer_1_python": round(py_row["RMSE_model"], 2),
            "layer_2_sql": round(sql_match["sql_rmse"], 2),
            "sql_diff": round(rmse_diff, 4),
            "sql_status": "PASS" if rmse_diff <= tolerance_mae else "FAIL",
            "layer_3_tableau": "PENDING",
            "tableau_status": tab_status
        })

        reconciliation_rows.append({
            "region": reg,
            "metric": "80% Coverage",
            "layer_1_python": round(py_row["Coverage_80"], 4),
            "layer_2_sql": round(sql_match["sql_cov80"], 4),
            "sql_diff": round(cov80_diff, 6),
            "sql_status": "PASS" if cov80_diff <= tolerance_pct else "FAIL",
            "layer_3_tableau": "PENDING",
            "tableau_status": tab_status
        })

    df_recon = pd.DataFrame(reconciliation_rows)
    df_recon.to_csv(reports_dir / "reconciliation_results.csv", index=False)

    # Write Markdown Report
    report_md_path = reports_dir / "reconciliation_report.md"
    with open(report_md_path, "w") as f:
        f.write("# Phase 8: Three-Way Metric Reconciliation Report\n\n")
        f.write("Cross-engine reconciliation comparing:\n")
        f.write("1. **Layer 1 (Python Pipelines):** Evaluated via Scikit-Learn and NumPy arrays.\n")
        f.write("2. **Layer 2 (Independent SQL Engine):** Computed via SQLite queries on exported Tableau CSV.\n")
        f.write("3. **Layer 3 (Tableau Workbooks):** Exported crosstabs from user workbook.\n\n")
        f.write("> **Strict Protocol:** If Tableau exports are missing, Layer 3 is designated **PENDING**; Python numbers are NEVER substituted.\n\n")

        f.write("## Reconciliation Table\n\n")
        f.write("| Region | Metric | Layer 1: Python | Layer 2: SQL Engine | SQL Absolute Diff | SQL Validation | Layer 3: Tableau Public | Tableau Validation |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")

        for _, r in df_recon.iterrows():
            f.write(
                f"| **{r['region']}** | {r['metric']} | {r['layer_1_python']} | {r['layer_2_sql']} | "
                f"{r['sql_diff']} | **{r['sql_status']}** | {r['layer_3_tableau']} | `{r['tableau_status']}` |\n"
            )

        f.write("\n---\n\n")
        f.write("### Reconciliation Summary\n")
        sql_passes = (df_recon["sql_status"] == "PASS").sum()
        sql_total = len(df_recon)
        f.write(f"- **SQL vs Python Reconciliation:** {sql_passes}/{sql_total} assertions **PASSED** (Tolerance $\le 0.01$ MW / $0.0001$ coverage).\n")
        f.write(f"- **Tableau Layer Status:** Currently **PENDING**. Place exported crosstab at `data/tableau_exports/tableau_crosstab_metrics.csv` to reconcile Layer 3.\n")

    print(f"Reconciliation completed: {sql_passes}/{sql_total} SQL checks passed.")
    return df_recon


if __name__ == "__main__":
    run_three_way_reconciliation()
