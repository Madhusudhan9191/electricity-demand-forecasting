# Phase 8: Multi-Layer Three-Way Metric Reconciliation Report

**Verification Summary:** 9/9 checks strictly **PASSED** (3-Way: Python Pipeline vs. SQLite Engine vs. Tableau Desktop UI).

### Scope & Methodology Disclosure
- **Model Scope:** Reconciled metrics strictly reflect the pre-declared model selection winner (`HistGradientBoosting_Point_Conformal`) evaluated across the entire Calendar 2024 single-touch holdout (8,784 hourly timestamps per region).
- **Metric Scope:** Covers the 3 core operational evaluation metrics: Mean Absolute Error (MAE in MW), Mean Error / Directional Bias (MW), and 80% Empirical Prediction Interval Coverage.
- **Rounding Tolerances:**
  - **MW Metrics (MAE & Bias):** Tableau Desktop UI displays whole-number integers (e.g. TEX MAE `2,784` vs Python `2,783.6`, NY MAE `541` vs Python `540.8`, TEX Bias `-2,472` vs Python `-2,472.5`, MIDA Bias `-1,766` vs Python `-1,766.1`). Allowed rounding tolerance is $|\text{Python} - \text{Tableau}| \le 0.5\text{ MW}$.
  - **Coverage Metric (80% Interval):** Tableau Desktop UI displays percentages formatted to one decimal place (e.g., `79.3%` $\to 0.793$, `78.5%` $\to 0.785$, `76.7%` $\to 0.767$). Allowed rounding tolerance is $|\text{Python} - \text{Tableau}| \le 0.001$ (0.1 percentage point).
  - **Python vs. SQL Engine:** Evaluated on full-precision floating point numbers. Allowed tolerance is $|\text{Python} - \text{SQL}| < 10^{-3}$.

### Three-Way Reconciliation Grid

| Region | Metric | Python Pipeline | SQL Engine (SQLite) | Tableau UI Export | Diff (Py - SQL) | Diff (Py - Tableau) | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **MIDA** | MAE | `2871.0` | `2871.0` | `2871.0` | `0.000000` | `0.000` | **PASS** |
| **MIDA** | Bias (ME) | `-1766.1` | `-1766.1` | `-1766.0` | `0.000000` | `0.100` | **PASS** |
| **MIDA** | Coverage_80 | `0.793` | `0.793` | `0.793` | `0.000000` | `0.000` | **PASS** |
| **NY** | MAE | `540.8` | `540.8` | `541.0` | `0.000000` | `0.200` | **PASS** |
| **NY** | Bias (ME) | `13.0` | `13.0` | `13.0` | `0.000000` | `0.000` | **PASS** |
| **NY** | Coverage_80 | `0.785` | `0.785` | `0.785` | `0.000000` | `0.000` | **PASS** |
| **TEX** | MAE | `2783.6` | `2783.6` | `2784.0` | `0.000000` | `0.400` | **PASS** |
| **TEX** | Bias (ME) | `-2472.5` | `-2472.5` | `-2472.0` | `0.000000` | `0.500` | **PASS** |
| **TEX** | Coverage_80 | `0.767` | `0.767` | `0.767` | `0.000000` | `0.000` | **PASS** |

---
