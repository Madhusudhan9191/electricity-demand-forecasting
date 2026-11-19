"""
Model Pipeline Module for Point Forecasts and Quantile Prediction Intervals.
Implements:
1. HistGradientBoostingRegressor (Squared Error for mean point forecast).
2. HistGradientBoostingRegressor (Quantile Loss for 10%, 50%, 90% and 2.5%, 97.5% quantiles).
3. Conformal Prediction Intervals (Calibrated empirical non-conformity intervals).
4. Equal-Weighted Ensemble (Linear Ridge + Gradient Boosting).
5. Model persistence and metadata logging in models/.
"""

import json
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from src.baselines import RidgeLinearBaseline

MODEL_FEATURE_COLS = [
    "hour", "dayofweek", "is_weekend", "month", "dayofyear",
    "is_holiday", "is_bridge_day",
    "fourier_daily_sin1", "fourier_daily_cos1", "fourier_daily_sin2", "fourier_daily_cos2",
    "fourier_weekly_sin1", "fourier_weekly_cos1",
    "fourier_annual_sin1", "fourier_annual_cos1", "fourier_annual_sin2", "fourier_annual_cos2",
    "temp_c", "temp_squared", "cooling_degrees", "heating_degrees",
    "rel_humidity_pct", "apparent_temp_c", "wind_speed_kmh",
    "cloud_cover_pct", "direct_solar_wm2",
    "lag_48h", "lag_72h", "lag_168h",
    "rolling_24h_mean_safe", "rolling_168h_mean_safe",
    "rolling_24h_max_safe", "rolling_24h_min_safe"
]


class QuantileHistGradientBoosting:
    """
    Multi-quantile HistGradientBoosting models for point and interval forecasting.
    Estimates quantiles: 0.025, 0.10, 0.50 (median point), 0.90, 0.975.
    """
    def __init__(self, max_iter=150, max_depth=6, learning_rate=0.08, min_samples_leaf=25, random_state=42):
        self.name = "HistGradientBoosting_Quantile"
        self.params = {
            "max_iter": max_iter,
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "min_samples_leaf": min_samples_leaf,
            "random_state": random_state
        }
        self.feature_cols = MODEL_FEATURE_COLS
        self.quantiles = [0.025, 0.10, 0.50, 0.90, 0.975]
        self.models = {}

    def fit(self, df_train):
        X = df_train[self.feature_cols].copy()
        mask = ~X.isna().any(axis=1)
        X_clean = X[mask]
        y_clean = df_train.loc[mask, "demand_mw"]

        # Train separate model for each quantile
        for q in self.quantiles:
            model = HistGradientBoostingRegressor(
                loss="quantile",
                quantile=q,
                max_iter=self.params["max_iter"],
                max_depth=self.params["max_depth"],
                learning_rate=self.params["learning_rate"],
                min_samples_leaf=self.params["min_samples_leaf"],
                random_state=self.params["random_state"]
            )
            model.fit(X_clean, y_clean)
            self.models[q] = model

    def predict_all(self, df_test):
        X = df_test[self.feature_cols].copy().bfill().ffill()
        preds = {}
        for q, model in self.models.items():
            preds[q] = model.predict(X)

        # Post-processing: monotonic quantile sorting to prevent quantile crossing
        # i.e. q_025 <= q_10 <= q_50 <= q_90 <= q_975
        matrix = np.column_stack([preds[q] for q in self.quantiles])
        matrix_sorted = np.sort(matrix, axis=1)

        result = {
            "q_025": matrix_sorted[:, 0],
            "q_10": matrix_sorted[:, 1],
            "point_pred": matrix_sorted[:, 2],  # Median
            "q_90": matrix_sorted[:, 3],
            "q_975": matrix_sorted[:, 4]
        }
        return result


class PointHistGradientBoosting:
    """
    Mean-squared-error optimized HistGradientBoosting with Conformal Prediction Intervals.
    """
    def __init__(self, max_iter=150, max_depth=6, learning_rate=0.08, min_samples_leaf=25, random_state=42):
        self.name = "HistGradientBoosting_Point_Conformal"
        self.params = {
            "max_iter": max_iter,
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "min_samples_leaf": min_samples_leaf,
            "random_state": random_state
        }
        self.feature_cols = MODEL_FEATURE_COLS
        self.model = HistGradientBoostingRegressor(
            loss="squared_error",
            max_iter=max_iter,
            max_depth=max_depth,
            learning_rate=learning_rate,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state
        )
        self.residual_q80 = None
        self.residual_q95 = None

    def fit(self, df_train):
        X = df_train[self.feature_cols].copy()
        mask = ~X.isna().any(axis=1)
        X_clean = X[mask]
        y_clean = df_train.loc[mask, "demand_mw"]

        # Train point model
        self.model.fit(X_clean, y_clean)

        # Calibrate conformal residuals on training set (or calibration slice)
        preds_train = self.model.predict(X_clean)
        abs_residuals = np.abs(y_clean.values - preds_train)
        # Empirical (1-alpha) quantiles of absolute error
        self.residual_q80 = float(np.percentile(abs_residuals, 80.0))
        self.residual_q95 = float(np.percentile(abs_residuals, 95.0))

    def predict(self, df_test):
        X = df_test[self.feature_cols].copy().bfill().ffill()
        point = self.model.predict(X)
        return {
            "point_pred": point,
            "q_10": point - self.residual_q80,
            "q_90": point + self.residual_q80,
            "q_025": point - self.residual_q95,
            "q_975": point + self.residual_q95
        }


class SimpleEnsemble:
    """
    Ensemble averaging Linear Ridge baseline and HistGradientBoosting point forecast.
    """
    def __init__(self):
        self.name = "Ensemble_Ridge_HGB"
        self.linear = RidgeLinearBaseline(alpha=10.0)
        self.hgb = PointHistGradientBoosting()
        self.residual_q80 = None
        self.residual_q95 = None

    def fit(self, df_train):
        self.linear.fit(df_train)
        self.hgb.fit(df_train)

        # Calibrate ensemble residuals
        p_lin = self.linear.predict(df_train)
        p_hgb = self.hgb.predict(df_train)["point_pred"]
        p_ens = 0.5 * (p_lin + p_hgb)

        y = df_train["demand_mw"].values
        # Drop warm-up rows
        mask = ~np.isnan(p_ens)
        abs_res = np.abs(y[mask] - p_ens[mask])
        self.residual_q80 = float(np.percentile(abs_res, 80.0))
        self.residual_q95 = float(np.percentile(abs_res, 95.0))

    def predict(self, df_test):
        p_lin = self.linear.predict(df_test)
        p_hgb = self.hgb.predict(df_test)["point_pred"]
        point = 0.5 * (p_lin + p_hgb)
        return {
            "point_pred": point,
            "q_10": point - self.residual_q80,
            "q_90": point + self.residual_q80,
            "q_025": point - self.residual_q95,
            "q_975": point + self.residual_q95
        }


def save_trained_pipeline(model, region_id, fold_name, metrics, models_dir="models"):
    """
    Saves model weights, feature list, and metadata to models/.
    """
    dir_path = Path(models_dir) / f"{region_id}_{fold_name}"
    dir_path.mkdir(parents=True, exist_ok=True)

    weights_path = dir_path / "model.joblib"
    joblib.dump(model, weights_path)

    metadata = {
        "model_name": model.name,
        "region": region_id,
        "fold": fold_name,
        "feature_count": len(MODEL_FEATURE_COLS),
        "features": MODEL_FEATURE_COLS,
        "metrics": metrics,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }
    with open(dir_path / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
