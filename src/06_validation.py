"""Validation, robustness and context checks. Writes outputs/validation_*.csv and outputs/sensitivity.csv"""
import pandas as pd, numpy as np
from scipy.stats import spearmanr
from common import *

A = load_assumptions(); op, cap, rv, vt = A['operating'], A['capital'], A['revenue'], A['taxes_if_not_rented_6_months_30day']
S = pd.read_csv(os.path.join(OUT, "seasonality_params.csv"), index_col=0)['value']
U = pd.read_csv(os.path.join(PROC, "unit_economics.csv"))
out = {}

# 1) Occupancy estimate (reviews-based, trailing 12m) vs the forward calendar (unavailable = booked OR blocked)
cal = pd.read_csv(ia_path(SNAP, "calendar.csv.gz"), usecols=['listing_id', 'date', 'available'])
cal['date'] = pd.to_datetime(cal.date, format="%Y-%m-%d")
c90 = cal[cal.date < pd.Timestamp("2026-09-13")].groupby('listing_id').available.apply(lambda s: (s == 'f').mean())
v = U.merge(c90.rename('unavail_90d'), left_on='id', right_index=True)
rho, pv = spearmanr(v.nights, v.unavail_90d)
out['occ_vs_calendar_spearman'] = rho; out['occ_vs_calendar_n'] = len(v)
out['median_est_occupancy_pct'] = (v.nights / 365).median(); out['median_calendar_unavailable_next90d'] = v.unavail_90d.median()
out['share_at_255_night_cap'] = (U.nights >= 255).mean()
out['share_est_occ_below_calendar_upper_bound'] = ((v.nights / 365) <= v.unavail_90d).mean()

# 2a) Split-half stability of the area ranking (areas with n>=20)
areas = U.groupby(['segment', 'local_area']).filter(lambda g: len(g) >= 20)
rng = np.random.default_rng(11); rs = []
for _ in range(300):
    m = rng.random(len(areas)) < .5
    a = areas[m].groupby(['segment', 'local_area']).yield_hybrid.median(); b = areas[~m].groupby(['segment', 'local_area']).yield_hybrid.median()
    j = pd.concat([a, b], axis=1).dropna(); rs.append(spearmanr(j.iloc[:, 0], j.iloc[:, 1])[0])
out['split_half_spearman_median'] = np.median(rs); out['split_half_spearman_p10'] = np.percentile(rs, 10)

# 2b) Is Downtown's lead a World Cup artefact? Re-rank condo areas using each listing's MARCH 2026 price
Mq = pd.read_csv(ia_path("2026-03-21", "listings.csv.gz"), usecols=['id', 'price', 'price_quote_checkin_date', 'price_quote_checkout_date', 'last_scraped'])
Mq['qn'] = (pd.to_datetime(Mq.price_quote_checkout_date) - pd.to_datetime(Mq.price_quote_checkin_date)).dt.days
Mq['p_mar'] = money(Mq.price); Mq = Mq[(Mq.qn <= 7) & Mq.p_mar.between(40, 3000)]
c = U[U.segment == 'condo_1-2br'].merge(Mq[['id', 'p_mar']], on='id')
idx = pd.read_csv(os.path.join(OUT, "seasonality_monthly.csv"), index_col=0)
mar_idx = idx.loc[[3, 4], 'adr_index_vs_june'].mean()
c['rev_str_mar'] = c.p_mar / mar_idx * S.annual_adr_factor * c.nights
k = c.groupby('local_area').filter(lambda g: len(g) >= 15).groupby('local_area')
rob = pd.DataFrame({'n': k.size(), 'rev_str_june_based': k.rev_str.median(), 'rev_str_march_based': k.rev_str_mar.median()})
rob['rank_june'] = rob.rev_str_june_based.rank(ascending=False); rob['rank_march'] = rob.rev_str_march_based.rank(ascending=False)
p = pd.read_csv(os.path.join(PROC, "june_quotes.csv")).merge(Mq[['id', 'p_mar']], on='id')
p = p[(p.qn <= 7) & (p.lead <= 30) & p.p.between(40, 3000)]
p = p.merge(pd.read_csv(os.path.join(PROC, "listings_all.csv"), usecols=['id', 'local_area', 'room_type']), on='id')
p = p[p.room_type == 'Entire home/apt']; p['jm'] = p.p / p.p_mar
rob['june_over_march_price'] = p.groupby('local_area').jm.median()
rob.sort_values('rank_june').round(3).to_csv(os.path.join(OUT, "validation_downtown_event_check.csv"))
print(rob.sort_values('rank_june').round(2).to_string())

# 2c) price-outlier threshold sensitivity on the median Downtown condo STR revenue
C0 = pd.read_csv(os.path.join(PROC, "listings_all.csv"))
base = U[(U.segment == 'condo_1-2br') & (U.local_area == 'Downtown')]
out['downtown_condo_median_rev_str'] = base.rev_str.median()

# 3) Long-term-rental benchmark for the same Downtown condo (CMHC Oct-2025 average rent, Downtown zone)
cm = pd.read_csv(os.path.join(RAW, "cmhc", "cmhc_rms_vancouver_cma_by_zone_oct2025.csv")).set_index('zone')
rent = float(cm.loc['Downtown', 'avg_rent']); price = base.price.iloc[0]; capital_ltr = base.capital.iloc[0] - cap['furnishing_condo']
noi_ltr = 12 * rent * (1 - 0.08 - op['maintenance_pct']) - op['strata_fee_condo_month'] * 12 - 600 - price * op['property_tax_rate']
out['ltr_benchmark_rent_month'] = rent; out['ltr_benchmark_yield'] = noi_ltr / capital_ltr
out['downtown_hybrid_median_yield'] = base.yield_hybrid.median(); out['downtown_str_only_median_yield'] = base.yield_str.median()

# 4) Compliance estimate by local area (ESTIMATE: listings and licences are not counted on the same basis)
lic = pd.read_csv(os.path.join(RAW, "vancouver_opendata", "str_business_licences_2024_2026.csv"))
lic.columns = [x.lstrip('﻿') for x in lic.columns]
li = lic[(lic.folderyear.astype(str) == '26') & (lic.status == 'Issued')].groupby('localarea').size()
act = C0[(C0.minimum_nights < 30) & (C0.last_review >= '2025-06-15')]
comp = pd.DataFrame({'active_nightly_listings': act.groupby('local_area').size(),
                     'share_showing_city_licence': act.groupby('local_area').apply(lambda d: (d.lic_cat == 'city_licence').mean()),
                     'issued_2026_licences': li}).fillna(0)
comp['licences_per_listing'] = comp.issued_2026_licences / comp.active_nightly_listings
comp.round(3).to_csv(os.path.join(OUT, "validation_compliance_estimate.csv"))
out['citywide_share_active_nightly_showing_licence'] = (act.lic_cat == 'city_licence').mean()
out['citywide_issued_2026_licences'] = int(li.sum()); out['citywide_active_nightly_listings'] = len(act)

# 5) Opt-out test: City of Vancouver = CMHC zones 1-10, unit-weighted vacancy
city = ["West End/Stanley Park", "English Bay", "Downtown", "South Granville/Oak", "Kitsilano/Point Grey",
        "Westside/Kerrisdale", "Marpole", "Mount Pleasant/Renfrew Heights", "East Hastings", "Southeast Vancouver"]
for y in [2023, 2024, 2025]:
    t = pd.read_csv(os.path.join(RAW, "cmhc", f"cmhc_rms_vancouver_cma_by_zone_oct{y}.csv")).set_index('zone')
    t = t.loc[city]; t['v'] = pd.to_numeric(t.vacancy_rate_pct, errors='coerce'); t = t.dropna(subset=['v'])
    out[f'city_vacancy_{y}'] = (t.v * t.units).sum() / t.units.sum()
    if y == 2025:
        oth = pd.read_csv(os.path.join(RAW, "cmhc", f"cmhc_rms_vancouver_cma_by_zone_oct{y}.csv")).set_index('zone')
        for z in ["North Burnaby", "New Westminster", "Surrey", "Richmond"]: out[f'vacancy_2025_{z}'] = float(oth.loc[z, 'vacancy_rate_pct'])
pd.Series(out).round(4).to_csv(os.path.join(OUT, "validation_summary.csv"), header=['value'])
print(pd.Series(out).round(4).to_string())

# 6) One-at-a-time sensitivity, recommended portfolio (12 Downtown 1-2BR condos), expected (mean) NOI yield
D = base.copy(); n_units = 12
str_fees = op['platform_fee_pct'] + op['management_pct_str'] + op['maintenance_pct']
def port_yield(adr=1, occ=1, mtr=0.85, price=1, mgmt=op['management_pct_str'], strata=op['strata_fee_condo_month'], fail6=False):
    pr = D.price * price; capu = D.capital * price
    str_rev = D.rev_str * adr * occ * 0.925 * (1 if fail6 else S.peak_may_oct_revenue_share)   # 0.925 = mean ramp-up factor, as in 05
    mtr_rev = 0 if fail6 else rv['mtr_months'] * D.mtr_rent * mtr
    fees = op['platform_fee_pct'] + mgmt + op['maintenance_pct']
    fixed = op['utilities_internet_condo_month'] * 12 + strata * 12 + op['insurance_condo_year'] + pr * op['property_tax_rate'] + op['city_str_licence_year'] + op['provincial_registration_year']
    vac = pr * (vt['empty_homes_tax_pct'] + vt['svt_pct']) if fail6 else 0
    noi = str_rev * (1 - fees) + mtr_rev * (1 - op['management_pct_mtr'] - op['maintenance_pct']) - fixed - vac
    return noi.mean() * n_units / (capu.mean() * n_units)
b = port_yield()
cases = [("Nightly rate (ADR) -10% / +10%", port_yield(adr=.9), port_yield(adr=1.1)),
         ("Occupancy -10% / +10%", port_yield(occ=.9), port_yield(occ=1.1)),
         ("Furnished monthly rent: 70% / 100% of lower-quartile ask", port_yield(mtr=.7), port_yield(mtr=1.0)),
         ("Purchase price +5% / -5%", port_yield(price=1.05), port_yield(price=.95)),
         ("Management 25% / 15%", port_yield(mgmt=.25), port_yield(mgmt=.15)),
         ("Strata fee $650 / $400 per month", port_yield(strata=650), port_yield(strata=400)),
         ("6-month 30-day test FAILED (STR all year + EHT + SVT)", port_yield(fail6=True), b)]
T = pd.DataFrame(cases, columns=['driver', 'low', 'high']); T['base'] = b
T.round(4).to_csv(os.path.join(OUT, "sensitivity.csv"), index=False); print(T.round(4).to_string(index=False))

# 7) Downtown comparables by bedrooms (mix guidance)
bd = base.groupby(base.bedrooms.fillna(1).clip(0, 2)).agg(n=('id', 'size'), rev_str=('rev_str', 'median'), adr=('adr_2027', 'median'), nights=('nights', 'median'))
bd.round(0).to_csv(os.path.join(OUT, "downtown_by_bedrooms.csv")); print(bd.round(0))
