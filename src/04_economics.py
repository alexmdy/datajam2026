"""2027 unit economics for every comparable listing, under two operating models:
  STR-only : nightly all year -> property counts as 'vacant' -> Empty Homes Tax 3% + SVT 1% of assessed value
  Hybrid   : nightly May-Oct, furnished 30+ night stays Nov-Apr (6 months) -> exempt from EHT and SVT
Return metric: 2027 unlevered net operating yield = NOI / all-in capital (price + PTT + closing + furnishing).
Writes data/processed/unit_economics.csv, outputs/area_ranking.csv, outputs/revenue_bridge.csv
"""
import pandas as pd, numpy as np
from common import *

A = load_assumptions(); cap, op, vt, rv = A['capital'], A['operating'], A['taxes_if_not_rented_6_months_30day'], A['revenue']
S = pd.read_csv(os.path.join(OUT, "seasonality_params.csv"), index_col=0)['value']
C = pd.read_csv(os.path.join(PROC, "comparables.csv"))
Q = pd.read_csv(os.path.join(PROC, "june_quotes.csv"))[['id', 'match_stay']]
C = C.merge(Q, on='id', how='left')
C = C[C.segment.isin(['condo_1-2br', 'house_3br+'])].copy()

# ---- revenue ----
C['price_june_quote'] = C.price_num
C['price_summer'] = np.where(C.match_stay, C.price_num / (1 + S.match_night_premium), C.price_num)   # strip World Cup
C['adr_2027'] = C.price_summer * S.annual_adr_factor                                                 # seasonal average
C['nights'] = C.estimated_occupancy_l365d
C['rev_ia_naive'] = C.price_num * C.nights            # what Inside Airbnb's estimated_revenue_l365d does
C['rev_str'] = C.adr_2027 * C.nights

# furnished monthly rent: lower quartile of Airbnb monthly-stay asks, by bedrooms (city-wide)
L = pd.read_csv(os.path.join(PROC, "listings_all.csv"))
import json
def monthly_ask(raw):
    try:
        for it in json.loads(raw)['quote']['raw_price_line_items']:
            if it['description'].startswith('Average monthly price'): return float(it['amount'])
    except Exception: pass
    return np.nan
M = L[(L.room_type == 'Entire home/apt') & (L.minimum_nights >= 30)].copy()
M['monthly'] = M.price_quote_raw.apply(monthly_ask)
M['br'] = M.bedrooms.fillna(1).clip(1, 4)
mtr = M.groupby('br').monthly.quantile(rv['mtr_rent_quantile'])
mtr_n = M.groupby('br').monthly.count()
pd.DataFrame({'monthly_rent_q': mtr, 'n': mtr_n}).to_csv(os.path.join(OUT, "mtr_rent_by_bedrooms.csv"))
print("MTR monthly rent (lower quartile ask):", mtr.round(0).to_dict())
C['mtr_rent'] = C.bedrooms.fillna(1).clip(1, 4).map(mtr)
C['rev_hybrid'] = C.rev_str * S.peak_may_oct_revenue_share + rv['mtr_months'] * C.mtr_rent

# ---- acquisition ----
V = pd.read_csv(os.path.join(OUT, "acquisition_cost_by_area.csv"))
C = C.merge(V[['local_area', 'segment', 'price_est_mid2026']], on=['local_area', 'segment'], how='left')
def ptt(p):
    t, lo = 0.0, 0.0
    for hi, r in cap['ptt_brackets']:
        if p > lo: t += (min(p, hi) - lo) * r
        lo = hi
    return t
is_condo = C.segment.str.startswith('condo')
C['price'] = C.price_est_mid2026
C['capital'] = C.price + C.price.apply(ptt) + C.price * cap['closing_costs_pct'] + np.where(is_condo, cap['furnishing_condo'], cap['furnishing_house'])

# ---- costs ----
fixed = (np.where(is_condo, op['utilities_internet_condo_month'], op['utilities_internet_house_month']) * 12
         + np.where(is_condo, op['strata_fee_condo_month'] * 12, 0)
         + np.where(is_condo, op['insurance_condo_year'], op['insurance_house_year'])
         + C.price * op['property_tax_rate'])
str_fees = op['platform_fee_pct'] + op['management_pct_str'] + op['maintenance_pct']
C['vacancy_taxes'] = C.price * (vt['empty_homes_tax_pct'] + vt['svt_pct'])
C['noi_str'] = C.rev_str * (1 - str_fees) - fixed - op['city_str_licence_year'] - op['provincial_registration_year'] - C.vacancy_taxes
str_part = C.rev_str * S.peak_may_oct_revenue_share
mtr_part = rv['mtr_months'] * C.mtr_rent
C['noi_hybrid'] = (str_part * (1 - str_fees) + mtr_part * (1 - op['management_pct_mtr'] - op['maintenance_pct'])
                   - fixed - op['city_str_licence_year'] - op['provincial_registration_year'])
C['noi_str_no_vacancy_tax'] = C.noi_str + C.vacancy_taxes
for k in ['noi_str', 'noi_hybrid', 'noi_str_no_vacancy_tax']:
    C['yield_' + k[4:]] = C[k] / C.capital
C.to_csv(os.path.join(PROC, "unit_economics.csv"), index=False)

# ---- area ranking (n >= 20 comparables), bootstrap CI on the median yield ----
rng = np.random.default_rng(7)
def boot(x, B=2000):
    x = x.values; m = [np.median(rng.choice(x, len(x))) for _ in range(B)]
    return np.percentile(m, [5, 95])
rows = []
for (seg, area), g in C.groupby(['segment', 'local_area']):
    if len(g) < 20: continue
    lo, hi = boot(g.yield_hybrid)
    rows.append(dict(segment=seg, local_area=area, n=len(g), price=g.price.iloc[0], capital=g.capital.iloc[0],
                     adr_2027=g.adr_2027.median(), nights=g.nights.median(), rev_str=g.rev_str.median(),
                     rev_hybrid=g.rev_hybrid.median(), yield_str=g.yield_str.median(), yield_hybrid=g.yield_hybrid.median(),
                     yield_hybrid_ci90_lo=lo, yield_hybrid_ci90_hi=hi, yield_no_vacancy_tax=g.yield_str_no_vacancy_tax.median(),
                     share_negative_noi_str=(g.noi_str < 0).mean()))
R = pd.DataFrame(rows).sort_values(['segment', 'yield_hybrid'], ascending=[True, False])
R.round(4).to_csv(os.path.join(OUT, "area_ranking.csv"), index=False)
pd.set_option('display.width', 250)
print(R[['segment','local_area','n','price','adr_2027','nights','rev_str','rev_hybrid','yield_str','yield_hybrid','yield_hybrid_ci90_lo','yield_hybrid_ci90_hi']].round(3).to_string(index=False))

# ---- revenue bridge (median condo comparable): what each correction does ----
c = C[is_condo]
br = pd.Series({"IA-style revenue (June quote x nights)": c.rev_ia_naive.median(),
                "after World Cup premium removed": (c.price_summer * c.nights).median(),
                "after seasonal ADR (2027 base, STR-only)": c.rev_str.median(),
                "hybrid: May-Oct nightly + 6 months furnished": c.rev_hybrid.median()})
br.round(0).to_csv(os.path.join(OUT, "revenue_bridge.csv"), header=["median_annual_revenue"]); print(br.round(0))
seg = C.groupby('segment')[['price','capital','rev_str','rev_hybrid','vacancy_taxes','noi_str','noi_hybrid','yield_str','yield_hybrid','yield_str_no_vacancy_tax']].median()
seg.round(3).to_csv(os.path.join(OUT, "segment_summary.csv")); print(seg.round(3).T)
