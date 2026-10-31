# MessCast: meal demand forecasting to reduce mess food waste

Predicts how many students will eat each meal (breakfast / lunch / dinner) so the mess cooks the right quantity instead of a
fixed one. Includes a FastAPI backend and a React dashboard.

**The data is SIMULATED (synthetic).** Results show the pipeline works; they are not proof for a real mess.

```
Data -> Cleaning + Features -> Models + Evaluation -> FastAPI -> React app -> Report
```

## Quick start

```bash
# 1. Python side (3.10+)
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.prepare_data        # clean + features + time-based train/val/test  -> data/*.csv
python -m src.train               # all models, tuning, metrics.json, model.joblib, figures
python -m src.eda                 # EDA charts + diagrams -> reports/figures/
python -m src.export_frontend_data  # refresh the UI's offline fallback data
python -m tests.test_forecast     # API-time features == training-time features

# 2. Backend  (docs page: http://localhost:8000/docs)
uvicorn api.main:app --reload

# 3. Frontend (new terminal)
cd frontend && npm install && npm run dev                 # http://localhost:5173
```

The UI falls back to embedded demo results if the backend is not running (an amber banner tells you).
Model files and reports are already generated in this repo, so steps 2 and 3 work straight away.

## Layout

| Path | What |
|---|---|
| `data/` | raw CSV, `history_clean.csv`, `train.csv`, `val.csv`, `test.csv` |
| `src/features.py` | `clean()`, `build_features()`, `time_split()` |
| `src/train.py` | baselines, Linear Regression, Random Forest, Gradient Boosting (+XGBoost if installed), Deep MLP |
| `src/nn.py` | deep MLP ensemble (scikit-learn estimator) |
| `src/waste.py` | cooking and saving rules shared by training and the API |
| `src/forecast.py` | inference + lag handling for future dates |
| `api/main.py` | FastAPI: `/predict`, `/forecast-week`, `/metrics` (+ `/options`, `/waste`, `/metrics-detailed`, `/test-predictions`) |
| `models/` | `model.joblib`, `feature_cols.json`, `model_meta.json` |
| `reports/` | `metrics.json`, `waste.json`, error analysis, `figures/` |
| `frontend/` | React + Vite + Tailwind + Recharts |
| `docs/` | assumptions table, viva notes |

## API

`POST /predict`  input: `date, meal, menu_item, is_holiday, is_exam_period, temperature_c, rain_mm`
(optional: `is_vacation, is_event`) -> `predicted_plates, suggested_cook_plates, expected_saving_kg` (+ `lag_source`)

`POST /forecast-week`  input: `start_date, meal, menu_item` + same flags (optional `menu_items`: 7 menus) -> list of 7 days

`GET /metrics` -> `reports/metrics.json`

Rules: `suggested_cook_plates = round(predicted x 1.05)`; `expected_saving_kg = max((fixed leftover - forecast leftover) x 0.35, 0)`.
Invalid input returns HTTP 422 with `{"error": "Invalid input", "problems": [...]}`.

## Rules we follow
1. Time-based split only, never a random shuffle. 2. Data assumptions are not changed to improve scores.
3. Own branch, merge by pull request. 4. Everyone writes their own report section. 5. Viva is individual.
