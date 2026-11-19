# Phase 5: Final Holdout Evaluation & Model Assessment Report

> **Point-in-Time Assurance:** The final holdout period (2023-05-01 to 2023-12-31, 5,880 hours per region) was evaluated exactly once. Zero tuning was performed on this split.
> **Attribution Disclosure:** All weather and feature associations reported herein are empirical model-based statistical associations, not causal predictions or real-time grid assertions.

## 1. Overall Model vs. Baseline Performance on Final Holdout

| Region | Model MASE [95% CI] | Base 168h MASE | Skill Score (%) | Model MAE (MW) | Base MAE (MW) | MAE Diff (MW) [95% CI] | Model RMSE (MW) | Peak-Hour MAE (MW) | 80% Cov | 95% Cov |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ERCOT** | **0.729** [0.686, 0.778] | 0.884 | **+17.5%** | 3,330.3 | 4,034.8 | -704.5 [-1152.9, -314.4] | 4,152.5 | 3,115.6 | 0.301 | 0.506 |
| **PJM** | **0.419** [0.387, 0.452] | 0.831 | **+49.6%** | 3,396.3 | 6,732.4 | -3,336.0 [-4065.3, -2632.8] | 4,660.1 | 3,852.9 | 0.564 | 0.769 |
| **NYIS** | **0.435** [0.407, 0.465] | 1.002 | **+56.6%** | 614.6 | 1,416.7 | -802.0 [-973.8, -651.8] | 839.8 | 785.2 | 0.539 | 0.735 |

---

## 2. Conditional Error Breakdown by Operating Segment

*Sample-size policy: <30 rows suppressed, 30–99 rows exploratory, 100+ rows interpretable.*

| Region | Dimension | Segment | Sample Size (N) | MAE (MW) | Bias (MW) | 80% Coverage | Reliability Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| ERCOT | Hour of Day | Hour 00 | 245 | 4,639.7 | -4,084.6 | 0.245 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 01 | 245 | 4,416.0 | -4,025.8 | 0.196 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 02 | 245 | 4,021.4 | -3,704.4 | 0.224 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 03 | 245 | 3,984.8 | -3,735.3 | 0.224 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 04 | 245 | 3,619.4 | -3,429.8 | 0.261 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 05 | 245 | 3,174.5 | -3,046.1 | 0.306 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 06 | 245 | 2,802.3 | -2,601.4 | 0.359 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 07 | 245 | 2,650.1 | -2,477.1 | 0.363 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 08 | 245 | 2,620.5 | -2,504.3 | 0.380 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 09 | 245 | 2,494.5 | -2,365.2 | 0.376 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 10 | 245 | 2,535.5 | -2,418.9 | 0.331 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 11 | 245 | 2,728.5 | -2,614.3 | 0.322 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 12 | 245 | 2,744.4 | -2,576.7 | 0.351 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 13 | 245 | 2,491.1 | -2,097.9 | 0.400 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 14 | 245 | 2,408.3 | -2,022.5 | 0.412 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 15 | 245 | 2,411.0 | -2,089.8 | 0.384 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 16 | 245 | 2,663.9 | -2,277.4 | 0.347 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 17 | 245 | 2,863.0 | -2,348.6 | 0.298 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 18 | 245 | 3,364.5 | -2,764.2 | 0.241 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 19 | 245 | 3,932.1 | -3,354.0 | 0.224 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 20 | 245 | 4,166.1 | -3,518.9 | 0.245 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 21 | 245 | 4,304.4 | -3,604.7 | 0.249 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 22 | 245 | 4,425.2 | -3,761.8 | 0.220 | Interpretable (100+) |
| ERCOT | Hour of Day | Hour 23 | 245 | 4,466.1 | -3,950.2 | 0.257 | Interpretable (100+) |
| ERCOT | Day Type | Weekday | 4200 | 3,342.8 | -3,095.2 | 0.290 | Interpretable (100+) |
| ERCOT | Day Type | Weekend | 1680 | 3,299.0 | -2,670.7 | 0.326 | Interpretable (100+) |
| ERCOT | Holiday Status | Regular Day | 5688 | 3,332.7 | -2,979.4 | 0.298 | Interpretable (100+) |
| ERCOT | Holiday Status | Holiday | 192 | 3,259.2 | -2,811.2 | 0.385 | Interpretable (100+) |
| ERCOT | Temperature Band | < 0°C (Freezing) | 1 | — | — | — | Suppressed (N < 30) |
| ERCOT | Temperature Band | 0-10°C (Cold) | 561 | 2,078.7 | -1,600.7 | 0.458 | Interpretable (100+) |
| ERCOT | Temperature Band | 10-20°C (Mild) | 1268 | 2,063.2 | -1,921.9 | 0.426 | Interpretable (100+) |
| ERCOT | Temperature Band | 20-30°C (Warm) | 2524 | 3,302.3 | -2,747.4 | 0.305 | Interpretable (100+) |
| ERCOT | Temperature Band | > 30°C (Hot) | 1526 | 4,891.3 | -4,728.9 | 0.130 | Interpretable (100+) |
| ERCOT | Peak Status | Off-Peak | 4165 | 3,418.7 | -3,117.6 | 0.298 | Interpretable (100+) |
| ERCOT | Peak Status | Peak Hours (14-20) | 1715 | 3,115.6 | -2,625.1 | 0.307 | Interpretable (100+) |
| PJM | Hour of Day | Hour 00 | 245 | 4,213.8 | +45.2 | 0.457 | Interpretable (100+) |
| PJM | Hour of Day | Hour 01 | 245 | 3,755.3 | -25.5 | 0.502 | Interpretable (100+) |
| PJM | Hour of Day | Hour 02 | 245 | 3,623.6 | +201.1 | 0.514 | Interpretable (100+) |
| PJM | Hour of Day | Hour 03 | 245 | 3,285.5 | +12.8 | 0.539 | Interpretable (100+) |
| PJM | Hour of Day | Hour 04 | 245 | 3,092.7 | -231.4 | 0.596 | Interpretable (100+) |
| PJM | Hour of Day | Hour 05 | 245 | 2,762.1 | -311.4 | 0.645 | Interpretable (100+) |
| PJM | Hour of Day | Hour 06 | 245 | 2,598.4 | -350.2 | 0.665 | Interpretable (100+) |
| PJM | Hour of Day | Hour 07 | 245 | 2,535.1 | -372.4 | 0.653 | Interpretable (100+) |
| PJM | Hour of Day | Hour 08 | 245 | 2,509.9 | -60.4 | 0.690 | Interpretable (100+) |
| PJM | Hour of Day | Hour 09 | 245 | 2,538.6 | -195.5 | 0.690 | Interpretable (100+) |
| PJM | Hour of Day | Hour 10 | 245 | 2,525.2 | -169.1 | 0.673 | Interpretable (100+) |
| PJM | Hour of Day | Hour 11 | 245 | 2,626.0 | +5.3 | 0.653 | Interpretable (100+) |
| PJM | Hour of Day | Hour 12 | 245 | 2,603.3 | +438.6 | 0.641 | Interpretable (100+) |
| PJM | Hour of Day | Hour 13 | 245 | 2,862.3 | +693.4 | 0.633 | Interpretable (100+) |
| PJM | Hour of Day | Hour 14 | 245 | 3,213.7 | +866.6 | 0.571 | Interpretable (100+) |
| PJM | Hour of Day | Hour 15 | 245 | 3,206.8 | +830.6 | 0.551 | Interpretable (100+) |
| PJM | Hour of Day | Hour 16 | 245 | 3,378.3 | +1,121.5 | 0.527 | Interpretable (100+) |
| PJM | Hour of Day | Hour 17 | 245 | 3,847.3 | +1,386.4 | 0.465 | Interpretable (100+) |
| PJM | Hour of Day | Hour 18 | 245 | 4,177.8 | +1,546.7 | 0.453 | Interpretable (100+) |
| PJM | Hour of Day | Hour 19 | 245 | 4,519.5 | +1,825.1 | 0.482 | Interpretable (100+) |
| PJM | Hour of Day | Hour 20 | 245 | 4,626.9 | +1,953.7 | 0.473 | Interpretable (100+) |
| PJM | Hour of Day | Hour 21 | 245 | 4,253.4 | +1,305.5 | 0.522 | Interpretable (100+) |
| PJM | Hour of Day | Hour 22 | 245 | 4,206.0 | +1,001.7 | 0.506 | Interpretable (100+) |
| PJM | Hour of Day | Hour 23 | 245 | 4,549.8 | +786.1 | 0.437 | Interpretable (100+) |
| PJM | Day Type | Weekday | 4200 | 3,534.6 | +473.3 | 0.554 | Interpretable (100+) |
| PJM | Day Type | Weekend | 1680 | 3,050.6 | +611.1 | 0.589 | Interpretable (100+) |
| PJM | Holiday Status | Regular Day | 5688 | 3,355.5 | +477.5 | 0.570 | Interpretable (100+) |
| PJM | Holiday Status | Holiday | 192 | 4,605.3 | +1,553.8 | 0.375 | Interpretable (100+) |
| PJM | Temperature Band | < 0°C (Freezing) | 117 | 4,834.2 | -1,750.6 | 0.333 | Interpretable (100+) |
| PJM | Temperature Band | 0-10°C (Cold) | 1226 | 2,798.8 | -834.3 | 0.603 | Interpretable (100+) |
| PJM | Temperature Band | 10-20°C (Mild) | 2063 | 2,208.4 | +448.4 | 0.725 | Interpretable (100+) |
| PJM | Temperature Band | 20-30°C (Warm) | 2205 | 4,510.3 | +1,219.9 | 0.428 | Interpretable (100+) |
| PJM | Temperature Band | > 30°C (Hot) | 269 | 5,472.8 | +2,332.1 | 0.368 | Interpretable (100+) |
| PJM | Peak Status | Off-Peak | 4165 | 3,208.3 | +163.2 | 0.589 | Interpretable (100+) |
| PJM | Peak Status | Peak Hours (14-20) | 1715 | 3,852.9 | +1,361.5 | 0.503 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 00 | 245 | 643.5 | -2.0 | 0.506 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 01 | 245 | 607.7 | -2.3 | 0.551 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 02 | 245 | 583.6 | +3.6 | 0.567 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 03 | 245 | 539.1 | -17.8 | 0.596 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 04 | 245 | 522.1 | -49.2 | 0.596 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 05 | 245 | 479.8 | -36.6 | 0.629 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 06 | 245 | 450.4 | -12.9 | 0.649 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 07 | 245 | 427.8 | +9.4 | 0.686 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 08 | 245 | 405.3 | +37.8 | 0.669 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 09 | 245 | 393.0 | +21.6 | 0.686 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 10 | 245 | 423.9 | -3.4 | 0.661 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 11 | 245 | 430.0 | +3.4 | 0.673 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 12 | 245 | 453.6 | +171.2 | 0.645 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 13 | 245 | 511.1 | +254.7 | 0.592 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 14 | 245 | 597.3 | +353.8 | 0.502 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 15 | 245 | 699.7 | +464.5 | 0.478 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 16 | 245 | 733.3 | +498.1 | 0.445 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 17 | 245 | 775.4 | +486.4 | 0.420 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 18 | 245 | 889.5 | +538.6 | 0.327 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 19 | 245 | 895.8 | +503.7 | 0.343 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 20 | 245 | 905.3 | +502.2 | 0.363 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 21 | 245 | 861.0 | +464.2 | 0.424 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 22 | 245 | 784.3 | +312.8 | 0.457 | Interpretable (100+) |
| NYIS | Hour of Day | Hour 23 | 245 | 738.8 | +139.2 | 0.469 | Interpretable (100+) |
| NYIS | Day Type | Weekday | 4200 | 594.9 | +156.2 | 0.559 | Interpretable (100+) |
| NYIS | Day Type | Weekend | 1680 | 663.9 | +286.3 | 0.489 | Interpretable (100+) |
| NYIS | Holiday Status | Regular Day | 5688 | 607.7 | +190.2 | 0.542 | Interpretable (100+) |
| NYIS | Holiday Status | Holiday | 192 | 818.7 | +287.2 | 0.448 | Interpretable (100+) |
| NYIS | Temperature Band | < 0°C (Freezing) | 195 | 291.0 | +0.1 | 0.815 | Interpretable (100+) |
| NYIS | Temperature Band | 0-10°C (Cold) | 1241 | 365.2 | +84.2 | 0.740 | Interpretable (100+) |
| NYIS | Temperature Band | 10-20°C (Mild) | 2247 | 465.0 | +116.1 | 0.626 | Interpretable (100+) |
| NYIS | Temperature Band | 20-30°C (Warm) | 2061 | 929.5 | +348.4 | 0.315 | Interpretable (100+) |
| NYIS | Temperature Band | > 30°C (Hot) | 136 | 1,054.6 | +394.2 | 0.265 | Interpretable (100+) |
| NYIS | Peak Status | Off-Peak | 4165 | 544.4 | +76.1 | 0.592 | Interpretable (100+) |
| NYIS | Peak Status | Peak Hours (14-20) | 1715 | 785.2 | +478.2 | 0.411 | Interpretable (100+) |

---

## 3. Weather Sensitivity Scenario (Temperature Perturbations)

> **Disclaimer:** *Model-based association under historical correlation structure, not a physical simulation of grid operations or climate forecast.*

| Region | Scenario | Mean Demand (MW) | Peak Demand (MW) | Delta Mean (MW) | Delta Demand (%) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| ERCOT | Base Actual | 51,691.4 | 77,145.7 | +0.0 | +0.00% |
| ERCOT | Base +2°C | 52,682.6 | 78,461.5 | +991.2 | +1.92% |
| ERCOT | Base +5°C | 54,032.1 | 78,685.1 | +2,340.8 | +4.53% |
| PJM | Base Actual | 89,595.9 | 145,503.0 | +0.0 | +0.00% |
| PJM | Base +2°C | 90,267.5 | 145,503.0 | +671.5 | +0.75% |
| PJM | Base +5°C | 91,421.4 | 145,503.0 | +1,825.5 | +2.04% |
| NYIS | Base Actual | 17,266.5 | 29,665.8 | +0.0 | +0.00% |
| NYIS | Base +2°C | 17,461.5 | 29,665.8 | +195.0 | +1.13% |
| NYIS | Base +5°C | 17,755.0 | 29,665.8 | +488.5 | +2.83% |

---

## 4. Failure Analysis: Top 5 Worst Forecast Days per Region

| Region | Date | Daily MAE (MW) | Daily Bias (MW) | Peak Actual (MW) | Max Temp (°C) | Min Temp (°C) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| ERCOT | 2023-09-23 | 8,046.7 | -8,046.7 | 77,755.0 | 35.8 | 25.8 |
| ERCOT | 2023-06-15 | 8,011.6 | -8,011.6 | 76,602.0 | 32.6 | 19.4 |
| ERCOT | 2023-07-11 | 7,971.6 | -7,971.6 | 78,802.0 | 33.4 | 24.4 |
| ERCOT | 2023-08-19 | 7,524.3 | -7,524.3 | 84,804.0 | 41.4 | 29.6 |
| ERCOT | 2023-08-18 | 7,454.9 | -7,454.9 | 84,967.0 | 42.9 | 28.8 |
| PJM | 2023-08-15 | 13,195.1 | -2,761.6 | 122,639.0 | 32.7 | 22.7 |
| PJM | 2023-06-14 | 11,873.9 | +11,873.9 | 95,385.0 | 25.6 | 16.5 |
| PJM | 2023-06-13 | 10,474.4 | +10,474.4 | 95,104.0 | 28.1 | 14.9 |
| PJM | 2023-06-15 | 9,890.4 | +9,890.4 | 102,339.0 | 27.8 | 14.9 |
| PJM | 2023-08-22 | 9,021.6 | -9,021.6 | 132,711.0 | 28.3 | 21.1 |
| NYIS | 2023-06-02 | 1,538.8 | -1,538.8 | 22,861.0 | 30.8 | 15.2 |
| NYIS | 2023-08-25 | 1,526.4 | +1,437.8 | 21,408.0 | 28.0 | 19.7 |
| NYIS | 2023-06-18 | 1,495.4 | +1,495.4 | 17,718.0 | 26.5 | 15.8 |
| NYIS | 2023-07-09 | 1,448.8 | -1,448.8 | 23,110.0 | 27.0 | 21.6 |
| NYIS | 2023-08-20 | 1,439.1 | +1,439.1 | 21,365.0 | 29.9 | 15.2 |
