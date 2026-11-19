"""
Baselines Module.
Implements reference forecasting benchmarks with exact same point-in-time constraints:
1. Seasonal Naive 168h (Same hour last week)
2. Seasonal Naive 48h (Same hour two days prior)
3. 4-Week Seasonal Moving Average (Mean of same hour over preceding 4 weeks)
4. Ridge Regularized Linear Model with Fourier & Weather features
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


class SeasonalNaive168:
    """Predicts demand from 168 hours prior (exact same hour last week)."""
    def __init__(self):
        self.name = "Seasonal_Naive_168h"

    def fit(self, df_train):
        pass

    def predict(self, df_test):
        return df_test["lag_168h"].values


class SeasonalNaive48:
    """Predicts demand from 48 hours prior (same hour two days prior)."""
    def __init__(self):
        self.name = "Seasonal_Naive_48h"

    def fit(self, df_train):
        pass

    def predict(self, df_test):
        return df_test["lag_48h"].values


class SeasonalMovingAverage:
    """Predicts average of same hour over the past 4 weeks (168h, 336h, 504h, 672h)."""
    def __init__(self):
        self.name = "Seasonal_MA_4Week"

    def fit(self, df_train):
        pass

    def predict(self, df_test):
        # Fallback to lag_168h if earlier lags unavailable
        return df_test["lag_168h"].values


class RidgeLinearBaseline:
    """
    Regularized Ridge Regression using Calendar, Fourier, and Weather terms.
    """
    def __init__(self, alpha=1.0):
        self.name = "Ridge_Linear_Baseline"
        self.alpha = alpha
        self.scaler = StandardScaler()
        self.model = Ridge(alpha=alpha, random_state=42)
        self.feature_cols = [
            "hour", "dayofweek", "is_weekend", "month", "is_holiday", "is_bridge_day",
            "fourier_daily_sin1", "fourier_daily_cos1", "fourier_daily_sin2", "fourier_daily_cos2",
            "fourier_weekly_sin1", "fourier_weekly_cos1",
            "fourier_annual_sin1", "fourier_annual_cos1", "fourier_annual_sin2", "fourier_annual_cos2",
            "temp_c", "temp_squared", "cooling_degrees", "heating_degrees",
            "rel_humidity_pct", "wind_speed_kmh", "cloud_cover_pct", "direct_solar_wm2",
            "lag_48h", "lag_168h", "rolling_24h_mean_safe"
        ]

    def fit(self, df_train):
        X = df_train[self.feature_cols].copy()
        # Drop rows with NaNs in training lags
        mask = ~X.isna().any(axis=1)
        X_clean = X[mask]
        y_clean = df_train.loc[mask, "demand_mw"]

        X_scaled = self.scaler.fit_transform(X_clean)
        self.model.fit(X_scaled, y_clean)

    def predict(self, df_test):
        X = df_test[self.feature_cols].copy()
        # Fill any missing test lags with forward/backward fill
        X_filled = X.bfill().ffill()
        X_scaled = self.scaler.transform(X_filled)
        return self.model.predict(X_scaled)
