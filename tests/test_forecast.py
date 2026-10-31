"""Run: python -m tests.test_forecast  (or pytest). Checks that API-time features equal training-time features."""
from datetime import date, timedelta
import numpy as np
import pandas as pd
from src.forecast import Forecaster
from src.features import FEATURE_COLS

fc = Forecaster()
feat = pd.concat([pd.read_csv(f"data/{n}.csv", parse_dates=["date"]) for n in ["train", "val", "test"]])
feat = feat.dropna(subset=["lag_7"])


def test_features_match_training_table():
    for _, r in feat.sample(25, random_state=1).iterrows():
        X, src = fc.features_for(r.date.date(), r.meal, r.menu_item, r.is_holiday, r.is_exam_period, r.is_vacation,
                                 r.is_event, r.temperature_c, r.rain_mm)
        assert src == "history"
        assert np.allclose(X.iloc[0].values.astype(float), r[FEATURE_COLS].values.astype(float)), (r.date, r.meal)


def test_prediction_sane_and_rules():
    p, _ = fc.predict(fc.history_end + timedelta(days=3), "Lunch", "Paneer Special")
    out = fc.package(p, "Lunch")
    assert 200 < out["predicted_plates"] < 1100
    assert out["suggested_cook_plates"] == round(p * 1.05) or abs(out["suggested_cook_plates"] - p * 1.05) <= 1
    assert out["expected_saving_kg"] >= 0


def test_week_is_recursive_and_seven_long():
    wk = fc.forecast_week(fc.history_end + timedelta(days=1), "Dinner", ["Chicken Curry"] * 7)
    assert len(wk) == 7 and wk[0]["lag_source"] in ("history", "fallback") and wk[-1]["lag_source"] == "recursive"


if __name__ == "__main__":
    test_features_match_training_table(); test_prediction_sane_and_rules(); test_week_is_recursive_and_seven_long()
    print("all tests passed")
