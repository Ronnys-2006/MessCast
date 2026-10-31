"""Cleaning + feature engineering. build_features(df) is the single entry point (used by training AND the API)."""
import numpy as np
import pandas as pd

MEALS = ["Breakfast", "Lunch", "Dinner"]
MENU = {  # menu_item -> special_dish flag, as observed in the dataset
    "Poha": 0, "Upma": 0, "Sandwich": 0, "Idli": 0, "Aloo Paratha": 0,
    "Dal Rice": 0, "Regular Veg Thali": 0, "Chole Bhature": 0, "Veg Biryani": 1,
    "Paneer Special": 1, "Chicken Curry": 1, "Egg Curry": 0,
}
MENU_BY_MEAL = {
    "Breakfast": ["Poha", "Upma", "Sandwich", "Idli", "Aloo Paratha"],
    "Lunch": ["Paneer Special", "Dal Rice", "Chole Bhature", "Regular Veg Thali", "Veg Biryani"],
    "Dinner": ["Chicken Curry", "Dal Rice", "Paneer Special", "Egg Curry", "Regular Veg Thali"],
}
MENU_ITEMS = sorted(MENU)
FLAGS = ["special_dish", "is_holiday", "is_exam_period", "is_vacation", "is_event"]
WEATHER = ["temperature_c", "rain_mm"]
CAL = ["day_of_week_num", "is_weekend", "month", "week_of_year"]
LAGS = ["lag_1", "lag_7", "rolling_mean_7"]
MEAL_COLS = [f"meal_{m}" for m in MEALS]
MENU_COLS = [f"menu_{m}" for m in MENU_ITEMS]
FEATURE_COLS = CAL + FLAGS + WEATHER + MEAL_COLS + LAGS + MENU_COLS
TARGET = "plates_served"


def clean(df):
    """Parse dates, sort, and fill missing plates_served CAUSALLY: median of the same meal + same weekday
    from EARLIER dates (fallback: median of that meal so far, then of the meal overall). Adds target_imputed flag."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["meal"] = pd.Categorical(df["meal"], MEALS, ordered=True)
    df = df.sort_values(["date", "meal"]).reset_index(drop=True)
    df["meal"] = df["meal"].astype(str)
    df["target_imputed"] = df[TARGET].isna().astype(int)
    for i in df.index[df[TARGET].isna()]:
        past = df.loc[(df.index < i) & (df.meal == df.at[i, "meal"]) & df[TARGET].notna()]
        same_wd = past[past.day_of_week == df.at[i, "day_of_week"]][TARGET]
        if len(same_wd):
            val = same_wd.median()
        elif len(past):
            val = past[TARGET].median()
        else:
            val = df.loc[(df.meal == df.at[i, "meal"]) & df[TARGET].notna(), TARGET].median()
        df.at[i, TARGET] = val
    return df


def add_lags(df):
    """lag_1, lag_7, rolling_mean_7 per meal. shift(1) BEFORE rolling so today's value never leaks in."""
    df = df.sort_values(["meal", "date"]).copy()
    g = df.groupby("meal")[TARGET]
    df["lag_1"] = g.shift(1)
    df["lag_7"] = g.shift(7)
    df["rolling_mean_7"] = g.transform(lambda s: s.shift(1).rolling(7).mean())
    return df.sort_values(["date", "meal"]).reset_index(drop=True)


def calendar_and_onehot(df):
    """Calendar + one-hot columns (shared with the API, which builds one row at a time)."""
    d = pd.to_datetime(df["date"])
    df["day_of_week_num"] = d.dt.dayofweek
    df["is_weekend"] = (d.dt.dayofweek >= 5).astype(int)
    df["month"] = d.dt.month
    df["week_of_year"] = d.dt.isocalendar().week.astype(int)
    for m in MEALS:
        df[f"meal_{m}"] = (df["meal"] == m).astype(int)
    for m in MENU_ITEMS:
        df[f"menu_{m}"] = (df["menu_item"] == m).astype(int)
    return df


def build_features(df, drop_na=False):
    """Raw (or cleaned) mess dataframe -> feature table with FEATURE_COLS (+ keys + target)."""
    if "target_imputed" not in df.columns:
        df = clean(df)
    df = calendar_and_onehot(add_lags(df))
    keep = ["date", "meal", "menu_item", "target_imputed", TARGET, "plates_prepared"] + FEATURE_COLS
    out = df[[c for c in keep if c in df.columns]]
    return out.dropna(subset=LAGS).reset_index(drop=True) if drop_na else out


def time_split(feat, train_frac=0.70, val_frac=0.15):
    """Split by DATE (all 3 meals of a date stay together). No shuffling."""
    dates = np.sort(feat["date"].unique())
    n = len(dates)
    n_tr, n_va = int(round(n * train_frac)), int(round(n * val_frac))
    tr, va, te = dates[:n_tr], dates[n_tr:n_tr + n_va], dates[n_tr + n_va:]
    return (feat[feat.date.isin(tr)].copy(), feat[feat.date.isin(va)].copy(), feat[feat.date.isin(te)].copy())
