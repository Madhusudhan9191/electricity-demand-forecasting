# Metric Definitions & Evaluation Framework

This document provides formal mathematical definitions, grain, exclusions, and operational context for all evaluation metrics used in the project.

---

## 1. Primary Model-Selection Metric: MASE (Mean Absolute Scaled Error)

### Formula
$$\text{MASE} = \frac{\frac{1}{N}\sum_{t=1}^N |y_t - \hat{y}_t|}{\frac{1}{T - 168}\sum_{s=169}^T |y_s - y_{s-168}|}$$

- **Numerator:** Out-of-sample MAE of the candidate model over evaluation horizon $N$.
- **Denominator:** In-sample 168-hour (1 week) seasonal naive MAE computed on the historical training set of length $T$.

### Grain & Exclusions
- **Grain:** Evaluated per region across rolling validation folds and overall.
- **Exclusions:** Hours where actual demand $y_t$ is unrecorded or flagged invalid are excluded from both numerator and denominator.

### Operational Interpretation
- **Scale-Free:** Because the denominator normalizes error by the intrinsic historical variability of the specific balancing authority, MASE can be compared across ERCOT (~70,000 MW peak) and NYIS (~25,000 MW peak).
- **Benchmark Interpretation:**
  - $\text{MASE} < 1.0$: The model is superior to the baseline 168-hour persistence forecast (predicting exact demand from the same hour one week prior).
  - $\text{MASE} \ge 1.0$: The model has failed to beat a zero-cost weekly seasonal persistence rule.

---

## 2. Secondary Point Forecast Metrics

### A. MAE (Mean Absolute Error)
$$\text{MAE} = \frac{1}{N}\sum_{t=1}^N |y_t - \hat{y}_t|$$
- **Grain:** Regional hourly ($MW$).
- **Role:** Direct intuitive operational scale of average magnitude error.

### B. RMSE (Root Mean Squared Error)
$$\text{RMSE} = \sqrt{\frac{1}{N}\sum_{t=1}^N (y_t - \hat{y}_t)^2}$$
- **Grain:** Regional hourly ($MW$).
- **Role:** Penalizes large outliers heavily; reflects grid stress risks where unexpected large forecast swings require fast-start peaker plants.

### C. sMAPE (Symmetric Mean Absolute Percentage Error)
$$\text{sMAPE} = \frac{100\%}{N}\sum_{t=1}^N \frac{|y_t - \hat{y}_t|}{(|y_t| + |\hat{y}_t|) / 2}$$
- **Grain:** Percentage (%).
- **Why avoid plain MAPE near zero?** Standard MAPE ($\frac{|y_t - \hat{y}_t|}{y_t}$) suffers from catastrophic numerical instability as the actual demand $y_t \to 0$ (producing arbitrarily huge percentage errors) and is asymmetric (penalizes over-forecasts more heavily than under-forecasts). While hourly grid demand rarely hits zero, sub-regional components and low-demand off-peak hours skew standard MAPE. sMAPE bounds the maximum error per observation to $200\%$ and treats relative differences symmetrically.

### D. Bias (Mean Error)
$$\text{Bias} = \frac{1}{N}\sum_{t=1}^N (\hat{y}_t - y_t)$$
- **Grain:** Regional hourly ($MW$).
- **Role:** Measures whether the forecast exhibits persistent over-forecasting ($\text{Bias} > 0$, excess reserve commitment) or under-forecasting ($\text{Bias} < 0$, grid scarcity risk).

### E. Peak-Hour MAE
$$\text{MAE}_{\text{peak}} = \frac{1}{|P|}\sum_{t \in P} |y_t - \hat{y}_t|, \quad P = \{t : \text{hour}(t) \in [14, 20]\}$$
- **Grain:** Regional hourly ($MW$) restricted to peak operating windows (14:00 to 20:00 local time).
- **Role:** Focuses strictly on capacity stress windows when wholesale electricity costs and reserve margins are most critical.

---

## 3. Uncertainty & Interval Metrics

### A. Pinball Loss (Quantile Loss at Target Quantile $\tau$)
$$L_\tau(y_t, \hat{q}_\tau(t)) = \begin{cases} \tau (y_t - \hat{q}_\tau(t)) & \text{if } y_t \ge \hat{q}_\tau(t) \\ (1 - \tau)(\hat{q}_\tau(t) - y_t) & \text{if } y_t < \hat{q}_\tau(t) \end{cases}$$
- **Quantiles Evaluated:** $\tau \in \{0.025, 0.10, 0.50, 0.90, 0.975\}$.
- **Role:** Evaluates whether quantile estimates are properly calibrated without assuming Gaussianity.

### B. Empirical Interval Coverage
$$\text{Coverage}_{1-\alpha} = \frac{1}{N}\sum_{t=1}^N \mathbf{1}\big(\hat{q}_{\alpha/2}(t) \le y_t \le \hat{q}_{1-\alpha/2}(t)\big)$$
- **Nominal Targets:**
  - $80\%$ Interval: $[\hat{q}_{0.10}, \hat{q}_{0.90}]$ (Acceptable validation range: $77.0\% - 83.0\%$)
  - $95\%$ Interval: $[\hat{q}_{0.025}, \hat{q}_{0.975}]$ (Acceptable validation range: $92.0\% - 97.0\%$)
- **Interpretation:** If empirical coverage is substantially below nominal target, the intervals are under-covering (overconfident). If coverage is significantly higher, intervals are overly wide (conservative/uninformative).

### C. Interval Width (Sharpness)
$$\bar{W}_{1-\alpha} = \frac{1}{N}\sum_{t=1}^N \big(\hat{q}_{1-\alpha/2}(t) - \hat{q}_{\alpha/2}(t)\big)$$
- **Grain:** Absolute $MW$ and normalized as percentage of region mean demand ($\bar{W} / \bar{y}$).
- **Role:** A valid interval must be as narrow (sharp) as possible while meeting the coverage constraint.
