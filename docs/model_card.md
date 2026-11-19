# Model Card: Day-Ahead Electricity Demand Forecasting with Uncertainty

## 1. Model Details
- **Model Name:** HistGradientBoosting Point Regressor with Empirical Conformalized Prediction Intervals
- **Version:** 1.0.0
- **Model Type:** Gradient Boosted Decision Trees (`HistGradientBoostingRegressor` via Scikit-Learn)
- **Primary Optimization Objective:** Mean Squared Error (squared error loss) for conditional expectation, paired with empirical conformal residual quantiles for 80% and 95% nominal prediction intervals.
- **Developer Context:** Independent portfolio project (Project 4 of 4: Time-Series Forecasting & Uncertainty).
- **Date:** November 2026.
- **License:** MIT / CC-BY 4.0.

---

## 2. Intended Use & Scope Boundaries
- **Primary Intended Use:** Educational and portfolio demonstration of point-in-time time-series feature engineering, machine learning baselining, calibrated prediction intervals, and dashboard specification.
- **Simulated Stakeholder Personas:**
  - *Planning Analyst (Simulated):* Multi-day reserve capacity buffer assessment and tail risk evaluation.
  - *Operations Analyst (Simulated):* Day-ahead hourly schedule alignment and 14:00–20:00 peak error minimization.
- **Explicit Out-of-Scope Uses:**
  - **NOT** an operational power system dispatch or market clearing tool.
  - **NOT** for real-time frequency regulation or automatic generation control (AGC).
  - **NO Causal Inferences:** Forecast changes and weather sensitivity scenarios represent observational statistical correlations, not real-world causal mechanisms.

---

## 3. Data & Time Horizon
- **Electricity Demand Source:** U.S. Energy Information Administration (EIA) Form EIA-930 (Hourly Electric Grid Monitor), curated via the peer-reviewed Ruggles et al. (Nature Scientific Data 2020/2025) pipeline. U.S. Public Domain.
- **Weather Covariates Source:** Open-Meteo Historical Weather API based on ECMWF ERA5 Reanalysis. CC-BY 4.0.
- **Regions Evaluated:**
  - ERCOT (Texas – summer cooling peaking, extreme freeze vulnerability)
  - PJM (Mid-Atlantic/Midwest – largest dual-peaking US RTO)
  - NYIS (New York – urban density and upstate seasonal transitions)
- **Timing Architecture:**
  - Forecast Origin: Day $D-1$ at 10:00 AM Local Standard Time.
  - Forecast Horizon: 24 hours of Day $D$ (00:00 to 23:00).
  - Lead Time: 14 hours. Demand known strictly up to 09:00 $D-1$.
  - Lag constraint: Demand lag features require $\ge 48$ hours. Same-hour yesterday ($t-24$) is strictly forbidden.

---

## 4. Evaluation Splits & Methodology
- **Warmup & Initial Training:** 2021-01-01 to 2022-06-30 (18 months). (2020 excluded from primary training due to COVID commercial lockdown structural break).
- **Rolling-Origin Validation Folds ($K=4$):** 2022-07-01 to 2023-04-30 (10 months). Used for programmatic model selection.
- **Final Holdout Split (Test):** 2023-05-01 to 2023-12-31 (8 months = 5,880 hours per region). **Touched exactly ONCE.**

---

## 5. Quantitative Performance Summary (Holdout)

| Region | Model MASE [95% Block-Bootstrap CI] | Baseline 168h MASE | Skill Score (%) | Model MAE (MW) | Baseline MAE (MW) | Model RMSE (MW) | 80% Nom Coverage | 95% Nom Coverage |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ERCOT** | **0.729** [0.686, 0.778] | 0.884 | **+17.5%** | 3,330.3 | 4,034.8 | 4,496.2 | 0.301 | 0.506 |
| **PJM** | **0.419** [0.387, 0.452] | 0.831 | **+49.6%** | 3,396.3 | 6,732.4 | 4,535.8 | 0.564 | 0.769 |
| **NYIS** | **0.435** [0.407, 0.465] | 1.002 | **+56.6%** | 614.6 | 1,416.7 | 864.0 | 0.539 | 0.735 |

---

## 6. Key Limitations & Drift Warnings
1. **Weather Proxy Limitation:** Weather actuals (ERA5 reanalysis) serve as a proxy for operational day-ahead numerical weather predictions. In reality, weather forecast errors ($\sigma \approx 1.5^\circ\text{C}$) will introduce additional forecast variance.
2. **Structural Drift in Growing Grids (ERCOT):** ERCOT's 80% nominal coverage dropped to 0.301 in the holdout due to a massive, unprecedented Summer 2023 heatwave paired with rapid secular Texas load growth (+17.6% mean demand increase, PSI = 0.6293). Static prediction intervals trained on prior cooler years under-covered this tail regime.
3. **Correlation vs. Causation:** Heat index and degree day terms are correlated with clock time, solar irradiance, and seasonal patterns; feature importance must not be interpreted as physical causal levers.
