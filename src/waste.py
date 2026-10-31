"""Shared waste / cooking rules. Imported by training code AND the API so both always agree."""
import numpy as np

FIXED_PLATES = {"Breakfast": 650, "Lunch": 850, "Dinner": 900}  # what the mess cooks today (from the data)
BUFFER = 1.05          # 5% safety buffer on top of the forecast
KG_PER_PLATE = 0.35    # leftover food weight per plate (observed ratio in the data)


def suggested_cook(predicted):
    return np.rint(np.asarray(predicted, dtype=float) * BUFFER)


def expected_saving_kg(predicted, meal):
    """Saving at prediction time (actual demand unknown): treat the forecast as the expected demand.
    leftover_fixed    = fixed plates cooked - expected demand      (never below 0)
    leftover_forecast = suggested plates cooked - expected demand  (never below 0)
    saving_kg = (leftover_fixed - leftover_forecast) * 0.35        (never below 0)"""
    predicted = np.asarray(predicted, dtype=float)
    fixed = FIXED_PLATES[meal]
    left_fixed = np.maximum(fixed - predicted, 0)
    left_fc = np.maximum(suggested_cook(predicted) - predicted, 0)
    return np.maximum((left_fixed - left_fc) * KG_PER_PLATE, 0)


def waste_summary(actual, cooked):
    """Evaluate a cooking policy against ACTUAL demand."""
    actual, cooked = np.asarray(actual, float), np.asarray(cooked, float)
    left = np.maximum(cooked - actual, 0)
    short = np.maximum(actual - cooked, 0)
    return {"leftover_plates": float(left.sum()), "leftover_kg": float(left.sum() * KG_PER_PLATE),
            "shortage_plates": float(short.sum()), "shortage_days": int((short > 0).sum())}
