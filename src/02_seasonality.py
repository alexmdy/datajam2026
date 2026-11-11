"""Seasonal ADR factor: converts mid-June 2026 quoted prices into a 2027 annual-average nightly rate.
1) Demand seasonality = monthly review counts (reviews are a proxy for stays), 2024-2025, nightly entire homes.
2) Same-listing price ratio Mar-2026 vs Jun-2026 (the Dec-2025 snapshot has no prices).
3) FIFA World Cup 2026 (7 matches at BC Place, Jun 13 - Jul 7) overlaps the June quotes: measure the
   match-night premium with each listing's March price as control, and strip it.
4) ADR_m / ADR_Jun = (D_m / D_Jun)^beta, beta calibrated from (2); annual factor = demand-weighted mean.
Writes outputs/seasonality_monthly.csv, outputs/seasonality_params.csv, data/processed/june_quotes.csv
"""
import pandas as pd, numpy as np
from common import *

MATCH = pd.to_datetime(["2026-06-13","2026-06-18","2026-06-21","2026-06-24","2026-06-26","2026-07-02","2026-07-07"])
def quotes(s):
    d = pd.read_csv(ia_path(s, "listings.csv.gz"), usecols=['id','last_scraped','price','price_quote_checkin_date',
            'price_quote_checkout_date','room_type','minimum_nights'])
    d['ci'] = pd.to_datetime(d.price_quote_checkin_date, format="%Y-%m-%d"); d['co'] = pd.to_datetime(d.price_quote_checkout_date, format="%Y-%m-%d")
    d['qn'] = (d.co - d.ci).dt.days; d['lead'] = (d.ci - pd.to_datetime(d.last_scraped, format="%Y-%m-%d")).dt.days
    d['p'] = money(d.price)
    return d
def match_stay(ci, co):
    out = []
    for a, b in zip(ci, co):
        if pd.isna(a): out.append(False); continue
        nights = pd.date_range(a, b - pd.Timedelta(days=1))
        out.append(bool(np.isin(nights, MATCH.union(MATCH - pd.Timedelta(days=1))).any()))
    return np.array(out)

J = quotes("2026-06-15"); J['match_stay'] = match_stay(J.ci, J.co)
J[['id','p','qn','lead','ci','match_stay']].to_csv(os.path.join(PROC, "june_quotes.csv"), index=False)
keep = lambda d: d[(d.qn <= 7) & (d.lead <= 30) & (d.room_type == 'Entire home/apt') & (d.minimum_nights < 30) & d.p.between(40, 3000)]
M = keep(quotes("2026-03-21")).merge(keep(J), on='id', suffixes=('_m', '_j'))
M['lr'] = np.log(M.p_j / M.p_m)
a, b = M.loc[M.match_stay, 'lr'], M.loc[~M.match_stay, 'lr']
match_prem = np.exp(a.mean() - b.mean()) - 1
rng = np.random.default_rng(42)
bs = [rng.choice(a.values, len(a)).mean() - rng.choice(b.values, len(b)).mean() for _ in range(2000)]
lo, hi = np.exp(np.percentile(bs, [2.5, 97.5])) - 1
mar_over_jun = np.exp(-b.mean())          # non-match June stays only
print(f"matched listings {len(M)}; match-night premium {match_prem:.3f} (95% CI {lo:.3f}-{hi:.3f}); Mar/Jun price {mar_over_jun:.3f}")

# demand seasonality from reviews (2024 + 2025 full years)
A = pd.read_csv(os.path.join(PROC, "listings_all.csv"), usecols=['id','room_type','minimum_nights'])
ids = A[(A.room_type == 'Entire home/apt') & (A.minimum_nights < 30)].id
R = pd.read_csv(ia_path(SNAP, "reviews.csv.gz"), usecols=['listing_id','date'])
R['date'] = pd.to_datetime(R.date, format="%Y-%m-%d"); R = R[R.listing_id.isin(ids) & R.date.dt.year.isin([2024, 2025])]
cnt = R.groupby([R.date.dt.year, R.date.dt.month]).size().unstack(0)
share = (cnt / cnt.sum()).mean(axis=1)            # average monthly share across 2024 and 2025
share.index.name = "month"
D_mar = share.loc[[3, 4]].mean()   # March quotes check in late Mar / Apr
D_jun = share.loc[6]
beta = np.log(mar_over_jun) / np.log(D_mar / D_jun)
idx = (share / D_jun) ** beta                      # ADR relative to June (non-match)
annual_factor = float((share * idx).sum())         # occupied-night-weighted mean ADR / June ADR
peak = [5, 6, 7, 8, 9, 10]
peak_rev_share = float((share * idx)[peak].sum() / (share * idx).sum())
print(f"beta {beta:.3f}; annual ADR = {annual_factor:.3f} x June non-match price; May-Oct share of STR revenue {peak_rev_share:.3f}")
mon = pd.DataFrame({"night_share": share, "adr_index_vs_june": idx, "revenue_share": share*idx/(share*idx).sum()})
mon.round(4).to_csv(os.path.join(OUT, "seasonality_monthly.csv"))
print(mon.round(3).to_string())
pd.Series({"matched_listings": len(M), "match_stays": len(a), "nonmatch_stays": len(b),
           "match_night_premium": match_prem, "match_premium_ci_lo": lo, "match_premium_ci_hi": hi,
           "mar_over_jun_price": mar_over_jun, "beta": beta, "annual_adr_factor": annual_factor,
           "peak_may_oct_revenue_share": peak_rev_share}).round(4).to_csv(os.path.join(OUT, "seasonality_params.csv"), header=["value"])
