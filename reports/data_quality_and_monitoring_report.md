# Phase 6: Monitoring, Drift & Data Quality Assurance Report

All assertions, PSI drift statistics, and rolling alert hours are computed programmatically.

## 1. Data Quality Assertions Log

| Region | Assertion ID | Assertion Name | Status | Failed Count | Total Rows | Threshold Rule |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| TEX | `DQ_01_NO_DUPLICATES` | Zero Duplicate Timestamps | **PASS** | 0 | 43,848 | `count == 0` |
| TEX | `DQ_02_GRID_CONTINUITY` | Continuous Hourly Grid | **PASS** | 0 | 43,848 | `count == 0` |
| TEX | `DQ_03_DEMAND_POSITIVE` | Demand Values Strictly Positive | **PASS** | 0 | 43,848 | `demand_mw > 0` |
| TEX | `DQ_04_RAW_FEED_DISCREPANCY` | Raw EIA Stream Discrepancy Rate | `WARNING` | 549 | 43,848 | `rate < 3.0%` |
| TEX | `DQ_05_TEMP_PHYSICAL_BOUNDS` | Temperature Physically Bounded | **PASS** | 0 | 43,848 | `-40C <= temp <= 60C` |
| TEX | `DQ_06_WEATHER_ALIGNMENT` | 100% Demand-Weather Timestamp Alignment | **PASS** | 0 | 43,848 | `nulls == 0` |
| MIDA | `DQ_01_NO_DUPLICATES` | Zero Duplicate Timestamps | **PASS** | 0 | 43,848 | `count == 0` |
| MIDA | `DQ_02_GRID_CONTINUITY` | Continuous Hourly Grid | **PASS** | 0 | 43,848 | `count == 0` |
| MIDA | `DQ_03_DEMAND_POSITIVE` | Demand Values Strictly Positive | **PASS** | 0 | 43,848 | `demand_mw > 0` |
| MIDA | `DQ_04_RAW_FEED_DISCREPANCY` | Raw EIA Stream Discrepancy Rate | `WARNING` | 1,050 | 43,848 | `rate < 3.0%` |
| MIDA | `DQ_05_TEMP_PHYSICAL_BOUNDS` | Temperature Physically Bounded | **PASS** | 0 | 43,848 | `-40C <= temp <= 60C` |
| MIDA | `DQ_06_WEATHER_ALIGNMENT` | 100% Demand-Weather Timestamp Alignment | **PASS** | 0 | 43,848 | `nulls == 0` |
| NY | `DQ_01_NO_DUPLICATES` | Zero Duplicate Timestamps | **PASS** | 0 | 43,848 | `count == 0` |
| NY | `DQ_02_GRID_CONTINUITY` | Continuous Hourly Grid | **PASS** | 0 | 43,848 | `count == 0` |
| NY | `DQ_03_DEMAND_POSITIVE` | Demand Values Strictly Positive | **PASS** | 0 | 43,848 | `demand_mw > 0` |
| NY | `DQ_04_RAW_FEED_DISCREPANCY` | Raw EIA Stream Discrepancy Rate | `WARNING` | 475 | 43,848 | `rate < 3.0%` |
| NY | `DQ_05_TEMP_PHYSICAL_BOUNDS` | Temperature Physically Bounded | **PASS** | 0 | 43,848 | `-40C <= temp <= 60C` |
| NY | `DQ_06_WEATHER_ALIGNMENT` | 100% Demand-Weather Timestamp Alignment | **PASS** | 0 | 43,848 | `nulls == 0` |

---

## 2. Feature & Target Distribution Drift (Train vs Holdout)

*PSI < 0.10: Stable, 0.10–0.25: Moderate Drift, >= 0.25: Severe Drift.*

| Region | Feature | KS Statistic | KS p-value | PSI | Drift Classification | Train Mean | Holdout Mean | Mean Delta (%) |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: |
| **TEX** | `demand_mw` | 0.2924 | 0.00e+00 | **0.6293** | Severe Drift (PSI >= 0.25) | 46,502.7 | 54,665.3 | +17.6% |
| **TEX** | `temp_c` | 0.2266 | 1.76e-206 | **0.2814** | Severe Drift (PSI >= 0.25) | 19.6 | 24.2 | +23.0% |
| **TEX** | `cooling_degrees` | 0.2266 | 1.76e-206 | **0.2600** | Severe Drift (PSI >= 0.25) | 4.2 | 7.3 | +70.7% |
| **TEX** | `heating_degrees` | 0.1613 | 3.24e-104 | **0.1412** | Moderate Drift (0.10-0.25) | 2.9 | 1.4 | -51.9% |
| **TEX** | `rel_humidity_pct` | 0.0841 | 1.67e-28 | **0.0349** | Stable (PSI < 0.10) | 69.2 | 65.9 | -4.7% |
| **TEX** | `wind_speed_kmh` | 0.1177 | 1.68e-55 | **0.1516** | Moderate Drift (0.10-0.25) | 13.9 | 12.3 | -11.8% |
| **TEX** | `lag_168h` | 0.2824 | 0.00e+00 | **0.5304** | Severe Drift (PSI >= 0.25) | 46,477.4 | 54,531.0 | +17.3% |
| **MIDA** | `demand_mw` | 0.0433 | 7.15e-08 | **0.0199** | Stable (PSI < 0.10) | 89,736.6 | 89,083.2 | -0.7% |
| **MIDA** | `temp_c` | 0.2299 | 1.37e-212 | **0.3857** | Severe Drift (PSI >= 0.25) | 11.5 | 16.2 | +41.0% |
| **MIDA** | `cooling_degrees` | 0.1569 | 1.32e-98 | **0.1029** | Moderate Drift (0.10-0.25) | 1.6 | 2.3 | +41.6% |
| **MIDA** | `heating_degrees` | 0.2299 | 1.37e-212 | **0.3826** | Severe Drift (PSI >= 0.25) | 8.4 | 4.4 | -47.9% |
| **MIDA** | `rel_humidity_pct` | 0.0460 | 7.99e-09 | **0.0097** | Stable (PSI < 0.10) | 69.9 | 71.0 | +1.5% |
| **MIDA** | `wind_speed_kmh` | 0.1578 | 1.03e-99 | **0.1727** | Moderate Drift (0.10-0.25) | 13.8 | 12.1 | -12.8% |
| **MIDA** | `lag_168h` | 0.0626 | 5.34e-16 | **0.0306** | Stable (PSI < 0.10) | 89,858.2 | 88,878.6 | -1.1% |
| **NY** | `demand_mw` | 0.0439 | 4.57e-08 | **0.0225** | Stable (PSI < 0.10) | 17,215.1 | 17,073.1 | -0.8% |
| **NY** | `temp_c` | 0.2309 | 1.96e-214 | **0.3893** | Severe Drift (PSI >= 0.25) | 10.9 | 15.6 | +42.6% |
| **NY** | `cooling_degrees` | 0.1537 | 1.30e-94 | **0.0497** | Stable (PSI < 0.10) | 1.4 | 2.0 | +45.5% |
| **NY** | `heating_degrees` | 0.2309 | 1.96e-214 | **0.3878** | Severe Drift (PSI >= 0.25) | 8.7 | 4.6 | -46.7% |
| **NY** | `rel_humidity_pct` | 0.0558 | 8.19e-13 | **0.0279** | Stable (PSI < 0.10) | 71.4 | 73.2 | +2.6% |
| **NY** | `wind_speed_kmh` | 0.1201 | 7.91e-58 | **0.1286** | Moderate Drift (0.10-0.25) | 14.2 | 12.2 | -14.2% |
| **NY** | `lag_168h` | 0.0611 | 2.82e-15 | **0.0333** | Stable (PSI < 0.10) | 17,235.4 | 17,035.1 | -1.2% |

---

## 3. Operational Monitoring & Alert Tracking Summary

| Region | Holdout Hours | Error Spike Alert Hours (MAE > 1.5x) | Coverage Breach Hours (Cov < 65%) | Max 7-Day Rolling MAE (MW) | Min 7-Day Rolling Cov80 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **MIDA** | 8,784 | 1,279 (14.56%) | 1,659 (18.89%) | 9,414.9 | 0.202 |
| **NY** | 8,784 | 1,174 (13.37%) | 1,051 (11.96%) | 1,257.0 | 0.220 |
| **TEX** | 8,784 | 717 (8.16%) | 1,550 (17.65%) | 10,278.9 | 0.250 |
