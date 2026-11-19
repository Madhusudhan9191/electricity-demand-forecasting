# Model Comparison & Selection Report (Rolling-Origin Validation Folds)

**Pre-declared Decision Rule:** Minimize Mean MASE across 4 rolling validation folds and 3 regions.

### Model Leaderboard (Averaged Across 4 Folds and 3 Regions)

| Rank | Model | Mean MASE | Mean MAE (MW) | Mean RMSE (MW) | Mean sMAPE (%) | Mean Bias (MW) | Peak MAE (MW) | 80% Coverage | 95% Coverage | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `HistGradientBoosting_Point_Conformal` | **0.403** | 1,981.7 | 2,679.3 | 3.59% | -628.7 | 2,087.5 | 0.577 | 0.788 | **SELECTED WINNER** |
| 2 | `HistGradientBoosting_Quantile` | **0.407** | 2,000.2 | 2,701.4 | 3.62% | -654.6 | 2,105.5 | 0.655 | 0.879 | Candidate |
| 3 | `Ensemble_Ridge_HGB` | **0.415** | 2,015.5 | 2,645.4 | 3.75% | -486.3 | 2,187.9 | 0.694 | 0.888 | Candidate |
| 4 | `Ridge_Linear_Baseline` | **0.505** | 2,389.8 | 3,068.1 | 4.60% | -334.6 | 2,665.7 | 0.631 | 0.827 | Candidate |
| 5 | `Seasonal_Naive_48h` | **0.832** | 3,949.2 | 5,142.6 | 7.41% | +132.3 | 4,534.1 | 0.710 | 0.873 | Candidate |
| 6 | `Seasonal_MA_4Week` | **0.923** | 4,393.8 | 5,980.7 | 8.02% | +340.2 | 4,704.2 | 0.746 | 0.878 | Candidate |
| 7 | `Seasonal_Naive_168h` | **0.923** | 4,393.8 | 5,980.7 | 8.02% | +340.2 | 4,704.2 | 0.746 | 0.878 | Candidate |

---

### Fold-by-Fold Detailed Breakdown (Mean MASE across Regions)

| Model | fold_1_summer | fold_2_fall | fold_3_winter | fold_4_spring |
| :--- | :---: | :---: | :---: | :---: |
| `Ensemble_Ridge_HGB` | 0.500 | 0.356 | 0.437 | 0.369 |
| `HistGradientBoosting_Point_Conformal` | 0.518 | 0.323 | 0.433 | 0.337 |
| `HistGradientBoosting_Quantile` | 0.528 | 0.322 | 0.435 | 0.341 |
| `Ridge_Linear_Baseline` | 0.592 | 0.449 | 0.515 | 0.464 |
| `Seasonal_MA_4Week` | 1.254 | 0.774 | 1.033 | 0.630 |
| `Seasonal_Naive_168h` | 1.254 | 0.774 | 1.033 | 0.630 |
| `Seasonal_Naive_48h` | 1.048 | 0.742 | 0.845 | 0.693 |

---
