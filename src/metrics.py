"""
Metrics Module.
Rule 4: Every number in docs and dashboards must come from code or a query.
Never type metrics by hand. Never hard-code PASS or FAIL.
"""

import numpy as np
import pandas as pd


def compute_mae(y_true, y_pred):
    return float(np.mean(np.abs(y_true - y_pred)))


def compute_rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def compute_bias(y_true, y_pred):
    # Mean Error: positive = overforecast, negative = underforecast
    return float(np.mean(y_pred - y_true))


def compute_smape(y_true, y_pred):
    # Bound between 0% and 200%
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    # Avoid zero division
    mask = denom > 1e-6
    if not np.any(mask):
        return 0.0
    return float(np.mean(np.abs(y_true[mask] - y_pred[mask]) / denom[mask]) * 100.0)


def compute_mase(y_true, y_pred, y_train_history, seasonality=168):
    """
    Mean Absolute Scaled Error (MASE).
    Denominator is the in-sample mean absolute error of the seasonal naive baseline (seasonality=168h).
    """
    denom = np.mean(np.abs(y_train_history[seasonality:] - y_train_history[:-seasonality]))
    if denom < 1e-6:
        denom = 1e-6
    mae = compute_mae(y_true, y_pred)
    return float(mae / denom)


def compute_peak_mae(y_true, y_pred, hours, peak_hours=None):
    if peak_hours is None:
        peak_hours = [14, 15, 16, 17, 18, 19, 20]
    mask = np.isin(hours, peak_hours)
    if not np.any(mask):
        return np.nan
    return float(np.mean(np.abs(y_true[mask] - y_pred[mask])))


def compute_pinball_loss(y_true, q_pred, tau):
    """
    Pinball (Quantile) Loss for quantile tau in (0, 1).
    """
    err = y_true - q_pred
    loss = np.maximum(tau * err, (tau - 1.0) * err)
    return float(np.mean(loss))


def compute_interval_coverage(y_true, q_lower, q_upper):
    """
    Empirical coverage fraction in [0, 1].
    """
    inside = (y_true >= q_lower) & (y_true <= q_upper)
    return float(np.mean(inside))


def compute_interval_width(q_lower, q_upper):
    return float(np.mean(q_upper - q_lower))


def evaluate_forecast(y_true, y_pred, y_train_history, hours, q_lower_80=None, q_upper_80=None, q_lower_95=None, q_upper_95=None):
    """
    Comprehensive evaluation dictionary.
    """
    metrics = {
        "MAE": compute_mae(y_true, y_pred),
        "RMSE": compute_rmse(y_true, y_pred),
        "sMAPE": compute_smape(y_true, y_pred),
        "Bias": compute_bias(y_true, y_pred),
        "MASE": compute_mase(y_true, y_pred, y_train_history),
        "Peak_MAE": compute_peak_mae(y_true, y_pred, hours),
    }

    if q_lower_80 is not None and q_upper_80 is not None:
        metrics["Coverage_80"] = compute_interval_coverage(y_true, q_lower_80, q_upper_80)
        metrics["Width_80"] = compute_interval_width(q_lower_80, q_upper_80)
        metrics["Pinball_10"] = compute_pinball_loss(y_true, q_lower_80, 0.10)
        metrics["Pinball_90"] = compute_pinball_loss(y_true, q_upper_80, 0.90)

    if q_lower_95 is not None and q_upper_95 is not None:
        metrics["Coverage_95"] = compute_interval_coverage(y_true, q_lower_95, q_upper_95)
        metrics["Width_95"] = compute_interval_width(q_lower_95, q_upper_95)
        metrics["Pinball_025"] = compute_pinball_loss(y_true, q_lower_95, 0.025)
        metrics["Pinball_975"] = compute_pinball_loss(y_true, q_upper_95, 0.975)

    return metrics
