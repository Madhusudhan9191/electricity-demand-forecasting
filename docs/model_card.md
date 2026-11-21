# Model Card: Day-Ahead Multi-Region Electricity Demand Forecasting with Uncertainty

## 1. Model Details
- **Evaluated Models:**
  1. `HistGradientBoosting_Point_Conformal` (Pre-declared selection winner from Calendar 2023 rolling validation)
  2. `HistGradientBoosting_Residual` (Level-anchored model targeting $\Delta_t = y_t - y_{t-168}$ to reduce tree extrapolation bias)
- **Version:** 0.3.1
- **Model Type:** Gradient Boosted Decision Trees (`HistGradientBoostingRegressor` via Scikit-Learn) with Rolling Conformal Prediction Intervals.
- **Primary Optimization Objective:**
  - `Point_Conformal`: Squared error loss on raw demand level ($y_t$), paired with trailing empirical non-conformity quantiles.
  - `Residual`: Squared error loss on seasonal delta ($\Delta_t = y_t - y_{t-168}$), anchored to trailing weekly demand ($y_{t-168}$).
- **Developer Context:** Independent offline portfolio project (Day-Ahead Multi-Region Forecasting with Uncertainty).
- **Date:** November 2026.
- **License:** MIT / CC-BY 4.0.
- **Dataset Attribution:** Ruggles et al. (*Nature Scientific Data*, 2020), Cleaned EIA-930 Regional Footprints (`TEX`, `MIDA`, `NY`).

---

## 2. Intended Use & Scope Boundaries
- **Primary Intended Use:** Educational and portfolio demonstration of point-in-time feature engineering, machine learning baselining, calibrated prediction intervals, and dashboard specification.
- **Simulated Stakeholder Personas:**
  - *Planning Analyst (Simulated):* Multi-day reserve capacity buffer assessment and tail risk evaluation.
  - *Operations Analyst (Simulated):* Day-ahead hourly schedule alignment and season-specific peak error minimization.
- **Explicit Out-of-Scope Uses:**
  - **NOT** an operational power system dispatch or market clearing tool.
  - **NOT** for real-time frequency regulation or automatic generation control (AGC).
  - **NO Causal Inferences:** Forecast changes and weather sensitivity scenarios represent observational statistical associations, not physical counterfactuals.

---

## 3. Data & Split Architecture
- **Training Window:** `2021-01-01` to `2022-12-31` (17,520 hours).
- **Validation Window:** Calendar 2023 (`2023-01-01` to `2023-12-31`, 8,760 hours across 4 seasonal expanding folds).
- **Refit Protocol:** Final models were refit on combined train + validation (`2021-01-01` to `2023-12-31`, 26,280 hours) prior to evaluating on the single-touch 2024 holdout.
- **Single-Touch Holdout:** Calendar 2024 (`2024-01-01` to `2024-12-31`, 8,784 hours, leap year).
- **Environment & Pinned Libraries:** Python 3.11.4, `scikit-learn==1.9.0`, `joblib==1.5.3`, `pandas==2.3.3`, `numpy==1.26.4`, `scipy==1.17.1`, `duckdb==1.5.4`.
- **Imputation Tracking:** 1.84% (TEX), 2.93% (MIDA), 1.99% (NY) of hours imputed in source EIA-930 data; model evaluated separately on non-imputed hours.

---

## 4. Evaluated Metrics (Calendar 2024 Holdout)

### Skill vs. Best Available Baselines
| Region | Winner MAE | 48h Naive MAE | Winner / 48h Naive | Ridge Baseline MAE | Winner / Ridge | 168h Naive MAE | Winner / 168h Naive (rMAE) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TEX** | **2,783.6 MW** | 3,478.5 MW | **0.800** (+20.0% skill) | 3,167.3 MW | **0.879** (+12.1% skill) | 4,476.0 MW | **0.622** (+37.8% skill) |
| **MIDA** | **2,871.0 MW** | 7,299.2 MW | **0.393** (+60.7% skill) | 4,160.5 MW | **0.690** (+31.0% skill) | 8,854.4 MW | **0.324** (+67.6% skill) |
| **NY** | **540.8 MW** | 1,314.7 MW | **0.411** (+58.9% skill) | 940.2 MW | **0.575** (+42.5% skill) | 1,524.1 MW | **0.355** (+64.5% skill) |

### Model 1: `HistGradientBoosting_Point_Conformal` (Pre-declared Winner)
- **TEX (Texas footprint):** MAE = 2,783.6 MW [95% CI: 2,599.9, 2,984.1], rMAE = 0.622, Bias = -2,472.5 MW, 80% Coverage = 76.7%, 95% Coverage = 93.1%.
- **MIDA (Mid-Atlantic footprint):** MAE = 2,871.0 MW [95% CI: 2,695.4, 3,067.8], rMAE = 0.324, Bias = -1,766.1 MW, 80% Coverage = 79.3%, 95% Coverage = 93.2%.
- **NY (New York footprint):** MAE = 540.8 MW [95% CI: 516.0, 568.6], rMAE = 0.355, Bias = +13.0 MW, 80% Coverage = 78.5%, 95% Coverage = 93.8%.

### Model 2: `HistGradientBoosting_Residual` (Level-Anchored Model)
- **TEX (Texas footprint):** MAE = 2,758.6 MW [95% CI: 2,577.2, 2,954.9], rMAE = 0.616, Bias = -2,224.2 MW, 80% Coverage = 78.4%, 95% Coverage = 93.1%.
- **MIDA (Mid-Atlantic footprint):** MAE = 3,255.9 MW [95% CI: 3,026.9, 3,530.7], rMAE = 0.368, Bias = -1,649.1 MW, 80% Coverage = 78.3%, 95% Coverage = 92.5%.
- **NY (New York footprint):** MAE = 604.7 MW [95% CI: 575.7, 639.5], rMAE = 0.397, Bias = -26.8 MW, 80% Coverage = 78.5%, 95% Coverage = 93.3%.

---

## 5. Documented Limitations & Calibration Notes
1. **Weather Forecast Optimistic Lower Bound:** Uses ERA5 reanalysis weather as an idealized proxy for day-ahead numerical weather predictions.
2. **Distribution Drift & Persistent Bias:** In high-growth regions like Texas (mean load grew 44.8 GW to 52.9 GW), tree models suffer from negative bias. The residual formulation reduced this bias by ~248 MW, but persistent under-forecasting remains.
3. **95% Interval Coverage Caveat:** While 80% intervals are well-calibrated (76.7% to 79.3%), 95% intervals achieve 92.5% to 93.8% coverage, slightly under-covering in extreme peak hours.
4. **Imputation:** Historical reporting dropouts in EIA-930 were imputed by Ruggles et al.; non-imputed hour accuracy matches full holdout within 0.003 rMAE.
