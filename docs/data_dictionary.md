# Data Dictionary

Comprehensive schema documentation for all raw datasets, processed feature matrices, and Tableau Public export files.

---

## 1. Raw Data Tables (`data/raw/`)

### Demand Files (`data/raw/demand/{REGION}_raw.csv`)
- **`date_time`** *(String / UTC Timestamp)*: Hourly timestamp formatted as `YYYY-MM-DD HH:MM:SS` in UTC.
- **`raw demand (MW)`** *(Numeric / Float)*: Unprocessed electricity demand reported directly on Form EIA-930. May contain dropouts, nulls, or zeros from reporting transmission outages.
- **`cleaned demand (MW)`** *(Numeric / Float)*: Peer-reviewed cleaned electricity demand series from Tyler Ruggles et al. (Nature Scientific Data). Imputes genuine transmission reporting gaps while screening anomalous spikes.

### Weather Files (`data/raw/weather/{REGION}_weather_raw.json`)
- **`temperature_2m`** *(Float / °C)*: 2-meter dry-bulb air temperature from ECMWF ERA5 Reanalysis.
- **`relative_humidity_2m`** *(Float / %)*: Relative humidity percentage at 2 meters $[0, 100]$.
- **`wind_speed_10m`** *(Float / km/h)*: 10-meter surface wind speed.
- **`cloud_cover`** *(Float / %)*: Total fractional cloud cover $[0, 100]$.
- **`direct_normal_irradiance`** *(Float / W/m²)*: Direct normal solar radiation flux.

---

## 2. Tableau Export Files (`data/exports/`)

### `tableau_hourly_forecasts.csv` (Primary Time-Series Table)
- **`timestamp`** *(DateTime)*: Hourly UTC timestamp.
- **`region`** *(String)*: Balancing authority identifier (`TEX`, `MIDA`, `NY`).
- **`actual_demand_mw`** *(Float)*: Ground truth observed demand in Megawatts (MW).
- **`forecast_mw`** *(Float)*: HistGradientBoosting point forecast (conditional mean).
- **`lower_bound_80`** *(Float)*: Lower bound of 80% nominal prediction interval (10th percentile).
- **`upper_bound_80`** *(Float)*: Upper bound of 80% nominal prediction interval (90th percentile).
- **`lower_bound_95`** *(Float)*: Lower bound of 95% nominal prediction interval (2.5th percentile).
- **`upper_bound_95`** *(Float)*: Upper bound of 95% nominal prediction interval (97.5th percentile).
- **`baseline_forecast_mw`** *(Float)*: 168-hour seasonal naive benchmark (same hour last week).
- **`error_mw`** *(Float)*: Point error ($\hat{y} - y$). Positive = over-forecast; negative = under-forecast.
- **`abs_error_mw`** *(Float)*: Absolute magnitude of error $|\hat{y} - y|$.
- **`temp_c`** *(Float)*: Surface air temperature in °C.
- **`hour`** *(Integer)*: Local Standard Time hour $\in [0, 23]$.
- **`is_weekend`** *(Binary / 0 or 1)*: 1 if Saturday or Sunday.
- **`is_holiday`** *(Binary / 0 or 1)*: 1 if US Federal Holiday.

### `tableau_region_dimension.csv`
- **`region_id`** *(String)*: Unique region code (`TEX`, `MIDA`, `NY`).
- **`region_name`** *(String)*: Full balancing authority title.
- **`latitude`** *(Float)*: Regional centroid latitude coordinate.
- **`longitude`** *(Float)*: Regional centroid longitude coordinate.
- **`timezone`** *(String)*: Local timezone identifier (`US/Central`, `US/Eastern`).

### `tableau_subgroup_metrics.csv`
- **`region`** *(String)*: Regional entity.
- **`dimension`** *(String)*: Evaluated operational segment (Hour of Day, Day Type, Holiday Status, Temp Band, Peak Status).
- **`segment`** *(String)*: Specific bucket name.
- **`n_obs`** *(Integer)*: Sample size count.
- **`mae`** *(Float)*: Mean Absolute Error in MW (suppressed if $N < 30$).
- **`bias`** *(Float)*: Mean Error in MW (suppressed if $N < 30$).
- **`coverage_80`** *(Float)*: Empirical 80% coverage rate.
- **`reliability`** *(String)*: Data reliability tier (`Suppressed (N < 30)`, `Exploratory (30-99)`, `Interpretable (100+)`).
