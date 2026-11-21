# Model Comparison & Selection Report (Rolling-Origin Validation Folds 2023)

**Pre-declared Decision Rule:** Minimize Geometric-Mean Relative MAE ($\text{rMAE}$) subject to empirical 80% coverage constraint in [0.77, 0.83].
**Rule Audit Status:** PASSED: Winner satisfies pre-declared 80% coverage constraint [0.77, 0.83]

### Model Leaderboard (Averaged Across 4 Folds and 3 Regions: TEX, MIDA, NY)

| Rank | Model | GM rMAE | Mean MASE | Mean MAE (MW) | Mean RMSE (MW) | Mean sMAPE (%) | Mean Bias (MW) | Peak MAE (MW) | 80% Coverage | 95% Coverage | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | `HistGradientBoosting_Point_Conformal` | **0.457** | 0.402 | 1,842.4 | 2,384.2 | 3.54% | -922.2 | 2,211.2 | 0.787 | 0.936 | **SELECTED WINNER** |
| 2 | `HistGradientBoosting_Residual` | **0.487** | 0.422 | 1,939.9 | 2,544.3 | 3.72% | -644.3 | 2,297.8 | 0.792 | 0.935 | Compliant |
| 3 | `Ensemble_Ridge_HGBResidual` | **0.521** | 0.449 | 2,034.2 | 2,620.4 | 4.00% | -758.7 | 2,227.9 | 0.792 | 0.935 | Compliant |
| 4 | `Ridge_Linear_Baseline` | **0.662** | 0.566 | 2,533.7 | 3,217.4 | 5.10% | -856.1 | 2,561.8 | 0.965 | 0.998 | Non-compliant (96.5%) |
| 5 | `Seasonal_Naive_48h` | **0.953** | 0.817 | 3,813.2 | 5,006.2 | 7.24% | -20.6 | 4,240.4 | 0.866 | 0.983 | Non-compliant (86.6%) |
| 6 | `Seasonal_Naive_168h` | **1.000** | 0.875 | 4,024.4 | 5,562.5 | 7.58% | +91.8 | 4,732.3 | 0.835 | 0.963 | Non-compliant (83.5%) |
| 7 | `ETS_HoltWinters` | **1.005** | 0.882 | 4,174.5 | 5,542.3 | 7.68% | -1,499.5 | 5,447.6 | 0.837 | 0.970 | Non-compliant (83.7%) |
| 8 | `Seasonal_MA_4Week` | **1.013** | 0.896 | 4,128.0 | 5,378.5 | 7.78% | +186.8 | 4,918.7 | 0.839 | 0.969 | Non-compliant (83.9%) |

---

### Fold-by-Fold Detailed Breakdown (rMAE by Fold across Regions)

| Model | fold_1_winter_2023 | fold_2_spring_2023 | fold_3_summer_2023 | fold_4_fall_2023 |
| :--- | :---: | :---: | :---: | :---: |
| `ETS_HoltWinters` | 0.922 | 1.052 | 1.084 | 1.005 |
| `Ensemble_Ridge_HGBResidual` | 0.465 | 0.650 | 0.452 | 0.544 |
| `HistGradientBoosting_Point_Conformal` | 0.398 | 0.565 | 0.464 | 0.458 |
| `HistGradientBoosting_Residual` | 0.434 | 0.576 | 0.467 | 0.492 |
| `Ridge_Linear_Baseline` | 0.604 | 0.844 | 0.526 | 0.727 |
| `Seasonal_MA_4Week` | 0.882 | 1.134 | 1.032 | 1.035 |
| `Seasonal_Naive_168h` | 1.000 | 1.000 | 1.000 | 1.000 |
| `Seasonal_Naive_48h` | 0.848 | 1.110 | 0.808 | 1.128 |

---

### Holdout Protocol & Dual-Model Evaluation Disclosure
Under the pre-declared rule above, `HistGradientBoosting_Point_Conformal` was selected as the winner (GM rMAE = 0.457, 80% coverage = 0.787). In an earlier iteration, `HistGradientBoosting_Residual` (rank 2, GM rMAE = 0.487) was evaluated on the 2024 holdout due to Texas level drift. To adhere strictly to scientific integrity and single-touch holdout discipline, both models are evaluated on Calendar 2024 and reported side-by-side in `reports/final_holdout_report.md` and `README.md` without choosing between them on holdout results.
