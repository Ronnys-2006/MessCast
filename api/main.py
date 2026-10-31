"""MessCast backend.  Run from the repo root:  uvicorn api.main:app --reload   ->  http://localhost:8000/docs"""
import csv
import json
import sys
from datetime import date as Date
from pathlib import Path
from typing import List, Literal, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.features import MENU, MENU_BY_MEAL
from src.forecast import Forecaster
from src.waste import BUFFER, FIXED_PLATES, KG_PER_PLATE

Meal = Literal["Breakfast", "Lunch", "Dinner"]
app = FastAPI(title="MessCast API", version="1.0",
              description="Meal demand forecasting for a hostel mess. Demo data is SIMULATED (synthetic).")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])
fc = Forecaster(ROOT)


class Conditions(BaseModel):
    meal: Meal
    menu_item: str
    is_holiday: int = Field(0, ge=0, le=1)
    is_exam_period: int = Field(0, ge=0, le=1)
    is_vacation: int = Field(0, ge=0, le=1)      # optional extras (default 0)
    is_event: int = Field(0, ge=0, le=1)
    temperature_c: float = Field(25.0, ge=-10, le=50)
    rain_mm: float = Field(0.0, ge=0, le=500)


class PredictIn(Conditions):
    date: Date


class WeekIn(Conditions):
    start_date: Date
    menu_items: Optional[List[str]] = Field(None, min_length=7, max_length=7, description="optional: one menu per day")


class PredictOut(BaseModel):
    predicted_plates: int
    suggested_cook_plates: int
    expected_saving_kg: float
    lag_source: str


def check_menu(item: str):
    if item not in MENU:
        raise HTTPException(422, f"Unknown menu_item '{item}'. Choose one of: {', '.join(sorted(MENU))}")


@app.exception_handler(RequestValidationError)
async def friendly_errors(_: Request, exc: RequestValidationError):
    problems = [f"{'.'.join(str(p) for p in e['loc'][1:])}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(status_code=422, content={"error": "Invalid input", "problems": problems})


@app.post("/predict", response_model=PredictOut)
def predict(body: PredictIn):
    check_menu(body.menu_item)
    kw = body.model_dump(exclude={"date", "meal", "menu_item"})
    pred, source = fc.predict(body.date, body.meal, body.menu_item, **kw)
    return {**fc.package(pred, body.meal), "lag_source": source}


@app.post("/forecast-week")
def forecast_week(body: WeekIn):
    menus = body.menu_items or [body.menu_item] * 7
    for m in menus:
        check_menu(m)
    kw = body.model_dump(exclude={"start_date", "meal", "menu_item", "menu_items"})
    return fc.forecast_week(body.start_date, body.meal, menus, **kw)


def _json(name):
    path = ROOT / "reports" / name
    if not path.exists():
        raise HTTPException(404, f"{name} not found. Run `python -m src.train` first.")
    return json.load(open(path))


@app.get("/metrics")
def metrics():
    return _json("metrics.json")


@app.get("/metrics-detailed")
def metrics_detailed():
    return _json("metrics_detailed.json")


@app.get("/waste")
def waste():
    return _json("waste.json")


@app.get("/test-predictions")
def test_predictions():
    path = ROOT / "reports" / "test_predictions.csv"
    return list(csv.DictReader(open(path)))


@app.get("/options")
def options():
    return {"meals": list(FIXED_PLATES), "menu_by_meal": MENU_BY_MEAL, "special": [k for k, v in MENU.items() if v],
            "fixed_plates": FIXED_PLATES, "buffer": BUFFER, "kg_per_plate": KG_PER_PLATE,
            "history_end": fc.history_end.isoformat(), "model": fc.meta["model"], "data_is": "simulated"}


@app.get("/health")
def health():
    return {"status": "ok", "model": fc.meta["model"]}
