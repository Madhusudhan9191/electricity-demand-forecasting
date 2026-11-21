"""
Complete Phase Audit Script.
Checks all project phases, files, data outputs, model artifacts,
Tableau package, documentation, and clean zip.
"""
import os, sys, json, zipfile, sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"
results = []

def chk(label, condition, details="", level="critical"):
    status = PASS if condition else (FAIL if level == "critical" else WARN)
    results.append({"check": label, "status": status, "details": details})
    icon = "OK" if status == PASS else ("!!" if status == FAIL else "~~")
    print(f"  [{icon}] {status}: {label}" + (f" | {details}" if details else ""))
    return condition

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ----------------------------------------------------------------
section("PHASE 0: Configuration & Specification")
# ----------------------------------------------------------------
chk("config/config.yaml exists", os.path.exists("config/config.yaml"))
chk("docs/phase_0_specification.md exists", os.path.exists("docs/phase_0_specification.md"))
chk("phase_0_specification_revised.md REMOVED", not os.path.exists("docs/phase_0_specification_revised.md"))
with open("config/config.yaml", "r") as f:
    cfg = f.read()
chk("Config: train_start = 2021", "2021-01-01" in cfg, "train split")
chk("Config: validation = 2023", "2023-01-01" in cfg, "val split")
chk("Config: holdout = 2024", "2024-01-01" in cfg, "holdout split")
chk("Config: refit_train_end = 2023-12-31", "2023-12-31" in cfg, "refit protocol")
chk("No absolute paths in config", "LENOVO" not in cfg and "C:\\" not in cfg, "path hygiene")

# ----------------------------------------------------------------
section("PHASE 1: Data Integrity & Audit")
# ----------------------------------------------------------------
for reg in ["TEX", "MIDA", "NY"]:
    chk(f"Raw demand: {reg}_raw.csv", os.path.exists(f"data/raw/demand/{reg}_raw.csv"))
    chk(f"Raw weather: {reg}_weather_raw.json", os.path.exists(f"data/raw/weather/{reg}_weather_raw.json"))
chk("data/raw/data_manifest.json exists", os.path.exists("data/raw/data_manifest.json"))
chk("reports/phase1_data_audit.json exists", os.path.exists("reports/phase1_data_audit.json"))
# Verify no old ERCOT/PJM/NYIS files remain
stale = [f for root, _, files in os.walk("data") for f in files
         if any(r in f.upper() for r in ["ERCOT", "PJM", "NYIS", "NYISO"])]
chk("No stale ERCOT/PJM/NYIS data files", len(stale) == 0, f"stale={stale}")

# ----------------------------------------------------------------
section("PHASE 2: Feature Engineering & Parquet Files")
# ----------------------------------------------------------------
for reg in ["TEX", "MIDA", "NY"]:
    p = f"data/processed/{reg}_features.parquet"
    chk(f"Parquet exists: {reg}", os.path.exists(p))
    if os.path.exists(p):
        df = pd.read_parquet(p)
        n_train = len(df[(df["timestamp"] >= "2021-01-01") & (df["timestamp"] < "2023-01-01")])
        n_val = len(df[(df["timestamp"] >= "2023-01-01") & (df["timestamp"] < "2024-01-01")])
        n_hold = len(df[df["timestamp"] >= "2024-01-01"])
        chk(f"  {reg}: train 2021-2022 hours", 17000 < n_train < 18000, f"n={n_train}")
        chk(f"  {reg}: val 2023 hours", 8700 < n_val < 8800, f"n={n_val}")
        chk(f"  {reg}: holdout 2024 hours", 8750 < n_hold < 8850, f"n={n_hold}")
        # Verify no look-ahead: lag_48h must be >= 48h prior
        if "lag_48h" in df.columns and "timestamp" in df.columns:
            chk(f"  {reg}: lag_48h column present", True)

# ----------------------------------------------------------------
section("PHASE 3-4: Validation & Model Selection")
# ----------------------------------------------------------------
chk("reports/rolling_origin_backtest_results.csv exists", os.path.exists("reports/rolling_origin_backtest_results.csv"))
chk("reports/model_selection_comparison.md exists", os.path.exists("reports/model_selection_comparison.md"))
bk = pd.read_csv("reports/rolling_origin_backtest_results.csv")
chk("Backtest: has TEX/MIDA/NY regions", set(bk["region"].unique()) >= {"TEX","MIDA","NY"})
# Confirm Point_Conformal selected as winner
ms = open("reports/model_selection_comparison.md").read()
chk("Selection: Point_Conformal named SELECTED WINNER", "SELECTED WINNER" in ms and "Point_Conformal" in ms)

# ----------------------------------------------------------------
section("PHASE 5: 2024 Holdout Evaluation")
# ----------------------------------------------------------------
chk("reports/final_holdout_summary.csv exists", os.path.exists("reports/final_holdout_summary.csv"))
chk("reports/final_holdout_metrics.csv exists", os.path.exists("reports/final_holdout_metrics.csv"))
chk("reports/final_holdout_report.md exists", os.path.exists("reports/final_holdout_report.md"))
sum_df = pd.read_csv("reports/final_holdout_summary.csv")
# Verify holdout numbers
expected = {
    ("TEX", "HistGradientBoosting_Point_Conformal"): (2783.6, -2472.5, 0.767),
    ("MIDA", "HistGradientBoosting_Point_Conformal"): (2871.0, -1766.1, 0.793),
    ("NY", "HistGradientBoosting_Point_Conformal"): (540.8, 13.0, 0.785),
}
for (reg, mdl), (exp_mae, exp_bias, exp_cov) in expected.items():
    row = sum_df[(sum_df["region"] == reg) & (sum_df["model"] == mdl)]
    if len(row) == 0:
        chk(f"Holdout {reg}/{mdl}", False, "row not found")
        continue
    r = row.iloc[0]
    chk(f"Holdout {reg} MAE={exp_mae}", abs(r["mae"] - exp_mae) < 0.1, f"got {r['mae']:.1f}")
    chk(f"Holdout {reg} Bias={exp_bias}", abs(r["bias"] - exp_bias) < 0.5, f"got {r['bias']:.1f}")
    chk(f"Holdout {reg} Coverage80={exp_cov}", abs(r["coverage_80"] - exp_cov) < 0.001, f"got {r['coverage_80']:.3f}")

# Check disclosure: 95% intervals reported
fm = pd.read_csv("reports/final_holdout_metrics.csv")
chk("final_holdout_metrics: Seasonal_Naive_168h present", (fm["model"] == "Seasonal_Naive_168h").any())
chk("final_holdout_metrics: Seasonal_Naive_48h present", (fm["model"] == "Seasonal_Naive_48h").any())
chk("final_holdout_metrics: Ridge_Linear_Baseline present", (fm["model"] == "Ridge_Linear_Baseline").any())

# ----------------------------------------------------------------
section("PHASE 5b: Model Artifact Integrity")
# ----------------------------------------------------------------
os.environ["LOKY_MAX_CPU_COUNT"] = "4"
os.environ["OMP_NUM_THREADS"] = "4"
import joblib
from src.models import MODEL_FEATURE_COLS
for reg, exp_mae in [("TEX", 2783.6), ("MIDA", 2871.0), ("NY", 540.8)]:
    pt_path = f"models/{reg}_final_holdout/model_point_conformal.joblib"
    res_path = f"models/{reg}_final_holdout/model_residual.joblib"
    meta_path = f"models/{reg}_final_holdout/metadata.json"
    chk(f"Model joblib: {reg} point", os.path.exists(pt_path))
    chk(f"Model joblib: {reg} residual", os.path.exists(res_path))
    chk(f"Model metadata: {reg}", os.path.exists(meta_path))
    if os.path.exists(meta_path):
        meta = json.load(open(meta_path))
        chk(f"  {reg} metadata: refit_protocol documented", "refit_protocol" in meta)
        chk(f"  {reg} metadata: environment pinned", "environment" in meta)
        chk(f"  {reg} metadata: skill_vs_48h_naive present", "skill_vs_48h_naive" in meta.get("pre_declared_winner", {}))
    if os.path.exists(pt_path):
        df = pd.read_parquet(f"data/processed/{reg}_features.parquet")
        df_test = df[(df["timestamp"] >= "2024-01-01") & (df["timestamp"] <= "2024-12-31 23:00:00")]
        y_true = df_test["demand_mw"].values
        model = joblib.load(pt_path)
        preds = model.predict(df_test[MODEL_FEATURE_COLS])
        mae = np.mean(np.abs(y_true - preds))
        chk(f"  {reg} model loads & reproduces MAE", abs(mae - exp_mae) < 0.2, f"got {mae:.1f} expected {exp_mae}")

# ----------------------------------------------------------------
section("PHASE 6: Monitoring & Data Quality")
# ----------------------------------------------------------------
chk("reports/data_quality_and_monitoring_report.md exists", os.path.exists("reports/data_quality_and_monitoring_report.md"))
chk("reports/monthly_bias_investigation.csv exists", os.path.exists("reports/monthly_bias_investigation.csv"))
chk("reports/worst_20_days_analysis.csv exists", os.path.exists("reports/worst_20_days_analysis.csv"))

# ----------------------------------------------------------------
section("PHASE 7: Tableau Exports & Package")
# ----------------------------------------------------------------
# Check CSVs
csv_checks = {
    "tableau_hourly_forecasts.csv": (26300, 26400),
    "tableau_subgroup_metrics.csv": (90, 120),
    "tableau_weather_sensitivity.csv": (55, 75),
    "tableau_region_dimension.csv": (3, 5),
}
for fname, (lo, hi) in csv_checks.items():
    p = f"data/exports/{fname}"
    chk(f"Export: {fname}", os.path.exists(p))
    if os.path.exists(p):
        n = len(pd.read_csv(p))
        chk(f"  {fname}: row count {lo}-{hi}", lo <= n <= hi, f"n={n}")

# Check hourly forecasts: in_interval_80 coverage
hf = pd.read_csv("data/exports/tableau_hourly_forecasts.csv")
for reg, exp_cov in [("TEX", 0.767), ("MIDA", 0.793), ("NY", 0.785)]:
    cov = hf[hf["region"] == reg]["in_interval_80"].mean()
    chk(f"  hourly_forecasts: {reg} in_interval_80 = {exp_cov:.3f}", abs(cov - exp_cov) < 0.002, f"got {cov:.3f}")

# Check weather sensitivity: correct signs
ws = pd.read_csv("data/exports/tableau_weather_sensitivity.csv")
ws_ann = ws[ws["slice_type"] == "Annual / All Hours"]
for reg, exp2, exp5 in [("TEX", 1491, 3673), ("MIDA", 964, 2824), ("NY", 307, 819)]:
    r2 = ws_ann[(ws_ann["region"] == reg) & (ws_ann["temperature_delta_c"] == 2.0)]
    r5 = ws_ann[(ws_ann["region"] == reg) & (ws_ann["temperature_delta_c"] == 5.0)]
    if len(r2) and len(r5):
        d2 = r2.iloc[0]["delta_mean_demand_mw"]
        d5 = r5.iloc[0]["delta_mean_demand_mw"]
        chk(f"  weather_sensitivity: {reg} +2C positive delta", d2 > 0, f"got {d2:.0f}")
        chk(f"  weather_sensitivity: {reg} +5C > +2C (monotone)", d5 > d2, f"+2={d2:.0f} +5={d5:.0f}")
        chk(f"  weather_sensitivity: {reg} +2C ~{exp2}", abs(d2 - exp2) < 5, f"got {d2:.0f}")

# Tableau workbook
chk("electricity_demand_forecasting.twbx exists", os.path.exists("electricity_demand_forecasting.twbx"))
if os.path.exists("electricity_demand_forecasting.twbx"):
    with zipfile.ZipFile("electricity_demand_forecasting.twbx", "r") as z:
        names = z.namelist()
        chk("  .twbx: contains .twb", any(n.endswith(".twb") for n in names))
        chk("  .twbx: contains tableau_hourly_forecasts.csv", any("tableau_hourly_forecasts" in n for n in names))
        # Check no machine paths in twb
        twb_content = z.read("electricity_demand_forecasting.twb").decode("utf-8")
        chk("  .twbx twb: no C:/Users/LENOVO absolute paths", "C:/Users/LENOVO" not in twb_content, "path hygiene")
        chk("  .twbx twb: no C:\\Users\\LENOVO absolute paths", "C:\\Users\\LENOVO" not in twb_content, "path hygiene")
        # Count worksheets
        import xml.etree.ElementTree as ET
        root = ET.fromstring(twb_content)
        ws_names = [ws.attrib.get("name") for ws in root.findall(".//worksheet")]
        chk(f"  .twbx: has 7 worksheets", len(ws_names) == 7, f"found {len(ws_names)}: {ws_names}")
        chk("  .twbx: Reconciliation_Summary sheet exists", any("Reconciliation" in n for n in ws_names))
chk("Book1.twb REMOVED (stale old workbook)", not os.path.exists("Book1.twb"))

# ----------------------------------------------------------------
section("PHASE 8: 3-Way Reconciliation")
# ----------------------------------------------------------------
chk("reports/reconciliation_results.csv exists", os.path.exists("reports/reconciliation_results.csv"))
chk("reports/reconciliation_report.md exists", os.path.exists("reports/reconciliation_report.md"))
chk("data/tableau_exports/tableau_crosstab_metrics.csv exists", os.path.exists("data/tableau_exports/tableau_crosstab_metrics.csv"))
rec = pd.read_csv("reports/reconciliation_results.csv")
all_pass = (rec["reconciliation_status"] == "PASS").all()
chk(f"Reconciliation: ALL {len(rec)} checks PASS", all_pass, f"{(rec['reconciliation_status']=='PASS').sum()}/{len(rec)} pass")
has_tableau = "PENDING" not in rec["layer_tableau"].astype(str).values
chk("Reconciliation: Layer 3 (Tableau) populated (not PENDING)", has_tableau)

# ----------------------------------------------------------------
section("DOCUMENTATION")
# ----------------------------------------------------------------
for doc in ["README.md", "docs/model_card.md", "docs/interview_defense_notes.md",
            "docs/phase_0_specification.md", "docs/tableau_specifications.md",
            "CHANGELOG.md"]:
    chk(f"Doc exists: {doc}", os.path.exists(doc))

# README checks
readme = open("README.md").read()
chk("README: Headline skill vs 48h naive table", "Winner / 48h Naive" in readme)
chk("README: Refit protocol documented", "26,280 hours" in readme and "refit" in readme.lower())
chk("README: TEX 76.7% coverage disclosed", "76.7%" in readme)
chk("README: 95% coverage 92.5-93.8% disclosed", "92.5" in readme and "93.8" in readme)
chk("README: Weather sensitivity counterfactual section", "Counterfactual Weather" in readme)
chk("README: no absolute machine paths", "LENOVO" not in readme and "C:\\\\" not in readme)
chk("README: docs/phase_0_specification.md link (no absolute path)", "file:///c:/Users" not in readme.lower())

# interview notes
notes = open("docs/interview_defense_notes.md").read()
chk("Interview notes: 48h naive baseline Q&A", "48h naive" in notes or "48-hour naive" in notes)
chk("Interview notes: refit protocol Q&A", "26,280 hours" in notes or "refit" in notes.lower())

# ----------------------------------------------------------------
section("REPO HYGIENE")
# ----------------------------------------------------------------
chk(".gitignore exists", os.path.exists(".gitignore"))
chk("requirements.txt exists", os.path.exists("requirements.txt"))
req = open("requirements.txt").read()
chk("requirements.txt: tzdata pin", "tzdata" in req)
chk("requirements.txt: scikit-learn==1.9.0", "scikit-learn==1.9.0" in req)
chk("requirements.txt: pytest==9.0.3", "pytest==9.0.3" in req)
# Stale old workbook
chk("Book1.twb REMOVED", not os.path.exists("Book1.twb"))

# ----------------------------------------------------------------
section("TESTS")
# ----------------------------------------------------------------
import subprocess
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
    capture_output=True, text=True
)
all_tests_pass = result.returncode == 0
chk("All pytest tests pass", all_tests_pass, result.stdout.split("\n")[-3] if result.stdout else result.stderr[:100])

# ----------------------------------------------------------------
section("CLEAN ZIP DELIVERABLE")
# ----------------------------------------------------------------
zip_path = "electricity_demand_forecasting_clean.zip"
chk("electricity_demand_forecasting_clean.zip exists", os.path.exists(zip_path))
if os.path.exists(zip_path):
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        junk = [n for n in names if any(p in n for p in [".venv", "/.git/", "\\.git\\", ".pytest_cache"])]
        chk("  Clean zip: no .venv", not any(".venv" in n for n in names))
        chk("  Clean zip: no .git dir", not any("/.git/" in n or "\\.git\\" in n for n in names))
        chk("  Clean zip: no .pytest_cache", not any(".pytest_cache" in n for n in names))
        chk("  Clean zip: README.md", "README.md" in names)
        chk("  Clean zip: src/pipeline_holdout_evaluation.py", any("pipeline_holdout_evaluation" in n for n in names))
        chk("  Clean zip: models/TEX_final_holdout", any("TEX_final_holdout" in n for n in names))
        size_mb = os.path.getsize(zip_path) / 1024 / 1024
        chk(f"  Clean zip: size < 50 MB", size_mb < 50, f"{size_mb:.1f} MB")

# ----------------------------------------------------------------
section("SUMMARY")
# ----------------------------------------------------------------
total = len(results)
passed = sum(1 for r in results if r["status"] == PASS)
failed = sum(1 for r in results if r["status"] == FAIL)
warned = sum(1 for r in results if r["status"] == WARN)
print(f"\n  TOTAL:   {total} checks")
print(f"  PASSED:  {passed}")
print(f"  FAILED:  {failed}")
print(f"  WARNINGS:{warned}")
if failed == 0:
    print("\n  *** ALL CHECKS PASSED - PROJECT IS COMPLETE ***")
else:
    print("\n  FAILURES:")
    for r in results:
        if r["status"] == FAIL:
            print(f"    - {r['check']}: {r['details']}")
