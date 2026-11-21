"""
Splits Module.
Manages expanding-window time-based rolling-origin folds and isolates the final holdout.
Rule 5: Model selection must be programmatic and based only on validation or rolling-origin results, never on the final holdout.
Rule 6: The final holdout period is touched once. Do not tune or choose thresholds on it.

2021-2024 Re-Split Architecture:
- Train: 2021-01-01 to 2022-12-31 (17,520 hours)
- Validation: Calendar 2023 (8,760 hours across 4 expanding seasonal folds)
- Single-Touch Holdout: Calendar 2024 (8,784 hours, leap year, touched strictly once)
"""

import pandas as pd
import yaml

CONFIG_PATH = "config/config.yaml"


def get_folds_definition(config):
    return config["splits"]["validation_folds_2023"]


def get_holdout_dates(config):
    return {
        "start": pd.Timestamp(config["splits"]["holdout_start"], tz="UTC"),
        "end": pd.Timestamp(config["splits"]["holdout_end"], tz="UTC")
    }


def split_data_for_fold(df, fold_cfg):
    """
    Given a feature dataframe for a region and a fold configuration dict:
    Returns (df_train, df_val).
    """
    train_end = pd.Timestamp(fold_cfg["train_end"], tz="UTC")
    val_start = pd.Timestamp(fold_cfg["val_start"], tz="UTC")
    val_end = pd.Timestamp(fold_cfg["val_end"], tz="UTC")

    # Training window starts at 2021-01-01 (excluding 2020 COVID structural break)
    train_start = pd.Timestamp("2021-01-01 00:00:00", tz="UTC")

    df_train = df[(df["timestamp"] >= train_start) & (df["timestamp"] <= train_end)].copy()
    df_val = df[(df["timestamp"] >= val_start) & (df["timestamp"] <= val_end)].copy()

    return df_train, df_val


def get_final_holdout_split(df, config):
    """
    Returns (df_train_full, df_test_holdout).
    df_train_full covers 2021-01-01 up to 2023-12-31 23:00:00 UTC (3 full years = 26,280 hours).
    df_test_holdout covers Calendar 2024: 2024-01-01 00:00:00 up to 2024-12-31 23:00:00 UTC (8,784 hours).
    """
    train_start = pd.Timestamp(config["splits"]["train_start"], tz="UTC")
    train_full_end = pd.Timestamp(config["splits"]["validation_end"], tz="UTC")
    holdout_start = pd.Timestamp(config["splits"]["holdout_start"], tz="UTC")
    holdout_end = pd.Timestamp(config["splits"]["holdout_end"], tz="UTC")

    df_train_full = df[(df["timestamp"] >= train_start) & (df["timestamp"] <= train_full_end)].copy()
    df_test = df[(df["timestamp"] >= holdout_start) & (df["timestamp"] <= holdout_end)].copy()

    return df_train_full, df_test
