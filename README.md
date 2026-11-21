# Day-Ahead Multi-Region Electricity Demand Forecasting with Uncertainty

An offline observational machine learning and uncertainty calibration system for day-ahead hourly regional electricity load forecasting across three major US grid footprints: **TEX** (Texas footprint), **MIDA** (Mid-Atlantic footprint), and **NY** (New York footprint).

---

## 1. Project Overview & Scientific Dataset Attribution

- **Primary Question:** *Can we forecast next-day hourly regional electricity demand better than 168-hour seasonal naive baselines, and calibrate prediction intervals to maintain empirical coverage under structural load growth and weather extremes?*
- **Demand Dataset Attribution:** Ruggles et al. (*Nature Scientific Data*, 2020), *"An open-access hourly electricity consumption dataset for the United States"*, licensed under CC BY 4.0. Cleaned EIA-930 regional aggregates with audited imputation tracking.
- **Weather Dataset Attribution:** Open-Meteo Historical Weather API (ERA5 reanalysis and national weather services), licensed under CC BY 4.0. Population-weighted multi-city hourly ambient temperature, wind speed, solar irradiance, and relative humidity.
- **Point-in-Time Constraint:** Strict forecast origin at **10:00 AM Local Standard Time on Day $D-1$**. Horizon: **Day $D$ (24 hourly steps)**. All demand lag features are strictly $\ge 48$ hours prior to guarantee zero look-ahead bias.
- **Scientific Re-Split:**
  - **Training:** `2021-01-01` to `2022-12-31` (17,520 hours).
  - **Validation:** Calendar 2023 (`2023-01-01` to `2023-12-31`, 8,760 hours across 4 expanding seasonal folds).
  - **Single-Touch Holdout:** Calendar 2024 (`2024-01-01` to `2024-12-31`, 8,784 hours, leap year).
  - **Refit Protocol:** Final holdout models were refit on combined train + validation (`2021-01-01` to `2023-12-31`, 26,280 hours) prior to evaluating on the 2024 holdout.

---

## 2. Model Selection & Dual Holdout Leaderboard (Calendar 2024)

### Model Selection Rule & Protocol Disclosure
Under the pre-declared decision rule from Phase 0 / Phase 4, **`HistGradientBoosting_Point_Conformal`** was the numeric **SELECTED WINNER** (GM rMAE = 0.457, 80% validation coverage = 78.7%). 

In an earlier iteration, the holdout was evaluated using `HistGradientBoosting_Residual` (rank 2, GM rMAE = 0.487), which was developed after the 2023 Texas bias analysis to address tree extrapolation failure in trending grids. Because Calendar 2024 had already been inspected with the Residual model, we report **BOTH models side-by-side** below. We do not select between them post-hoc using the holdout.

### Headline Skill vs. Best Available Baselines
While skill is conventionally reported against the 168-hour seasonal naive baseline ($y_{t-168}$), the 48-hour naive forecast ($y_{t-48}$) and a regularized linear model (`RidgeLinearBaseline`) are valid at our 10:00 AM Day $D-1$ forecast origin and represent substantially stronger benchmarks:

| Region | Winner MAE (MW) | 48h Naive MAE (MW) | Winner / 48h Naive | Ridge Baseline MAE (MW) | Winner / Ridge | 168h Naive MAE (MW) | Winner / 168h Naive (rMAE) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TEX** | **2,783.6** | 3,478.5 | **0.800** (+20.0% skill) | 3,167.3 | **0.879** (+12.1% skill) | 4,476.0 | **0.622** (+37.8% skill) |
| **MIDA** | **2,871.0** | 7,299.2 | **0.393** (+60.7% skill) | 4,160.5 | **0.690** (+31.0% skill) | 8,854.4 | **0.324** (+67.6% skill) |
| **NY** | **540.8** | 1,314.7 | **0.411** (+58.9% skill) | 940.2 | **0.575** (+42.5% skill) | 1,524.1 | **0.355** (+64.5% skill) |

*Texas displays a narrower skill margin (+20.0% over 48h naive, +12.1% over Ridge) due to rapid structural load growth that trailing autoregressive levels track more effectively than stationary tree cuts.*

### Full Holdout Evaluation Table
All numbers below are generated programmatically from `reports/final_holdout_summary.csv` and `reports/final_holdout_metrics.csv`.

| Region | Model | Role | Holdout MAE (MW) | 95% Bootstrap CI | Baseline 168h MAE (MW) | rMAE | 80% Coverage | 95% Coverage | Bias (MW) | Non-Imputed rMAE | Imputed Pct |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TEX** | `HistGradientBoosting_Point_Conformal` | Pre-declared Validation Winner | **2,783.6** | [2,599.9, 2,984.1] | 4,476.0 | **0.622** | **76.7%** | 93.1% | -2,472.5 | **0.621** | 1.84% |
| **TEX** | `HistGradientBoosting_Residual` | Level-Anchored Comparison Model | **2,758.6** | [2,577.2, 2,954.9] | 4,476.0 | **0.616** | **78.4%** | 93.1% | -2,224.2 | **0.617** | 1.84% |
| **MIDA** | `HistGradientBoosting_Point_Conformal` | Pre-declared Validation Winner | **2,871.0** | [2,695.4, 3,067.8] | 8,854.4 | **0.324** | **79.3%** | 93.2% | -1,766.1 | **0.328** | 2.93% |
| **MIDA** | `HistGradientBoosting_Residual` | Level-Anchored Comparison Model | **3,255.9** | [3,026.9, 3,530.7] | 8,854.4 | **0.368** | **78.3%** | 92.5% | -1,649.1 | **0.371** | 2.93% |
| **NY** | `HistGradientBoosting_Point_Conformal` | Pre-declared Validation Winner | **540.8** | [516.0, 568.6] | 1,524.1 | **0.355** | **78.5%** | 93.8% | +13.0 | **0.355** | 1.99% |
| **NY** | `HistGradientBoosting_Residual` | Level-Anchored Comparison Model | **604.7** | [575.7, 639.5] | 1,524.1 | **0.397** | **78.5%** | 93.3% | -26.8 | **0.397** | 1.99% |

*rMAE = Relative MAE vs 168h seasonal naive ($	ext{rMAE} < 1.0$ indicates model superiority).*

### Interval Calibration Limits
- **80% Nominal Prediction Intervals:** Calibrated via Rolling Conformal Prediction. MIDA (79.3%) and NY (78.5%) fall squarely in the nominal [77%, 83%] validation band. Texas pre-declared winner achieves **76.7%**, just below the nominal 77% lower boundary, reflecting persistent uncaptured upward load drift.
- **95% Nominal Prediction Intervals:** Empirically achieve **92.5% to 93.8%** coverage. While far superior to raw uncalibrated quantiles, they modestly under-cover the nominal 95% target during winter freeze peaks and summer record heat events.

---

## 3. Structural Findings: Tree Extrapolation & Texas (TEX) Bias

Decision trees and gradient boosting models are piecewise-constant estimators bounded by the target extremes observed in training data. When annual regional demand in Texas grew from 44.8 GW (2021) to 49.2 GW (2022) to 51.0 GW (2023) and 52.9 GW (2024), standard tree models suffered from persistent negative bias.

By formulating the forecasting problem relative to the known seasonal anchor ($\Delta_t = y_t - y_{t-168}$), `HistGradientBoosting_Residual` reduced the annual under-forecast bias in Texas from -2,472.5 MW (point model) to -2,224.2 MW (residual model). The bias was **reduced** by ~248 MW, though persistent negative bias remains across all months because demand growth outpaced even trailing 168h load levels:

| Month | TEX Actual Mean (MW) | Point Conformal Bias (MW) | Residual Model Bias (MW) | Point Model MAE (MW) | Residual Model MAE (MW) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 01 | 51,466.5 | -5,106.1 | **-4,526.1** | 5,337.8 | 4,897.4 |
| 02 | 44,197.5 | -1,054.8 | **-941.6** | 1,331.5 | 1,401.3 |
| 03 | 43,594.8 | -1,217.2 | **-1,022.8** | 1,396.2 | 1,304.9 |
| 04 | 46,726.0 | -1,789.3 | **-1,677.6** | 1,926.6 | 1,865.4 |
| 05 | 54,008.8 | -1,539.2 | **-1,242.8** | 2,217.7 | 2,365.9 |
| 06 | 62,032.5 | -2,804.8 | **-3,124.6** | 3,150.3 | 3,696.9 |
| 07 | 60,191.5 | -1,635.2 | **-1,183.1** | 2,967.9 | 3,218.8 |
| 08 | 66,575.6 | -3,293.2 | **-2,432.0** | 3,326.1 | 2,843.2 |
| 09 | 57,306.8 | -2,342.6 | **-2,379.2** | 2,668.1 | 2,742.2 |
| 10 | 53,186.3 | -3,060.0 | **-3,128.3** | 3,074.7 | 3,176.1 |
| 11 | 47,370.0 | -2,383.3 | **-2,177.4** | 2,527.8 | 2,578.8 |
| 12 | 47,414.0 | -3,332.7 | **-2,785.5** | 3,355.2 | 2,918.1 |

---


---

## 4. Counterfactual Weather Sensitivity & Stress Testing

To simulate the operational grid impact of climate extremes, we conduct a point-in-time counterfactual simulation shifting hourly observed temperatures by $\Delta T \in [+2^\circ	ext{C}, +5^\circ	ext{C}]$.

### Methodological Rule: Preventing Model Bias Leakage
Comparing counterfactual model predictions against *observed actual demand* leaks the model's structural bias into the estimated weather effect (e.g. creating the illusion that demand falls during warming in under-forecasted regions). Therefore, **all deltas are strictly evaluated relative to the model's own baseline forecast at $\Delta T = 0$**.

Furthermore, because annual averages aggregate opposite summer cooling and winter heating effects, we evaluate seasonal and diurnal segments independently:

| Region | Slice | Base Forecast (ΔT=0) | +2°C Warming (MW) | +2°C Delta (%) | +5°C Warming (MW) | +5°C Delta (%) | Nature of Estimate |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **TEX** | **Annual / All Hours** | 50,408.7 | +1,491.9 | **+2.96%** | +3,673.1 | **+7.29%** | Counterfactual model association |
| **TEX** | **Summer (Jun-Aug)** | 60,368.1 | +2,711.2 | **+4.49%** | +5,710.4 | **+9.46%** | Counterfactual model association |
| **TEX** | **Winter (Dec-Feb)** | 44,559.2 | -453.1 | **-1.02%** | -457.2 | **-1.03%** | Counterfactual model association |
| **MIDA** | **Annual / All Hours** | 89,654.5 | +964.7 | **+1.08%** | +2,824.4 | **+3.15%** | Counterfactual model association |
| **MIDA** | **Summer (Jun-Aug)** | 101,128.4 | +4,363.1 | **+4.31%** | +9,961.2 | **+9.85%** | Counterfactual model association |
| **MIDA** | **Winter (Dec-Feb)** | 94,151.3 | -2,210.4 | **-2.35%** | -4,993.1 | **-5.30%** | Counterfactual model association |
| **NY** | **Annual / All Hours** | 17,190.5 | +307.0 | **+1.79%** | +819.5 | **+4.77%** | Counterfactual model association |
| **NY** | **Summer (Jun-Aug)** | 20,138.2 | +1,097.4 | **+5.45%** | +2,506.1 | **+12.44%** | Counterfactual model association |
| **NY** | **Winter (Dec-Feb)** | 17,535.1 | -289.2 | **-1.65%** | -670.3 | **-3.82%** | Counterfactual model association |

- **Monotonicity Compliance:** During summer cooling peak hours ($M \in [6,7,8]$, $H \in [14\dots20]$), predicted demand increases monotonically ($\hat{y}_{+5} \ge \hat{y}_{+2} \ge \hat{y}_0$) across **100.0% of hours in TEX and MIDA**, and **99.64% of hours in NY**.
- **Important Disclosure:** These figures reflect an offline machine-learning sensitivity association (holding calendar and autoregressive lag anchors fixed) rather than a dynamic general-equilibrium simulation of real-world grid operations.

## 5. Repository Structure & Relative Paths

```text
├── config/
│   └── config.yaml                 # Formal configuration, footprints, split dates, and parameters
├── data/
│   ├── raw/                        # Raw EIA-930 cleaned CSVs and ERA5 weather JSONs
│   │   └── data_manifest.json      # Cryptographic SHA-256 integrity hashes
│   ├── processed/                  # Point-in-time engineered feature parquets
│   └── exports/                    # Flat extracts formatted for Tableau Desktop / Public
├── docs/
│   ├── phase_0_specification.md    # Formal signed-off engineering specification
│   ├── tableau_specifications.md   # Parameters, calculated fields, LODs, and dashboard guides
│   ├── model_card.md               # Model cards, audit boundaries, and limitations
│   └── interview_defense_notes.md  # Detailed interview defense and technical talking points
├── models/
│   ├── TEX_final_holdout/          # Serialized models and metadata for Texas
│   ├── MIDA_final_holdout/         # Serialized models and metadata for Mid-Atlantic
│   └── NY_final_holdout/           # Serialized models and metadata for New York
├── reports/
│   ├── model_selection_comparison.md # Backtest leaderboard across Calendar 2023 folds
│   ├── final_holdout_report.md       # Final single-touch evaluation on Calendar 2024
│   ├── final_holdout_metrics.csv     # Multi-model evaluation across all baselines
│   ├── holdout_reconciliation_crosstab.csv # Clean crosstab for Tableau reconciliation
│   └── reconciliation_report.md      # Python vs SQL SQLite 3-way reconciliation
├── src/
│   ├── baselines.py                # 168h naive, 48h naive, 4-week MA, ETS Holt-Winters
│   ├── features.py                 # Point-in-time safe lags (>=48h), multi-city weather, Fourier
│   ├── models.py                   # Residual gradient boosting & rolling conformal intervals
│   ├── pipeline_backtest.py        # Expanding-window 4-fold validation on Calendar 2023
│   ├── pipeline_holdout_evaluation.py # Single-touch holdout evaluation on Calendar 2024
│   └── reconciliation.py           # Independent SQL query verification
└── README.md
```

---

## 6. Reproduction Protocol

To reproduce the end-to-end pipeline from source data:

1. **Verify Integrity Manifest:**
   ```bash
   python src/verify_data_manifest.py
   ```
2. **Execute Data Audit (Phase 1):**
   ```bash
   python src/data_audit.py
   ```
3. **Generate Point-in-Time Features (Phase 2):**
   ```bash
   python src/process_all_features.py
   ```
4. **Execute 2023 Rolling-Origin Validation & Model Selection (Phases 3 & 4):**
   ```bash
   python src/pipeline_backtest.py
   ```
5. **Evaluate Single-Touch 2024 Holdout & Export Tableau Data (Phases 5 & 7):**
   ```bash
   python src/pipeline_holdout_evaluation.py
   python src/generate_tableau_package.py
   ```
6. **Verify Multi-Layer Reconciliation (Phase 8):**
   ```bash
   python src/reconciliation.py
   ```
