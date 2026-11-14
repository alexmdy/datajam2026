"""Few high-value vs many modest: Monte Carlo of 2027 portfolio NOI yield for candidate portfolios.
Each unit's performance = a random comparable from its area/segment pool (idiosyncratic risk),
times market-wide shocks shared by every unit (systematic risk). Hybrid operating model.
Then, for the RECOMMENDED portfolio (B, 12 Downtown condos) and on the SAME 10,000 simulated years:
  - the three operating models (nightly all year / seasonal hybrid / long-term rental)   -> slide 4
  - one-at-a-time sensitivity, each case = P50 with one assumption changed              -> slide 6
  - D2 check: the hybrid yield if Inside Airbnb's naive revenue had been used           -> slide 9
  - cost of listing the furnished months on Airbnb (15.5% fee)                           -> slide 12
so every portfolio yield in the pitch comes from one simulation and the base case is always the headline P50.
Writes outputs/portfolio_options.csv, portfolio_sims_recommended.csv, portfolio_operating_models.csv,
sensitivity.csv, validation_furnished_fee.csv
"""
import pandas as pd, numpy as np
from common import *

A = load_assumptions(); cap, op, rv, vt, lt = A['capital'], A['operating'], A['revenue'], A['taxes_if_not_rented_6_months_30day'], A['long_term_rental']
S = pd.read_csv(os.path.join(OUT, "seasonality_params.csv"), index_col=0)['value']
U = pd.read_csv(os.path.join(PROC, "unit_economics.csv"), low_memory=False)
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

def draw(units):
    """Draw the random parts of 10,000 simulated 2027s: shared market shocks + which comparable each unit gets."""
    pools = {k: U[(U.segment == k[0]) & (U.local_area == k[1])] for k in set(units)}
    d = dict(adr=rng.normal(1.0, 0.07, N_SIM),     # 2027 ADR vs base (demand, competition, residual event premium)
             occ=rng.normal(1.0, 0.08, N_SIM),     # 2027 occupancy vs trailing-12-month estimate
             mtr=rng.uniform(0.70, 1.00, N_SIM),   # furnished monthly rent: lower-quartile ask is the top of the range
             ramp=rng.uniform(0.85, 1.00, N_SIM),  # new listings start with no reviews (May 2027 launch)
             slip=rng.normal(1.0, 0.03, N_SIM))    # price paid vs area estimate
    d['picks'] = [(k, pools[k].iloc[rng.integers(0, len(pools[k]), N_SIM)]) for k in units]
    return d

def evaluate(d, model="hybrid", adr_m=1.0, occ_m=1.0, mtr_fixed=None, price_m=1.0, mgmt=None, strata=None,
             naive_revenue=False, furnished_on_airbnb=False, ltr_rent=None):
    """Portfolio NOI and capital in each simulated year, for one operating model / assumption set.
    model: 'hybrid' (the plan), 'nightly' (nightly all year -> counts as vacant -> 3% EHT + 1% SVT), 'ltr' (12-month lease)."""
    fees = str_fees if mgmt is None else op['platform_fee_pct'] + mgmt + op['maintenance_pct']
    strata_m = op['strata_fee_condo_month'] if strata is None else strata
    mtr = d['mtr'] if mtr_fixed is None else mtr_fixed
    mtr_keep = 1 - op['management_pct_mtr'] - op['maintenance_pct'] - (op['platform_fee_pct'] if furnished_on_airbnb else 0)
    noi = np.zeros(N_SIM); capital = np.zeros(N_SIM)
    for k, r in d['picks']:
        is_condo = k[0].startswith('condo')
        price = r.price.values * d['slip'] * price_m
        cap_u = r.capital.values * d['slip'] * price_m
        rev = r.rev_ia_naive.values if naive_revenue else r.rev_str.values
        if model == "ltr":      # unfurnished 12-month lease: tenant pays utilities; no STR licences; landlord insurance
            noi += (12 * ltr_rent * (1 - lt['management_pct'] - op['maintenance_pct']) - strata_m * 12
                    - lt['insurance_condo_year'] - price * op['property_tax_rate'])
            capital += cap_u - cap['furnishing_condo'] * d['slip'] * price_m
            continue
        fixed = ((op['utilities_internet_condo_month'] if is_condo else op['utilities_internet_house_month']) * 12
                 + (strata_m * 12 if is_condo else 0)
                 + (op['insurance_condo_year'] if is_condo else op['insurance_house_year'])
                 + price * op['property_tax_rate'] + op['city_str_licence_year'] + op['provincial_registration_year'])
        if model == "nightly":
            str_rev = rev * d['adr'] * adr_m * d['occ'] * occ_m * d['ramp']
            noi += str_rev * (1 - fees) - fixed - price * (vt['empty_homes_tax_pct'] + vt['svt_pct'])
        else:
            str_rev = rev * d['adr'] * adr_m * d['occ'] * occ_m * d['ramp'] * S.peak_may_oct_revenue_share
            mtr_rev = rv['mtr_months'] * r.mtr_rent.values * mtr
            noi += str_rev * (1 - fees) + mtr_rev * mtr_keep - fixed
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
    d = draw(units)
    noi, capital = evaluate(d)
    y = noi / capital
    mix = pd.Series([f"{a} ({s.split('_')[0]})" for s, a in units]).value_counts().to_dict()
    rows.append(dict(option=name, units=len(units), capital_deployed=round(spent, -3), mix="; ".join(f"{v}x {k}" for k, v in mix.items()),
                     noi_p10=np.percentile(noi, 10), noi_p50=np.median(noi), noi_p90=np.percentile(noi, 90), yield_p10=np.percentile(y, 10), yield_p50=np.median(y), yield_p90=np.percentile(y, 90),
                     spread_p90_p10=np.percentile(y, 90) - np.percentile(y, 10), prob_yield_below_2pct=(y < .02).mean(),
                     yield_on_10m_p50=np.median(noi) / cap['mandate_cad']))
    if name.startswith("B."):           # the recommended portfolio
        DB = d
        pd.DataFrame({"noi": noi, "capital": capital, "yield": y}).to_csv(os.path.join(OUT, "portfolio_sims_recommended.csv"), index=False)
R = pd.DataFrame(rows); R.round(4).to_csv(os.path.join(OUT, "portfolio_options.csv"), index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 80)
print(R.round(4).to_string(index=False))

# ---------- recommended portfolio: operating models, sensitivity, D2, furnished fee (same 10,000 years) ----------
def p50(**kw):
    noi, capital = evaluate(DB, **kw); return np.median(noi / capital)
def pcts(**kw):
    noi, capital = evaluate(DB, **kw); y = noi / capital
    return dict(yield_p10=np.percentile(y, 10), yield_p50=np.median(y), yield_p90=np.percentile(y, 90), noi_p50=np.median(noi))
downtown = U[(U.segment == 'condo_1-2br') & (U.local_area == 'Downtown')]
rent, _ = ltr_rent_condo(downtown)
OM = pd.DataFrame([dict(model="Nightly all year (+3% EHT + 1% SVT)", **pcts(model="nightly")),
                   dict(model="Seasonal hybrid (plan)", **pcts()),
                   dict(model="Long-term rental (12-month lease)", **pcts(model="ltr", ltr_rent=rent))])
OM['ltr_rent_month'] = rent
OM.round(4).to_csv(os.path.join(OUT, "portfolio_operating_models.csv"), index=False); print(OM.round(4).to_string(index=False))

base = p50()
cases = [("Nightly rate (ADR) -10% / +10%", p50(adr_m=.9), p50(adr_m=1.1)),
         ("Occupancy -10% / +10%", p50(occ_m=.9), p50(occ_m=1.1)),
         ("Furnished monthly rent: 70% / 100% of lower-quartile ask", p50(mtr_fixed=.7), p50(mtr_fixed=1.0)),
         ("Purchase price +5% / -5%", p50(price_m=1.05), p50(price_m=.95)),
         ("Management 25% / 15%", p50(mgmt=.25), p50(mgmt=.15)),
         ("Strata fee $650 / $400 per month", p50(strata=650), p50(strata=400)),
         ("6-month 30-day test FAILED (STR all year + EHT + SVT)", p50(model="nightly"), base)]
T = pd.DataFrame(cases, columns=['driver', 'low', 'high']); T['base'] = base
T.round(4).to_csv(os.path.join(OUT, "sensitivity.csv"), index=False); print(T.round(4).to_string(index=False))

extra = pd.Series({"furnished_on_airbnb_yield_cost": base - p50(furnished_on_airbnb=True),
                   "hybrid_yield_naive_revenue_p50": p50(naive_revenue=True)})
extra.round(4).to_csv(os.path.join(OUT, "validation_furnished_fee.csv"), header=["value"]); print(extra.round(4).to_string())
