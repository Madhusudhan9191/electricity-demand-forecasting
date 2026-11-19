"""
Splits Module.
Manages expanding-window time-based rolling-origin folds and isolates the final holdout.
Rule 5: Model selection must be programmatic and based only on validation or rolling-origin results, never on the final holdout.
Rule 6: The final holdout period is touched once. Do not tune or choose thresholds on it.
"""

import pandas as pd
import yaml

CONFIG_PATH = "config/config.yaml"


def get_folds_definition(config):
    return config["splits"]["rolling_folds"]


def get_holdout_dates(config):
    return {
        "start": pd.Timestamp(config["splits"]["validation_end"], tz="UTC") + pd.Timedelta(days=1),
        "end": pd.Timestamp(config["splits"]["test_end"], tz="UTC") + pd.Timedelta(hours=23)
    }


def split_data_for_fold(df, fold_cfg):
    """
    Given a feature dataframe for a region and a fold configuration dict:
    Returns (df_train, df_val).
    """
    train_end = pd.Timestamp(fold_cfg["train_end"], tz="UTC") + pd.Timedelta(hours=23)
    val_start = pd.Timestamp(fold_cfg["val_start"], tz="UTC")
    val_end = pd.Timestamp(fold_cfg["val_end"], tz="UTC") + pd.Timedelta(hours=23)

    # Note: training window starts at 2021-01-01 (ignoring 2020 COVID structural break)
    train_start = pd.Timestamp("2021-01-01 00:00:00", tz="UTC")

    df_train = df[(df["timestamp"] >= train_start) & (df["timestamp"] <= train_end)].copy()
    df_val = df[(df["timestamp"] >= val_start) & (df["timestamp"] <= val_end)].copy()

    return df_train, df_val


def get_final_holdout_split(df, config):
    """
    Returns (df_train_full, df_test_holdout).
    df_train_full covers 2021-01-01 up to 2023-04-30 23:00 UTC.
    df_test_holdout covers 2023-05-01 up to 2023-12-31 23:00 UTC.
    """
    train_start = pd.Timestamp("2021-01-01 00:00:00", tz="UTC")
    val_end = pd.Timestamp(config["splits"]["validation_end"], tz="UTC") + pd.Timedelta(hours=23)
    test_start = val_end + pd.Timedelta(hours=1)
    test_end = pd.Timestamp(config["splits"]["test_end"], tz="UTC") + pd.Timedelta(hours=23)

    df_train_full = df[(df["timestamp"] >= train_start) & (df["timestamp"] <= val_end)].copy()
    df_test = df[(df["timestamp"] >= test_start) & (df["timestamp"] <= test_end)].copy()

    return df_train_full, df_test
