# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

## [0.3.1] - 2026-11-20

### Dual-Model Holdout Reporting & Clean Verification
- **Dual-Model Holdout Evaluation & Single-Touch Disclosure:**
  - Evaluated the pre-declared selection winner (`HistGradientBoosting_Point_Conformal`, GM rMAE 0.457) on the 2024 holdout alongside `HistGradientBoosting_Residual`.
  - Disclosed that the 2024 holdout was first evaluated with the Residual model (introduced post-hoc to mitigate tree extrapolation), and reported both models side-by-side without selecting between them using holdout data.
  - Reported results across all regions: Point Conformal achieved superior accuracy in MIDA (rMAE 0.324 vs 0.368) and NY (rMAE 0.355 vs 0.397) while being competitive in TEX (rMAE 0.622 vs 0.616).
- **Honest Uncertainty & Bias Reporting:**
  - Clarified interval calibration: while 80% intervals are well-calibrated (76.7% to 79.3%), 95% intervals slightly under-cover (92.5% to 93.8%) in extreme peak tail hours.
  - Clarified Texas bias: the residual model reduced annual negative bias by ~248 MW (from -2,472.5 MW to -2,224.2 MW), but persistent under-forecasting remains across all months due to continuous multi-year load growth outstripping 7-day levels.
- **Repository Hygiene & Artifact Alignment:**
  - Added `tzdata>=2024.1` to `requirements.txt` for clean cross-platform timezone resolution in fresh virtual environments.
  - Generated active model artifacts in `models/TEX_final_holdout/`, `models/MIDA_final_holdout/`, and `models/NY_final_holdout/`.
  - Deleted all stale `ERCOT_*`, `PJM_*`, and `NYIS_*` raw demand, weather, processed parquet, and model artifact files.
  - Regenerated `data/raw/data_manifest.json` with SHA-256 hashes for the 6 active files only.
  - Regenerated `data/exports/tableau_subgroup_metrics.csv` and `data/exports/tableau_weather_sensitivity.csv` for TEX, MIDA, and NY on Calendar 2024.
  - Removed `Book1.twb` and verified zero occurrences of absolute paths across all documentation, code, and config files.
  - Exported `reports/holdout_reconciliation_crosstab.csv` to allow straightforward Tableau layer verification.

## [0.3.0] - 2026-11-19

### Critical Scientific Corrections & Re-Execution
- **Timeline Reset & Single-Touch Holdout Restoration:**
  - **Train:** `2021-01-01` to `2022-12-31` (24 months, 17,520 hours per region).
  - **Validation:** Calendar 2023 (`2023-01-01` to `2023-12-31`, 8,760 hours per region) across 4 seasonal expanding folds. *Audit Note: 2023 was previously inspected during exploratory prototyping and is now formally assigned to model validation and hyperparameter selection.*
  - **Single-Touch Holdout:** Calendar 2024 (`2024-01-01` to `2024-12-31`, 8,784 hours per region, leap year), strictly quarantined and touched only once for the final post-selection evaluation.
- **Academic Attribution & Region Relabeling:**
  - Relabeled balancing authority acronyms to formal EIA regional aggregates: `TEX` (Texas footprint), `MIDA` (Mid-Atlantic footprint), and `NY` (New York footprint).
  - Cited underlying benchmark repository: Ruggles et al. (*Nature Scientific Data*, 2020), published under CC-BY 4.0.
  - Implemented dual evaluation on all hours vs. non-imputed hours (`raw demand == cleaned demand`) to account for the 1.08% to 2.39% imputation rates in the Ruggles cleaned demand dataset.
- **Selection Rule & Calibrated Conformal Intervals:**
  - Programmatically enforced the pre-declared model selection rule requiring validation interval coverage within $[77\%, 83\%]$.
  - Replaced static in-sample conformal bounds with **Rolling Conformal Prediction** computed over the most recent 14-day residuals known at origin ($\ge 48$h lag) to dynamically adjust interval widths to local grid volatility and load drift.
- **Tree Extrapolation Fix (Relative Residual Modeling):**
  - Diagnosed structural failure of tree models in growing load regimes (negative bias across all months in ERCOT/TEX as mean load grew from 49.2 GW to 52.9 GW).
  - Added `HistGradientBoosting_Residual` candidate modeling demand relative to the known seasonal anchor ($\Delta_t = y_t - y_{t-168}$), guaranteeing proper scale tracking across multi-year trend shifts.
- **Baseline Fixes & Metrics Standardization:**
  - Resolved `Seasonal_MA_4Week` fallback bug: implemented exact multi-week lag average ($\frac{1}{4}\sum_{w=1}^4 y_{t-168w}$).
  - Added Exponential Smoothing / Holt-Winters ETS seasonal baseline.
  - Standardized MASE definition using in-sample seasonal naive mean absolute scaling factor ($\frac{1}{N-168}\sum |y_t - y_{t-168}|$) and relative MAE ($\text{rMAE} = \frac{\text{MAE}_{\text{model}}}{\text{MAE}_{\text{base168}}}$) with Geometric-Mean cross-region aggregation.
- **Population-Weighted Multi-City Weather:**
  - Ingested multi-city hourly ERA5 weather for TEX (DFW 45%, Houston 40%, Austin/San Antonio 15%), MIDA (Chicago 35%, Philly 25%, DC 25%, Columbus 15%), and NY (NYC 70%, Upstate 30%).
- **Automated Report Generation & Repo Hygiene:**
  - Automated all README and report metric tables directly from generated CSVs.
  - Removed local virtual environment cache, temporary artifacts, and absolute local paths.

## [0.2.0] - 2026-11-19
- Initial Phase 0 revision draft.

## [0.1.0] - 2026-11-18
- Initial project formulation and exploratory pipeline.
