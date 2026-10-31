"""Run: python -m src.prepare_data  -> data/history_clean.csv, train.csv, val.csv, test.csv + reports/dataset_profile.json"""
import json
import pandas as pd
from src.features import clean, build_features, time_split

raw = pd.read_csv("data/mess_synthetic_data.csv")
profile = {"rows": int(raw.shape[0]), "columns": int(raw.shape[1]), "duplicates": int(raw.duplicated().sum()),
           "missing": {k: int(v) for k, v in raw.isna().sum().items() if v}, "dtypes": {k: str(v) for k, v in raw.dtypes.items()},
           "date_min": str(raw.date.min()), "date_max": str(raw.date.max()), "n_days": int(raw.date.nunique())}
hist = clean(raw)
hist.to_csv("data/history_clean.csv", index=False)           # used by the API for lag features
feat = build_features(hist)                                   # first 7 days keep NaN lags
tr, va, te = time_split(feat)
for name, part in [("train", tr), ("val", va), ("test", te)]:
    part.to_csv(f"data/{name}.csv", index=False)
    profile[name] = {"rows": len(part), "from": str(part.date.min().date()), "to": str(part.date.max().date()),
                     "usable_rows_after_lag_drop": int(part.dropna(subset=["lag_7"]).shape[0])}
json.dump(profile, open("reports/dataset_profile.json", "w"), indent=2)
print(json.dumps(profile, indent=2))
