# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

## [0.1.0] - 2026-11-19

### Added
- **Phase 0 Specification**: Defined problem statement, simulated stakeholders (Planning Analyst, Operations Analyst), scope, out-of-scope boundaries, and acceptance criteria.
- **Data Source Evaluation**: Evaluated US EIA-930, ENTSO-E, UK NESO, and Indian Grid sources; evaluated Open-Meteo and NOAA ISD weather sources.
- **Timing & Horizon Definition**: Established 10:00 AM D-1 forecast origin, 14-hour lead time, and 24-hour Day D horizon with strict point-in-time constraints.
- **Metric Definitions Sheet**: Documented MAE, RMSE, MASE, sMAPE, Bias, Peak-Hour MAE, Pinball Loss, Interval Coverage, and Interval Width.
- **Model Selection Rule**: Pre-declared MASE minimization with coverage and peak-hour constraints on rolling validation folds.
- **Holdout Architecture**: Designed 36-month timeline (18m train, 10m rolling validation covering summer/winter, 8m final isolated holdout).
- **Environment & Config**: Created `.gitignore`, `config/config.yaml`, and Python virtual environment.
