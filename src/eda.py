"""Run: python -m src.eda  -> EDA charts in reports/figures/ + diagrams (pipeline, MLP architecture)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
from src.features import MEALS, FEATURE_COLS
from src.waste import KG_PER_PLATE

df = pd.read_csv("data/history_clean.csv", parse_dates=["date"])
raw = pd.read_csv("data/mess_synthetic_data.csv", parse_dates=["date"])
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": .25})
C = {"Breakfast": "#f59e0b", "Lunch": "#10b981", "Dinner": "#6366f1"}
F = "reports/figures/"
order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# 1 meal x weekday
piv = raw.pivot_table(index="day_of_week", columns="meal", values="plates_served").loc[order, MEALS]
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
raw.groupby("meal").plates_served.mean()[MEALS].plot.bar(ax=ax[0], color=[C[m] for m in MEALS], rot=0)
ax[0].set_title("Average plates by meal", fontweight="bold"); ax[0].set_ylabel("plates served")
piv.plot.bar(ax=ax[1], color=[C[m] for m in MEALS], rot=30, width=.8)
ax[1].set_title("Average plates by weekday and meal", fontweight="bold"); ax[1].set_xlabel("")
plt.tight_layout(); plt.savefig(F + "eda_meal_weekday.png", dpi=170); plt.close()

# 2 condition effects (normalised to each meal's overall mean so meals are comparable)
d = raw.dropna(subset=["plates_served"]).copy()
d["rel"] = d.plates_served / d.groupby("meal").plates_served.transform("mean")
conds = {"Holiday": "is_holiday", "Exam period": "is_exam_period", "Vacation": "is_vacation", "Event": "is_event", "Special dish": "special_dish"}
fig, a = plt.subplots(figsize=(7.5, 3.8))
vals = [d[d[c] == 1].rel.mean() * 100 - 100 for c in conds.values()]
bars = a.bar(conds.keys(), vals, color=["#ef4444" if v < 0 else "#10b981" for v in vals])
a.axhline(0, color="k", lw=.8); a.set_ylabel("% change vs meal average")
for b, v in zip(bars, vals): a.text(b.get_x() + b.get_width() / 2, v + (1 if v >= 0 else -4), f"{v:+.0f}%", ha="center", fontsize=9)
a.set_title("Effect of conditions on demand", fontweight="bold")
plt.tight_layout(); plt.savefig(F + "eda_conditions.png", dpi=170); plt.close()

# 3 menu item
mi = d.groupby(["meal", "menu_item"]).plates_served.mean().reset_index().sort_values("plates_served")
fig, a = plt.subplots(figsize=(8, 4.6))
lab = mi.menu_item + " (" + mi.meal.str[0] + ")"
a.barh(lab, mi.plates_served, color=[C[m] for m in mi.meal]); a.set_xlabel("average plates served")
a.set_title("Demand by menu item (B / L / D)", fontweight="bold")
plt.tight_layout(); plt.savefig(F + "eda_menu.png", dpi=170); plt.close()

# 4 weather
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
for m in MEALS:
    s = d[d.meal == m]
    ax[0].scatter(s.rain_mm, s.plates_served, s=14, alpha=.7, color=C[m], label=m)
    ax[1].scatter(s.temperature_c, s.plates_served, s=14, alpha=.7, color=C[m], label=m)
ax[0].set_xlabel("rain (mm)"); ax[1].set_xlabel("temperature (°C)")
for a in ax: a.set_ylabel("plates served")
ax[0].legend(fontsize=8); ax[0].set_title("Rain vs plates", fontweight="bold"); ax[1].set_title("Temperature vs plates", fontweight="bold")
plt.tight_layout(); plt.savefig(F + "eda_weather.png", dpi=170); plt.close()

# 5 trend
fig, a = plt.subplots(figsize=(11, 3.8))
for m in MEALS:
    s = df[df.meal == m]; a.plot(s.date, s.plates_served, lw=1.1, color=C[m], label=m)
for c, col, lbl in [("is_vacation", "#f97316", "Vacation"), ("is_exam_period", "#0ea5e9", "Exam")]:
    dd = df[df[c] == 1].date.unique()
    for x in dd: a.axvspan(x, x + pd.Timedelta(days=1), color=col, alpha=.10)
a.set_ylabel("plates served"); a.legend(ncol=3, fontsize=8); a.set_title("Demand over time (shaded: exam = blue, vacation = orange)", fontweight="bold")
plt.tight_layout(); plt.savefig(F + "eda_trend.png", dpi=170); plt.close()

# 6 leftover vs shortage under today's fixed cooking
x = raw.dropna(subset=["plates_served"]).groupby("meal")[["leftover_kg", "shortage_plates"]].sum().loc[MEALS]
fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
ax[0].bar(MEALS, x.leftover_kg, color=[C[m] for m in MEALS]); ax[0].set_title("Leftover food (kg), whole dataset", fontweight="bold")
ax[1].bar(MEALS, x.shortage_plates, color=[C[m] for m in MEALS]); ax[1].set_title("Shortage (plates), whole dataset", fontweight="bold")
plt.tight_layout(); plt.savefig(F + "eda_leftover_shortage.png", dpi=170); plt.close()


def box(a, x, y, w, h, text, fc, fs=9, tc="white"):
    a.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec="none"))
    a.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, fontweight="bold")


def arrow(a, x1, y1, x2, y2):
    a.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color="#475569", lw=1.6))


# 7 pipeline block diagram
fig, a = plt.subplots(figsize=(12, 3.4)); a.set_xlim(0, 12); a.set_ylim(0, 3.4); a.axis("off")
steps = [("Synthetic\nmess data\n450 rows", "#64748b"), ("Cleaning\n+ causal\nimputation", "#0ea5e9"),
         ("Feature\nengineering\n(lags, flags)", "#10b981"), ("Time-based\nsplit\n70/15/15", "#f59e0b"),
         ("Models\n(Baseline, LR,\nRF, GB, MLP)", "#e11d48"), ("FastAPI\n/predict\n/forecast-week", "#6366f1"),
         ("React\ndashboard", "#0f172a")]
w = 1.35
for i, (t, c) in enumerate(steps):
    x0 = 0.15 + i * 1.7
    box(a, x0, 1.0, w, 1.4, t, c, 8.5)
    if i < len(steps) - 1: arrow(a, x0 + w + .03, 1.7, x0 + 1.7 - .03, 1.7)
a.text(6, 0.35, "Time order is respected at every step: no random shuffling, lag features use only past values.",
       ha="center", fontsize=9, color="#475569")
plt.savefig(F + "pipeline.png", dpi=170, bbox_inches="tight"); plt.close()

# 8 deep MLP architecture
fig, a = plt.subplots(figsize=(11, 4.6)); a.set_xlim(0, 11); a.set_ylim(0, 4.6); a.axis("off")
layers = [("Input\n%d features" % len(FEATURE_COLS), 4, "#64748b"), ("Dense 64\nReLU", 5, "#0ea5e9"), ("Dense 32\nReLU", 4, "#10b981"),
          ("Dense 16\nReLU", 3, "#f59e0b"), ("Output\nplates", 1, "#e11d48")]
xs = [0.8, 3.0, 5.2, 7.4, 9.6]
for (t, n, c), x in zip(layers, xs):
    ys = np.linspace(1.4, 3.6, n) if n > 1 else [2.5]
    for yy in ys: a.add_patch(plt.Circle((x, yy), .17, color=c, zorder=3))
    a.text(x, 0.7, t, ha="center", fontsize=9, fontweight="bold")
for (_, n1, _), x1, (_, n2, _), x2 in zip(layers[:-1], xs[:-1], layers[1:], xs[1:]):
    y1 = np.linspace(1.4, 3.6, n1) if n1 > 1 else [2.5]; y2 = np.linspace(1.4, 3.6, n2) if n2 > 1 else [2.5]
    for p in y1:
        for q in y2: a.plot([x1 + .17, x2 - .17], [p, q], color="#cbd5e1", lw=.5, zorder=1)
a.text(5.5, 4.35, "Deep MLP (5-member ensemble, averaged)  |  Adam, L2 penalty, standardised inputs", ha="center", fontsize=10, color="#0f172a")
a.text(5.5, 0.15, "Example shown: hidden layers (64, 32, 16), as selected by time-series CV", ha="center", fontsize=8.5, color="#475569")
plt.savefig(F + "mlp_architecture.png", dpi=170, bbox_inches="tight"); plt.close()
print("figures done")
