"""Run: python -m src.stats_check -> reports/bootstrap.json
Paired bootstrap (5000 resamples of the 69 test rows) of the MAE difference between models."""
import json
import numpy as np, pandas as pd

p = pd.read_csv("reports/test_predictions.csv")
y = p.actual.values
rng = np.random.default_rng(0)
idx = [rng.integers(0, len(y), len(y)) for _ in range(5000)]
out = {}
for a, b in [("Deep MLP", "Gradient Boosting"), ("Linear Regression", "Gradient Boosting"), ("Random Forest", "Gradient Boosting"),
             ("Baseline", "Gradient Boosting"), ("Deep MLP", "Baseline")]:
    ea, eb = np.abs(y - p[a]).values, np.abs(y - p[b]).values
    d = [ea[i].mean() - eb[i].mean() for i in idx]
    out[f"{a} minus {b}"] = {"mean_diff": round(float(ea.mean() - eb.mean()), 2),
                             "ci95": [round(float(np.percentile(d, 2.5)), 1), round(float(np.percentile(d, 97.5)), 1)]}
json.dump(out, open("reports/bootstrap.json", "w"), indent=1)
print(json.dumps(out, indent=1))
