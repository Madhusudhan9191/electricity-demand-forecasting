# Phase 6: Monitoring, Drift & Data Quality Assurance Report

All assertions, PSI drift statistics, and rolling alert hours are computed programmatically.

## 1. Data Quality Assertions Log

| Region | Assertion ID | Assertion Name | Status | Failed Count | Total Rows | Threshold Rule |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| ERCOT | `DQ_01_NO_DUPLICATES` | Zero Duplicate Timestamps | **PASS** | 0 | 43,848 | `count == 0` |
| ERCOT | `DQ_02_GRID_CONTINUITY` | Continuous Hourly Grid | **PASS** | 0 | 43,848 | `count == 0` |
| ERCOT | `DQ_03_DEMAND_POSITIVE` | Demand Values Strictly Positive | **PASS** | 0 | 43,848 | `demand_mw > 0` |
| ERCOT | `DQ_04_RAW_FEED_DISCREPANCY` | Raw EIA Stream Discrepancy Rate | `WARNING` | 549 | 43,848 | `rate < 3.0%` |
| ERCOT | `DQ_05_TEMP_PHYSICAL_BOUNDS` | Temperature Physically Bounded | **PASS** | 0 | 43,848 | `-40C <= temp <= 60C` |
| ERCOT | `DQ_06_WEATHER_ALIGNMENT` | 100% Demand-Weather Timestamp Alignment | **PASS** | 0 | 43,848 | `nulls == 0` |
| PJM | `DQ_01_NO_DUPLICATES` | Zero Duplicate Timestamps | **PASS** | 0 | 43,848 | `count == 0` |
| PJM | `DQ_02_GRID_CONTINUITY` | Continuous Hourly Grid | **PASS** | 0 | 43,848 | `count == 0` |
| PJM | `DQ_03_DEMAND_POSITIVE` | Demand Values Strictly Positive | **PASS** | 0 | 43,848 | `demand_mw > 0` |
| PJM | `DQ_04_RAW_FEED_DISCREPANCY` | Raw EIA Stream Discrepancy Rate | `WARNING` | 1,050 | 43,848 | `rate < 3.0%` |
| PJM | `DQ_05_TEMP_PHYSICAL_BOUNDS` | Temperature Physically Bounded | **PASS** | 0 | 43,848 | `-40C <= temp <= 60C` |
| PJM | `DQ_06_WEATHER_ALIGNMENT` | 100% Demand-Weather Timestamp Alignment | **PASS** | 0 | 43,848 | `nulls == 0` |
| NYIS | `DQ_01_NO_DUPLICATES` | Zero Duplicate Timestamps | **PASS** | 0 | 43,848 | `count == 0` |
| NYIS | `DQ_02_GRID_CONTINUITY` | Continuous Hourly Grid | **PASS** | 0 | 43,848 | `count == 0` |
| NYIS | `DQ_03_DEMAND_POSITIVE` | Demand Values Strictly Positive | **PASS** | 0 | 43,848 | `demand_mw > 0` |
| NYIS | `DQ_04_RAW_FEED_DISCREPANCY` | Raw EIA Stream Discrepancy Rate | `WARNING` | 475 | 43,848 | `rate < 3.0%` |
| NYIS | `DQ_05_TEMP_PHYSICAL_BOUNDS` | Temperature Physically Bounded | **PASS** | 0 | 43,848 | `-40C <= temp <= 60C` |
| NYIS | `DQ_06_WEATHER_ALIGNMENT` | 100% Demand-Weather Timestamp Alignment | **PASS** | 0 | 43,848 | `nulls == 0` |

---

## 2. Feature & Target Distribution Drift (Train vs Holdout)

*PSI < 0.10: Stable, 0.10–0.25: Moderate Drift, >= 0.25: Severe Drift.*

| Region | Feature | KS Statistic | KS p-value | PSI | Drift Classification | Train Mean | Holdout Mean | Mean Delta (%) |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: |
| **ERCOT** | `demand_mw` | 0.2924 | 0.00e+00 | **0.6293** | Severe Drift (PSI >= 0.25) | 46,502.7 | 54,665.3 | +17.6% |
| **ERCOT** | `temp_c` | 0.2147 | 3.41e-185 | **0.2696** | Severe Drift (PSI >= 0.25) | 18.7 | 23.7 | +26.8% |
| **ERCOT** | `cooling_degrees` | 0.2147 | 3.41e-185 | **0.2409** | Moderate Drift (0.10-0.25) | 4.3 | 7.4 | +70.1% |
| **ERCOT** | `heating_degrees` | 0.1870 | 3.18e-140 | **0.1631** | Moderate Drift (0.10-0.25) | 3.7 | 1.7 | -53.5% |
| **ERCOT** | `rel_humidity_pct` | 0.0670 | 2.86e-18 | **0.0229** | Stable (PSI < 0.10) | 64.3 | 61.4 | -4.5% |
| **ERCOT** | `wind_speed_kmh` | 0.1036 | 4.57e-43 | **0.1123** | Moderate Drift (0.10-0.25) | 15.0 | 13.2 | -12.0% |
| **ERCOT** | `lag_168h` | 0.2824 | 0.00e+00 | **0.5304** | Severe Drift (PSI >= 0.25) | 46,477.4 | 54,531.0 | +17.3% |
| **PJM** | `demand_mw` | 0.0433 | 7.15e-08 | **0.0199** | Stable (PSI < 0.10) | 89,736.6 | 89,083.2 | -0.7% |
| **PJM** | `temp_c` | 0.2053 | 3.17e-169 | **0.2981** | Severe Drift (PSI >= 0.25) | 12.7 | 17.1 | +35.5% |
| **PJM** | `cooling_degrees` | 0.1704 | 2.48e-116 | **0.1028** | Moderate Drift (0.10-0.25) | 2.0 | 3.1 | +50.0% |
| **PJM** | `heating_degrees` | 0.2053 | 3.17e-169 | **0.2964** | Severe Drift (PSI >= 0.25) | 7.4 | 3.9 | -46.9% |
| **PJM** | `rel_humidity_pct` | 0.0330 | 9.18e-05 | **0.0155** | Stable (PSI < 0.10) | 66.7 | 67.7 | +1.6% |
| **PJM** | `wind_speed_kmh` | 0.0820 | 3.99e-27 | **0.0585** | Stable (PSI < 0.10) | 12.0 | 10.7 | -11.5% |
| **PJM** | `lag_168h` | 0.0626 | 5.34e-16 | **0.0306** | Stable (PSI < 0.10) | 89,858.2 | 88,878.6 | -1.1% |
| **NYIS** | `demand_mw` | 0.0439 | 4.57e-08 | **0.0225** | Stable (PSI < 0.10) | 17,215.1 | 17,073.1 | -0.8% |
| **NYIS** | `temp_c` | 0.2186 | 5.28e-192 | **0.2873** | Severe Drift (PSI >= 0.25) | 11.8 | 16.2 | +37.4% |
| **NYIS** | `cooling_degrees` | 0.1561 | 1.51e-97 | **0.1013** | Moderate Drift (0.10-0.25) | 1.7 | 2.5 | +45.5% |
| **NYIS** | `heating_degrees` | 0.2186 | 5.28e-192 | **0.2872** | Severe Drift (PSI >= 0.25) | 7.9 | 4.3 | -45.9% |
| **NYIS** | `rel_humidity_pct` | 0.0484 | 9.59e-10 | **0.0282** | Stable (PSI < 0.10) | 70.0 | 72.3 | +3.3% |
| **NYIS** | `wind_speed_kmh` | 0.1181 | 6.71e-56 | **0.0987** | Stable (PSI < 0.10) | 13.9 | 11.8 | -14.6% |
| **NYIS** | `lag_168h` | 0.0611 | 2.82e-15 | **0.0333** | Stable (PSI < 0.10) | 17,235.4 | 17,035.1 | -1.2% |

---

## 3. Operational Monitoring & Alert Tracking Summary

| Region | Holdout Hours | Error Spike Alert Hours (MAE > 1.5x) | Coverage Breach Hours (Cov < 65%) | Max 7-Day Rolling MAE (MW) | Min 7-Day Rolling Cov80 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **ERCOT** | 5,880 | 802 (13.64%) | 5,726 (97.38%) | 6,443.4 | 0.000 |
| **NYIS** | 5,880 | 838 (14.25%) | 3,788 (64.42%) | 1,169.6 | 0.179 |
| **PJM** | 5,880 | 859 (14.61%) | 3,954 (67.24%) | 9,383.1 | 0.060 |
