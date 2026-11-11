"""Exports everything the pitch deck displays into outputs/deck_data.json (the deck builder reads only this)."""
import json, pandas as pd
from common import *
r = lambda f: os.path.join(OUT, f)
def num(v):
    try: return float(v)
    except (TypeError, ValueError): return v
K = {k: num(v) for k, v in pd.read_csv(r("key_numbers.csv")).set_index('key')['value'].items()}
d = {"k": K}
d["waterfall"] = pd.read_csv(r("cleaning_waterfall.csv")).values.tolist()
seg = pd.read_csv(r("segment_summary.csv"), index_col=0)
vs = pd.read_csv(r("validation_summary.csv"), index_col=0)['value']
d["opmodel"] = {"condo": [seg.loc['condo_1-2br', 'yield_str'], seg.loc['condo_1-2br', 'yield_hybrid'], vs['ltr_benchmark_yield']],
                "house": [seg.loc['house_3br+', 'yield_str'], seg.loc['house_3br+', 'yield_hybrid']]}  # no house long-term benchmark computed: condo only
d["season"] = pd.read_csv(r("seasonality_monthly.csv"), index_col=0).revenue_share.tolist()
d["bridge"] = pd.read_csv(r("revenue_bridge.csv"), index_col=0).iloc[:, 0].tolist()
ar = pd.read_csv(r("area_ranking.csv")).sort_values('yield_hybrid', ascending=False)
d["areas"] = ar[['segment', 'local_area', 'n', 'price', 'yield_hybrid', 'yield_hybrid_ci90_lo', 'yield_hybrid_ci90_hi', 'yield_str']].values.tolist()
po = pd.read_csv(r("portfolio_options.csv"))
d["portfolio"] = po[['option', 'units', 'capital_deployed', 'mix', 'yield_p10', 'yield_p50', 'yield_p90', 'prob_yield_below_2pct']].values.tolist()
d["tornado"] = pd.read_csv(r("sensitivity.csv")).values.tolist()
d["vacancy"] = [[f"City of Vancouver {y}", vs[f'city_vacancy_{y}']] for y in (2023, 2024, 2025)] + \
               [[f"{z} 2025", vs[f'vacancy_2025_{z}']] for z in ("North Burnaby", "New Westminster", "Surrey", "Richmond")]
d["value_check"] = pd.read_csv(r("value_validation.csv")).values.tolist()
d["event_check"] = pd.read_csv(r("validation_downtown_event_check.csv")).values.tolist()
d["mtr"] = pd.read_csv(r("mtr_rent_by_bedrooms.csv")).values.tolist()
# Monthly net income, median Downtown 1-2BR condo comparable: nightly (after platform, co-host, maintenance)
# vs a furnished 30+ night stay (after placement fee, maintenance). Furnished rent is flat: no monthly seasonality data.
A = load_assumptions(); op = A['operating']
U = pd.read_csv(os.path.join(PROC, "unit_economics.csv"), low_memory=False)
dt = U[(U.segment == 'condo_1-2br') & (U.local_area == 'Downtown')]
share = pd.read_csv(r("seasonality_monthly.csv"), index_col=0).revenue_share
f_str = 1 - op['platform_fee_pct'] - op['management_pct_str'] - op['maintenance_pct']
f_mtr = 1 - op['management_pct_mtr'] - op['maintenance_pct']
d["month_compare"] = {"nightly": [float((dt.rev_str * share[m] * f_str).median()) for m in range(1, 13)],
                      "furnished": [float((dt.mtr_rent * f_mtr).median())] * 12, "n": int(len(dt))}
json.dump(d, open(r("deck_data.json"), "w"), indent=1, default=float)
print("wrote deck_data.json")
