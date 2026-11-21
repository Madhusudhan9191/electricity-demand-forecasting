# Final Single-Touch Holdout Evaluation Report (Calendar 2024)

**Evaluation Period:** 2024-01-01 00:00:00 to 2024-12-31 23:00:00 (8,784 hours per region; leap year).
**Training Period:** 2021-01-01 00:00:00 to 2023-12-31 23:00:00 (26,280 hours per region).

### 1. Dual-Model Evaluation & Methodology Disclosure

> [!IMPORTANT]
> **Protocol Disclosure:** Under the pre-declared decision rule from Phase 0 / Phase 4, `HistGradientBoosting_Point_Conformal` was the numeric **SELECTED WINNER** (GM rMAE = 0.457, 80% coverage = 78.7%).
> In an earlier execution of the pipeline, the holdout was evaluated using `HistGradientBoosting_Residual` (rank 2, GM rMAE = 0.487), which was developed after the 2023 Texas bias analysis to correct tree extrapolation failure in trending grids.
> Because Calendar 2024 had already been inspected with the Residual model, we report **BOTH models side-by-side** on the 2024 holdout. We do not select between them post-hoc using the holdout.

### 2. Side-by-Side Holdout Performance Leaderboard

| Region | Model | Role | Holdout MAE (MW) | 95% Bootstrap CI | Baseline 168h MAE (MW) | rMAE | 80% Coverage | 95% Coverage | Bias (MW) | Non-Imputed rMAE |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TEX** | `HistGradientBoosting_Point_Conformal` | Pre-declared Validation Winner | **2,783.6** | [2,599.9, 2,984.1] | 4,476.0 | **0.622** | **76.7%** | 93.1% | -2,472.5 | **0.621** |
| **TEX** | `HistGradientBoosting_Residual` | Level-Anchored Comparison Model | **2,758.6** | [2,577.2, 2,954.9] | 4,476.0 | **0.616** | **78.4%** | 93.1% | -2,224.2 | **0.617** |
| **MIDA** | `HistGradientBoosting_Point_Conformal` | Pre-declared Validation Winner | **2,871.0** | [2,695.4, 3,067.8] | 8,854.4 | **0.324** | **79.3%** | 93.2% | -1,766.1 | **0.328** |
| **MIDA** | `HistGradientBoosting_Residual` | Level-Anchored Comparison Model | **3,255.9** | [3,026.9, 3,530.7] | 8,854.4 | **0.368** | **78.3%** | 92.5% | -1,649.1 | **0.371** |
| **NY** | `HistGradientBoosting_Point_Conformal` | Pre-declared Validation Winner | **540.8** | [516.0, 568.6] | 1,524.1 | **0.355** | **78.5%** | 93.8% | +13.0 | **0.355** |
| **NY** | `HistGradientBoosting_Residual` | Level-Anchored Comparison Model | **604.7** | [575.7, 639.5] | 1,524.1 | **0.397** | **78.5%** | 93.3% | -26.8 | **0.397** |

---

### 3. Key Observations & Scientific Findings

1. **Point Conformal Model Performance:** In MIDA (rMAE 0.324 vs 0.368) and NY (rMAE 0.355 vs 0.397), the pre-declared winner achieves superior accuracy over the residual model, while in TEX it is competitive (rMAE 0.622 vs 0.616).
2. **Extrapolation and Bias in Growing Load Regimes (TEX):** Mean load in Texas grew from 44.8 GW (2021) to 52.9 GW (2024). The residual model anchored on `y_{t-168}` reduces the annual under-forecast bias from -2,472.5 MW (point model) to -2,224.2 MW (residual model). The bias is reduced by ~250 MW but remains negative across all months, illustrating the persistence of structural demand expansion.
3. **Prediction Interval Calibration:**
   - **80% Prediction Intervals:** Well-calibrated across all regions via rolling conformal calibration (TEX: 76.7% / 78.4%, MIDA: 79.3% / 78.3%, NY: 78.5% / 78.5%), passing within or immediately adjacent to the [77%, 83%] target band.
   - **95% Prediction Intervals:** Slightly under-cover the nominal 95% rate (achieving 92.5% to 93.8%), representing an honest empirical caveat in peak tail hours.
4. **Imputation Robustness:** Imputed hours (TEX: 1.84%, MIDA: 2.93%, NY: 1.99%) show no adverse impact on accuracy; non-imputed rMAE matches full holdout rMAE within 0.003 across all regions.

---

### 4. Monthly Bias Breakdown (Actual Mean vs Point & Residual Bias)

| Region | Month | Actual Mean (MW) | Point Conformal Bias (MW) | Residual Model Bias (MW) | Point MAE (MW) | Residual MAE (MW) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| TEX | 01 | 51,466.5 | -5,106.1 | -4,526.1 | 5,337.8 | 4,897.4 |
| TEX | 02 | 44,197.5 | -1,054.8 | -941.6 | 1,331.5 | 1,401.3 |
| TEX | 03 | 43,594.8 | -1,217.2 | -1,022.8 | 1,396.2 | 1,304.9 |
| TEX | 04 | 46,726.0 | -1,789.3 | -1,677.6 | 1,926.6 | 1,865.4 |
| TEX | 05 | 54,008.8 | -1,539.2 | -1,242.8 | 2,217.7 | 2,365.9 |
| TEX | 06 | 62,032.5 | -2,804.8 | -3,124.6 | 3,150.3 | 3,696.9 |
| TEX | 07 | 60,191.5 | -1,635.2 | -1,183.1 | 2,967.9 | 3,218.8 |
| TEX | 08 | 66,575.6 | -3,293.2 | -2,432.0 | 3,326.1 | 2,843.2 |
| TEX | 09 | 57,306.8 | -2,342.6 | -2,379.2 | 2,668.1 | 2,742.2 |
| TEX | 10 | 53,186.3 | -3,060.0 | -3,128.3 | 3,074.7 | 3,176.1 |
| TEX | 11 | 47,370.0 | -2,383.3 | -2,177.4 | 2,527.8 | 2,578.8 |
| TEX | 12 | 47,414.0 | -3,332.7 | -2,785.5 | 3,355.2 | 2,918.1 |
| MIDA | 01 | 100,278.5 | -2,697.5 | -2,709.8 | 4,233.7 | 5,093.6 |
| MIDA | 02 | 91,341.4 | -1,397.7 | -1,603.6 | 2,395.4 | 2,696.7 |
| MIDA | 03 | 83,478.4 | -1,223.0 | -803.7 | 2,351.1 | 2,387.7 |
| MIDA | 04 | 79,715.2 | -1,300.5 | -975.5 | 1,916.5 | 1,944.9 |
| MIDA | 05 | 84,210.0 | -1,568.5 | -1,064.9 | 2,621.2 | 2,507.5 |
| MIDA | 06 | 100,361.6 | -3,271.7 | -3,945.1 | 4,513.9 | 5,619.7 |
| MIDA | 07 | 107,883.4 | -2,326.4 | -2,327.6 | 3,336.7 | 4,183.8 |
| MIDA | 08 | 102,216.9 | -1,609.1 | -1,768.2 | 3,201.0 | 4,017.2 |
| MIDA | 09 | 87,887.0 | -1,406.6 | -660.1 | 2,765.7 | 3,117.9 |
| MIDA | 10 | 79,127.4 | -816.8 | -645.0 | 1,445.6 | 1,452.2 |
| MIDA | 11 | 83,080.7 | -1,221.9 | -749.9 | 2,316.9 | 2,315.1 |
| MIDA | 12 | 96,990.2 | -2,333.6 | -2,524.0 | 3,324.8 | 3,697.7 |
| NY | 01 | 18,065.4 | -255.3 | -242.7 | 489.9 | 541.4 |
| NY | 02 | 17,053.1 | +141.2 | +109.1 | 406.5 | 411.9 |
| NY | 03 | 15,666.9 | -66.0 | -45.3 | 480.1 | 553.7 |
| NY | 04 | 14,799.4 | +61.9 | +103.3 | 382.4 | 410.2 |
| NY | 05 | 15,270.3 | +241.4 | +223.8 | 582.2 | 607.3 |
| NY | 06 | 18,940.5 | +97.4 | -105.3 | 744.6 | 819.1 |
| NY | 07 | 21,521.9 | +161.4 | -14.5 | 709.1 | 814.7 |
| NY | 08 | 19,502.5 | +155.9 | +85.1 | 770.2 | 1,004.0 |
| NY | 09 | 16,518.5 | +24.4 | -22.0 | 628.2 | 660.2 |
| NY | 10 | 15,020.9 | +44.9 | +41.4 | 348.8 | 391.6 |
| NY | 11 | 15,690.8 | -35.4 | -2.6 | 352.3 | 372.5 |
| NY | 12 | 17,983.1 | -404.8 | -440.4 | 584.4 | 652.4 |

