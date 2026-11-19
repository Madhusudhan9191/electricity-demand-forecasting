# Tableau Workbook Specification & Build Guide

Project: Electricity Demand Forecasting with Uncertainty
Platform: Tableau Public / Desktop (Offline Extract Mode)

## 1. Parameters Specification

| Parameter Name | Data Type | Allowable Values | Display As / Current Value | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `p_Region_Selector` | String | List: `All`, `ERCOT`, `PJM`, `NYIS` | Default: `ERCOT` | Global regional filter across dashboards |
| `p_Confidence_Level` | String | List: `80% Nominal`, `95% Nominal` | Default: `80% Nominal` | Toggles prediction interval ribbons |
| `p_Date_Range_Start` | Date | Range | Default: `2023-05-01` | Start of interactive time inspection window |
| `p_Date_Range_End` | Date | Range | Default: `2023-12-31` | End of interactive time inspection window |
| `p_Metric_View` | String | List: `MAE (MW)`, `MASE (Scaled)`, `Bias (MW)`, `sMAPE (%)` | Default: `MASE (Scaled)` | Dynamic KPI card switching |

---

## 2. Documented Calculated Fields & LOD Expressions

All formulas verified in Python and DuckDB.

### CF 1: Dynamic Lower Prediction Bound
- **Formula:**
  ```tableau
  IF [p_Confidence_Level] = '80% Nominal' THEN [lower_bound_80]
  ELSE [lower_bound_95]
  END
  ```
- **Purpose:** Swaps lower ribbon between 80% (10th percentile) and 95% (2.5th percentile).

### CF 2: Dynamic Upper Prediction Bound
- **Formula:**
  ```tableau
  IF [p_Confidence_Level] = '80% Nominal' THEN [upper_bound_80]
  ELSE [upper_bound_95]
  END
  ```
- **Purpose:** Swaps upper ribbon between 80% (90th percentile) and 95% (97.5th percentile).

### CF 3: Prediction Interval Band Width (MW)
- **Formula:** `[CF_Dynamic_Upper_Bound] - [CF_Dynamic_Lower_Bound]`
- **Purpose:** Renders the shading area on dual-axis line charts.

### CF 4: Prediction Interval Breach Flag
- **Formula:**
  ```tableau
  IF [actual_demand_mw] < [CF_Dynamic_Lower_Bound] OR [actual_demand_mw] > [CF_Dynamic_Upper_Bound] THEN 1
  ELSE 0
  END
  ```
- **Purpose:** Identifies hours when actual load breached the prediction interval.

### CF 5: Regional Average Demand (LOD Expression)
- **Formula:** `{FIXED [Region] : AVG([actual_demand_mw])}`
- **Purpose:** Scale normalization baseline for cross-regional tooltips.

### CF 6: Relative Error vs. Regional Scale
- **Formula:** `ABS([forecast_mw] - [actual_demand_mw]) / [CF_Regional_Avg_Demand_LOD]`
- **Purpose:** Scale-free normalized error comparison across ERCOT, PJM, and NYIS.

### CF 7: Directional Bias Indicator
- **Formula:**
  ```tableau
  IF [error_mw] > 0 THEN 'Over-Forecast (Reserve Excess)'
  ELSEIF [error_mw] < 0 THEN 'Under-Forecast (Reserve Scarcity Risk)'
  ELSE 'Exact Match'
  END
  ```
- **Purpose:** Color-coding directional risk for simulated operations analysts.

---

## 3. Dashboard Specifications & Step-by-Step Build Steps

### Dashboard 1: Problem & Benchmark Baselines
- **Goal:** Introduce the business problem, compare candidate models against seasonal persistence baselines across the 4 rolling validation folds.
- **Views:**
  1. *Executive KPI Banner:* Mean MASE (0.403), Baseline MASE (0.923), Overall Error Reduction (+56.3%).
  2. *Fold Comparison Chart:* Bar chart of MASE by fold and model, showing seasonal naive failure in Summer (1.254) and Winter (1.033).
  3. *Error Distribution:* Boxplot of absolute errors comparing HistGradientBoosting vs Seasonal Naive.

### Dashboard 2: Forecast vs. Actual with Prediction Interval Bands
- **Goal:** High-resolution time-series inspection of actual load, point forecast, and calibrated uncertainty ribbon.
- **Views:**
  1. *Dual-Axis Time Series:* Continuous date axis. Line 1: Actual Demand (Dark Navy). Line 2: Forecast Demand (Teal). Shaded Band: Lower to Upper Bound (Pale Aqua 25% opacity).
  2. *Breach Highlight Strip:* Red dot markers on actuals whenever load breaches the interval.
  3. *Date Range Slider:* Controlled via `p_Date_Range_Start` and `p_Date_Range_End`.

### Dashboard 3: Model vs. Baseline Skill by Hour & Season
- **Goal:** Operational drilldown showing when and where the model creates the greatest value.
- **Views:**
  1. *Hourly Skill Heatmap:* Rows = Region, Columns = Hour of Day (0–23). Color = MAE Skill Score (%).
  2. *Peak-Hour Stress Window:* Highlight on hours 14:00–20:00 showing peak MAE reduction.
  3. *Directional Bias Strip:* Bar chart showing positive vs negative bias by hour.

### Dashboard 4: Regional Geographic Map & Cross-Balancing Authority Analysis
- **Goal:** Geographic overview of ERCOT, PJM, and NYIS.
- **Views:**
  1. *Centroid Map:* Map plot with pie or circle markers sized by Average Demand (MW) and colored by Holdout MASE.
  2. *Regional Summary Cards:* Distinct scale cards showing ERCOT (~54k MW), PJM (~89k MW), and NYIS (~17k MW).

### Dashboard 5: Extreme Weather & Temperature Sensitivity Scenarios
- **Goal:** Stress-testing forecast responsiveness under extreme weather and temperature shifts.
- **Views:**
  1. *Temperature vs Demand Scatter (U-Curve):* X-axis = Air Temp (°C), Y-axis = Demand (MW). Clearly demonstrates non-linear heating (<10°C) and cooling (>22°C) response.
  2. *Simulation Scenario Waterfall:* Demand change under Base Actual, Base +2°C (+3.2% load), and Base +5°C (+8.7% load).
  3. *Explicit Callout:* 'Model-based statistical association, not a prediction of real physical grid events.'

### Dashboard 6: Monitoring, Data Quality & Model Card
- **Goal:** Audit transparency, production drift tracking, and model card documentation.
- **Views:**
  1. *Data Quality Assertion Grid:* Status badges (PASS / WARNING) for all 6 assertions across all regions.
  2. *PSI Drift Gauge:* Displaying ERCOT demand drift (PSI = 0.6293) due to 2023 heatwave and growth.
  3. *Formal Model Card:* Embedded text card with intended use, training window, holdout isolation notice, and documented limitations.
