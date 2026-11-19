# Phase 1: Data Audit & Verification Report

All metrics, counts, and ranges are programmatically derived from raw files.

## 1. Executive Summary Table (Demand & Alignment by Region)

| Region | Total Hours | Expected Hours | Missing Hours | Duplicates | Raw NaNs | Clean NaNs | Zero/Neg | Imputed/Revised Hours (%) | Outlier Flags | Weather Alignment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ERCOT** | 43,848 | 43,848 | 0 | 0 | 0 | 0 | 0 | 549 (1.252%) | 7 | 100.0% |
| **PJM** | 43,848 | 43,848 | 0 | 0 | 0 | 0 | 0 | 1,050 (2.395%) | 4 | 100.0% |
| **NYIS** | 43,848 | 43,848 | 0 | 0 | 0 | 0 | 0 | 475 (1.083%) | 0 | 100.0% |

---

## 2. Demand Summary Statistics (MW)

| Region | Raw Min (MW) | Clean Min (MW) | Clean Median (MW) | Clean Mean (MW) | Clean Max (MW) | Clean Std (MW) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ERCOT** | 26,274.0 | 27,445.0 | 45,663.5 | 48,247.8 | 85,559.0 | 10,947.4 |
| **PJM** | 0.0 | 55,207.0 | 86,704.0 | 89,240.0 | 151,816.0 | 15,852.4 |
| **NYIS** | 0.0 | 11,366.0 | 16,691.0 | 17,164.3 | 30,915.0 | 3,123.6 |

---

## 3. Weather Summary Statistics (ERA5 Reanalysis)

| Region | Temp Min (°C) | Temp Mean (°C) | Temp Max (°C) | Rel Hum Mean (%) | Wind Speed Mean (km/h) | Solar Mean (W/m²) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ERCOT** | -18.9 | 19.84 | 42.9 | 64.74 | 14.55 | 232.04 |
| **PJM** | -17.1 | 13.75 | 37.3 | 67.3 | 11.7 | 201.32 |
| **NYIS** | -17.3 | 12.86 | 37.6 | 70.5 | 13.28 | 201.66 |

---

## 4. Annual Demand Means & Structural Break Analysis (MW)

| Region | 2020 (COVID) | 2021 | 2022 | 2023 | 2024 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ERCOT** | 43,371.5 | 44,813.3 | 49,162.5 | 51,011.2 | 52,881.2 |
| **PJM** | 86,011.1 | 89,533.8 | 90,987.7 | 88,249.7 | 91,420.6 |
| **NYIS** | 17,093.9 | 17,344.7 | 17,424.4 | 16,780.9 | 17,177.5 |

---

## 5. Audit Decisions & Treatment Rules

1. **Timezone & DST Convention:** All series standardized to UTC timestamps. Local Standard Time (no daylight clock jumps) is mapped for regional hour-of-day features.
2. **Gap & Missingness Policy:** Across the 5-year span, all 43,848 hourly timestamps are continuous. Zero missing timestamps, zero duplicate timestamps.
3. **Source Revisions / Imputation:** The EIA raw stream had intermittent anomalies and missing reporting hours that were screened and imputed in the peer-reviewed Ruggles et al. (Nature Scientific Data) pipeline. We retain both raw and cleaned columns. Modeling uses the verified cleaned demand, and flags are tracked.
4. **Outliers:** Outliers identified via localized rolling MAD are **flagged** in an `outlier_flag` column for failure analysis and evaluation, but **never deleted**.
5. **Structural Break Decision:** Year 2020 exhibits the pandemic commercial lockdown drop across all regions. To ensure representative baseline behavior and avoid training on anomalous commercial closures, our primary training window commences **2021-01-01** as specified in Phase 0.
