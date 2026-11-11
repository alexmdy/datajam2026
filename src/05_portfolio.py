"""Few high-value vs many modest: Monte Carlo of 2027 portfolio NOI yield for candidate portfolios.
Each unit's performance = a random comparable from its area/segment pool (idiosyncratic risk),
times market-wide shocks shared by every unit (systematic risk). Hybrid operating model.
Writes outputs/portfolio_options.csv, outputs/portfolio_sims_recommended.csv
"""
import pandas as pd, numpy as np
from common import *

A = load_assumptions(); cap, op, rv = A['capital'], A['operating'], A['revenue']
S = pd.read_csv(os.path.join(OUT, "seasonality_params.csv"), index_col=0)['value']
U = pd.read_csv(os.path.join(PROC, "unit_economics.csv"))
budget = cap['mandate_cad'] * (1 - cap['cash_reserve_pct'])
N_SIM = 10000
rng = np.random.default_rng(2027)

def build(plan):
    """plan = list of (segment, local_area, weight). Fill the budget greedily in proportion to weights."""
    units, spent = [], 0.0
    cost = {(s, a): U[(U.segment == s) & (U.local_area == a)].capital.iloc[0] for s, a, _ in plan}
    targets = {k: w for k, _, w in [((s, a), None, w) for s, a, w in plan]}
    counts = {k: 0 for k in cost}
    while True:
        # next unit: the area furthest below its target share that still fits
        tot = sum(counts.values()) + 1
        cand = sorted(cost, key=lambda k: counts[k] / tot - targets[k])
        placed = False
        for k in cand:
            if spent + cost[k] <= budget:
                counts[k] += 1; spent += cost[k]; units.append(k); placed = True; break
        if not placed: break
    return units, spent

str_fees = op['platform_fee_pct'] + op['management_pct_str'] + op['maintenance_pct']
def simulate(units):
    pools = {k: U[(U.segment == k[0]) & (U.local_area == k[1])] for k in set(units)}
    adr = rng.normal(1.0, 0.07, N_SIM)          # 2027 ADR vs base (demand, competition, residual event premium)
    occ = rng.normal(1.0, 0.08, N_SIM)          # 2027 occupancy vs trailing-12-month estimate
    mtr = rng.uniform(0.70, 1.00, N_SIM)        # furnished monthly rent: lower-quartile ask is the top of the range
    ramp = rng.uniform(0.85, 1.00, N_SIM)       # new listings start with no reviews (May 2027 launch)
    slip = rng.normal(1.0, 0.03, N_SIM)         # price paid vs area estimate
    noi = np.zeros(N_SIM); capital = np.zeros(N_SIM)
    for k in units:
        p = pools[k]; idx = rng.integers(0, len(p), N_SIM); r = p.iloc[idx]
        is_condo = k[0].startswith('condo')
        price = r.price.values * slip
        cap_u = r.capital.values * slip
        str_rev = r.rev_str.values * adr * occ * ramp * S.peak_may_oct_revenue_share
        mtr_rev = rv['mtr_months'] * r.mtr_rent.values * mtr
        fixed = ((op['utilities_internet_condo_month'] if is_condo else op['utilities_internet_house_month']) * 12
                 + (op['strata_fee_condo_month'] * 12 if is_condo else 0)
                 + (op['insurance_condo_year'] if is_condo else op['insurance_house_year'])
                 + price * op['property_tax_rate'] + op['city_str_licence_year'] + op['provincial_registration_year'])
        noi += str_rev * (1 - str_fees) + mtr_rev * (1 - op['management_pct_mtr'] - op['maintenance_pct']) - fixed
        capital += cap_u
    return noi, capital

PLANS = {
  "A. Few high-value: detached houses": [("house_3br+", "Hastings-Sunrise", .5), ("house_3br+", "Kensington-Cedar Cottage", .5)],
  "B. Many modest: condos, Downtown only": [("condo_1-2br", "Downtown", 1.0)],
  "C. Many modest: condos, Downtown + West End + Strathcona": [("condo_1-2br", "Downtown", .70), ("condo_1-2br", "West End", .15), ("condo_1-2br", "Strathcona", .15)],
  "D. Barbell: 1 house + condos": [("house_3br+", "Hastings-Sunrise", .12), ("condo_1-2br", "Downtown", .88)],
}
rows = []
for name, plan in PLANS.items():
    units, spent = build(plan)
    noi, capital = simulate(units)
    y = noi / capital
    mix = pd.Series([f"{a} ({s.split('_')[0]})" for s, a in units]).value_counts().to_dict()
    rows.append(dict(option=name, units=len(units), capital_deployed=round(spent, -3), mix="; ".join(f"{v}x {k}" for k, v in mix.items()),
                     noi_p10=np.percentile(noi, 10), noi_p50=np.median(noi), noi_p90=np.percentile(noi, 90), yield_p10=np.percentile(y, 10), yield_p50=np.median(y), yield_p90=np.percentile(y, 90),
                     spread_p90_p10=np.percentile(y, 90) - np.percentile(y, 10), prob_yield_below_2pct=(y < .02).mean(),
                     yield_on_10m_p50=np.median(noi) / cap['mandate_cad']))
    if name.startswith("C."):
        pd.DataFrame({"noi": noi, "capital": capital, "yield": y}).to_csv(os.path.join(OUT, "portfolio_sims_recommended.csv"), index=False)
R = pd.DataFrame(rows); R.round(4).to_csv(os.path.join(OUT, "portfolio_options.csv"), index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 80)
print(R.round(4).to_string(index=False))
