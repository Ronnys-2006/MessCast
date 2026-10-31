"""Run: python -m src.train
Baselines, Linear Regression, Random Forest, Gradient Boosting (+XGBoost if installed), Deep MLP.
Tuning: RandomizedSearchCV with an expanding-window, DATE-based CV on train+val only. Test set touched once."""
import json, warnings
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import RandomizedSearchCV
from src.features import FEATURE_COLS, TARGET, MEALS
from src.nn import MLPEnsemble
from src.waste import BUFFER, waste_summary, suggested_cook, KG_PER_PLATE

warnings.filterwarnings("ignore")
SEED = 42
PAL = {"Baseline": "#94a3b8", "Naive (yesterday)": "#cbd5e1", "Linear Regression": "#f59e0b",
       "Random Forest": "#10b981", "Gradient Boosting": "#0ea5e9", "XGBoost": "#6366f1", "Deep MLP": "#e11d48"}


def load(name):
    d = pd.read_csv(f"data/{name}.csv", parse_dates=["date"])
    return d.dropna(subset=["lag_1", "lag_7", "rolling_mean_7"]).reset_index(drop=True)


def metrics(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    return {"MAE": float(np.mean(np.abs(y - p))), "RMSE": float(np.sqrt(np.mean((y - p) ** 2))),
            "MAPE": float(np.mean(np.abs(y - p) / y) * 100)}


def date_cv(df, n_splits=4, min_train_frac=0.5):
    """Expanding-window CV over unique DATES (all meals of a date stay together)."""
    dates = np.sort(df.date.unique())
    start = int(len(dates) * min_train_frac)
    edges = np.linspace(start, len(dates), n_splits + 1).astype(int)
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        tr = np.where(df.date.isin(dates[:a]))[0]
        va = np.where(df.date.isin(dates[a:b]))[0]
        out.append((tr, va))
    return out


def cv_mae_fixed(df, cv, pred_col):
    return float(np.mean([np.mean(np.abs(df[TARGET].values[va] - df[pred_col].values[va])) for _, va in cv]))


tr, va, te = load("train"), load("val"), load("test")
tv = pd.concat([tr, va]).reset_index(drop=True)
obs = tv[tv.target_imputed == 0].reset_index(drop=True)          # train only on genuinely observed targets
Xtv, ytv = obs[FEATURE_COLS], obs[TARGET]
te_obs = te[te.target_imputed == 0].reset_index(drop=True)
cv = date_cv(obs)
print(f"train+val rows={len(obs)}  test rows (observed)={len(te_obs)}  CV folds={len(cv)}")

# ---------- model zoo ----------
zoo = {
    "Linear Regression": (LinearRegression(), {}),
    "Random Forest": (RandomForestRegressor(random_state=SEED, n_jobs=1),
                      {"n_estimators": [200, 400], "max_depth": [4, 6, 8, None], "min_samples_leaf": [1, 2, 4, 8],
                       "max_features": [0.5, 0.8, 1.0]}),
    "Gradient Boosting": (GradientBoostingRegressor(random_state=SEED),
                          {"n_estimators": [100, 200, 400], "learning_rate": [0.03, 0.05, 0.1], "max_depth": [2, 3, 4],
                           "subsample": [0.7, 0.9, 1.0], "min_samples_leaf": [1, 3, 6]}),
    "Deep MLP": (MLPEnsemble(random_state=SEED),
                 {"hidden_layer_sizes": [(32, 16), (64, 32), (64, 32, 16), (128, 64, 32)],
                  "alpha": [1e-4, 1e-3, 1e-2, 1e-1], "learning_rate_init": [1e-3, 3e-3]}),
}
try:
    from xgboost import XGBRegressor
    zoo["XGBoost"] = (XGBRegressor(random_state=SEED, n_jobs=1, verbosity=0),
                      {"n_estimators": [100, 200, 400], "learning_rate": [0.03, 0.05, 0.1], "max_depth": [2, 3, 4, 5],
                       "subsample": [0.7, 0.9, 1.0], "colsample_bytree": [0.7, 1.0]})
except ImportError:
    print("xgboost not installed -> skipped (pip install xgboost to add it)")

# ---------- tuning (train+val only) ----------
fitted, params, cv_scores = {}, {}, {}
for name, (est, grid) in zoo.items():
    if grid:
        rs = RandomizedSearchCV(est, grid, n_iter=12, cv=cv, scoring="neg_mean_absolute_error",
                                random_state=SEED, n_jobs=1, refit=False)
        rs.fit(Xtv, ytv)
        params[name], cv_scores[name] = rs.best_params_, float(-rs.best_score_)
        final = clone(est).set_params(**rs.best_params_)
    else:
        scores = []
        for a, b in cv:
            scores.append(np.mean(np.abs(ytv.values[b] - clone(est).fit(Xtv.iloc[a], ytv.iloc[a]).predict(Xtv.iloc[b]))))
        params[name], cv_scores[name], final = {}, float(np.mean(scores)), clone(est)
    fitted[name] = final.fit(Xtv, ytv)
    print(f"{name:20s} CV-MAE={cv_scores[name]:.2f}  params={params[name]}")

cv_scores["Baseline"] = cv_fixed = cv_mae_fixed(obs, cv, "lag_7")
cv_scores["Naive (yesterday)"] = cv_mae_fixed(obs, cv, "lag_1")
best = min(fitted, key=lambda k: cv_scores[k])                    # chosen on CV (train+val), NOT on test
print("best by CV:", best)

# ---------- final evaluation: test set touched once ----------
preds = {"Baseline": te_obs["lag_7"].values, "Naive (yesterday)": te_obs["lag_1"].values}
for name, m in fitted.items():
    preds[name] = m.predict(te_obs[FEATURE_COLS])
y = te_obs[TARGET].values
overall = {k: metrics(y, p) for k, p in preds.items()}
per_meal = {k: {m: metrics(y[te_obs.meal == m], p[(te_obs.meal == m).values]) for m in MEALS} for k, p in preds.items()}
order = ["Baseline", "Naive (yesterday)"] + [k for k in zoo if k in fitted]
out = {k: {m: round(v, 3) for m, v in overall[k].items()} for k in order}
out["best_model"] = best
json.dump(out, open("reports/metrics.json", "w"), indent=2)
print(pd.DataFrame(overall).T.round(2).loc[order])

# ---------- save model + feature list ----------
joblib.dump(fitted[best], "models/model.joblib")
json.dump(FEATURE_COLS, open("models/feature_cols.json", "w"), indent=2)
json.dump({"model": best, "params": {k: (list(v) if isinstance(v, tuple) else v) for k, v in params[best].items()},
           "trained_on": f"{obs.date.min().date()} to {obs.date.max().date()}", "n_train_rows": int(len(obs)),
           "cv_mae": cv_scores[best], "test_mae": overall[best]["MAE"]}, open("models/model_meta.json", "w"), indent=2)
pd.DataFrame({"date": te_obs.date, "meal": te_obs.meal, "menu_item": te_obs.menu_item, "actual": y,
              **{k: np.round(p, 1) for k, p in preds.items()}}).to_csv("reports/test_predictions.csv", index=False)

# ---------- waste saving (test period) ----------
pb = preds[best]
cook_fc, cook_fx = suggested_cook(pb), te_obs["plates_prepared"].values
waste = {"period": f"{te_obs.date.min().date()} to {te_obs.date.max().date()}", "model": best, "buffer": BUFFER,
         "fixed": waste_summary(y, cook_fx), "forecast": waste_summary(y, cook_fc)}
w0, w1 = waste["fixed"], waste["forecast"]
waste["leftover_reduction_pct"] = 100 * (1 - w1["leftover_kg"] / w0["leftover_kg"])
waste["kg_saved"] = w0["leftover_kg"] - w1["leftover_kg"]
waste["extra_shortage_plates"] = w1["shortage_plates"] - w0["shortage_plates"]
waste["per_meal"] = {m: {"fixed": waste_summary(y[te_obs.meal == m], cook_fx[(te_obs.meal == m).values]),
                         "forecast": waste_summary(y[te_obs.meal == m], cook_fc[(te_obs.meal == m).values])} for m in MEALS}
waste["baseline_forecast"] = waste_summary(y, suggested_cook(preds["Baseline"]))
waste["buffer_sensitivity"] = [{"buffer": b, **waste_summary(y, np.rint(pb * b))} for b in [1.0, 1.05, 1.10, 1.15, 1.20]]
daily = pd.DataFrame({"date": te_obs.date.dt.strftime("%Y-%m-%d"), "meal": te_obs.meal, "actual": y,
                      "fixed_cook": cook_fx, "forecast_cook": cook_fc})
daily["fixed_leftover_kg"] = np.maximum(daily.fixed_cook - daily.actual, 0) * KG_PER_PLATE
daily["forecast_leftover_kg"] = np.maximum(daily.forecast_cook - daily.actual, 0) * KG_PER_PLATE
g = daily.groupby("date")[["fixed_leftover_kg", "forecast_leftover_kg"]].sum().round(1).reset_index()
waste["daily"] = g.to_dict("records")
json.dump(waste, open("reports/waste.json", "w"), indent=2)
print(json.dumps({k: waste[k] for k in ["fixed", "forecast", "leftover_reduction_pct", "kg_saved", "extra_shortage_plates"]}, indent=1))

# ---------- error analysis ----------
ea_df = te_obs.assign(pred=pb, base=preds["Baseline"])
groups = {"Normal day": (ea_df[["is_holiday", "is_exam_period", "is_vacation", "is_event"]].sum(axis=1) == 0),
          "Exam period": ea_df.is_exam_period == 1, "Holiday": ea_df.is_holiday == 1, "Vacation": ea_df.is_vacation == 1,
          "Event": ea_df.is_event == 1, "Special dish": ea_df.special_dish == 1, "Rain > 5 mm": ea_df.rain_mm > 5}
ea = {}
for k, msk in groups.items():
    if msk.sum():
        ea[k] = {"n": int(msk.sum()), "model_MAE": float(np.mean(np.abs(ea_df.pred[msk] - ea_df[TARGET][msk]))),
                 "baseline_MAE": float(np.mean(np.abs(ea_df.base[msk] - ea_df[TARGET][msk])))}
json.dump(ea, open("reports/error_analysis.json", "w"), indent=2)

# ---------- importance ----------
pi = permutation_importance(fitted[best], te_obs[FEATURE_COLS], y, n_repeats=30, random_state=SEED,
                            scoring="neg_mean_absolute_error")
imp = pd.Series(pi.importances_mean, index=FEATURE_COLS).sort_values(ascending=False)
imp.round(3).to_json("reports/permutation_importance.json")
try:  # optional SHAP for tree models, only if installed
    import shap
    if best in ("Random Forest", "Gradient Boosting", "XGBoost"):
        sv = shap.TreeExplainer(fitted[best]).shap_values(te_obs[FEATURE_COLS])
        shap.summary_plot(sv, te_obs[FEATURE_COLS], show=False)
        plt.tight_layout(); plt.savefig("reports/figures/shap_summary.png", dpi=160); plt.close()
except Exception as e:
    print("SHAP skipped:", type(e).__name__)

# ---------- figures ----------
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": .25, "figure.dpi": 100})
fig, ax = plt.subplots(1, 3, figsize=(12, 3.8))
for a, mt in zip(ax, ["MAE", "RMSE", "MAPE"]):
    vals = [overall[k][mt] for k in order]
    bars = a.bar(range(len(order)), vals, color=[PAL.get(k, "#64748b") for k in order])
    a.set_xticks(range(len(order))); a.set_xticklabels([k.replace(" ", "\n", 1) for k in order], fontsize=7.5)
    a.set_title(mt + (" (%)" if mt == "MAPE" else " (plates)"), fontweight="bold")
    for b, v in zip(bars, vals): a.text(b.get_x() + b.get_width() / 2, v, f"{v:.1f}", ha="center", va="bottom", fontsize=8)
plt.tight_layout(); plt.savefig("reports/figures/model_comparison.png", dpi=170); plt.close()

fig, ax = plt.subplots(3, 1, figsize=(11, 8.5), sharex=True)
for a, m in zip(ax, MEALS):
    k = te_obs.meal == m
    a.plot(te_obs.date[k], y[k], "o-", color="#0f172a", lw=1.6, ms=4, label="Actual")
    a.plot(te_obs.date[k], pb[k], "s--", color=PAL.get(best, "#e11d48"), lw=1.6, ms=4, label=f"{best}")
    a.plot(te_obs.date[k], preds["Baseline"][k.values], ":", color="#94a3b8", lw=1.6, label="Baseline (lag_7)")
    a.axhline(te_obs.plates_prepared[k].iloc[0], color="#f97316", lw=1, ls="-.", label="Fixed cooking")
    a.set_title(m, loc="left", fontweight="bold"); a.set_ylabel("plates")
ax[0].legend(ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(.5, 1.38))
plt.xticks(rotation=30); plt.tight_layout(); plt.savefig("reports/figures/actual_vs_predicted.png", dpi=170); plt.close()

fig, a = plt.subplots(figsize=(8, 4))
names = list(ea); xs = np.arange(len(names))
a.bar(xs - .2, [ea[n]["baseline_MAE"] for n in names], .4, color="#94a3b8", label="Baseline")
a.bar(xs + .2, [ea[n]["model_MAE"] for n in names], .4, color=PAL.get(best, "#e11d48"), label=best)
a.set_xticks(xs); a.set_xticklabels([f"{n}\n(n={ea[n]['n']})" for n in names], fontsize=8)
a.set_ylabel("MAE (plates)"); a.legend(); a.set_title("Error analysis on the test period", fontweight="bold")
plt.tight_layout(); plt.savefig("reports/figures/error_analysis.png", dpi=170); plt.close()

top = imp.head(12)[::-1]
fig, a = plt.subplots(figsize=(7, 4.2))
a.barh(top.index, top.values, color="#0ea5e9"); a.set_xlabel("Increase in MAE when feature is shuffled (plates)")
a.set_title(f"Permutation importance ({best}, test set)", fontweight="bold")
plt.tight_layout(); plt.savefig("reports/figures/feature_importance.png", dpi=170); plt.close()

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
lab = ["Fixed cooking", f"Forecast x{BUFFER}"]
ax[0].bar(lab, [w0["leftover_kg"], w1["leftover_kg"]], color=["#f97316", "#10b981"])
ax[0].set_ylabel("Leftover food (kg)"); ax[0].set_title("Leftover food, test period", fontweight="bold")
for i, v in enumerate([w0["leftover_kg"], w1["leftover_kg"]]): ax[0].text(i, v, f"{v:.0f} kg", ha="center", va="bottom")
ax[1].bar(lab, [w0["shortage_plates"], w1["shortage_plates"]], color=["#f97316", "#10b981"])
ax[1].set_ylabel("Shortage (plates)"); ax[1].set_title("Plates short of demand", fontweight="bold")
for i, v in enumerate([w0["shortage_plates"], w1["shortage_plates"]]): ax[1].text(i, v, f"{v:.0f}", ha="center", va="bottom")
plt.tight_layout(); plt.savefig("reports/figures/waste_comparison.png", dpi=170); plt.close()

bs = pd.DataFrame(waste["buffer_sensitivity"])
fig, a = plt.subplots(figsize=(6.5, 4)); a2 = a.twinx()
a.plot(bs.buffer, bs.leftover_kg, "o-", color="#10b981", label="Leftover (kg)")
a2.plot(bs.buffer, bs.shortage_plates, "s-", color="#e11d48", label="Shortage (plates)")
a.set_xlabel("Safety buffer multiplier"); a.set_ylabel("Leftover (kg)", color="#10b981"); a2.set_ylabel("Shortage (plates)", color="#e11d48")
a2.spines["right"].set_visible(True); a.set_title("Buffer trade-off (analysis only; deployed buffer = 1.05)", fontweight="bold", fontsize=9)
plt.tight_layout(); plt.savefig("reports/figures/buffer_tradeoff.png", dpi=170); plt.close()

if "Deep MLP" in fitted:
    lc = fitted["Deep MLP"].loss_curve_
    json.dump([float(v) for v in lc], open("reports/mlp_loss_curve.json", "w"))
    fig, a = plt.subplots(figsize=(6.5, 3.8)); a.plot(lc, color="#e11d48"); a.set_yscale("log")
    a.set_xlabel("Epoch"); a.set_ylabel("Training loss (MSE/2, scaled)"); a.set_title("Deep MLP training curve (member 1)", fontweight="bold")
    plt.tight_layout(); plt.savefig("reports/figures/mlp_loss_curve.png", dpi=170); plt.close()
json.dump({"cv_mae": cv_scores, "params": {k: {a: (list(b) if isinstance(b, tuple) else b) for a, b in v.items()} for k, v in params.items()},
           "per_meal": per_meal, "importance_top10": imp.head(10).round(3).to_dict(), "n_test_rows": int(len(te_obs)),
           "n_trainval_rows": int(len(obs))}, open("reports/metrics_detailed.json", "w"), indent=2)
print("done")
