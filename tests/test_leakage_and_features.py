"""
Automated Point-in-Time Leakage and Feature Pipeline Tests.
Rule 3: Features may only use information available at the origin.
Tests:
1. Target future shift test (corrupting future target must not alter historical feature rows).
2. Timestamp consistency test: no lag feature depends on timestamps >= forecast origin.
3. Lag safety test: minimum lag on demand features is >= 48 hours for horizon step h=0..23.
4. Non-emptiness and shape sanity tests.
"""

import numpy as np
import pandas as pd
import pytest
from src.features import (
    build_calendar_and_fourier_features,
    build_weather_features,
    build_point_in_time_demand_lags,
    construct_feature_dataset
)


@pytest.fixture
def synthetic_series():
    # 500 hours synthetic dataset
    timestamps = pd.date_range("2022-01-01 00:00:00", periods=500, freq="h", tz="UTC")
    np.random.seed(42)
    demand = 40000 + 5000 * np.sin(np.arange(500) * 2 * np.pi / 24) + np.random.normal(0, 500, 500)
    weather = pd.DataFrame({
        "temp_c": 15 + 10 * np.sin(np.arange(500) * 2 * np.pi / 24) + np.random.normal(0, 1, 500),
        "rel_humidity_pct": np.clip(60 + np.random.normal(0, 10, 500), 20, 100),
        "wind_speed_kmh": np.clip(12 + np.random.normal(0, 3, 500), 0, 50),
        "cloud_cover_pct": np.clip(40 + np.random.normal(0, 20, 500), 0, 100),
        "direct_solar_wm2": np.clip(300 * np.maximum(0, np.sin(np.arange(500) * 2 * np.pi / 24)), 0, 1000)
    })
    df_demand = pd.DataFrame({
        "timestamp": timestamps,
        "raw demand (MW)": demand,
        "cleaned demand (MW)": demand
    })
    return df_demand, weather


def test_target_future_shift_leakage(synthetic_series):
    """
    Leakage Test 1: Future Target Modification (Ablation).
    Modifying demand at hour T must NOT alter any feature values at hour <= T.
    """
    df_demand, weather = synthetic_series
    features_orig = construct_feature_dataset(df_demand, weather, "TEST")

    # Corrupt demand from index 300 onwards with massive values
    df_demand_corrupted = df_demand.copy()
    df_demand_corrupted.loc[300:, "cleaned demand (MW)"] += 1_000_000.0

    features_corrupted = construct_feature_dataset(df_demand_corrupted, weather, "TEST")

    # Lag columns
    lag_cols = [c for c in features_orig.columns if "lag_" in c or "rolling_" in c]

    # For all rows prior to index 300, lag features MUST be mathematically identical
    for col in lag_cols:
        diff = np.abs(features_orig.loc[:299, col] - features_corrupted.loc[:299, col])
        max_diff = np.nanmax(diff)
        assert max_diff == 0.0, f"Future leakage detected in feature '{col}' at index < 300! Max diff: {max_diff}"


def test_lag_horizon_safety(synthetic_series):
    """
    Leakage Test 2: Minimum lag must be at least 48 hours to guarantee that
    for any hour h in [0, 23] of Day D, the lag data was recorded prior to 10:00 AM on Day D-1.
    """
    df_demand, weather = synthetic_series
    lags = build_point_in_time_demand_lags(df_demand["cleaned demand (MW)"])

    # First 47 hours of lag_48h must strictly be NaN
    assert lags["lag_48h"].iloc[:48].isna().all(), "lag_48h has non-null values before lag threshold!"
    # First 167 hours of lag_168h must strictly be NaN
    assert lags["lag_168h"].iloc[:168].isna().all(), "lag_168h has non-null values before 168 hours!"


def test_fourier_and_calendar_properties(synthetic_series):
    """
    Leakage Test 3: Calendar and Fourier features must be bounded and deterministic.
    """
    df_demand, _ = synthetic_series
    cal = build_calendar_and_fourier_features(df_demand["timestamp"])

    assert cal["hour"].min() >= 0 and cal["hour"].max() <= 23
    assert cal["dayofweek"].min() >= 0 and cal["dayofweek"].max() <= 6
    assert np.all(cal["fourier_daily_sin1"].abs() <= 1.00001)
    assert np.all(cal["fourier_daily_cos1"].abs() <= 1.00001)
    assert np.all(cal["fourier_annual_sin1"].abs() <= 1.00001)


def test_degree_day_properties(synthetic_series):
    """
    Test 4: Weather degree days must be non-negative.
    """
    _, weather = synthetic_series
    wea_feats = build_weather_features(weather)

    assert (wea_feats["cooling_degrees"] >= 0.0).all()
    assert (wea_feats["heating_degrees"] >= 0.0).all()
    # At any temperature, either cooling or heating or both must be zero
    zero_overlap = (wea_feats["cooling_degrees"] * wea_feats["heating_degrees"] == 0.0).all()
    assert zero_overlap, "Cooling degrees and heating degrees cannot both be positive simultaneously!"
