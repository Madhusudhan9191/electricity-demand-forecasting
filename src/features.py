"""
Feature Engineering Module (Strictly Point-in-Time Safe).
Rule 3: Features may only use information available at the forecast origin (10:00 AM D-1).
Forecast Horizon: Day D (hours 00:00 to 23:00).
"""

import numpy as np
import pandas as pd
from src.holidays import get_us_federal_holidays


def build_calendar_and_fourier_features(df_timestamps, timezone_str="US/Eastern"):
    """
    Constructs calendar and periodic Fourier terms from timestamp.
    All calendar terms are known deterministically in advance (zero leakage).
    """
    df = pd.DataFrame(index=df_timestamps.index)
    ts_utc = df_timestamps
    ts_local = ts_utc.dt.tz_convert(timezone_str)

    df["hour"] = ts_local.dt.hour
    df["hour_utc"] = ts_utc.dt.hour
    df["dayofweek"] = ts_local.dt.dayofweek
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    df["month"] = ts_local.dt.month
    df["dayofyear"] = ts_local.dt.dayofyear

    # Daily Fourier harmonics (Period = 24h)
    hour_rad = 2 * np.pi * df["hour"] / 24.0
    df["fourier_daily_sin1"] = np.sin(hour_rad)
    df["fourier_daily_cos1"] = np.cos(hour_rad)
    df["fourier_daily_sin2"] = np.sin(2 * hour_rad)
    df["fourier_daily_cos2"] = np.cos(2 * hour_rad)

    # Weekly Fourier harmonics (Period = 168h)
    hour_of_week = df["dayofweek"] * 24 + df["hour"]
    week_rad = 2 * np.pi * hour_of_week / 168.0
    df["fourier_weekly_sin1"] = np.sin(week_rad)
    df["fourier_weekly_cos1"] = np.cos(week_rad)

    # Annual Fourier harmonics (Period = 8760h)
    hour_of_year = (df["dayofyear"] - 1) * 24 + df["hour"]
    annual_rad = 2 * np.pi * hour_of_year / 8760.0
    df["fourier_annual_sin1"] = np.sin(annual_rad)
    df["fourier_annual_cos1"] = np.cos(annual_rad)
    df["fourier_annual_sin2"] = np.sin(2 * annual_rad)
    df["fourier_annual_cos2"] = np.cos(2 * annual_rad)

    # Holidays
    years = sorted(ts_local.dt.year.unique())
    holidays_df = get_us_federal_holidays(int(years[0]), int(years[-1]))
    holiday_dates = set(holidays_df["date"])
    dates = ts_local.dt.date

    df["is_holiday"] = dates.isin(holiday_dates).astype(int)

    # Bridge day: Friday after Thanksgiving
    thx_dates = set(holidays_df[holidays_df["holiday_name"] == "Thanksgiving"]["date"])
    black_fridays = {d + pd.Timedelta(days=1) for d in thx_dates}
    df["is_bridge_day"] = dates.isin(black_fridays).astype(int)

    return df


def build_weather_features(df_weather):
    """
    Constructs non-linear heating/cooling degrees, heat index, and interaction terms.
    """
    df = pd.DataFrame(index=df_weather.index)

    temp_c = df_weather["temp_c"]
    rel_hum = df_weather["rel_humidity_pct"]

    df["temp_c"] = temp_c
    df["temp_squared"] = temp_c ** 2
    # Base temperature for degree days: 18.3 C (approx 65 F)
    df["cooling_degrees"] = np.maximum(0.0, temp_c - 18.3)
    df["heating_degrees"] = np.maximum(0.0, 18.3 - temp_c)

    df["rel_humidity_pct"] = rel_hum
    df["wind_speed_kmh"] = df_weather["wind_speed_kmh"]
    df["cloud_cover_pct"] = df_weather.get("cloud_cover_pct", pd.Series(0.0, index=df_weather.index))
    df["direct_solar_wm2"] = df_weather["direct_solar_wm2"]

    # Heat index approximation for high heat & humidity (Steadman formulation)
    df["apparent_temp_c"] = (
        temp_c + 0.33 * (rel_hum / 100.0 * 6.105 * np.exp(17.27 * temp_c / (237.7 + temp_c)))
        - 0.70 * (df_weather["wind_speed_kmh"] / 3.6) - 4.0
    )

    return df


def build_point_in_time_demand_lags(df_cleaned_demand):
    """
    Computes demand lag features guaranteed available at forecast origin (10:00 AM D-1).
    All lags are >= 48 hours.
    - lag_48h: same hour 2 days prior
    - lag_72h: same hour 3 days prior
    - lag_168h: same hour 7 days prior (same day last week)
    - lag_336h: same hour 14 days prior (2 weeks ago)
    - lag_504h: same hour 21 days prior (3 weeks ago)
    - lag_672h: same hour 28 days prior (4 weeks ago)
    - rolling_24h_mean_safe: rolling 24h mean shifted by 48h
    - rolling_168h_mean_safe: rolling 7d mean shifted by 48h
    """
    series = df_cleaned_demand.copy()

    lag_48 = series.shift(48)
    lag_72 = series.shift(72)
    lag_168 = series.shift(168)
    lag_336 = series.shift(336)
    lag_504 = series.shift(504)
    lag_672 = series.shift(672)

    rolling_24h_mean = series.shift(48).rolling(window=24, min_periods=12).mean()
    rolling_168h_mean = series.shift(48).rolling(window=168, min_periods=48).mean()
    rolling_24h_max = series.shift(48).rolling(window=24, min_periods=12).max()
    rolling_24h_min = series.shift(48).rolling(window=24, min_periods=12).min()

    # Lagged delta: change observed between D-2 and D-9 (point-in-time safe delta)
    lag_delta_48_168 = lag_48 - series.shift(216)

    df_lags = pd.DataFrame({
        "lag_48h": lag_48,
        "lag_72h": lag_72,
        "lag_168h": lag_168,
        "lag_336h": lag_336,
        "lag_504h": lag_504,
        "lag_672h": lag_672,
        "lag_delta_48_168": lag_delta_48_168,
        "rolling_24h_mean_safe": rolling_24h_mean,
        "rolling_168h_mean_safe": rolling_168h_mean,
        "rolling_24h_max_safe": rolling_24h_max,
        "rolling_24h_min_safe": rolling_24h_min,
    }, index=series.index)

    return df_lags


def construct_feature_dataset(df_demand, df_weather, region_id, timezone_str="US/Eastern"):
    """
    Merges and constructs the full point-in-time feature matrix for one region.
    Includes imputation flags and extreme-event policy flags.
    """
    timestamps = pd.to_datetime(df_demand["date_time"] if "date_time" in df_demand.columns else df_demand["timestamp"], utc=True)

    cal_feats = build_calendar_and_fourier_features(timestamps, timezone_str=timezone_str)
    wea_feats = build_weather_features(df_weather)
    lag_feats = build_point_in_time_demand_lags(df_demand["cleaned demand (MW)"])

    # Imputation flag: 1 if raw demand was revised or imputed by Ruggles et al.
    is_imputed = (df_demand["raw demand (MW)"] != df_demand["cleaned demand (MW)"]).astype(int)

    # Extreme event policy flags:
    # Uri: 2021-02-13 to 2021-02-19 (TEX)
    # Elliott: 2022-12-22 to 2022-12-26 (MIDA)
    is_uri = (
        (region_id == "TEX") &
        (timestamps >= pd.Timestamp("2021-02-13 00:00:00", tz="UTC")) &
        (timestamps <= pd.Timestamp("2021-02-19 23:00:00", tz="UTC"))
    ).astype(int)

    is_elliott = (
        (region_id == "MIDA") &
        (timestamps >= pd.Timestamp("2022-12-22 00:00:00", tz="UTC")) &
        (timestamps <= pd.Timestamp("2022-12-26 23:00:00", tz="UTC"))
    ).astype(int)

    is_extreme = (is_uri | is_elliott).astype(int)

    # Peak hour status:
    # Summer peak (Jun-Sep): 15-20 Central (TEX), 14-19 Eastern (MIDA, NY)
    # Winter peak (Dec-Feb): 07-09 and 17-20
    local_hour = cal_feats["hour"]
    month = cal_feats["month"]
    is_summer = month.isin([6, 7, 8, 9])
    is_winter = month.isin([12, 1, 2])

    if region_id == "TEX":
        peak_summer = is_summer & local_hour.isin([15, 16, 17, 18, 19, 20])
    else:
        peak_summer = is_summer & local_hour.isin([14, 15, 16, 17, 18, 19])

    peak_winter = is_winter & local_hour.isin([7, 8, 9, 17, 18, 19, 20])
    is_peak = (peak_summer | peak_winter).astype(int)

    # Target: raw demand MW, and relative delta (y_t - y_{t-168})
    demand_mw = df_demand["cleaned demand (MW)"]
    target_delta_168 = demand_mw - lag_feats["lag_168h"]

    df_full = pd.concat([
        pd.DataFrame({
            "timestamp": timestamps,
            "region": region_id,
            "demand_mw": demand_mw,
            "raw_demand_mw": df_demand["raw demand (MW)"],
            "is_imputed": is_imputed,
            "is_extreme_event": is_extreme,
            "is_peak_hour": is_peak,
            "target_delta_168": target_delta_168
        }),
        cal_feats,
        wea_feats,
        lag_feats
    ], axis=1)

    return df_full
