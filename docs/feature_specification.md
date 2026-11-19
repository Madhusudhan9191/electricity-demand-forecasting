# Feature Specification Table (Point-in-Time Safe)

This document formalizes every feature used in model training and inference, documenting its mathematical definition, primary source, data availability timing relative to the forecast origin (10:00 AM Local Standard Time on Day $D-1$), and leakage risk mitigation.

---

## 1. Feature Catalog

| Feature Name | Category | Mathematical / Algorithmic Definition | Source | Availability Timing | Leakage Risk & Safe Handling |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `hour` | Calendar | Hour of day $\in [0, 23]$ (Local Standard Time) | Deterministic timestamp | Known indefinitely in advance | **Zero Risk:** Pure calendar attribute. |
| `dayofweek` | Calendar | Day of week $\in [0, 6]$ (0=Monday, 6=Sunday) | Deterministic timestamp | Known indefinitely in advance | **Zero Risk:** Pure calendar attribute. |
| `is_weekend` | Calendar | Binary indicator: $\mathbf{1}(\text{dayofweek} \in \{5, 6\})$ | Deterministic timestamp | Known indefinitely in advance | **Zero Risk:** Calendar indicator. |
| `month` | Calendar | Month of year $\in [1, 12]$ | Deterministic timestamp | Known indefinitely in advance | **Zero Risk:** Calendar attribute. |
| `is_holiday` | Calendar | Binary indicator: $\mathbf{1}(\text{date} \in \text{US Federal Holidays})$ | Federal statute schedule | Known indefinitely in advance | **Zero Risk:** Pre-scheduled public calendar. |
| `is_bridge_day` | Calendar | Binary indicator for bridge workdays (e.g. Day after Thanksgiving) | Federal schedule heuristic | Known indefinitely in advance | **Zero Risk:** Pre-scheduled calendar rules. |
| `fourier_daily_sin1`, `cos1` | Harmonic | $\sin(2\pi h / 24)$, $\cos(2\pi h / 24)$ | Mathematical transformation | Known indefinitely in advance | **Zero Risk:** Bounded periodic functions $[-1, 1]$. |
| `fourier_daily_sin2`, `cos2` | Harmonic | $\sin(4\pi h / 24)$, $\cos(4\pi h / 24)$ | Mathematical transformation | Known indefinitely in advance | **Zero Risk:** Second daily harmonic. |
| `fourier_weekly_sin1`, `cos1` | Harmonic | $\sin(2\pi \cdot \text{hour\_of\_week} / 168)$, $\cos(\dots)$ | Mathematical transformation | Known indefinitely in advance | **Zero Risk:** Weekly cycle harmonic. |
| `fourier_annual_sin1`, `cos1` | Harmonic | $\sin(2\pi \cdot \text{hour\_of\_year} / 8760)$, $\cos(\dots)$ | Mathematical transformation | Known indefinitely in advance | **Zero Risk:** Annual solar cycle harmonic. |
| `fourier_annual_sin2`, `cos2` | Harmonic | $\sin(4\pi \cdot \text{hour\_of\_year} / 8760)$, $\cos(\dots)$ | Mathematical transformation | Known indefinitely in advance | **Zero Risk:** Semi-annual harmonic. |
| `temp_c` | Weather | 2m Air Temperature in °C | Open-Meteo ERA5 Reanalysis | Forecast available at origin (proxy) | **Low Risk (Proxy):** Observed actuals used as day-ahead forecast proxy. Quantified in Phase 5 via noise test ($\sigma=1.5^\circ\text{C}$). |
| `temp_squared` | Weather | $(\text{temp\_c})^2$ | Transformation of `temp_c` | Synchronous with `temp_c` | **Low Risk:** Captures U-shaped cooling/heating demand curve. |
| `cooling_degrees` | Weather | $\max(0, \text{temp\_c} - 18.0)$ (CDH) | Transformation of `temp_c` | Synchronous with `temp_c` | **Low Risk:** Non-linear cooling load above 18°C. |
| `heating_degrees` | Weather | $\max(0, 18.0 - \text{temp\_c})$ (HDH) | Transformation of `temp_c` | Synchronous with `temp_c` | **Low Risk:** Non-linear heating load below 18°C. |
| `rel_humidity_pct` | Weather | Relative humidity percentage $[0, 100]$ | Open-Meteo ERA5 Reanalysis | Forecast available at origin | **Low Risk:** Amplifies perceived heat and AC load. |
| `apparent_temp_c` | Weather | Steadman apparent temperature approximation (°C) | Transformation of temp & humidity | Synchronous with weather | **Low Risk:** Combined comfort index. |
| `wind_speed_kmh` | Weather | 10m Wind Speed (km/h) | Open-Meteo ERA5 Reanalysis | Forecast available at origin | **Low Risk:** Affects building infiltration and wind chill. |
| `cloud_cover_pct` | Weather | Total cloud cover percentage $[0, 100]$ | Open-Meteo ERA5 Reanalysis | Forecast available at origin | **Low Risk:** Proxy for rooftop solar generation offset. |
| `direct_solar_wm2` | Weather | Direct normal solar irradiance ($W/m^2$) | Open-Meteo ERA5 Reanalysis | Forecast available at origin | **Low Risk:** Drives behind-the-meter solar suppression. |
| `lag_48h` | Demand Lag | $y_{t-48}$ (Demand same hour two days prior) | Historical grid demand | Available at origin for all $h \in [0, 23]$ | **Zero Risk:** $48\text{h} \ge 15\text{h} + h$, strictly recorded prior to origin 10:00 D-1. |
| `lag_72h` | Demand Lag | $y_{t-72}$ (Demand same hour three days prior) | Historical grid demand | Available at origin for all $h \in [0, 23]$ | **Zero Risk:** Recorded prior to origin. |
| `lag_168h` | Demand Lag | $y_{t-168}$ (Demand same hour one week prior) | Historical grid demand | Available at origin for all $h \in [0, 23]$ | **Zero Risk:** 7-day persistence anchor. |
| `rolling_24h_mean_safe` | Demand Stat | Mean demand over 24h window ending at lag 48h | Historical grid demand | Available at origin | **Zero Risk:** Lagged rolling window. |
| `rolling_168h_mean_safe`| Demand Stat | Mean demand over 168h window ending at lag 48h | Historical grid demand | Available at origin | **Zero Risk:** Lagged rolling window. |
| `region` | Identifier | Categorical indicator (`ERCOT`, `PJM`, `NYIS`) | Metadata | Fixed | **Zero Risk:** Static structural entity. |

---

## 2. Forbidden Features (Explicitly Excluded)
1. **$y_{t-24}$ (Same-Hour Yesterday):** Strictly **FORBIDDEN** for hours 10:00 to 23:00 because at 10:00 AM on Day $D-1$, yesterday's hours 10:00 through 23:00 have not occurred yet.
2. **Same-Day Weather Observations:** Using actual weather measurements recorded at target hour $t$ without day-ahead proxy designation.
3. **Future Rolling Window Aggregations:** Any centered moving average that incorporates $t+k$ observations.
