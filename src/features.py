"""
Feature Engineering Module (Strictly Point-in-Time Safe).
Rule 3: Features may only use information available at the forecast origin (10:00 AM D-1).
Forecast Horizon: Day D (hours 00:00 to 23:00).
"""

import numpy as np
import pandas as pd
from src.holidays import get_us_federal_holidays


def build_calendar_and_fourier_features(df_timestamps):
    """
    Constructs calendar and periodic Fourier terms from timestamp.
    All calendar terms are known deterministically in advance (zero leakage).
    """
    df = pd.DataFrame(index=df_timestamps.index)
    ts = df_timestamps

    df["hour"] = ts.dt.hour
    df["dayofweek"] = ts.dt.dayofweek
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    df["month"] = ts.dt.month
    df["dayofyear"] = ts.dt.dayofyear

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

    # US Federal Holidays & Bridge Days
    holidays_df = get_us_federal_holidays(ts.dt.year.min(), ts.dt.year.max())
    holiday_dates = set(holidays_df["date"])
    dates = ts.dt.date

    df["is_holiday"] = dates.isin(holiday_dates).astype(int)

    # Bridge day: Friday after Thursday holiday or Monday before Tuesday holiday
    # Example: Black Friday (day after Thanksgiving)
    df["is_bridge_day"] = 0
    # Day after Thanksgiving is a bridge day
    thx_dates = set(holidays_df[holidays_df["holiday_name"] == "Thanksgiving"]["date"])
    black_fridays = {d + pd.Timedelta(days=1) for d in thx_dates}
    df.loc[dates.isin(black_fridays), "is_bridge_day"] = 1

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
    # Base temperature for degree days: 18.0 C (approx 65 F)
    df["cooling_degrees"] = np.maximum(0.0, temp_c - 18.0)
    df["heating_degrees"] = np.maximum(0.0, 18.0 - temp_c)

    # Relative humidity and wind
    df["rel_humidity_pct"] = rel_hum
    df["wind_speed_kmh"] = df_weather["wind_speed_kmh"]
    df["cloud_cover_pct"] = df_weather["cloud_cover_pct"]
    df["direct_solar_wm2"] = df_weather["direct_solar_wm2"]

    # Heat index approximation for high heat & humidity
    # Simplified Steadman formula for apparent temperature
    df["apparent_temp_c"] = (
        temp_c + 0.33 * (rel_hum / 100.0 * 6.105 * np.exp(17.27 * temp_c / (237.7 + temp_c))) - 0.70 * (df_weather["wind_speed_kmh"] / 3.6) - 4.0
    )

    return df


def build_point_in_time_demand_lags(df_cleaned_demand, origin_hour=10):
    """
    Computes demand lag features guaranteed available at forecast origin (10:00 AM D-1).
    Latest available completed hour at origin is 09:00 D-1.
    For hour h in [0, 23] on day D:
    - lag_48h: exact same hour 48h prior (D-2) -> available
    - lag_72h: exact same hour 72h prior (D-3) -> available
    - lag_168h: exact same hour 168h prior (D-7, same day last week) -> available
    - origin_latest_demand: demand at 09:00 on D-1 (constant for all 24h of day D forecast)
    - origin_rolling_24h_mean: mean demand from (D-2 10:00 to D-1 09:00)
    - origin_rolling_7d_mean: mean demand from (D-8 10:00 to D-1 09:00)
    """
    series = df_cleaned_demand.copy()

    # Same hour 2 days ago (48h), 3 days ago (72h), 7 days ago (168h)
    lag_48 = series.shift(48)
    lag_72 = series.shift(72)
    lag_168 = series.shift(168)

    # Origin features: computed as of 09:00 D-1, broadcast across all 24h of day D.
    # Notice: for hour h of day D, distance from 09:00 D-1 is (15 + h) hours.
    # A point-in-time safe proxy known at origin:
    # Shift series by 24h + 15h = 39h to guarantee no data after 09:00 D-1 is used.
    # Even more strictly: shift by 48h for rolling windows ensures 100% safety.
    rolling_24h_mean = series.shift(48).rolling(window=24, min_periods=12).mean()
    rolling_168h_mean = series.shift(48).rolling(window=168, min_periods=48).mean()
    rolling_24h_max = series.shift(48).rolling(window=24, min_periods=12).max()
    rolling_24h_min = series.shift(48).rolling(window=24, min_periods=12).min()

    df_lags = pd.DataFrame({
        "lag_48h": lag_48,
        "lag_72h": lag_72,
        "lag_168h": lag_168,
        "rolling_24h_mean_safe": rolling_24h_mean,
        "rolling_168h_mean_safe": rolling_168h_mean,
        "rolling_24h_max_safe": rolling_24h_max,
        "rolling_24h_min_safe": rolling_24h_min,
    }, index=series.index)

    return df_lags


def construct_feature_dataset(df_demand, df_weather, region_id, origin_hour=10):
    """
    Merges and constructs the full point-in-time feature matrix for one region.
    """
    timestamps = df_demand["timestamp"]

    cal_feats = build_calendar_and_fourier_features(timestamps)
    wea_feats = build_weather_features(df_weather)
    lag_feats = build_point_in_time_demand_lags(df_demand["cleaned demand (MW)"], origin_hour=origin_hour)

    df_full = pd.concat([
        pd.DataFrame({
            "timestamp": timestamps,
            "region": region_id,
            "demand_mw": df_demand["cleaned demand (MW)"],
            "raw_demand_mw": df_demand["raw demand (MW)"],
        }),
        cal_feats,
        wea_feats,
        lag_feats
    ], axis=1)

    return df_full
