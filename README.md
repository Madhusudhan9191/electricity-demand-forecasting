# Electricity Demand Forecasting with Uncertainty

An independent portfolio project demonstrating point-in-time time-series forecasting, calibrated prediction intervals, operational monitoring, and Tableau Public dashboard design across multiple regional balancing authorities.

---

## 1. Important Disclosures & Project Boundaries
- **Independent Portfolio Project:** Project 4 of 4 (demonstrating time-series forecasting, quantile uncertainty, and Tableau craft).
- **Not an Operational Tool:** This project is offline and observational. It is not affiliated with or deployed by any grid operator or balancing authority.
- **No Causal Inferences:** Relationships between weather covariates and demand represent empirical model-based statistical associations, not physical causal assertions.
- **Point-in-Time Assurance:** All features adhere to a strict forecast origin cutoff (10:00 AM Local Standard Time on Day $D-1$). The final holdout period (2023-05-01 to 2023-12-31) was evaluated exactly once.

---

## 2. Business Question & Stakeholders

> *Can we forecast next-day hourly electricity demand for several regional balancing authorities better than simple seasonal baselines, and how uncertain are those forecasts, especially at peak hours and during extreme weather conditions?*

- **Planning Analyst (Simulated):** Assesses multi-day reserve capacity, extreme-weather tail risks, scale-free forecast error (MASE), and 80%/95% prediction interval coverage.
- **Operations Analyst (Simulated):** Focuses on day-ahead dispatch alignment, directional bias, and peak-hour error (MAE during 14:00–20:00).

---

## 3. Data Sources & Open Licenses

| Source | Dataset | Geographic Scope | Time Horizon | License | Citation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **U.S. Energy Information Administration (EIA)** | Form EIA-930 Hourly Electric Grid Monitor (`BALANCES`) | Balancing Authorities: ERCOT (Texas), PJM (Mid-Atlantic/Midwest), NYIS (New York) | 2020-01-01 to 2024-12-31 (43,848 continuous hours) | **U.S. Government Work / Public Domain** (17 U.S.C. § 105) | U.S. Energy Information Administration; Curated via Ruggles et al. (Nature Scientific Data 2020/2025). |
| **Open-Meteo Historical Weather API** | ECMWF ERA5 Reanalysis | Population centroids: Dallas/Fort Worth, Philadelphia, New York City | 2020-01-01 to 2024-12-31 (Hourly) | **CC-BY 4.0** (Attribution: *"Weather data by Open-Meteo.com"*) | Hersbach et al. (2020), ERA5 global reanalysis, ECMWF; Open-Meteo API. |

---

## 4. Quantitative Results on Final Holdout (Touched Once)

Evaluated over 5,880 out-of-sample hours per region (May 1, 2023 to December 31, 2023) with 1,000 block-bootstrap resamples (block size = 24 hours):

| Region | Model MASE [95% CI] | Base 168h MASE | Skill Score (%) | Model MAE (MW) | Base MAE (MW) | MAE Diff (MW) [95% CI] | Model RMSE (MW) | Peak-Hour MAE (MW) | 80% Nom Cov | 95% Nom Cov |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ERCOT** | **0.729** [0.686, 0.778] | 0.884 | **+17.5%** | 3,330.3 | 4,034.8 | -704.5 [-937.1, -485.4] | 4,496.2 | 3,923.4 | 0.301 | 0.506 |
| **PJM** | **0.419** [0.387, 0.452] | 0.831 | **+49.6%** | 3,396.3 | 6,732.4 | -3,336.1 [-3,812.5, -2,883.2] | 4,535.8 | 3,697.5 | 0.564 | 0.769 |
| **NYIS** | **0.435** [0.407, 0.465] | 1.002 | **+56.6%** | 614.6 | 1,416.7 | -802.1 [-907.3, -700.1] | 864.0 | 737.9 | 0.539 | 0.735 |

---

## 5. Key Empirical Findings & Monitoring Drift
1. **Machine Learning vs. Seasonal Naive:** HistGradientBoosting outperformed the 168-hour persistence baseline across all regions, delivering a **49.6% error reduction in PJM** and **56.6% in NYIS**.
2. **Seasonal Fragility of Baselines:** During Summer Peak (Fold 1) and Winter Peak (Fold 3), seasonal naive baselines failed severely ($\text{MASE} = 1.254$ and $1.033$), whereas the ML model maintained consistent accuracy.
3. **Drift & Under-Coverage in Growing Grids (ERCOT):** On the holdout, ERCOT exhibited severe feature drift ($\text{PSI} = 0.6293$) due to an all-time record heatwave (+26.8% mean temperature, +70.1% cooling degrees) combined with secular load growth (+17.6% mean demand increase). This caused static intervals calibrated on historical data to drop to 30.1% coverage, illustrating the real-world operational need for dynamic interval updating.
4. **Programmatic 3-Way Reconciliation:** Verified that Python metrics and an independent SQL query (SQLite / DuckDB) match across all regions within 0.0000 tolerance.

---

## 6. How to Reproduce from Scratch

```bash
# 1. Clone repository and set up environment
git clone <repo_url>
cd electricity-demand-forecasting

# 2. Run data download pipeline (saves immutable raw files)
python src/data_loader.py

# 3. Execute Phase 1 data audit
python src/data_audit.py

# 4. Run automated unit & point-in-time leakage tests
pytest tests/test_leakage_and_features.py -v

# 5. Run feature generation and rolling-origin backtests (Phase 2, 3, 4)
python src/pipeline_backtest.py

# 6. Execute final holdout evaluation (Phase 5)
python src/pipeline_holdout_evaluation.py

# 7. Run drift monitoring and data quality assertions (Phase 6)
python src/pipeline_monitoring.py

# 8. Export Tableau package and specification (Phase 7)
python src/generate_tableau_package.py

# 9. Run cross-engine reconciliation (Phase 8)
python src/reconciliation.py
```

---

## 7. Project Artifacts & Documentation
- [Phase 0 Specification](file:///c:/Users/LENOVO/OneDrive/Desktop/electricity-demand%20forecasting/docs/phase_0_specification.md)
- [Data Audit Report](file:///c:/Users/LENOVO/OneDrive/Desktop/electricity-demand%20forecasting/reports/phase1_data_audit.md)
- [Feature Specification Table](file:///c:/Users/LENOVO/OneDrive/Desktop/electricity-demand%20forecasting/docs/feature_specification.md)
- [Model Selection Leaderboard](file:///c:/Users/LENOVO/OneDrive/Desktop/electricity-demand%20forecasting/reports/model_selection_comparison.md)
- [Final Holdout Evaluation Report](file:///c:/Users/LENOVO/OneDrive/Desktop/electricity-demand%20forecasting/reports/final_holdout_report.md)
- [Data Quality & Monitoring Report](file:///c:/Users/LENOVO/OneDrive/Desktop/electricity-demand%20forecasting/reports/data_quality_and_monitoring_report.md)
- [Tableau Workbook Specifications & Build Steps](file:///c:/Users/LENOVO/OneDrive/Desktop/electricity-demand%20forecasting/docs/tableau_specifications.md)
- [Reconciliation Report](file:///c:/Users/LENOVO/OneDrive/Desktop/electricity-demand%20forecasting/reports/reconciliation_report.md)
- [Interview Defense Notes](file:///c:/Users/LENOVO/OneDrive/Desktop/electricity-demand%20forecasting/docs/interview_defense_notes.md)
