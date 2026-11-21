# Interview Defense Notes: Technical & Analytical Decisions

Key questions, design justifications, and strategic tradeoffs for portfolio project discussions.

---

### Q1: Why didn't you use a 24-hour lag ($y_{t-24}$) for forecasting next-day demand?
**Defense:** 
"In an operational day-ahead setting, the forecast must be committed by a fixed morning deadline (e.g., 10:00 AM on Day $D-1$) for all 24 hours of Day $D$. At 10:00 AM on Day $D-1$, hours 10:00 through 23:00 of Day $D-1$ have not occurred yet! Using $y_{t-24}$ for afternoon and evening hours of Day $D$ would be a catastrophic future information leak. To ensure strict point-in-time correctness, the latest demand observation known at origin is 09:00 $D-1$, so our minimum safe seasonal lag is 48 hours ($y_{t-48}$), alongside weekly persistence ($y_{t-168}$)."

---

### Q2: Why did you choose rMAE (Relative MAE) and MASE instead of standard MAPE or RMSE as the primary model-selection metric?
**Defense:** 
"We evaluate three regional footprints with vastly different scales: TEX peaks at ~85,000 MW, MIDA at ~150,000 MW, and NY at ~30,000 MW. Standard MAE or RMSE cannot be averaged across these regions fairly because MIDA would dominate the loss function. On the other hand, plain MAPE becomes numerically volatile during off-peak low-demand hours. We report both Relative MAE ($\text{rMAE} = \text{MAE}_{\text{model}} / \text{MAE}_{\text{base168}}$) aggregated via Geometric Mean and in-sample scaled MASE (Hyndman & Koehler). An rMAE below 1.0 has a clear, intuitive meaning: the model beats a zero-cost 168h seasonal persistence baseline."

---

### Q3: Why did standard tree models suffer from negative bias in growing grids like Texas (TEX), and did the residual formulation solve it?
**Defense:** 
"Decision trees and gradient-boosted trees are piecewise-constant step functions that cannot extrapolate beyond the maximum target values seen in the training data. In the Texas grid footprint (TEX), annual mean demand expanded continuously from 44.8 GW (2021) to 49.2 GW (2022), 51.0 GW (2023), and 52.9 GW (2024). When training a tree model on raw MW levels from 2021–2023, the model capped out during high-load periods, resulting in persistent negative bias (-2,472.5 MW) across all months.

We introduced `HistGradientBoosting_Residual` to predict the delta relative to the known seasonal baseline:
$$\Delta_t = y_t - y_{t-168}$$
Because $y_{t-168}$ is strictly known at the origin, the baseline anchor carries the shifting multi-year load level. This structural modification **reduced** the annual bias in Texas by ~248 MW (from -2,472.5 MW to -2,224.2 MW). However, it did not eliminate it: demand growth outpaces even trailing 7-day levels, demonstrating that level anchoring partially mitigates but cannot completely remove structural multi-year trend bias."

---

### Q4: How did you calibrate prediction intervals under load drift and weather volatility, and what are their limitations?
**Defense:** 
"Static in-sample conformal prediction or quantile loss models assume that test residuals follow the same distribution as training residuals. Under climate volatility and rapid load growth, test variance increases, causing static intervals to under-cover.

To enforce our pre-declared selection constraint requiring 80% coverage in $[77\%, 83\%]$, we implemented **Rolling Conformal Prediction**. At each forecast origin, the model computes the empirical 80th percentile of absolute residuals from the trailing 21 days of forecasts that are already realized ($\ge 48$ hours prior). This dynamically adjusts interval width to current volatility: widening during summer heatwaves and tightening during mild shoulder seasons, successfully maintaining 76.7% to 79.3% empirical coverage across all holdout regions in Calendar 2024.

However, an honest audit reveals that **95% prediction intervals under-cover**, reaching 92.5% to 93.8%. In the extreme 5% tails (unprecedented peak hours), empirical error distributions exhibit heavy tails that a 21-day rolling window does not fully capture."

---

### Q5: How do you verify that Tableau displays exact numbers without calculation drift?
**Defense:** 
"We implemented a programmatic 3-way reconciliation pipeline. We export flat CSVs from Python, query the identical CSV independently using an in-memory SQL database (SQLite), and programmatically compare the resulting MAE, Bias, and coverage metrics. All 9 assertions strictly PASS. When the user exports crosstabs from Tableau, the same script reconciles Layer 3, ensuring zero hardcoding and zero manual transcription errors."

---

### Q6: How did you handle imputed data in the benchmark dataset?
**Defense:** 
"The benchmark dataset from Ruggles et al. (*Nature Scientific Data*, 2020) provides both `raw demand (MW)` and `cleaned demand (MW)` with an imputation rate of 1.84% (TEX), 2.93% (MIDA), and 1.99% (NY) due to real-world utility dropouts and transmission anomalies. Rather than ignoring this or pretending the data is pristine, we explicitly track an `is_imputed` flag throughout our pipeline and report holdout model accuracy separately on all hours vs. strictly non-imputed hours (e.g. TEX holdout rMAE is 0.622 on all hours vs. 0.621 on non-imputed hours), demonstrating that model performance is robust and unaffected by the imputation methodology."

---

### Q7: Why are both `HistGradientBoosting_Point_Conformal` and `HistGradientBoosting_Residual` reported on the 2024 holdout?
**Defense:** 
"Scientific integrity requires respecting pre-declared decision rules while maintaining transparency. Under our Phase 0 selection rule evaluated on 2023 rolling folds, `HistGradientBoosting_Point_Conformal` won with the lowest Geometric-Mean rMAE (0.457 vs 0.487) and compliant 80% coverage (78.7%). 

The Residual model was developed after the 2023 bias investigation specifically to address tree extrapolation. In an earlier iteration, the holdout was evaluated using the Residual model. Because 2024 had already been inspected with that candidate, choosing either model post-hoc on the basis of 2024 results would violate the single-touch holdout principle. Therefore, we disclose the sequence of events fully and report both models side-by-side: `Point_Conformal` achieved lower MAE in MIDA (2,871 vs 3,256 MW) and NY (541 vs 605 MW), while `Residual` achieved lower bias in Texas (-2,224 vs -2,473 MW)."

---

### Q8: Why is the 48-hour naive forecast a stronger baseline than 168-hour naive, and what does it reveal about model skill?
**Defense:**
"The 168-hour naive forecast assumes load today matches the same day last week. However, at our 10:00 AM Day $D-1$ forecast origin, the 48-hour lag ($y_{t-48}$) is also fully observed and available. Because it is closer in time, it captures recent weekly weather regimes and trailing multi-week demand drift far more effectively. 

Benchmarking against 48h naive reveals an important regional nuance: our winner achieves massive gains in MIDA (+60.7% skill, ratio 0.393) and NY (+58.9% skill, ratio 0.411), but a more modest +20.0% skill (ratio 0.800) in Texas (+12.1% against a Ridge linear model). In rapidly growing grids, recent level persistence is a formidable benchmark that tree models struggle to outpace by large margins."

---

### Q9: What was the refit protocol before evaluating on the 2024 holdout dataset?
**Defense:**
"Before deploying models to the strictly single-touch 2024 holdout evaluation (8,784 hours), final models were refit on the combined training and validation sets spanning 2021-01-01 to 2023-12-31 (exactly 26,280 hours = 3 full years). In machine learning forecasting pipelines, model selection and hyperparameter tuning are conducted on validation folds (e.g., 2021–2022 train, 2023 validation). Once the model architecture is fixed (`HistGradientBoosting_Point_Conformal`), refitting on all available historical data (2021–2023) prior to the holdout origin ensures the model incorporates the most recent seasonal transitions, recent load trends, and weather relationships without causing data leakage into 2024."
