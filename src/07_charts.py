"""All slide figures. Every number plotted is read from outputs/*.csv produced by scripts 01-06."""
import pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import *

FIG = os.path.join(OUT, "figures")
BLUE, ORANGE, GREY, LGREY, INK, INK2, RED = "#2a78d6", "#eb6834", "#a3a29c", "#d9d8d3", "#0b0b0b", "#52514e", "#e34948"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": LGREY, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": False, "figure.dpi": 200, "savefig.bbox": "tight", "savefig.facecolor": "white"})
CREDIT = "Data: Inside Airbnb, Vancouver, 15 June 2026, CC BY 4.0"
def finish(fig, name, note=CREDIT):
    # source/credit lines are placed on the slide itself, under each figure
    fig.savefig(os.path.join(FIG, name)); plt.close(fig)
def hbar_end_labels(ax, ys, vals, fmt, color=INK):
    for y, v in zip(ys, vals):
        ax.text(v + (abs(ax.get_xlim()[1]) * 0.01), y, fmt(v), va="center", fontsize=10, color=color)

# 1) revenue bridge
b = pd.read_csv(os.path.join(OUT, "revenue_bridge.csv"), index_col=0).iloc[:, 0]
lab = ["Inside Airbnb method\n(June quote x nights)", "Remove World Cup\nmatch-night premium", "Seasonal average rate\n(2027 base, nightly all year)", "Seasonal hybrid\n(nightly May-Oct + 6 mo furnished)"]
fig, ax = plt.subplots(figsize=(6.4, 3.3)); y = np.arange(len(b))[::-1]
cols = [GREY, GREY, GREY, BLUE]
ax.barh(y, b.values, color=cols, height=0.55); ax.set_xlim(0, b.max() * 1.18)
ax.set_yticks(y); ax.set_yticklabels(lab, fontsize=9.5); ax.set_xticks([])
ax.spines["bottom"].set_visible(False)
hbar_end_labels(ax, y, b.values, lambda v: f"${v/1000:,.1f}k")
ax.set_title("Median 1-2BR condo comparable (citywide, n=706): annual gross revenue", fontsize=10.5, color=INK, loc="left")
finish(fig, "fig_revenue_bridge.png")

# 2) operating model: median yields
seg = pd.read_csv(os.path.join(OUT, "segment_summary.csv"), index_col=0)
val = pd.read_csv(os.path.join(OUT, "validation_summary.csv"), index_col=0)['value']
rows = [("Nightly all year\n(+3% EHT + 1% SVT)", seg.loc['condo_1-2br', 'yield_str'], seg.loc['house_3br+', 'yield_str']),
        ("Seasonal hybrid\n(no vacancy taxes)", seg.loc['condo_1-2br', 'yield_hybrid'], seg.loc['house_3br+', 'yield_hybrid'])]
fig, ax = plt.subplots(figsize=(6.4, 3.2)); x = np.arange(len(rows)); w = 0.34
c = [r[1] * 100 for r in rows]; h = [r[2] * 100 for r in rows]
ax.bar(x - w/2 - 0.01, c, w, color=BLUE, label="1-2BR condo"); ax.bar(x + w/2 + 0.01, h, w, color=GREY, label="3BR+ detached house")
ax.axhline(0, color=INK2, lw=0.8)
ax.axhline(val['ltr_benchmark_yield'] * 100, color=ORANGE, lw=1.6, ls=(0, (4, 3)))
ax.text(-0.55, val['ltr_benchmark_yield'] * 100 + 0.2, f"Plain long-term rental, Downtown condo: {val['ltr_benchmark_yield']*100:.1f}%", fontsize=8.5, color=INK2, ha="left", va="bottom")
for xi, v in zip(x - w/2 - 0.01, c): ax.text(xi, v + (0.15 if v >= 0 else -0.45), f"{v:.1f}%", ha="center", fontsize=10, color=INK)
for xi, v in zip(x + w/2 + 0.01, h): ax.text(xi, v + (0.15 if v >= 0 else -0.45), f"{v:.1f}%", ha="center", fontsize=10, color=INK)
ax.set_xticks(x); ax.set_xticklabels([r[0] for r in rows]); ax.set_ylabel("Median 2027 net yield (%)")
ax.set_ylim(-4.2, 5.4); ax.legend(frameon=False, fontsize=9, loc="lower right")
finish(fig, "fig_operating_model.png", CREDIT + "; StatCan 46-10-0092-01 Q1 2026 asking rents; City of Vancouver 2026 assessments")

# 3) seasonality
m = pd.read_csv(os.path.join(OUT, "seasonality_monthly.csv"), index_col=0)
fig, ax = plt.subplots(figsize=(6.4, 2.9)); mo = list("JFMAMJJASOND")
cols = [BLUE if i in [5, 6, 7, 8, 9, 10] else GREY for i in m.index]
ax.bar(range(12), m.revenue_share * 100, color=cols, width=0.72)
ax.set_xticks(range(12)); ax.set_xticklabels(mo); ax.set_ylabel("% of annual nightly revenue")
ps = pd.read_csv(os.path.join(OUT, "seasonality_params.csv"), index_col=0)['value']
ax.text(-0.4, 15.0, f"May-Oct, nightly: {ps['peak_may_oct_revenue_share']*100:.0f}% of revenue", color=BLUE, fontsize=10, ha="left")
ax.text(-0.4, 6.4, "Nov-Apr: furnished\n30+ night stays", color=INK2, fontsize=9.5, ha="left")
ax.set_ylim(0, 16.5)
finish(fig, "fig_seasonality.png", CREDIT + " (reviews 2024-25 as stay proxy; Mar/Jun 2026 same-listing prices)")

# 4) area ranking with 90% CI
R = pd.read_csv(os.path.join(OUT, "area_ranking.csv"))
R['lbl'] = R.local_area + np.where(R.segment.str.startswith('condo'), "  - condo", "  - house") + "  (n=" + R.n.astype(str) + ")"
R = R.sort_values('yield_hybrid')
fig, ax = plt.subplots(figsize=(6.4, 3.4)); y = np.arange(len(R))
cols = [BLUE if a == 'Downtown' and s.startswith('condo') else GREY for a, s in zip(R.local_area, R.segment)]
ax.hlines(y, R.yield_hybrid_ci90_lo * 100, R.yield_hybrid_ci90_hi * 100, color=cols, lw=2.2)
ax.scatter(R.yield_hybrid * 100, y, color=cols, s=46, zorder=3, edgecolor="white", linewidth=1.5)
for yi, v, hi in zip(y, R.yield_hybrid * 100, R.yield_hybrid_ci90_hi * 100): ax.text(hi + 0.08, yi, f"{v:.1f}%", va="center", fontsize=9.5)
ax.set_yticks(y); ax.set_yticklabels(R.lbl, fontsize=9); ax.set_xlabel("Median 2027 net yield, seasonal hybrid (%) - bar = 90% bootstrap CI")
ax.set_xlim(1.8, 5.4)
finish(fig, "fig_area_ranking.png", CREDIT + "; areas with >= 20 comparables")

# 5) portfolio options
P = pd.read_csv(os.path.join(OUT, "portfolio_options.csv"))
short = {"A": "A. 5 detached houses", "B": "B. 12 condos, Downtown", "C": "C. 12 condos, 3 areas", "D": "D. 1 house + 10 condos"}
P['lbl'] = [short[o[0]] for o in P.option]; P = P.iloc[::-1]
fig, ax = plt.subplots(figsize=(6.4, 2.9)); y = np.arange(len(P))
cols = [BLUE if o.startswith("B") else GREY for o in P.option]
ax.hlines(y, P.yield_p10 * 100, P.yield_p90 * 100, color=cols, lw=7, alpha=0.35)
ax.scatter(P.yield_p50 * 100, y, color=cols, s=60, zorder=3, edgecolor="white", linewidth=1.5)
for yi, a, m_, b_ in zip(y, P.yield_p10 * 100, P.yield_p50 * 100, P.yield_p90 * 100):
    ax.text(b_ + 0.1, yi, f"P50 {m_:.1f}%  (P10 {a:.1f} - P90 {b_:.1f})", va="center", fontsize=9)
ax.set_yticks(y); ax.set_yticklabels(P.lbl); ax.set_xlim(1.5, 8.3); ax.set_xlabel("2027 net yield on capital deployed (%), 10,000 simulations")
finish(fig, "fig_portfolio_options.png")

# 6) tornado
T = pd.read_csv(os.path.join(OUT, "sensitivity.csv"))
T['rng'] = (T.high - T.low).abs(); T = T.sort_values('rng')
fig, ax = plt.subplots(figsize=(6.4, 3.2)); y = np.arange(len(T)); base = T.base.iloc[0] * 100
for yi, lo, hi, d in zip(y, T.low * 100, T.high * 100, T.driver):
    col = RED if "FAILED" in d else BLUE
    ax.barh(yi, lo - base, left=base, color=col, height=0.55); ax.barh(yi, hi - base, left=base, color=LGREY if "FAILED" not in d else LGREY, height=0.55)
    ax.text(min(lo, hi) - 0.12, yi, f"{min(lo,hi):.1f}%", ha="right", va="center", fontsize=8.5)
ax.axvline(base, color=INK, lw=1); ax.text(base, len(T) - 0.35, f"Base {base:.1f}%", ha="center", fontsize=9)
ax.set_yticks(y); ax.set_yticklabels(T.driver.str.replace("$", r"\$", regex=False), fontsize=8.5); ax.set_xlabel("Portfolio 2027 net yield (%)"); ax.set_xlim(-2.2, 5.8)
finish(fig, "fig_tornado.png")

# 7) opt-out test
fig, ax = plt.subplots(figsize=(6.4, 2.8))
yrs = [2023, 2024, 2025]; v = [val[f'city_vacancy_{y}'] for y in yrs]
labels = [f"City of Vancouver {y}" for y in yrs] + ["Burnaby 2025", "New Westminster 2025 (grade d)", "Surrey 2025", "Richmond 2025"]
vals = v + [val['vacancy_2025_Burnaby'], val['vacancy_2025_New Westminster'], val['vacancy_2025_Surrey'], val['vacancy_2025_Richmond']]
cols = [BLUE] * 3 + [GREY] * 4; yy = np.arange(len(vals))[::-1]
ax.barh(yy, vals, color=cols, height=0.6); ax.axvline(3, color=RED, lw=1.4, ls=(0, (4, 3)))
ax.text(3.05, len(vals) - 0.6, "3% opt-out test", color=INK2, fontsize=9)
for yi, x in zip(yy, vals): ax.text(x + 0.08, yi, f"{x:.1f}%", va="center", fontsize=9.5)
ax.set_yticks(yy); ax.set_yticklabels(labels, fontsize=9); ax.set_xlabel("Purpose-built rental vacancy rate, October (%)"); ax.set_xlim(0, 7)
finish(fig, "fig_optout.png", "Source: CMHC Rental Market Survey, HMIP table 2.1.31.2, published city (CSD) rates; grade d = use with caution")
print("figures:", sorted(os.listdir(FIG)))
