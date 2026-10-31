"""Inference logic used by the API (kept free of FastAPI so it can be tested on its own).

How lag features are built for a requested date (viva question!):
  * date is covered by the history CSV            -> use the real (cleaned) values from history
  * date is AFTER the history, inside a 7-day plan -> recursive forecasting: earlier predictions fill the lags
  * date is AFTER the history, no prediction yet   -> fallback = mean of that meal on the same weekday over the last 4 weeks
"""
import json
from datetime import date as Date, timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.features import FEATURE_COLS, MENU, calendar_and_onehot
from src.waste import expected_saving_kg, suggested_cook

ROOT = Path(__file__).resolve().parents[1]


class Forecaster:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.model = joblib.load(self.root / "models" / "model.joblib")
        self.cols = json.load(open(self.root / "models" / "feature_cols.json"))
        self.meta = json.load(open(self.root / "models" / "model_meta.json"))
        hist = pd.read_csv(self.root / "data" / "history_clean.csv", parse_dates=["date"])
        self.series = {m: {r.date.date(): float(r.plates_served) for r in g.itertuples()} for m, g in hist.groupby("meal")}
        self.history_end = hist.date.max().date()

    # ---- lag helpers ----
    def _fallback(self, meal, day):
        s = self.series[meal]
        same_wd = sorted((d for d in s if d.weekday() == day.weekday()), reverse=True)[:4]
        return float(np.mean([s[d] for d in same_wd]))

    def _value_at(self, meal, day, overrides):
        if day in overrides:
            return overrides[day], "recursive"
        if day in self.series[meal]:
            return self.series[meal][day], "history"
        return self._fallback(meal, day), "fallback"

    def features_for(self, day, meal, menu_item, is_holiday=0, is_exam_period=0, is_vacation=0, is_event=0,
                     temperature_c=25.0, rain_mm=0.0, overrides=None):
        overrides = overrides or {}
        lag1, s1 = self._value_at(meal, day - timedelta(days=1), overrides)
        lag7, s7 = self._value_at(meal, day - timedelta(days=7), overrides)
        win = [self._value_at(meal, day - timedelta(days=k), overrides) for k in range(1, 8)]
        row = pd.DataFrame([{"date": pd.Timestamp(day), "meal": meal, "menu_item": menu_item,
                             "special_dish": MENU[menu_item], "is_holiday": int(is_holiday),
                             "is_exam_period": int(is_exam_period), "is_vacation": int(is_vacation),
                             "is_event": int(is_event), "temperature_c": float(temperature_c), "rain_mm": float(rain_mm),
                             "lag_1": lag1, "lag_7": lag7, "rolling_mean_7": float(np.mean([w[0] for w in win]))}])
        row = calendar_and_onehot(row)
        sources = {s1, s7} | {w[1] for w in win}
        source = "history" if sources == {"history"} else ("recursive" if "recursive" in sources else "fallback")
        return row[self.cols], source

    def predict(self, day, meal, menu_item, overrides=None, **kw):
        X, source = self.features_for(day, meal, menu_item, overrides=overrides, **kw)
        return max(float(self.model.predict(X)[0]), 0.0), source

    @staticmethod
    def package(pred, meal):
        return {"predicted_plates": int(round(pred)), "suggested_cook_plates": int(suggested_cook(pred)),
                "expected_saving_kg": round(float(expected_saving_kg(pred, meal)), 1)}

    def forecast_week(self, start, meal, menu_items, **kw):
        """7 consecutive days, recursive: each day's prediction becomes a lag for the next day."""
        overrides, out = {}, []
        for i in range(7):
            day = start + timedelta(days=i)
            pred, source = self.predict(day, meal, menu_items[i], overrides=overrides, **kw)
            overrides[day] = pred
            out.append({"date": day.isoformat(), "weekday": day.strftime("%a"), "menu_item": menu_items[i],
                        "lag_source": source, **self.package(pred, meal)})
        return out
