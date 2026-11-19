# Interview Defense Notes: Technical & Analytical Decisions

Key questions, design justifications, and strategic tradeoffs for portfolio project discussions.

---

### Q1: Why didn't you use a 24-hour lag ($y_{t-24}$) for forecasting next-day demand?
**Defense:** 
"In an operational day-ahead setting, the forecast must be committed by a fixed morning deadline (e.g., 10:00 AM on Day $D-1$) for all 24 hours of Day $D$. At 10:00 AM on Day $D-1$, hours 10:00 through 23:00 of Day $D-1$ have not occurred yet! Using $y_{t-24}$ for afternoon and evening hours of Day $D$ would be a catastrophic future information leak. To ensure strict point-in-time correctness, the latest demand observation known at origin is 09:00 $D-1$, so our minimum safe seasonal lag is 48 hours ($y_{t-48}$), alongside weekly persistence ($y_{t-168}$)."

---

### Q2: Why did you choose MASE instead of standard MAPE or RMSE as the primary model-selection metric?
**Defense:** 
"We evaluate three balancing authorities with vastly different scales: ERCOT peaks at ~85,000 MW, PJM at ~150,000 MW, and NYIS at ~30,000 MW. Standard MAE or RMSE cannot be averaged across these regions fairly because PJM would dominate the loss function. On the other hand, plain MAPE becomes numerically volatile during off-peak low-demand hours. MASE scales each region's error by the in-sample mean absolute error of its own weekly seasonal naive baseline ($y_{t-168}$). A MASE below 1.0 has a clear, intuitive meaning: the model beats a zero-cost 1-week persistence benchmark."

---

### Q3: Why did ERCOT's empirical prediction interval coverage drop on the final holdout?
**Defense:** 
"That was one of the most critical analytical findings of the project! On our rolling validation folds, coverage matched nominal targets. But on the holdout (May–Dec 2023), Texas experienced an unprecedented historic heatwave (record summer peaks reaching 85.5k MW) combined with rapid demographic and industrial electrification growth (+17.6% mean demand increase, confirmed by a PSI of 0.6293). Because the model was trained on historical data from cooler, lower-demand years, the static prediction interval bands under-covered the extreme right tail. In an operations briefing, I would highlight this to simulated planning analysts as evidence that growing grids require dynamic interval recalibration rather than static historical bands."

---

### Q4: Why did you report Ridge regression alongside Gradient Boosting?
**Defense:** 
"In time-series forecasting, complex non-linear models can easily overfit local fluctuations. A regularized Ridge linear model with Fourier harmonics and degree days serves as a high-performing parametric baseline. HistGradientBoosting beat Ridge on MASE (0.403 vs 0.505) because it captures the severe non-linear interaction between extreme temperatures and humidity (cooling degree hours), but having the linear baseline and simple seasonal naives proved that every layer of complexity earned its place."

---

### Q5: How do you verify that Tableau displays exact numbers without calculation drift?
**Defense:** 
"We implemented a programmatic 3-way reconciliation pipeline. We export flat CSVs from Python, query the identical CSV independently using an in-memory SQL database (DuckDB / SQLite), and programmatically compare the resulting MAE, RMSE, and coverage metrics within a tolerance of 0.01 MW. When the user exports crosstabs from Tableau, the same script reconciles Layer 3, ensuring zero hardcoding and zero manual transcription errors."
