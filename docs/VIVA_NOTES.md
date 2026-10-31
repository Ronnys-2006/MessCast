# Viva notes (short answers)

**Why synthetic data?** No real mess records were available. We generated 150 days x 3 meals from documented assumptions (seed 42) so the pipeline can be built and tested. Scores validate the pipeline, not a real mess.

**Why a time-based split?** Forecasting predicts the future from the past. A random shuffle lets the model see days after the ones it is tested on, so scores look better than they will be in use.

**Where could leakage happen?** In lag features. `rolling_mean_7` uses `shift(1)` before the rolling mean, so today's value is never in its own feature. Missing values are filled only from earlier dates.

**How are missing values filled?** Median of the same meal and same weekday from earlier dates (fallback: meal median so far). Imputed rows are not used for training or scoring.

**How does the API make lag features for a future date?** Dates inside the history use real values. Inside a 7-day forecast, each day's prediction becomes the next day's lag (recursive forecasting). A single far-future date falls back to the average of that meal on the same weekday over the last 4 weeks. The response says which one was used in `lag_source`.

**Why did Gradient Boosting win and is it really better?** It had the lowest cross-validated error. On the test set Linear Regression, Random Forest and the deep MLP are within noise of it (bootstrap CI of the difference includes 0). All of them beat the baseline clearly. The data was built from simple rules, so even a linear model does well.

**Is the MLP deep learning?** It is a 3-hidden-layer feed-forward network trained with backpropagation and Adam, averaged over 5 seeds. With ~350 training rows it does not beat tree models, which is expected on small tabular data.

**MAE vs RMSE vs MAPE?** MAE = average miss in plates. RMSE punishes big misses more. MAPE = average miss as a % of demand (compares breakfast and dinner fairly).

**Why 5% buffer?** At x1.00 there were 508 shortage plates in the test period, at x1.05 only 35, and above x1.10 shortages vanish but leftovers climb back (see `reports/waste.json`).

**Limits.** Synthetic data, one hostel, 150 days, no real menu popularity or events beyond the flags. The what-if vacation effect is muted because lag features carry yesterday's normal level.

**What with real data?** Collect daily plates served and leftovers per meal for a full year, recalibrate, re-run the same pipeline, compare against the same baseline.
