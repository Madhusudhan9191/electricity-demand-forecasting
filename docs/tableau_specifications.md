# Tableau Workbook Specification & Build Guide

**Project:** Electricity Demand Forecasting with Uncertainty (Day-Ahead Multi-Region)
**Regions:** TEX (Texas Footprint / ERCOT), MIDA (Mid-Atlantic / PJM), NY (New York / NYISO)
**Dataset Source:** Ruggles et al. (*Nature Scientific Data*, 2020), CC-BY 4.0
**Evaluation Holdout:** Calendar 2024 (Single-Touch, 8,784 hours per region)
**Platform:** Tableau Desktop / Tableau Public (Extract Mode)

## 1. Parameters Specification

| Parameter Name | Data Type | Allowable Values | Display As / Current Value | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `p_Region_Selector` | String | List: `All`, `TEX`, `MIDA`, `NY` | Default: `TEX` | Global regional filter across dashboards |
| `p_Confidence_Level` | String | List: `80% Nominal`, `95% Nominal` | Default: `80% Nominal` | Toggles prediction interval ribbons |
| `p_Date_Range_Start` | Date | Range | Default: `2024-01-01` | Start of interactive time inspection window |
| `p_Date_Range_End` | Date | Range | Default: `2024-12-31` | End of interactive time inspection window |
| `p_Metric_View` | String | List: `MAE (MW)`, `rMAE (Relative)`, `Bias (MW)` | Default: `rMAE (Relative)` | Dynamic KPI card switching |

---

## 2. Documented Calculated Fields & LOD Expressions

### CF 1: Dynamic Lower Prediction Bound
```tableau
IF [p_Confidence_Level] = '80% Nominal' THEN [lower_bound_80]
ELSE [lower_bound_95]
END
```

### CF 2: Dynamic Upper Prediction Bound
```tableau
IF [p_Confidence_Level] = '80% Nominal' THEN [upper_bound_80]
ELSE [upper_bound_95]
END
```

### CF 3: Prediction Interval Band Width (MW)
```tableau
[Dynamic Upper Bound] - [Dynamic Lower Bound]
```

### CF 4: Prediction Interval Breach Flag
```tableau
IF [actual_demand_mw] < [Dynamic Lower Bound] OR [actual_demand_mw] > [Dynamic Upper Bound] THEN 1
ELSE 0
END
```

### CF 5: Regional Average Demand (LOD Expression)
```tableau
{FIXED [Region] : AVG([actual_demand_mw])}
```

### CF 6: Directional Bias Indicator
```tableau
IF [error_mw] > 0 THEN 'Over-Forecast (Reserve Excess)'
ELSEIF [error_mw] < 0 THEN 'Under-Forecast (Reserve Scarcity Risk)'
ELSE 'Exact Match'
END
```

---

## 3. Dashboard Architecture & Scope

The Tableau visual delivery is structured into **Core Executive & Operational Dashboards** (primary workbook deliverables) and **Modular Analytical Extensions**:

### Core Delivered Dashboards (In Primary Workbook)

#### Dashboard 02: Forecast vs. Actual with Prediction Uncertainty (`02_Forecast_and_Uncertainty`)
- **Primary Data Source:** `tableau_hourly_forecasts.csv`
- **Purpose:** Primary executive and operations monitoring view.
- **Components:**
  1. **KPI Banner Cards:** Holdout MAE (MW), Prediction Interval Breach Rate, and Selected Region indicator.
  2. **Main Time Series View (`Forecast vs Actual (Holdout)`):** Full-year Calendar 2024 hourly actual demand vs. day-ahead point forecast with synchronized shaded prediction interval ribbon.
  3. **Diurnal Profile (`Hourly Peak Profile`):** Average 24-hour diurnal load curve comparing actual peak vs. forecasted peak hour.
- **Interactivity:** Filtered dynamically by `p_Region_Selector` and `p_Confidence_Level` (80% vs 95%).

#### Dashboard 03: Operational Accuracy & Operating Conditions (`03_Operational_Performance`)
- **Primary Data Source:** `tableau_hourly_forecasts.csv` (and `tableau_subgroup_metrics.csv`)
- **Purpose:** Operational decision-support for dispatch and reserve planners.
- **Components:**
  1. **Directional Bias Profile (`Hourly Directional Bias`):** 24-hour divergent bar chart displaying over-forecast (excess reserve) vs. under-forecast (scarcity risk) hours.
  2. **Error by Condition (`Error by Operating Condition`):** Segmented bar chart analyzing MAE across temperature bands (<0°C, 0-10°C, 10-20°C, 20-30°C, >30°C) and peak vs off-peak operating states.
- **Interactivity:** Linked to global region selector.

---

### Modular Analytical Extensions (Template Specifications)

The following views are formally designed as modular extensions connecting to the generated flat extracts:
- **Dashboard 01 (Model Selection & Folds):** Multi-model validation leaderboard across 4 seasonal folds (`tableau_backtest_folds.csv`).
- **Dashboard 04 (Regional Overview):** Centroid geospatial map of TEX, MIDA, and NY footprints (`tableau_region_dimension.csv`).
- **Dashboard 05 (Temperature Sensitivity U-Curve):** Non-linear load response curve by 2°C temperature bins (`tableau_hourly_forecasts.csv` / `tableau_weather_sensitivity.csv`).
- **Dashboard 06 (Data Quality & Monitoring):** Automated audit pipeline status grid and drift tracking (`tableau_data_quality_log.csv`).
