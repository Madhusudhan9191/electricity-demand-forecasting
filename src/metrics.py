"""
Metrics Module.
Rule 4: Every number in docs and dashboards must come from code or a query.
Never type metrics by hand. Never hard-code PASS or FAIL.

Defines:
- MAE, RMSE, sMAPE, Bias (Mean Error).
- rMAE: Relative MAE vs. 168h seasonal persistence baseline (rMAE_base168 = 1.000 by definition).
- MASE: Mean Absolute Scaled Error using in-sample seasonal naive scale factor.
- Region & Season specific Peak MAE.
- Geometric Mean aggregation for scale-free ratios.
- Pinball loss, Empirical Coverage, and Interval Width.
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
    mask = denom > 1e-6
    if not np.any(mask):
        return 0.0
    return float(np.mean(np.abs(y_true[mask] - y_pred[mask]) / denom[mask]) * 100.0)


def compute_rmae(y_true, y_pred, y_base168):
    """
    Relative MAE vs 168h Seasonal Naive Baseline.
    rMAE = MAE_model / MAE_base168.
    By definition, rMAE of base168 is exactly 1.000.
    Values < 1.0 indicate skill superior to seasonal persistence.
    """
    mae_model = compute_mae(y_true, y_pred)
    mae_base = compute_mae(y_true, y_base168)
    if mae_base < 1e-6:
        return 1.0
    return float(mae_model / mae_base)


def compute_mase(y_true, y_pred, y_train_history, seasonality=168):
    """
    Mean Absolute Scaled Error (Hyndman & Koehler, 2006).
    Scale factor is the in-sample mean absolute error of seasonal naive baseline on training data.
    """
    if len(y_train_history) <= seasonality:
        denom = compute_mae(y_true, y_pred)
    else:
        denom = np.mean(np.abs(y_train_history[seasonality:] - y_train_history[:-seasonality]))
    if denom < 1e-6:
        denom = 1e-6
    mae = compute_mae(y_true, y_pred)
    return float(mae / denom)


def compute_geometric_mean(ratios):
    """
    Geometric mean aggregation across folds and regions:
    GM = exp( (1/N) * sum(ln(r)) )
    Guarantees symmetry and prevents distortion from large positive ratios.
    """
    clean_ratios = [float(r) for r in ratios if r > 1e-6 and not np.isnan(r)]
    if not clean_ratios:
        return 1.0
    return float(np.exp(np.mean(np.log(clean_ratios))))


def compute_peak_mae(y_true, y_pred, hours, peak_hours):
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


def evaluate_forecast(
    y_true,
    y_pred,
    y_train_history,
    hours,
    y_base168,
    peak_hours,
    q_lower_80=None,
    q_upper_80=None,
    q_lower_95=None,
    q_upper_95=None
):
    """
    Comprehensive evaluation dictionary.
    """
    metrics = {
        "MAE": compute_mae(y_true, y_pred),
        "RMSE": compute_rmse(y_true, y_pred),
        "sMAPE": compute_smape(y_true, y_pred),
        "Bias": compute_bias(y_true, y_pred),
        "rMAE": compute_rmae(y_true, y_pred, y_base168),
        "MASE": compute_mase(y_true, y_pred, y_train_history),
        "Peak_MAE": compute_peak_mae(y_true, y_pred, hours, peak_hours),
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
