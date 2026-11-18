"""Extra charts for the report (they replace tables). Numbers come from the tables in reports/hypothesis_results.csv
and the notebook outputs. Run: python src/04_report_figures.py"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
for p in Path.home().glob("AppData/Local/Microsoft/Windows/Fonts/Merriweather-*.ttf"):
    fm.fontManager.addfont(str(p))

GREEN, BURG, GREY, INK, LIGHT = "#2F5A45", "#8B2635", "#8A8A8A", "#1b1b1b", "#DDDDDD"
plt.rcParams.update({"font.family": ["Merriweather", "DejaVu Serif", "serif"], "font.size": 9, "savefig.dpi": 300, "figure.dpi": 110,
                     "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "text.color": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": LIGHT, "grid.linewidth": 0.7,
                     "axes.axisbelow": True})


def save(name):
    plt.tight_layout()
    plt.savefig(FIG / name, bbox_inches="tight")
    plt.close()


# 1. applications per year
years = [2018, 2019, 2020, 2021, 2022, 2023]
rows = [213875, 219896, 242691, 257792, 213413, 172560]
fig, ax = plt.subplots(figsize=(6, 3.2))
b = ax.bar([str(y) for y in years], rows, color=GREEN, width=0.6)
ax.bar_label(b, labels=[f"{r:,}" for r in rows], padding=3, fontsize=8)
ax.set_ylabel("Applications in the sample"); ax.set_ylim(0, 300000); ax.grid(axis="x", visible=False)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v/1000)}k"))
save("r01_applications_per_year.png")

# 2. missing vs complete
fig, ax = plt.subplots(figsize=(5, 3.2))
b = ax.bar(["Complete rows\n(1,170,521)", "DTI, LTV or income\nmissing (149,706)"], [9, 44], color=[GREEN, BURG], width=0.5)
ax.bar_label(b, labels=["9%", "44%"], padding=3, fontsize=10)
ax.set_ylabel("Denial rate (%)"); ax.set_ylim(0, 52); ax.grid(axis="x", visible=False)
save("r02_missing_vs_complete.png")

# 3. RDD window sensitivity (forest)
labels = ["+/-2 points", "+/-3 points (main)", "+/-5 points", "+/-7 points"]
est = np.array([-0.85, -0.50, 0.05, 0.51]); lo = np.array([-1.42, -0.85, -0.25, 0.26]); hi = np.array([-0.27, -0.14, 0.35, 0.75])
fig, ax = plt.subplots(figsize=(6, 3))
y = np.arange(len(labels))[::-1]
ax.errorbar(est, y, xerr=[est - lo, hi - est], fmt="o", color=GREEN, ecolor=GREEN, capsize=4, markersize=6)
ax.axvline(0, color=BURG, lw=1.2, ls="--")
ax.set_yticks(y); ax.set_yticklabels(labels); ax.set_xlabel("Jump in denial rate at DTI 43 (percentage points, 95% CI)")
ax.grid(axis="y", visible=False)
save("r03_rdd_windows.png")

# 4. model comparison
models = ["DTI rule", "Logistic\nregression", "LightGBM"]
allr = [0.668, 0.833, 0.880]; comp = [0.682, 0.770, 0.825]
x = np.arange(3); w = 0.36
fig, ax = plt.subplots(figsize=(6, 3.3))
b1 = ax.bar(x - w / 2, allr, w, color=GREY, label="All 2023 rows")
b2 = ax.bar(x + w / 2, comp, w, color=GREEN, label="Complete cases")
ax.bar_label(b1, fmt="%.3f", padding=2, fontsize=8); ax.bar_label(b2, fmt="%.3f", padding=2, fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(models); ax.set_ylim(0.5, 0.95); ax.set_ylabel("AUC (higher is better)")
ax.legend(frameon=False, loc="upper left", fontsize=8); ax.grid(axis="x", visible=False)
save("r04_model_comparison.png")

# 5. fairness: actual vs predicted denial rate
groups = ["White\n(112,794)", "Black\n(15,880)", "Asian\n(12,108)", "Joint\n(4,804)", "Not\navailable\n(24,924)", "Other /\n2+ races\n(2,050)"]
actual = [13.3, 27.0, 11.0, 12.7, 18.2, 26.7]; pred = [11.9, 21.5, 7.7, 10.7, 14.5, 23.4]
x = np.arange(6); w = 0.38
fig, ax = plt.subplots(figsize=(6.4, 3.4))
b1 = ax.bar(x - w / 2, actual, w, color=GREY, label="Actual denial rate")
b2 = ax.bar(x + w / 2, pred, w, color=GREEN, label="Model's flagged rate")
ax.bar_label(b1, fmt="%.1f", padding=2, fontsize=7.5); ax.bar_label(b2, fmt="%.1f", padding=2, fontsize=7.5)
ax.set_xticks(x); ax.set_xticklabels(groups, fontsize=7.5); ax.set_ylabel("%"); ax.set_ylim(0, 38)
ax.legend(frameon=False, fontsize=8, loc="upper center", ncol=2); ax.grid(axis="x", visible=False)
save("r05_fairness_actual_vs_predicted.png")

# 6. adjusted odds ratios (forest, log scale)
names = ["H2: Black vs White applicants", "H3: low-income vs other tracts", "H7: non-bank vs bank lenders"]
orr = np.array([1.73, 1.17, 0.56]); lo = np.array([1.65, 1.11, 0.52]); hi = np.array([1.82, 1.22, 0.61])
fig, ax = plt.subplots(figsize=(6.2, 2.7))
y = np.arange(3)[::-1]
ax.errorbar(orr, y, xerr=[orr - lo, hi - orr], fmt="s", color=GREEN, ecolor=GREEN, capsize=4, markersize=6)
ax.axvline(1, color=BURG, lw=1.2, ls="--"); ax.set_xscale("log")
ax.set_xticks([0.5, 0.75, 1, 1.5, 2]); ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter()); ax.get_xaxis().set_minor_formatter(matplotlib.ticker.NullFormatter())
ax.set_yticks(y); ax.set_yticklabels(names); ax.set_xlabel("Adjusted odds ratio of denial, 95% CI (1 = no difference)")
for yi, o in zip(y, orr):
    ax.text(o, yi + 0.18, f"{o:.2f}", ha="center", fontsize=8)
ax.grid(axis="y", visible=False)
save("r06_odds_ratios.png")

# 7. roadmap (gantt)
fig, ax = plt.subplots(figsize=(6.4, 2.4))
phases = [("1  Shadow pilot with credit scores", 0, 3), ("2  Triage of borderline applications", 3, 3), ("3  Monitoring and policy review", 6, 6)]
for i, (n, s, d) in enumerate(phases[::-1]):
    ax.barh(i, d, left=s, color=[GREEN, GREY, BURG][::-1][i], height=0.5)
ax.set_yticks(range(3)); ax.set_yticklabels([p[0] for p in phases[::-1]], fontsize=8)
ax.set_xticks(range(0, 13, 3)); ax.set_xlabel("Months after the start of the pilot"); ax.set_xlim(0, 12)
ax.grid(axis="y", visible=False)
save("r07_roadmap.png")

# 8. leakage columns
cols = ["interest_rate", "rate_spread", "total_loan_costs", "origination_charges", "discount_points"]
appr = [2.2, 3.5, 5.4, 4.7, 62.4]
x = np.arange(5); w = 0.38
fig, ax = plt.subplots(figsize=(6.4, 3.2))
b1 = ax.bar(x - w / 2, appr, w, color=GREEN, label="Approved loans")
b2 = ax.bar(x + w / 2, [100] * 5, w, color=BURG, label="Denied loans")
ax.bar_label(b1, fmt="%.1f", padding=2, fontsize=7.5); ax.bar_label(b2, fmt="%.0f", padding=2, fontsize=7.5)
ax.set_xticks(x); ax.set_xticklabels([c.replace("_", "\n", 1) if c.count("_") else c for c in cols], fontsize=7.5)
ax.set_ylabel("Share of values missing (%)"); ax.set_ylim(0, 128); ax.legend(frameon=False, fontsize=8, loc="upper center", ncol=2); ax.grid(axis="x", visible=False)
save("r08_leakage_columns.png")

# 9. threshold trade-off
thr = [0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]
flag = [20.2, 10.7, 8.2, 7.1, 6.6, 5.9, 5.1]; prec = [33.5, 52.3, 63.0, 68.7, 71.8, 75.6, 80.4]; rec = [64.9, 53.6, 49.2, 46.8, 45.5, 43.1, 39.3]
fig, ax = plt.subplots(figsize=(6.2, 3.4))
ax.plot(thr, prec, "-o", color=GREEN, label="Precision"); ax.plot(thr, rec, "-s", color=BURG, label="Recall")
ax.plot(thr, flag, "-^", color=GREY, label="Share of applications flagged")
ax.axvline(0.31, color=INK, lw=1, ls=":"); ax.text(0.315, 92, "chosen threshold 0.31", fontsize=8)
ax.set_xlabel("Decision threshold"); ax.set_ylabel("%"); ax.set_ylim(0, 100); ax.legend(frameon=False, fontsize=8, loc="upper left")
save("r09_threshold_tradeoff.png")
print("saved 9 figures to", FIG)
