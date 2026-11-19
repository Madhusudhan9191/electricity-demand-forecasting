# Phase 8: Three-Way Metric Reconciliation Report

Cross-engine reconciliation comparing:
1. **Layer 1 (Python Pipelines):** Evaluated via Scikit-Learn and NumPy arrays.
2. **Layer 2 (Independent SQL Engine):** Computed via SQLite queries on exported Tableau CSV.
3. **Layer 3 (Tableau Workbooks):** Exported crosstabs from user workbook.

> **Strict Protocol:** If Tableau exports are missing, Layer 3 is designated **PENDING**; Python numbers are NEVER substituted.

## Reconciliation Table

| Region | Metric | Layer 1: Python | Layer 2: SQL Engine | SQL Absolute Diff | SQL Validation | Layer 3: Tableau Public | Tableau Validation |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **ERCOT** | MAE (MW) | 3330.3 | 3330.3 | 0.0 | **PASS** | PENDING | `PENDING (Awaiting User Tableau Crosstab Export)` |
| **ERCOT** | RMSE (MW) | 4152.53 | 4152.53 | 0.0 | **PASS** | PENDING | `PENDING (Awaiting User Tableau Crosstab Export)` |
| **ERCOT** | 80% Coverage | 0.3007 | 0.3007 | 0.0 | **PASS** | PENDING | `PENDING (Awaiting User Tableau Crosstab Export)` |
| **PJM** | MAE (MW) | 3396.3 | 3396.3 | 0.0 | **PASS** | PENDING | `PENDING (Awaiting User Tableau Crosstab Export)` |
| **PJM** | RMSE (MW) | 4660.07 | 4660.07 | 0.0 | **PASS** | PENDING | `PENDING (Awaiting User Tableau Crosstab Export)` |
| **PJM** | 80% Coverage | 0.5641 | 0.5641 | 0.0 | **PASS** | PENDING | `PENDING (Awaiting User Tableau Crosstab Export)` |
| **NYIS** | MAE (MW) | 614.64 | 614.64 | 0.0 | **PASS** | PENDING | `PENDING (Awaiting User Tableau Crosstab Export)` |
| **NYIS** | RMSE (MW) | 839.83 | 839.83 | 0.0 | **PASS** | PENDING | `PENDING (Awaiting User Tableau Crosstab Export)` |
| **NYIS** | 80% Coverage | 0.5389 | 0.5389 | 0.0 | **PASS** | PENDING | `PENDING (Awaiting User Tableau Crosstab Export)` |

---

### Reconciliation Summary
- **SQL vs Python Reconciliation:** 9/9 assertions **PASSED** (Tolerance $\le 0.01$ MW / $0.0001$ coverage).
- **Tableau Layer Status:** Currently **PENDING**. Place exported crosstab at `data/tableau_exports/tableau_crosstab_metrics.csv` to reconcile Layer 3.
